# Haberci — Günlük Haber Ajanı Planı

> Taslak v0.1 · 26 Ekim 2026 · Birlikte netleştirilecek

## 1. Amaç

Her sabah otomatik çalışan, yerli ve yabancı **güvenilir** kaynaklardan haberleri toplayan,
tekrarları birleştiren, önem sırasına koyan ve Türkçe özetleyerek tek bir **günlük bülten**
halinde sunan kişisel bir ajan.

Temel ilkeler:
- **Kaynak gösterme zorunlu:** her özetin altında orijinal habere link.
- **Çapraz doğrulama:** aynı olay 2+ bağımsız kaynakta geçiyorsa "teyitli", tek kaynaktaysa "tek kaynak" etiketi.
- **Denge:** Türkiye haberlerinde farklı yayın çizgilerinden kaynaklar birlikte okunur.
- **Telif:** haber metni kopyalanmaz; kısa özet + link verilir. Ücretli (paywall) sitelerden yalnızca RSS'te açık olan başlık/özet kullanılır.

## 2. Nasıl çalışacak (mimari)

```
 ┌───────────┐   ┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌────────────┐
 │ 1. TOPLA  │──▶│ 2. TEMİZLE  │──▶│ 3. KÜMELE    │──▶│ 4. ÖZETLE     │──▶│ 5. SUN     │
 │ RSS/Atom  │   │ son 24 saat │   │ aynı olayı   │   │ Claude:       │   │ HTML bülten│
 │ ~50 kaynak│   │ tekrar sil  │   │ birleştir    │   │ önem puanı,   │   │ (+Telegram/│
 │ (Python)  │   │ dil tespiti │   │ kaynak say   │   │ Türkçe özet   │   │  e-posta)  │
 └───────────┘   └─────────────┘   └──────────────┘   └───────────────┘   └────────────┘
                                                                                │
                                                       arşiv/  ◀────────────────┘ (her gün bir dosya)
```

- **Toplama** ücretsiz ve deterministik: Python + `feedparser`. Haber sitesi kazımaya (scraping) gerek yok; RSS en temiz ve en "izinli" yol.
- **Akıllı kısım** (önem sırası, kümeleme kontrolü, Türkçe özet, "neden önemli" notu) Claude'da.
- Reuters ve AP'nin herkese açık RSS'i yok → **Google News RSS** ile `site:reuters.com` / `site:apnews.com` araması kullanılır (test edildi, çalışıyor).

## 3. Otomasyon seçenekleri

| Seçenek | Nasıl | Artı | Eksi |
|---|---|---|---|
| **A. Claude masaüstü zamanlanmış görev** | Claude uygulaması her sabah görevi çalıştırır | API anahtarı gerekmez, en hızlı kurulum, aboneliğin içinde | Bilgisayar açık ve uygulama çalışıyor olmalı |
| **B. Python + Windows Görev Zamanlayıcı + Claude API** | Script her sabah kendi çalışır, API ile özetler | Claude uygulamasından bağımsız, tam kontrol | API anahtarı + küçük maliyet (Haiku ile ayda birkaç $) |
| **C. Bulut rutini (cloud)** | Claude bulutta zamanlanmış ajan | Bilgisayar kapalıyken de çalışır | GitHub deposu gerekir, teslimat e-posta/Telegram ile olmalı |

**Önerim:** A ile başla (bugün kurulabilir), toplama kodunu bağımsız yazalım ki gerekirse B veya C'ye taşımak kolay olsun.

## 4. Kaynak listesi (26.10.2026'da test edildi ✅)

### Güvenilirlik katmanları
- **Katman 1 — Haber ajansları & kamu yayıncıları:** olay haberinin birincil kaynağı.
- **Katman 2 — Köklü gazete/kanallar:** bağlam, analiz.
- **Katman 3 — Uzmanlık kaynakları:** bilim, teknoloji, ekonomi, sağlık.
- **Doğrulama kaynakları:** iddiaların kontrolü.

