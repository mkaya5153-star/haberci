# Haberci

Günde iki kez (07:30 ve 19:00) güvenilir yerli ve yabancı kaynaklardan haberleri toplayıp
Türkçe bülten hazırlayan kişisel haber ajanı. Bültenler `docs/` klasöründe, GitHub Pages ile yayınlanır.

| Dosya | Ne işe yarar |
|---|---|
| `kaynaklar.toml` | Haber kaynakları (RSS). Eklemek/çıkarmak için düzenle. |
| `ayarlar.toml` | Zaman aralığı, magazin filtresi, PubMed sorgusu. |
| `topla.py` | Kaynakları ve PubMed'i okur → `veri/<tarih>-<donem>.json` |
| `GOREV.md` | Ajanın bülteni nasıl yazacağına dair talimat. |
| `yayinla.py` | Bülten JSON'unu HTML'e çevirir, linkleri doğrular → `docs/` |
| `PLAN.md` | Proje planı ve alınan kararlar. |

Elle çalıştırmak için:

```
python topla.py
python yayinla.py bulten/<tarih>-<donem>.json
```

Yalnızca Python 3.11+ standart kütüphanesi kullanılır; API anahtarı gerekmez.
