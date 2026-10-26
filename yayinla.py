"""Bülten JSON'unu HTML sayfaya çevirir, docs/index.html arşivini günceller
ve kullanılan PubMed makalelerini bir daha gelmesin diye işaretler.

Kullanım:
    python yayinla.py bulten/2026-10-27-sabah.json
"""
import json
import sys
from datetime import date
from html import escape
from pathlib import Path

from topla import pubmed_isaretle

KOK = Path(__file__).resolve().parent
DOCS = KOK / "docs"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
         "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
DONEM_AD = {"sabah": "Sabah Bülteni", "aksam": "Akşam Bülteni"}

CSS = """
:root{--bg:#f7f5f0;--kart:#fff;--yazi:#1d1d1b;--soluk:#6b6862;--cizgi:#e4e0d6;--vurgu:#b3261e;
--teyit:#1f6f43;--teyit-bg:#e3f1e8;--tek:#8a5a00;--tek-bg:#f8edd5;--link:#1a4f8b}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--kart:#1e1e1c;--yazi:#ecebe6;--soluk:#a19e96;
--cizgi:#34332f;--vurgu:#f08077;--teyit:#7fd3a0;--teyit-bg:#1c3326;--tek:#e8b85c;--tek-bg:#3a2e14;--link:#8ab8f0}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--yazi);font:17px/1.6 Georgia,"Times New Roman",serif}
a{color:var(--link)}
.sayfa{max-width:860px;margin:0 auto;padding:24px 16px 64px}
header.ust{border-bottom:3px double var(--yazi);padding-bottom:12px;margin-bottom:24px;text-align:center}
.logo{font-size:44px;font-weight:700;letter-spacing:-1px;margin:0}
.logo a{color:inherit;text-decoration:none}
.tarih{font:600 13px/1.4 system-ui,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:var(--soluk)}
.giris{font-size:19px;font-style:italic;border-left:3px solid var(--vurgu);padding-left:16px;margin:0 0 32px}
nav.icindekiler{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 32px;font:14px system-ui,sans-serif}
nav.icindekiler a{border:1px solid var(--cizgi);border-radius:999px;padding:4px 12px;text-decoration:none;color:var(--yazi);background:var(--kart)}
h2{font-size:26px;margin:40px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--cizgi)}
h2 small{font:600 12px system-ui,sans-serif;color:var(--soluk);letter-spacing:.1em;text-transform:uppercase;margin-left:8px}
article{background:var(--kart);border:1px solid var(--cizgi);border-radius:10px;padding:16px 18px;margin:12px 0}
article h3{margin:0 0 6px;font-size:20px;line-height:1.3}
.one article{border-left:4px solid var(--vurgu)}
.one article h3{font-size:22px}
article p{margin:6px 0}
.neden{font-size:15px;color:var(--soluk)}
.neden b{color:var(--yazi)}
.alt{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin-top:10px;font:13px/1.4 system-ui,sans-serif}
.etiket{border-radius:4px;padding:2px 8px;font-weight:600}
.etiket.teyitli{color:var(--teyit);background:var(--teyit-bg)}
.etiket.tek{color:var(--tek);background:var(--tek-bg)}
.kaynaklar a{margin-right:10px;white-space:nowrap}
.makale .meta{font:13px system-ui,sans-serif;color:var(--soluk);margin-bottom:8px}
.makale h3 .tr{display:block;font-size:16px;font-weight:400;color:var(--soluk);margin-top:4px}
.diller{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px}
.diller div{font-size:15px}
.diller h4{margin:0 0 4px;font:600 11px system-ui,sans-serif;letter-spacing:.12em;color:var(--soluk)}
@media (max-width:640px){.diller{grid-template-columns:1fr}.logo{font-size:34px}}
footer{margin-top:48px;font:13px system-ui,sans-serif;color:var(--soluk);text-align:center}
ul.arsiv{list-style:none;padding:0}
ul.arsiv li{background:var(--kart);border:1px solid var(--cizgi);border-radius:10px;margin:8px 0}
ul.arsiv a{display:flex;justify-content:space-between;padding:12px 16px;text-decoration:none;color:var(--yazi)}
ul.arsiv span{color:var(--soluk);font:14px system-ui,sans-serif}
"""


def e(metin):
    return escape(str(metin or ""))


def guvenli_link(url):
    url = str(url or "")
    return escape(url) if url.startswith(("https://", "http://")) else "#"


def tarih_yazi(iso):
    g = date.fromisoformat(iso)
    return f"{g.day} {AYLAR[g.month - 1]} {g.year}, {GUNLER[g.weekday()]}"


def iskelet(baslik, govde):
    return f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(baslik)}</title><style>{CSS}</style></head>
<body><div class="sayfa">
<header class="ust"><p class="logo"><a href="index.html">Haberci</a></p>
{govde}
<footer>Haberci · Kişisel haber derlemesi · Özetler otomatik hazırlanır, ayrıntı için kaynağa gidin.</footer>
</div></body></html>"""


def kaynak_satiri(kaynaklar, etiket=None):
    linkler = "".join(f'<a href="{guvenli_link(k.get("link"))}" target="_blank" rel="noopener">{e(k.get("ad"))}</a>'
                      for k in kaynaklar or [])
    etk = ""
    if etiket:
        sinif = "teyitli" if etiket == "teyitli" else "tek"
        etk = f'<span class="etiket {sinif}">{"✓ Teyitli" if sinif == "teyitli" else "Tek kaynak"}</span>'
    return f'<div class="alt">{etk}<span class="kaynaklar">{linkler}</span></div>'


def haber_karti(h):
    neden = f'<p class="neden"><b>Neden önemli:</b> {e(h["neden_onemli"])}</p>' if h.get("neden_onemli") else ""
    return (f'<article><h3>{e(h.get("baslik"))}</h3><p>{e(h.get("ozet"))}</p>{neden}'
            f'{kaynak_satiri(h.get("kaynaklar"), h.get("etiket"))}</article>')


def makale_karti(m):
    yazar = ", ".join(m.get("yazarlar") or [])
    meta = " · ".join(x for x in [e(m.get("dergi")), e(m.get("tur")), e(yazar)] if x)
    linkler = [{"ad": "PubMed", "link": m.get("link")}]
    if m.get("doi"):
        linkler.append({"ad": "Makalenin kendisi (DOI)", "link": m["doi"]})
    neden = f'<p class="neden"><b>Neden önemli:</b> {e(m["neden_onemli"])}</p>' if m.get("neden_onemli") else ""
    return f"""<article class="makale"><h3>{e(m.get("baslik_en"))}<span class="tr">{e(m.get("baslik_tr"))}</span></h3>