### 🇹🇷 Yerli
| Kaynak | Katman | Not | RSS |
|---|---|---|---|
| Anadolu Ajansı | 1 | Resmî ajans; gündem/dünya/ekonomi/bilim kategorileri ayrı | ✅ |
| TRT Haber | 1 | Kamu yayıncısı | ✅ |
| BBC Türkçe | 1 | Yabancı kamu yayıncısı, Türkçe | ✅ |
| DW Türkçe | 1 | Yabancı kamu yayıncısı, Türkçe | ✅ |
| Euronews Türkçe | 1 | | ✅ |
| Independent Türkçe | 2 | | ✅ |
| NTV | 2 | | ✅ |
| Hürriyet | 2 | | ✅ |
| Habertürk | 2 | | ✅ |
| Sabah | 2 | | ✅ |
| Sözcü | 2 | | ✅ |
| Cumhuriyet | 2 | | ✅ |
| Medyascope | 2 | Bağımsız dijital | ✅ |
| Bloomberg HT | 3 | Ekonomi/piyasa | ✅ |
| Dünya Gazetesi | 3 | Ekonomi/iş dünyası | ✅ |
| Webtekno | 3 | Teknoloji | ✅ |
| Evrim Ağacı | 3 | Bilim (Türkçe) | ✅ |
| Teyit.org / Doğruluk Payı | doğrulama | RSS kapalı → web araması ile | ⚠️ |
| Google News Türkiye | toplayıcı | Gündem genel görünümü | ✅ |

### 🌍 Yabancı
| Kaynak | Katman | Not | RSS |
|---|---|---|---|
| Reuters | 1 | Google News üzerinden | ✅ |
| Associated Press (AP) | 1 | Google News üzerinden | ✅ |
| AFP | 1 | | ✅ |
| BBC News (World) | 1 | | ✅ |
| DW English | 1 | | ✅ |
| NPR | 1 | ABD kamu radyosu | ✅ |
| France 24 | 1 | | ✅ |
| Euronews | 1 | | ✅ |
| The Guardian | 2 | | ✅ |
| New York Times (World) | 2 | Paywall: sadece başlık/özet | ✅ |
| Wall Street Journal (World) | 2 | Paywall | ✅ |
| Financial Times | 2 | Paywall | ✅ |
| The Economist | 2 | Paywall, haftalık analiz | ✅ |
| Le Monde (EN) | 2 | | ✅ |
| Der Spiegel International | 2 | | ✅ |
| Al Jazeera | 2 | Orta Doğu odaklı | ✅ |
| Politico Europe | 2 | AB siyaseti | ✅ |
| CNBC | 3 | Ekonomi/piyasa | ✅ |
| Ars Technica / The Verge / TechCrunch / MIT Tech Review | 3 | Teknoloji | ✅ |
| Nature / Scientific American / New Scientist / ScienceDaily | 3 | Bilim | ✅ |
| arXiv (cs.AI) | 3 | Yapay zekâ makaleleri (günde ~300, filtrelenmeli) | ✅ |
| NASA | 3 | Uzay | ✅ |
| The Conversation | 3 | Akademisyenlerin yazdığı makaleler | ✅ |
| WHO | 3 | Sağlık | ✅ |
| Hacker News | 3 | Teknoloji topluluğu gündemi | ✅ |
| BBC Sport (Futbol) | 3 | Spor | ✅ |

Çalışmayanlar: AP/Reuters doğrudan RSS (→ Google News ile çözüldü), TRT Spor, NTV Spor, Resmî Gazete RSS (→ alternatif bakılacak).

## 5. Bülten formatı (taslak)

1. **Günün 5 başlığı** — en önemli olaylar, 2-3 cümle, kaç kaynakta geçtiği
2. **Türkiye** — siyaset, toplum, ekonomi
3. **Dünya**
4. **Ekonomi & Piyasalar**
5. **Bilim & Teknoloji & Yapay Zekâ**
6. **Sağlık**, **Spor**, **Kültür** (isteğe bağlı)
7. **Günün makalesi / uzun okuma** — 2-3 analiz yazısı
8. **Farklı bakışlar** — aynı olayı farklı yayın çizgileri nasıl veriyor (isteğe bağlı)

