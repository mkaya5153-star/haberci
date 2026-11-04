# Haberci - Kullanım ve Sorun Giderme (yapay zekâsız)

Bülten **kendiliğinden** çıkar. Claude ya da başka bir yapay zekâ gerekmez, ücret yoktur.
Okuma adresi: https://mkaya5153-star.github.io/haberci/

## 1. Nasıl çalışıyor?

```
GitHub Actions (her gün 07:30 ve 19:00)  →  otomatik.py  →  docs/*.html  →  GitHub Pages (site)
                                              ├ topla.py   (RSS + PubMed toplar)
                                              └ yayinla.py (HTML üretir, linkleri doğrular)
```

- Bilgisayarınızın açık olması gerekmez; her şey GitHub'da çalışır (açık depo = ücretsiz).
- Haberler kaç kaynakta geçtiğine göre seçilir; yabancı başlıklar ücretsiz makine çevirisiyle Türkçeye çevrilir.
- Yapay zekâ yazımı yok: özet olarak kaynağın kendi RSS özeti kullanılır, "neden önemli" notu yoktur.

## 2. Elle çalıştırma

**A) Bilgisayarınızdan (en kolayı):** `haberci` klasöründe `calistir.bat` dosyasına çift tıklayın.
Haber toplar, bülteni hazırlar, GitHub'a gönderir. Bitince sayfa birkaç dakikada güncellenir.
Dönemi zorlamak için komut satırında: `calistir.bat --donem sabah` (ya da `aksam`).

**B) GitHub'dan (bilgisayarsız, telefondan da olur):**
github.com/mkaya5153-star/haberci → **Actions** → **Bülten** → **Run workflow** → yeşil düğme.

## 3. Nerede ne değiştirilir?

| Ne istiyorum | Dosya |
|---|---|
| Kaynak eklemek/çıkarmak | `kaynaklar.toml` (bloğu sil ya da `aktif = false` yap) |
| Magazin/yasak kelime, PubMed sorgusu | `ayarlar.toml` |
| Bölüm başına haber sayısı | `otomatik.py` başındaki `BOLUM_SAYISI` |
| Çalışma saati | `.github/workflows/bulten.yml` (`cron`; saatler UTC, TR = UTC+3) |

Dosyaları GitHub sitesinde de kalem simgesiyle düzenleyebilirsiniz.

## 4. Sorun giderme

| Belirti | Neden / ne yapılır |
|---|---|
| Sitede yeni bülten yok | GitHub → **Actions** sekmesine bakın. Kırmızı ✗ varsa tıklayıp hata satırını okuyun. Düzeltince **Run workflow** ile yeniden çalıştırın. |
| `Yalnızca N haber toplanabildi` | İnternet/kaynak erişimi yok. Bir süre sonra tekrar çalıştırın; bülten boş yayınlanmaz. |
| Bir kaynak hep `403` veriyor | Siteler GitHub sunucularını engelliyor olabilir. `kaynaklar.toml`'da o kaynağa `aktif = false` yazın (diğerleri etkilenmez). |
| Çeviriler İngilizce kalıyor | Ücretsiz çeviri servisi geçici yanıt vermedi (günlükte "çevrilemedi" uyarısı). Sonraki çalışmada düzelir; yayını etkilemez. |
| Gün içinde bülten hiç tetiklenmedi | GitHub zamanlı görevleri birkaç dakika-saat geciktirebilir. Gelmezse **Run workflow**. Depoda 60 gün hiç etkinlik olmazsa zamanlama durur: Actions sekmesinden yeniden etkinleştirin. |
| `Toplanan veride olmayan linkler var` | `yayinla.py` uydurma link engeli. `otomatik.py` ile olmaz; elle yazılmış bülten JSON'unda link hatası vardır. |
| `calistir.bat` `git push` hatası veriyor | Önce `git pull --rebase` yapın; GitHub girişi (Git Credential Manager) açık olmalı. |
| Site hiç açılmıyor | GitHub → Settings → **Pages** → Source: `main` / `/docs` olmalı. |

Yeni sorun olursa Actions günlüğündeki kırmızı satır sorunun yerini söyler; hata mesajını bir yapay zekâya
ya da bir geliştiriciye yapıştırmak çoğu zaman yeter.

## 5. Dosya haritası

`otomatik.py` ana betik · `topla.py` toplayıcı · `yayinla.py` HTML üretici · `calistir.bat` elle çalıştırma ·
`.github/workflows/bulten.yml` zamanlama · `GOREV.md`/`PLAN.md` eski Claude tabanlı yöntemin notları.