<div class="meta">{meta}</div>
<div class="diller"><div><h4>TÜRKÇE</h4>{e(m.get("ozet_tr"))}</div><div lang="en"><h4>ENGLISH</h4>{e(m.get("ozet_en"))}</div></div>
{neden}{kaynak_satiri(linkler)}</article>"""


def bulten_html(b):
    baslik = f'{DONEM_AD.get(b["donem"], "Bülten")} · {tarih_yazi(b["tarih"])}'
    bolumler = [x for x in b.get("bolumler", []) if x.get("haberler")]
    nav = [("one", "Öne çıkanlar")] + [(x["id"], x["ad"]) for x in bolumler]
    if b.get("farkli_bakislar"):
        nav.append(("bakis", "Farklı bakışlar"))
    if b.get("makaleler"):
        nav.append(("makale", "Günün makaleleri"))
    parcalar = [
        f'<div class="tarih">{e(baslik)}</div></header>',
        f'<p class="giris">{e(b.get("giris"))}</p>' if b.get("giris") else "",
        '<nav class="icindekiler">' + "".join(f'<a href="#{e(i)}">{e(a)}</a>' for i, a in nav) + "</nav>",
        '<section class="one" id="one"><h2>Öne çıkanlar</h2>'
        + "".join(haber_karti(h) for h in b.get("one_cikanlar", [])) + "</section>",
    ]
    for bol in bolumler:
        parcalar.append(f'<section id="{e(bol["id"])}"><h2>{e(bol["ad"])}</h2>'
                        + "".join(haber_karti(h) for h in bol["haberler"]) + "</section>")
    if b.get("farkli_bakislar"):
        parcalar.append('<section id="bakis"><h2>Farklı bakışlar</h2>' + "".join(
            f'<article><h3>{e(f.get("konu"))}</h3><p>{e(f.get("aciklama"))}</p>{kaynak_satiri(f.get("kaynaklar"))}</article>'
            for f in b["farkli_bakislar"]) + "</section>")
    if b.get("makaleler"):
        parcalar.append('<section id="makale"><h2>Günün makaleleri<small>PubMed</small></h2>'
                        + "".join(makale_karti(m) for m in b["makaleler"]) + "</section>")
    return iskelet(f"Haberci · {baslik}", "\n".join(parcalar))


def arsiv_guncelle():
    satirlar = []
    for dosya in sorted(DOCS.glob("20*.html"), reverse=True):
        tarih, donem = dosya.stem.rsplit("-", 1)
        satirlar.append(f'<li><a href="{e(dosya.name)}">{e(tarih_yazi(tarih))}'
                        f'<span>{e(DONEM_AD.get(donem, donem))}</span></a></li>')
    govde = ('<div class="tarih">Günlük haber bülteni · Arşiv</div></header>'
             + (f'<p class="giris">En son bülten: <a href="{e(sorted(DOCS.glob("20*.html"))[-1].name)}">buradan oku</a></p>'
                if satirlar else "")
             + '<ul class="arsiv">' + "".join(satirlar) + "</ul>")
    (DOCS / "index.html").write_text(iskelet("Haberci", govde), "utf-8")


def bulten_linkleri(b):
    for h in b.get("one_cikanlar", []) + [h for bol in b.get("bolumler", []) for h in bol.get("haberler", [])] \
            + b.get("farkli_bakislar", []):
        for k in h.get("kaynaklar", []):
            yield k.get("link")
    for m in b.get("makaleler", []):
        yield m.get("link")
        if m.get("doi"):
            yield m["doi"]


def link_denetle(b):
    """Bültendeki her link topla.py'nin o dönemde topladığı veride bulunmalı (uydurma link engeli)."""
    veri = json.loads((KOK / "veri" / f'{b["tarih"]}-{b["donem"]}.json').read_text("utf-8"))
    bilinen = {h["link"] for v in veri["haberler"].values() for h in v}
    bilinen |= {d["link"] for v in veri["haberler"].values() for h in v for d in h["diger_kaynaklar"]}
    bilinen |= {p[a] for p in veri["pubmed_adaylari"] for a in ("link", "doi") if p.get(a)}
    return sorted({l for l in bulten_linkleri(b) if l not in bilinen})


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    b = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    bilinmeyen = link_denetle(b)
    if bilinmeyen:
        sys.exit("Toplanan veride olmayan linkler var, bülten yayınlanmadı:\n  " + "\n  ".join(bilinmeyen))
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").touch()
    hedef = DOCS / f'{b["tarih"]}-{b["donem"]}.html'
    hedef.write_text(bulten_html(b), "utf-8")
    arsiv_guncelle()
    pubmed_isaretle([m["pmid"] for m in b.get("makaleler", []) if m.get("pmid")])
    print(f"Yayınlandı: {hedef.relative_to(KOK)}")


if __name__ == "__main__":
    main()
