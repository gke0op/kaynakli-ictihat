# Kaynaklı İçtihat

Yapay zekâ sohbet araçları Yargıtay künyesi uydurabiliyor: esas/karar numarası, daire ya da tarih
gerçek gibi görünür ama kayıtlarda yoktur. Bu araç künyeyi **modelin hafızasından değil, koddan**
denetler ve karar metnini **birebir** getirir. Karar her zaman insanındır.

## Herkes için: özenli mod

Kurulum gerektirmeyen tek mesaj: ChatGPT, Claude, Gemini ve diğerlerinde her bilgiyi **[BELGE] / [KAYNAK] / [HAFIZA]** diye etiketletir. → [ozenli-mod](../ozenli-mod/README.md)

## Müteahhit kütüphanesi

İmar, yapı, iş güvenliği, ihale ve kentsel dönüşüm mevzuatı (17 belge), madde madde ve kelimesi kelimesine, son değişiklik notlarıyla → [yapi-mevzuati](../yapi-mevzuati/kutuphane/README.md)

## Nasıl kullanılır

Hukukçu hiçbir şey kurmaz. [`kurulum-tek-dosya.md`](kurulum-tek-dosya.md) dosyasını Claude'a ekler ve
"başla" yazar (ya da bu klasör Claude'da yetenek olarak ekliyse doğrudan [SKILL.md](SKILL.md) çalışır). Claude ne kuracağını söyler, onay ister, onay gelirse aracı bu depodan sabit bir
sürümle indirir, imzasını (SHA-256) doğrular, kendi kendini sınar ve adım adım gösterir.

## Ne yapar

| Komut | İş |
|---|---|
| `kontrol "<künye>"` | Künye var mı? **BULUNDU / KISMEN / YALNIZ İKİNCİL KAYNAKTA BULUNDU / BULUNAMADI** |
| `denetle <dosya>` | Dilekçedeki (txt, md, pdf, docx, udf) tüm Yargıtay künyelerini denetler |
| `konu k1 k2 --daire …` | Konu araması: 9,8 milyon kararın tam metninde terim arar, en çok geçen kararları getirir |
| `getir "<künye>"` · `cikar Kn --kelime …` | Karar metnini getirir, ilgili paragrafları birebir döker; her paragrafın kimin sözü olduğunu (Yargıtay / alt mahkeme / taraf / karşı oy) yazar |
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

## Ölçüm

On farklı hukuk sorusunda (birleşme, marka, kefalet, iş kazası, haksız tahrik…) önceden yazılmış ölçütle: **9/10 başarılı**, uydurma künye 0. Ayrıntı, hakem notları ve on taslak: [olcum/](../../olcum/README.md).

## Sınırlar

Araç atfın **varlığını** ve metnin **birebirliğini** denetler; alıntının iddiayı desteklediğine
hukukçu karar verir. "BULUNAMADI", taranan kaynaklarda bulunamadı demektir. Hukuki görüş değildir.

## Sürüm

**v2.4** = commit `e1595fd8725d30e97d1abac432f94e8edc699a9e` (önceki: v2.3 = `076fdf3`, v2.1 = `8ba8e3d`, v2.0 = `8afc5c2`). Talimat dosyası aracı bu commit'e sabitlenmiş adresten indirir; commit kimliği değiştirilemez.

## Doğrulama

```
sha256sum -c SHA256SUMS
```

Lisans: MIT (kod). Korpus verisi CC0, kaynağına aittir.
