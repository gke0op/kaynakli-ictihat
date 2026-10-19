---
name: yapi-mevzuati
description: Müteahhit ve yapı sektörü için resmî mevzuat kütüphanesi, madde madde ve kelimesi kelimesine: İmar Kanunu, imar, otopark, yangın, enerji performansı ve yapı denetimi yönetmelikleri, yapı işleri iş güvenliği, Kamu İhale Kanunları ve yapım işleri ihale mevzuatı, Kat Mülkiyeti, kentsel dönüşüm. Bu mevzuata dair bir soru ya da madde numarası geldiğinde bellekten değil buradan cevapla.
---

# Yapı mevzuatı kütüphanesi

17 belge, madde madde ayrılmış, her maddenin yanında son değişiklik notuyla. Kaynak: mevzuat.gov.tr kaynaklı resmî PDF'ler (derleme tarihi 19.10.2026). Katalog ve kaynak PDF bağlantıları: [kutuphane/README.md](kutuphane/README.md).

## Nasıl kullanılır

1. Kataloğa ([kutuphane/README.md](kutuphane/README.md)) bak, ilgili belgenin klasörünü bul (ör. `planli-alanlar-imar-yonetmeligi/`).
2. O klasördeki `index.md` madde listesini ve her maddenin son değişiklik notunu verir; konuya uyan maddeyi seç.
3. Madde dosyasını oku: `madde-031.md`, ek maddeler `madde-ek-1.md`, geçici maddeler `madde-gecici-1.md`.
4. Cevabı **yalnız o metne dayandır**, birebir alıntıla, belge + madde + fıkra/bent yaz, maddenin son değişiklik notunu belirt. Bellekten madde numarası ya da sayı verme.
5. Ölçü, süre, oran gibi sayıları [özenli mod](../ozenli-mod/SKILL.md) etiketleriyle ver: kütüphaneden gelen **[BELGE]**, doğrulanmayan **[HAFIZA]**.

## Bilmen gereken sınırlar

- **Güncellik:** "son değişiklik" PDF'in içindeki en yeni değişiklik notudur; indirildiği tarihten (19.10.2026) sonraki değişiklikleri içermez. Kullanıcıya mevzuat.gov.tr'de tarihi kontrol etmesini söyle.
- **⚠ işaretli maddeler** tablo içerir: metne çevirirken tablo düzeni bozulmuş olabilir. Sayıyı kaynak PDF'teki (`kutuphane/pdf/`) tablodan oku ve bunu söyle.
- **`islenemeyen-madde-...` dosyaları** ana kanunun maddesi değildir; kanunu değiştiren başka kanunların kendi hükümleridir. Ana kanunun maddesi gibi sunma.
- **Deprem yönetmeliği:** yalnız 6 maddelik yönetmelik gövdesi var. Asıl teknik esaslar taranmış görüntü olarak yayımlı olduğundan kütüphanede yok; kullanıcıyı Resmî Gazete'ye yönlendir.
- **2026 Yapı Yaklaşık Birim Maliyetleri Tebliği** m² başına yaklaşık maliyet verir; poz bazlı birim fiyat listesi değildir.
- Hukuki görüş değildir; hüküm gerektiren kararlarda yetkili makama ya da hukukçuya danış.

## Klasör düzeni

```
kutuphane/
  README.md            katalog: belge, madde sayısı, son değişiklik, kaynak PDF, parmak izi
  pdf/                 kaynak PDF'ler (SHA-256 parmak izleri katalogda)
  <belge-adi>/
    index.md           madde listesi + son değişiklik notları
    madde-NNN.md       tek madde (ek: madde-ek-N.md, geçici: madde-gecici-N.md)
    maddeler.json      makine okunur madde listesi (Ek-5 klasöründe yok)
scripts/               derleme araçları (PDF'ten madde madde ayırma)
```

`scripts/` altındaki araçlar kütüphaneyi üretirken kullanılan, ilk ortama özgü yollar içeren derleme araçlarıdır; kullanım için gerekmez.
