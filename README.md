# Operatör Yetenekleri

Yapay zekâ işe yarar, ama bazen çok emin bir sesle yanlış söyler: olmayan bir Yargıtay kararı, yanlış bir madde numarası, hatırlanmış gibi sunulan bir sayı. Burada, bu tür işleri daha güvenilir yapmak için hazırladığım, kullanıma hazır yetenekler duruyor. Her biri kendi klasöründe, kendi içinde eksiksiz; buyurun, alın kullanın. Liste zamanla büyüyecek.

## Yetenekler

| Yetenek | Ne işe yarar | Kime |
|---|---|---|
| [**özenli mod**](skills/ozenli-mod/) | Yapay zekâ verdiği her bilgiyi **[BELGE] / [KAYNAK] / [HAFIZA]** diye etiketler; bilmiyorsa uydurmaz. Kurulum yok, tek mesaj. | Herkes |
| [**yapı mevzuatı**](skills/yapi-mevzuati/) | İmar, yapı denetimi, iş güvenliği, ihale ve kentsel dönüşüm mevzuatı (17 belge), madde madde, kelimesi kelimesine, son değişiklik notlarıyla. | Müteahhit, yapı sektörü |
| [**kaynaklı içtihat**](skills/kaynakli-ictihat/) | Yargıtay künyesini model değil **kod** denetler; uydurma künyeyi yakalar, karar metnini birebir getirir. Karar her zaman insanındır. | Hukukçular |

## Nasıl kullanılır

- **Claude'da yetenek olarak:** yeteneğin klasörü, içindeki `SKILL.md` ile birlikte, Claude'a yetenek olarak eklenir.
- **Başka bir yapay zekâda ya da yetenek eklemeden:** her klasörde bir `README.md` var; oradan başlayın. Özenli mod, kuralları bir kez yapıştırarak her yapay zekâda çalışır.

## Depo düzeni

```
skills/            yetenekler, her biri kendi klasöründe (SKILL.md + araçlar + belgeler)
olcum/             kaynaklı içtihat aracının on vakalık ölçümü ve hakem notları
paylas/, araclar/  sunum sayfaları ve onları üreten araçlar
```

## Sınırlar

Hiçbiri hukuki ya da mühendislik görüşü değildir. Araçlar atfın **varlığını** ve metnin **birebirliğini** denetler; metnin işinize uyup uymadığına siz karar verirsiniz. Mevzuat kütüphanesi 19.10.2026 tarihli resmî metinlerdir; kullanmadan önce güncelliğine bakın.

Lisans: MIT (kod). Kaynaklı içtihat korpusu CC0'dır ve kaynağına aittir. Ekmel Gökçe Özdemir · [LinkedIn](https://www.linkedin.com/in/ekmel-gokce-ozdemir)
