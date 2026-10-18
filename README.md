# Kaynaklı İçtihat

Yapay zekâ sohbet araçları Yargıtay künyesi uydurabiliyor: esas/karar numarası, daire ya da tarih
gerçek gibi görünür ama kayıtlarda yoktur. Bu araç künyeyi **modelin hafızasından değil, koddan**
denetler ve karar metnini **birebir** getirir. Karar her zaman insanındır.

## Nasıl kullanılır

Hukukçu hiçbir şey kurmaz. [`kaynakli-ictihat.md`](kaynakli-ictihat.md) dosyasını Claude'a ekler ve
"başla" yazar. Claude ne kuracağını söyler, onay ister, onay gelirse aracı bu depodan sabit bir
sürümle indirir, imzasını (SHA-256) doğrular, kendi kendini sınar ve adım adım gösterir.

## Ne yapar

| Komut | İş |
|---|---|
| `kontrol "<künye>"` | Künye var mı? **BULUNDU / KISMEN / YALNIZ İKİNCİL KAYNAKTA BULUNDU / BULUNAMADI** |
| `denetle <dosya>` | Dilekçedeki (txt, md, pdf, docx, udf) tüm Yargıtay künyelerini denetler |
| `getir "<künye>"` · `cikar Kn --kelime …` | Karar metnini getirir, ilgili paragrafları birebir döker |
| `onayla` · `reddet` | İnsanın kararı kayda geçer |
| `dogrula <taslak>` | Taslaktaki `[[Kn-Pm]]` etiketlerini onaylı metinle değiştirir, etiketsiz künyeleri işaretler |
| `kur` · `oztest` | Künye dizinini kurar · kendini sınar (geçmezse kullanılmaz) |

## Kaynaklar

- **Künye dizini:** açık CC0 korpus [mrfg/turkish-court-decisions](https://huggingface.co/datasets/mrfg/turkish-court-decisions)
  (Hugging Face) — ~9,8 milyon Yargıtay kararı, 1997–Mayıs 2026. Her kaydın resmî belge numarası
  `https://mevzuat.adalet.gov.tr/ictihat/<no>` sayfasına karşılık gelir. Kapsam 2025 sonuna kadar
  geniş; 2026 kısmi.
- **Teyit:** Adalet Bakanlığı Mevzuat ve İçtihat servisi (açıksa), Hukuki Haber (künyeden kurulan
  adres; yalnız yayımladığı kararlar).
- Kaynaklara kendini tanıtarak, istekler arasında bekleyerek erişilir; captcha, giriş ya da
  engel aşılmaz.

## Sınırlar

Araç atfın **varlığını** ve metnin **birebirliğini** denetler; alıntının iddiayı desteklediğine
hukukçu karar verir. "BULUNAMADI", taranan kaynaklarda bulunamadı demektir. Hukuki görüş değildir.

## Sürüm

**v2.0** = commit `8afc5c23442c98781cc34867a35996bf112f97ce`. Talimat dosyası aracı bu commit'e sabitlenmiş adresten indirir; commit kimliği değiştirilemez.

## Doğrulama

```
sha256sum -c SHA256SUMS
```

Lisans: MIT (kod). Korpus verisi CC0, kaynağına aittir.