Her madde: başlık · özet · etiket (teyitli / tek kaynak) · kaynak linkleri.

## 6. Klasör yapısı (planlanan)

```
haberci/
├─ PLAN.md               ← bu dosya
├─ kaynaklar.yaml        ← kaynak listesi (kolayca ekle/çıkar)
├─ ilgi_alanlari.yaml    ← konular, öncelikler, hariç tutulanlar
├─ topla.py              ← RSS toplama + temizleme + kümeleme
├─ sablon.html           ← bülten tasarımı
├─ arsiv/2026-10-27.html ← her günün bülteni
└─ veri/                 ← ham toplanan haberler (JSON)
```

## 7. Yol haritası

| Aşama | İş | Çıktı |
|---|---|---|
| 1 | Kararları netleştir (aşağıdaki sorular) | Kesin kapsam |
| 2 | `kaynaklar.yaml` + `topla.py` | Elle çalışan toplayıcı |
| 3 | Claude ile özet + HTML bülten | İlk bülten |
| 4 | Zamanlanmış görev (her sabah) | Otomatik çalışma |
| 5 | Teslimat (Telegram / e-posta) – isteğe bağlı | Telefona bildirim |
| 6 | İnce ayar: kaynak ağırlıkları, ilgi alanları, geri bildirim | Kişiselleşmiş bülten |

## 8. Alınan kararlar (26.10.2026)

- **Çalışma yeri:** Bulut (bilgisayar kapalıyken de çalışsın)
- **Teslimat:** HTML sayfa
- **Konular:** Türkiye + Dünya, Ekonomi & Piyasalar, Bilim/Teknoloji/Yapay Zekâ, Sağlık/Spor/Kültür (hepsi)
- **Sıklık:** Sabah + akşam (iki bülten)

### Buluttan HTML'e nasıl ulaşılır?
Bulutta çalışan ajan bilgisayara dosya yazamaz. Çözüm:
**GitHub deposu + GitHub Pages** → ajan her bülteni depoya kaydeder, bülten
`https://<kullanici>.github.io/haberci/` adresinde yayınlanır. Bilgisayardan da telefondan da açılır,
arşiv otomatik birikir. Depo gizli (private) tutulursa Pages için GitHub Pro gerekir; açık depo ücretsiz.

Bulutta çalıştırmanın iki yolu:
1. **Claude bulut rutini** — aboneliğin içinde, API anahtarı yok; Claude depoyu açar, `topla.py`'ı çalıştırır, bülteni yazar, kaydeder.
2. **GitHub Actions + Claude API** — tamamen GitHub'da; API anahtarı ve küçük maliyet gerekir.

Önerim: **1. yol**.

### Ek kararlar (26.10.2026, ikinci görüşme)
- Magazin ve benzeri hafif konular yok, yalnızca ciddi haberler (filtre: `ayarlar.toml` + `GOREV.md`).
- Her bültende PubMed'den 3 makale: İngilizce özet + Türkçe çevirisi.
- GitHub hesabı var. API anahtarı veya MCP gerekirse kurmadan önce sorulacak.

## 9. Durum (26.10.2026)

- ✅ `topla.py`: 61 kaynak + PubMed (anahtarsız E-utilities), magazin filtresi, haber kümeleme
- ✅ `yayinla.py`: HTML bülten + arşiv sayfası + uydurma link engeli
- ✅ İlk bülten elle üretildi: `docs/2026-10-26-aksam.html`
- ✅ GitHub deposu (mkaya5153-star/haberci) + Pages (main/docs)
- ✅ Bulut rutinleri: Sabah 07:30 (trig_01AWi2JGJePVrZSF2sPdknnj), Akşam 19:00 (trig_01PSukR8sGin7SuLiD9RS6eR)
- ⚠️ İlk test: bulut ortamının ağ politikası haber sitelerini engelledi (403). Ortamın ağ erişimi
  "Full" yapılmalı ya da `izinli_alanlar.txt` içindeki alan adları izin listesine eklenmeli.
  Yeni kaynak eklenirse alan adı bu listeye de eklenmeli.
