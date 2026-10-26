"""Haberci toplayıcı: RSS/Atom akışlarını ve PubMed'i okur, süzer, kümeler,
veri/<tarih>-<donem>.json dosyasına yazar. Yalnızca Python standart kütüphanesi kullanır.

Kullanım:
    python topla.py                 # dönem saate göre seçilir (sabah/aksam)
    python topla.py --donem sabah
"""
import argparse
import html
import json
import re
import sys
import tomllib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent
VERI = KOK / "veri"
TR_SAAT = timezone(timedelta(hours=3))  # Türkiye 2016'dan beri sabit UTC+3
UA = "Mozilla/5.0 (Haberci kisisel haber derleyici)"
KATEGORILER = ["gundem_tr", "dunya", "ekonomi", "bilim_teknoloji", "saglik", "spor", "kultur"]


def indir(url, zaman_asimi=20):
    istek = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
        return yanit.read()


def yerel_ad(etiket):
    return etiket.rsplit("}", 1)[-1].lower()


def cocuk_metin(el, *adlar):
    """Adların verilen sırasıyla ilk dolu alt öğeyi döndürür (ör. önce link, yoksa guid)."""
    for ad in adlar:
        for c in el:
            if yerel_ad(c.tag) == ad:
                if (c.text or "").strip():
                    return c.text.strip()
                if ad == "link" and c.get("href"):
                    return c.get("href")
    return ""


def atom_link(el):
    for c in el:
        if yerel_ad(c.tag) == "link" and c.get("rel", "alternate") == "alternate" and c.get("href"):
            return c.get("href")
    return cocuk_metin(el, "link")


def tarih_coz(metin):
    if not metin:
        return None
    try:
        t = parsedate_to_datetime(metin)
    except (TypeError, ValueError):
        try:
            t = datetime.fromisoformat(metin.replace("Z", "+00:00"))
        except ValueError:
            return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc)


def temizle(metin, sinir=200):
    metin = re.sub(r"<[^>]+>", " ", metin or "")
    metin = re.sub(r"\s+", " ", html.unescape(metin)).strip()
    return metin if len(metin) <= sinir else metin[:sinir].rsplit(" ", 1)[0] + "…"


def akis_coz(veri):
    kok = ET.fromstring(veri)
    ogeler = [el for el in kok.iter() if yerel_ad(el.tag) in ("item", "entry")]
    sonuc = []
    for el in ogeler:
        atom = yerel_ad(el.tag) == "entry"
        sonuc.append({
            "baslik": temizle(cocuk_metin(el, "title"), 300),
            "link": atom_link(el) if atom else cocuk_metin(el, "link", "guid"),
            "ozet": temizle(cocuk_metin(el, "description", "summary", "content", "encoded")),
            "tarih": tarih_coz(cocuk_metin(el, "pubdate", "published", "updated", "date")),
        })
    return sonuc


def yasakli(oge, ayar):
    url = oge["link"].lower()
    baslik = oge["baslik"].lower()
    return any(p in url for p in ayar["url_yasak"]) or any(k in baslik for k in ayar["baslik_yasak"])


def kaynak_topla(kaynak, esik, ayar, en_fazla):
    try:
        ogeler = akis_coz(indir(kaynak["url"]))
    except Exception as hata:  # tek kaynak düşerse diğerleri devam etsin
        return kaynak, [], f"HATA: {type(hata).__name__}: {hata}"[:200]
    secilen = []
    for o in ogeler:
        if not o["baslik"] or not o["link"]:
            continue
        if o["tarih"] and o["tarih"] < esik:
            continue
        if yasakli(o, ayar):
            continue
        # Google Haberler başlıkları " - Kaynak Adı" ile biter
        if "news.google.com" in kaynak["url"]:
            o["baslik"] = re.sub(r"\s+-\s+[^-]+$", "", o["baslik"])
            o["ozet"] = ""
        secilen.append(o)
        if len(secilen) >= kaynak.get("en_fazla", en_fazla):
            break
    return kaynak, secilen, len(secilen)


DURAK = set("""ve ile bir bu da de için ile mi mı en çok daha olan oldu gibi ama the a an of to in on
for and or is are was were with at by from as after over says say new its it that this""".split())


def kelimeler(baslik):
    # Türkçe ekler yüzünden kelimenin ilk 5 harfi kök yerine kullanılır
    return {k[:5] for k in re.findall(r"\w+", baslik.lower()) if len(k) > 2 and k not in DURAK}


def ayni_olay(a, b):
    ortak = len(a & b)
    return ortak >= 3 and ortak / min(len(a), len(b)) >= 0.5


def kumele(haberler, sinir):
    """Başlık kelimeleri yeterince örtüşen haberleri aynı olay sayar (aynı dil içinde)."""
    kumeler = []
    for h in sorted(haberler, key=lambda x: x["katman"]):
        k = kelimeler(h["baslik"])
        for kume in kumeler:
            if kume["dil"] == h["dil"] and k and ayni_olay(k, kume["_k"]):
                kume["diger_kaynaklar"].append({"kaynak": h["kaynak"], "link": h["link"]})
                break
        else:
            kumeler.append({**h, "diger_kaynaklar": [], "_k": k})
    for kume in kumeler:
        del kume["_k"]
        kume["kaynak_sayisi"] = 1 + len({d["kaynak"] for d in kume["diger_kaynaklar"]} - {kume["kaynak"]})
    return sorted(kumeler, key=lambda x: (-x["kaynak_sayisi"], x["katman"]))[:sinir]


