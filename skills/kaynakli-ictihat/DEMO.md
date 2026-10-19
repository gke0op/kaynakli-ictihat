# Demo — kullanıcıyla adım adım

Önkoşul: [SKILL.md](SKILL.md) §1 tamamlandı ve öz-test geçti. Komutlar `~/ictihat` klasöründe çalışır.

Her demodan sonra yalnız orada yazan soruyu sor ve cevabı bekle.

**Demo 1 — Uydurma künye yakalanıyor.** Kullanıcıya: "Elimde, yapay zekâyla yazılmış gibi duran
örnek bir dilekçe var; içindeki her Yargıtay atfını kayıtlara karşı denetleyeceğim."
`python3 ictihat.py denetle ornek_dilekce.txt` çalıştır ve raporu olduğu gibi göster. Altına her
madde için tek kısa satır yaz (ne bulundu, ne anlama geliyor). Yanlış daireli madde için şunu
ekle: "Ankara'da 25 yıllık bir avukat hakkında, yapay zekânın künyeleri yanlış yazdığı bir dilekçe
yüzünden savcılık ve baro soruşturması açıldı; bu tam olarak o tür bir hata." (Kaynak:
https://www.haberler.com/haberler/yapay-zekaya-guvendi-basina-is-acti-25-yillik-19963915-haberi/)
Soru: "Devam edelim mi?"

**Demo 2 — Gerçek kararın birebir metni.** `python3 ictihat.py getir "Yargıtay 3. HD E. 2025/927 K. 2025/6060"`
ardından `python3 ictihat.py cikar K1 --kelime temyiz sınır kira`. Dökümü göster; araç zaten
"Hangi paragrafları kullanmak istersiniz?" diye soruyor, aynı soruyu tekrar sorma.
- Kullanıcı paragraf adlarıyla cevap verirse → `python3 ictihat.py onayla K1 P7 ...` (yalnız onlar).
- Yalnız "evet" derse → bir kez hangi paragrafı kullanacağını sor; yine belirtmezse ya da paragrafı
  numarasız tarif ederse tarife en uyan paragrafı seç; tarif yoksa dökümde parantez içi eşleşmesi en
  yüksek olanı (ör. 3/3) seç. Onaylamadan önce seçtiğin paragrafı numarasıyla söyle. `hepsi` yalnız kullanıcı
  açıkça "hepsini" derse.
- "Hayır" → `python3 ictihat.py reddet K1`, kullanıcıdan başka bir konu iste.

**Demo 3 — Taslakta atıf kodla yerleşiyor.** Onaylanan paragraf için kısa bir dilekçe paragrafı
yaz; atıf yerine yalnız `[[K1-P<onaylanan no>]]` etiketi kullan. Ardından, örnek dilekçedeki uydurma
künyeyi (Yargıtay 3. HD, E. 2023/4567 K. 2024/1234) bir cümle olarak **aynen** ekle; kendin yeni
künye uydurma. Kullanıcıya bunu bilerek eklediğini söyle. `taslak.md` olarak kaydet,
`python3 ictihat.py dogrula taslak.md` çalıştır, sonucu göster: etiket birebir metin + künye +
bağlantıyla değişti; uydurma künye `taslak_SORUNLU.md` içinde ⟦DOĞRULANMADI⟧ ile işaretlendi.
Sonra uydurma cümleyi taslaktan sil, `dogrula`yı yeniden çalıştır ve temiz çıktıyı
(`taslak_dogrulanmis.md`) göster. [SKILL.md](SKILL.md) §0 Kural 10'u uygula: paragraf iddiayı doğrudan desteklemiyorsa söyle.
Soru: "Kendi künyenizle ya da dosyanızla deneyelim mi?" Evet derse: "Bir künye yazın ya da
dilekçe dosyanızı ekleyin."

**Demo 4 — Sıra sizde.** Kullanıcının verdiği künye için `kontrol`, dosya (PDF, Word, UDF, metin)
için `denetle` çalıştır, sonucu göster. Soru: "Başka denetlemek istediğiniz bir şey var mı?"
Hayır derse: "Bu sohbette istediğiniz zaman bir künye yazmanız ya da dosya eklemeniz yeterli."
