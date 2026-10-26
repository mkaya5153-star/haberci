# Haberci — Bülten Hazırlama Görevi

Bu dosya, zamanlanmış ajanın her çalışmada izleyeceği talimattır. Sabah (07:30) ve akşam (19:00) çalışır.

## Adımlar

1. `python topla.py` çalıştır. Çıktı: `veri/<tarih>-<donem>.json`.
2. Bu JSON'u oku ve aşağıdaki kurallarla `bulten/<tarih>-<donem>.json` dosyasını yaz (şema aşağıda).
3. `python yayinla.py bulten/<tarih>-<donem>.json` çalıştır. HTML sayfayı `docs/` içine üretir, ana sayfayı günceller ve kullanılan PubMed makalelerini işaretler.
4. Değişiklikleri commit edip push et: `git add -A && git commit -m "Bülten <tarih> <donem>" && git push`.

## Editoryal kurallar

**Okur:** Türkçe konuşan, ciddi gündemi takip etmek isteyen biri. Bülten 10 dakikada okunmalı.

**Seçim:**
- Magazin, ünlü haberleri, dizi/şov dünyası, burç, kripto para spekülasyonu, tık tuzağı, "şok/flaş" başlıklar, galeri ve sıradan asayiş haberleri **alınmaz**.
- Öncelik: geniş kitleyi etkileyen kararlar, politika, ekonomi verileri, çatışmalar ve diplomasi, bilimsel gelişmeler, halk sağlığı.
- `kaynak_sayisi` yüksek olan haberler daha önemli sayılır, ama tek kaynakta geçen önemli bir haber de alınabilir.
- Aynı olayı farklı dillerdeki kaynaklar da veriyorsa (ör. AA + Reuters) bunları sen birleştir ve tüm kaynakları listele.
- Spor: yalnızca büyük sonuçlar ve kararlar (milli takım, Avrupa kupaları, büyük turnuvalar). Transfer söylentisi yok.
- Kültür: sanat, edebiyat, ödüller, miras, sinema festivalleri; ünlülerin özel hayatı yok.

**Yazım:**
- Her şey Türkçe. Yabancı kaynaklı haberleri Türkçe özetle.
- Özet 2-3 cümle, tarafsız, kendi cümlelerinle. Kaynak metni kopyalama.
- Yorum katma; iddiaları kime ait olduğunu belirterek aktar ("X'e göre…").
- Rakam, isim ve tarihleri kaynaktakinin aynısı yaz; emin değilsen yazma.
- `etiket`: haber 2+ bağımsız kaynakta varsa `"teyitli"`, yoksa `"tek kaynak"`.
- Her habere en az bir kaynak linki koy. Linkler yalnızca bu çalışmadaki topla.py çıktısından, **o haberin kendi kaydından** kopyalanır; asla link uydurma. `yayinla.py` veride olmayan bir link görürse yayını durdurur: bu durumda o linki doğrusuyla değiştir ya da haberi çıkar.
- `etiket: "teyitli"` verdiğin haberde en az iki farklı kaynağın linkini listele.

**Bölüm başına haber sayısı:** Öne çıkanlar 5 · Türkiye 6-8 · Dünya 6-8 · Ekonomi 4-6 · Bilim & Teknoloji 4-6 · Sağlık 2-4 · Spor 2-4 · Kültür 2-3.
Bir bölümde ciddi haber yoksa o bölümü boş bırak; dolgu haber koyma. Öne çıkanlarda yer alan haberi bölümlerde tekrarlama.

**Farklı bakışlar (isteğe bağlı, en fazla 2):** Türkiye'de farklı yayın çizgisindeki kaynakların (ör. TRT/Sabah ile Sözcü/Cumhuriyet ile BBC Türkçe/DW Türkçe) aynı olayı belirgin biçimde farklı çerçevelediği durumlar. Sadece çerçeve farkını tarafsızca anlat, taraf tutma.

**Günün makaleleri (PubMed):** `pubmed_adaylari` arasından `pubmed_secilecek` kadar makale seç.
- Tercih sırası: randomize kontrollü çalışma, meta-analiz, sistematik derleme, büyük kohort. Yorum, görüş yazısı, haber, mektup seçme.
- Geniş kitleyi ilgilendiren konuları seç (yaygın hastalıklar, beslenme, ilaç, halk sağlığı, yaşlanma, ruh sağlığı).
- Her makale için:
  - `baslik_en`: orijinal başlık (aynen) · `baslik_tr`: Türkçe çevirisi
  - `ozet_en`: bulguların İngilizce sade özeti, 3-4 cümle, kendi cümlelerinle (yöntem, katılımcı sayısı, ana sonuç, sınırlılık). Abstract'ı kopyalama; yalnızca abstract'ta yazan bulguları kullan.
  - `ozet_tr`: `ozet_en`'in Türkçe çevirisi
  - `neden_onemli`: tek cümle Türkçe, günlük hayata etkisi. Tıbbi tavsiye verme.

## Şema: `bulten/<tarih>-<donem>.json`

```json
{
  "tarih": "2026-10-27",
  "donem": "sabah",
  "giris": "Günün genel tablosunu veren 2-3 cümlelik Türkçe paragraf.",
  "one_cikanlar": [
    {"baslik": "", "ozet": "", "neden_onemli": "", "etiket": "teyitli",
     "kaynaklar": [{"ad": "Reuters", "link": "https://..."}]}
  ],
  "bolumler": [
    {"id": "gundem_tr", "ad": "Türkiye", "haberler": [
      {"baslik": "", "ozet": "", "etiket": "tek kaynak", "kaynaklar": [{"ad": "", "link": ""}]}
    ]}
  ],
  "farkli_bakislar": [
    {"konu": "", "aciklama": "", "kaynaklar": [{"ad": "", "link": ""}]}
  ],
  "makaleler": [
    {"pmid": "", "baslik_en": "", "baslik_tr": "", "dergi": "", "yazarlar": [], "tur": "",
     "ozet_en": "", "ozet_tr": "", "neden_onemli": "", "link": "", "doi": ""}
  ]
}
```

Bölüm `id` ve adları: `gundem_tr` Türkiye · `dunya` Dünya · `ekonomi` Ekonomi & Piyasalar ·
`bilim_teknoloji` Bilim, Teknoloji & Yapay Zekâ · `saglik` Sağlık · `spor` Spor · `kultur` Kültür & Sanat.

Yazdıktan sonra dosyanın geçerli JSON olduğundan emin ol (`python -m json.tool` ile kontrol et).