def pubmed_topla(ayar):
    gorulen_dosya = VERI / "pubmed_gorulen.json"
    gorulen = set(json.loads(gorulen_dosya.read_text("utf-8"))) if gorulen_dosya.exists() else set()
    taban = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    sorgu = " ".join(ayar["sorgu"].split())
    parametre = urllib.parse.urlencode({
        "db": "pubmed", "term": sorgu, "reldate": ayar["geriye_gun"], "datetype": "edat",
        "retmax": ayar["aday_sayisi"] * 2, "retmode": "json", "sort": "relevance", "tool": "haberci",
    })
    idler = json.loads(indir(taban + "esearch.fcgi?" + parametre))["esearchresult"]["idlist"]
    idler = [i for i in idler if i not in gorulen][: ayar["aday_sayisi"]]
    if not idler:
        return []
    xml = indir(taban + "efetch.fcgi?" + urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(idler), "retmode": "xml", "tool": "haberci"}), 40)
    makaleler = []
    for m in ET.fromstring(xml).iter("PubmedArticle"):
        pmid = m.findtext(".//PMID")
        ozet = " ".join(
            ((a.get("Label") + ": ") if a.get("Label") else "") + "".join(a.itertext())
            for a in m.iter("AbstractText"))
        yazarlar = [f"{a.findtext('LastName')} {a.findtext('Initials') or ''}".strip()
                    for a in m.iter("Author") if a.findtext("LastName")]
        doi = next((e.text for e in m.iter("ArticleId") if e.get("IdType") == "doi"), None)
        makaleler.append({
            "pmid": pmid,
            "baslik": "".join(m.find(".//ArticleTitle").itertext()).strip(),
            "dergi": m.findtext(".//Journal/Title"),
            "yazarlar": yazarlar[:3] + (["et al."] if len(yazarlar) > 3 else []),
            "tur": [t.text for t in m.iter("PublicationType")],
            "ozet": ozet.strip(),
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "doi": f"https://doi.org/{doi}" if doi else None,
        })
    return makaleler


def pubmed_isaretle(pmidler):
    """Bültende kullanılan makaleleri bir daha gelmesin diye kaydeder."""
    dosya = VERI / "pubmed_gorulen.json"
    gorulen = set(json.loads(dosya.read_text("utf-8"))) if dosya.exists() else set()
    gorulen.update(pmidler)
    dosya.write_text(json.dumps(sorted(gorulen)), "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donem", choices=["sabah", "aksam"])
    ap.add_argument("--pubmed-isaretle", nargs="*", metavar="PMID",
                    help="bültende kullanılan PMID'leri kaydet ve çık")
    arg = ap.parse_args()
    VERI.mkdir(exist_ok=True)
    if arg.pubmed_isaretle is not None:
        pubmed_isaretle(arg.pubmed_isaretle)
        return

    simdi = datetime.now(TR_SAAT)
    donem = arg.donem or ("sabah" if simdi.hour < 13 else "aksam")
    kaynaklar = tomllib.loads((KOK / "kaynaklar.toml").read_text("utf-8"))["kaynak"]
    ayar = tomllib.loads((KOK / "ayarlar.toml").read_text("utf-8"))
    esik = datetime.now(timezone.utc) - timedelta(hours=ayar["toplama"]["geriye_saat"])

    aktif = [k for k in kaynaklar if k.get("aktif", True)]
    with ThreadPoolExecutor(max_workers=12) as havuz:
        sonuclar = list(havuz.map(
            lambda k: kaynak_topla(k, esik, ayar["filtre"], ayar["toplama"]["kaynak_basina_en_fazla"]),
            aktif))

    durum, kategoriye = {}, {k: [] for k in KATEGORILER}
    for kaynak, ogeler, bilgi in sonuclar:
        durum[kaynak["ad"]] = bilgi
        for o in ogeler:
            kategoriye[kaynak["kategori"]].append({
                "baslik": o["baslik"], "ozet": o["ozet"], "link": o["link"],
                "kaynak": kaynak["ad"], "katman": kaynak["katman"], "dil": kaynak["dil"],
                "tarih": o["tarih"].astimezone(TR_SAAT).strftime("%d.%m %H:%M") if o["tarih"] else None,
            })

    try:
        pubmed = pubmed_topla(ayar["pubmed"])
    except Exception as hata:
        pubmed, durum["PubMed"] = [], f"HATA: {hata}"
    else:
        durum["PubMed"] = len(pubmed)

    cikti = {
        "tarih": simdi.strftime("%Y-%m-%d"),
        "donem": donem,
        "olusturma": simdi.isoformat(timespec="minutes"),
        "kaynak_durumu": durum,
        "haberler": {k: kumele(v, ayar["toplama"]["kategori_sinir"].get(k, 30))
                     for k, v in kategoriye.items()},
        "pubmed_adaylari": pubmed,
        "pubmed_secilecek": ayar["pubmed"]["secilecek"],
    }
    dosya = VERI / f"{cikti['tarih']}-{donem}.json"
    dosya.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), "utf-8")

    hatali = [ad for ad, b in durum.items() if isinstance(b, str)]
    toplam = sum(len(v) for v in cikti["haberler"].values())
    print(f"{dosya.name}: {toplam} haber kümesi, {len(pubmed)} PubMed adayı, "
          f"{len(aktif) - len(hatali)}/{len(aktif)} kaynak çalıştı")
    for ad in hatali:
        print(f"  ! {ad}: {durum[ad]}", file=sys.stderr)


if __name__ == "__main__":
    main()
