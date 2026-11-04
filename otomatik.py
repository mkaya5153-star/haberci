"""Haberci - yapay zekâsız otomatik bülten üretici.

topla.py'nin topladığı veriden bülten JSON'unu kurallarla kendisi hazırlar,
yabancı başlıkları ve PubMed özetlerini ücretsiz çeviri ile Türkçeye çevirir,
sonra yayinla.py ile docs/ içine HTML yazar. Claude ya da başka bir yapay zekâ gerekmez.

Kullanım:
    python otomatik.py                 # topla + bülten hazırla + yayınla (dönem saate göre)
    python otomatik.py --donem aksam
    python otomatik.py --veri-hazir    # topla.py'yi atla, bugünkü veri/ dosyasını kullan

Git işlemleri (commit/push) bu dosyada yok: calistir.bat ya da GitHub Actions yapar.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from topla import TR_SAAT, indir, kelimeler

KOK = Path(__file__).resolve().parent

# Bölüm başına en fazla haber (GOREV.md'deki aralıkların üst değerleri)
BOLUM_SAYISI = {"gundem_tr": 7, "dunya": 7, "ekonomi": 5, "bilim_teknoloji": 5,
                "saglik": 3, "spor": 3, "kultur": 2}
BOLUM_AD = {"gundem_tr": "Türkiye", "dunya": "Dünya", "ekonomi": "Ekonomi & Piyasalar",
            "bilim_teknoloji": "Bilim, Teknoloji & Yapay Zekâ", "saglik": "Sağlık",
            "spor": "Spor", "kultur": "Kültür & Sanat"}
ONE_CIKAN_KAYNAK = ["gundem_tr", "dunya", "ekonomi"]
ONE_CIKAN_SAYISI = 5
EN_AZ_HABER = 20          # bundan az haber toplandıysa (ağ sorunu) bülten yayınlanmaz
MAKALE_TUR_SIRASI = ["randomized controlled trial", "meta-analysis", "systematic review",
                     "clinical trial", "multicenter study", "cohort", "review"]
MAKALE_YASAK_TUR = {"comment", "editorial", "letter", "news", "published erratum", "retraction of publication"}

cevirilemeyen = 0


def cevir(metin):
    """Ücretsiz Google Translate uç noktası (anahtarsız, resmî olmayan). Hata olursa metni olduğu gibi döner."""
    global cevirilemeyen
    if not metin:
        return metin
    try:
        url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=tr&dt=t&q="
               + urllib.parse.quote(metin))
        parcalar = json.loads(indir(url, 20))[0]
        sonuc = "".join(p[0] for p in parcalar if p and p[0])
        return sonuc or metin
    except Exception:
        cevirilemeyen += 1
        return metin


def kaynaklar_of(h):
    gorulen, liste = set(), []
    for ad, link in [(h["kaynak"], h["link"])] + [(d["kaynak"], d["link"]) for d in h["diger_kaynaklar"]]:
        if ad in gorulen:
            continue
        gorulen.add(ad)
        liste.append({"ad": ad, "link": link})
    return liste[:4]


def sirala(kumeler):
    # çok kaynakta geçen önce, sonra güvenilirlik katmanı (1 en güvenilir)
    return sorted(kumeler, key=lambda h: (-h["kaynak_sayisi"], h["katman"]))


def haber_ham(h):
    return {"baslik": h["baslik"], "ozet": h["ozet"] if h["ozet"] != h["baslik"] else "",
            "etiket": "teyitli" if h["kaynak_sayisi"] >= 2 else "tek kaynak",
            "kaynaklar": kaynaklar_of(h), "_dil": h["dil"]}


def haberleri_cevir(haberler):
    """Yabancı dildeki başlık ve özetleri paralel olarak Türkçeye çevirir."""
    isler = []
    for h in haberler:
        if h["_dil"] != "tr":
            isler.append((h, "baslik"))
            if h["ozet"]:
                isler.append((h, "ozet"))
    with ThreadPoolExecutor(max_workers=6) as havuz:
        sonuclar = list(havuz.map(lambda i: cevir(i[0][i[1]]), isler))
    for (h, alan), metin in zip(isler, sonuclar):
        h[alan] = metin
    for h in haberler:
        h.pop("_dil", None)
    return haberler


def makale_sec(adaylar, adet):
    def puan(m):
        turler = {t.lower() for t in m["tur"]}
        if turler & MAKALE_YASAK_TUR or len(m["ozet"]) < 250 or "Formula: see text" in m["ozet"]:
            return None  # özetsiz, çok kısa ya da biçimi bozuk (ör. ACP Journal Club) kayıtları atla
        for i, ad in enumerate(MAKALE_TUR_SIRASI):
            if any(ad in t for t in turler):
                return i
        return len(MAKALE_TUR_SIRASI)
    uygun = [(puan(m), i, m) for i, m in enumerate(adaylar) if puan(m) is not None]
    return [m for _, _, m in sorted(uygun, key=lambda x: (x[0], x[1]))[:adet]]


def kisalt(metin, sinir=700):
    if len(metin) <= sinir:
        return metin
    kesik = metin[:sinir]
    nokta = kesik.rfind(". ")
    return (kesik[:nokta + 1] if nokta > sinir * 0.5 else kesik.rsplit(" ", 1)[0] + "…")


def makaleleri_hazirla(secilen):
    def hazirla(m):
        ozet_en = kisalt(m["ozet"])
        turler = [t for t in m["tur"] if t.lower() not in ("journal article", "research support, non-u.s. gov't")]
        return {"pmid": m["pmid"], "baslik_en": m["baslik"], "baslik_tr": cevir(m["baslik"]),
                "dergi": m["dergi"], "yazarlar": m["yazarlar"], "tur": ", ".join(turler[:2]),
                "ozet_en": ozet_en, "ozet_tr": cevir(ozet_en), "neden_onemli": "",
                "link": m["link"], "doi": m["doi"] or ""}
    with ThreadPoolExecutor(max_workers=3) as havuz:
        return list(havuz.map(hazirla, secilen))


def ayni_konu(a, b):
    """Türkçeye çevrilmiş iki başlık aynı olayı anlatıyor mu (farklı dillerdeki kaynakları birleştirmek için)."""
    ka, kb = kelimeler(a["baslik"]), kelimeler(b["baslik"])
    ortak = len(ka & kb)
    return ortak >= 3 or (ortak >= 2 and ortak / max(1, min(len(ka), len(kb))) >= 0.6)


def birlestir(hedef, ek):
    var = {k["ad"] for k in hedef["kaynaklar"]}
    hedef["kaynaklar"] += [k for k in ek["kaynaklar"] if k["ad"] not in var]
    hedef["kaynaklar"] = hedef["kaynaklar"][:5]
    hedef["etiket"] = "teyitli" if len(hedef["kaynaklar"]) >= 2 else "tek kaynak"


def bulten_olustur(veri):
    haberler = veri["haberler"]
    # Her grup için adayları seç (fazladan al: tekrarlar elenince yeterli haber kalsın)
    havuz = sirala([h for k in ONE_CIKAN_KAYNAK for h in haberler.get(k, [])])
    gruplar = [("one", ONE_CIKAN_SAYISI, [haber_ham(h) for h in havuz[:ONE_CIKAN_SAYISI * 4]])]
    gorulen_link = {h["link"] for h in havuz[:ONE_CIKAN_SAYISI * 4]}
    for kat, adet in BOLUM_SAYISI.items():
        aday = [h for h in sirala(haberler.get(kat, [])) if h["link"] not in gorulen_link][:adet * 3]
        gruplar.append((kat, adet, [haber_ham(h) for h in aday]))
    for _, _, liste in gruplar:
        haberleri_cevir(liste)

    # Tekrar eleme: aynı olayı anlatanları ilk geçtiği yerde birleştir, sonra grup sınırına kes
    kabul = []
    sonuc = {}
    for kimlik, adet, liste in gruplar:
        secilen = []
        for h in liste:
            es = next((k for k in kabul if ayni_konu(k, h)), None)
            if es is not None:
                birlestir(es, h)
            elif len(secilen) < adet:
                secilen.append(h)
                kabul.append(h)
        sonuc[kimlik] = secilen

    one_ham = sonuc["one"]
    for h in one_ham:
        h["neden_onemli"] = ""
    bolumler = [{"id": k, "ad": BOLUM_AD[k], "haberler": sonuc[k]} for k in BOLUM_SAYISI if sonuc[k]]

    kaynak_sayisi = sum(1 for d in veri["kaynak_durumu"].values() if not isinstance(d, str))
    toplam = len(veri["kaynak_durumu"])
    giris = (f"Bu bülten yapay zekâ kullanılmadan, {kaynak_sayisi}/{toplam} kaynaktan otomatik derlendi. "
             "Haberler kaç bağımsız kaynakta geçtiğine göre sıralanır; yabancı kaynaklı başlıklar makine çevirisidir, "
             "ayrıntı için kaynak bağlantısına gidin.")

    makaleler = makaleleri_hazirla(makale_sec(veri["pubmed_adaylari"], veri["pubmed_secilecek"]))
    return {"tarih": veri["tarih"], "donem": veri["donem"], "giris": giris,
            "one_cikanlar": one_ham, "bolumler": bolumler, "farkli_bakislar": [], "makaleler": makaleler}


def calistir(komut):
    print("$", " ".join(komut))
    sonuc = subprocess.run([sys.executable, *komut], cwd=KOK)
    if sonuc.returncode != 0:
        sys.exit(f"Komut başarısız oldu: {' '.join(komut)}")


def main():
    for akis in (sys.stdout, sys.stderr):
        akis.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--donem", choices=["sabah", "aksam"])
    ap.add_argument("--veri-hazir", action="store_true", help="topla.py'yi çalıştırma")
    arg = ap.parse_args()

    simdi = datetime.now(TR_SAAT)
    donem = arg.donem or ("sabah" if simdi.hour < 13 else "aksam")
    if not arg.veri_hazir:
        calistir(["topla.py", "--donem", donem])
    veri_yolu = KOK / "veri" / f"{simdi.strftime('%Y-%m-%d')}-{donem}.json"
    veri = json.loads(veri_yolu.read_text("utf-8"))

    toplam = sum(len(v) for v in veri["haberler"].values())
    if toplam < EN_AZ_HABER:
        sys.exit(f"Yalnızca {toplam} haber toplanabildi (en az {EN_AZ_HABER} gerekli). "
                 "İnternet bağlantısını kontrol edin; bülten yayınlanmadı.")

    bulten = bulten_olustur(veri)
    (KOK / "bulten").mkdir(exist_ok=True)
    hedef = KOK / "bulten" / f"{veri['tarih']}-{donem}.json"
    hedef.write_text(json.dumps(bulten, ensure_ascii=False, indent=1), "utf-8")
    if cevirilemeyen:
        print(f"Uyarı: {cevirilemeyen} metin çevrilemedi, özgün dilinde bırakıldı.")
    calistir(["yayinla.py", str(hedef)])


if __name__ == "__main__":
    main()
