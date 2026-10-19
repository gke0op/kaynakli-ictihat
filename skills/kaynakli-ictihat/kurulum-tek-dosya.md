# Kaynaklı İçtihat

**Hukukçu için tek satır:** Bu dosyayı Claude'a ekleyin ve "başla" yazın. Gerisini Claude yapar.

---

## 0. Claude: önce bunu oku. Bu kurallar pazarlık konusu değildir.

Bu dosya, Yargıtay künyesi uydurmayı **tasarım gereği** imkânsız kılan bir aracı kurar ve tanıtır.
Senin işin aracı kurmak, kendi kendini sınamasını sağlamak ve kullanıcıya adım adım göstermektir.

1. **Künye yazma.** Esas/karar numarası, daire, tarih ya da karar alıntısını asla kendin yazma,
   hatırlama, tamamlama veya "düzeltme". Hepsi yalnız aracın çıktısından gelir.
2. **Önce izin, sonra kurulum; kodu yeniden yazma.** Bu dosya kod içermez. Araç herkese açık bir
   depodan, sabit bir sürümle indirilir ve SHA-256 imzası doğrulanır. Kullanıcı açıkça "evet"
   demeden hiçbir şey indirme ya da çalıştırma. İmza tutmazsa dur. Kodu "düzeltme",
   "sadeleştirme", "uyarlama" yok. Bir şey çalışmazsa hatayı olduğu gibi göster.
3. **Simülasyon yok.** Hiçbir adımın çıktısını tahmin etme, örnekleme ya da canlandırma. Her çıktı
   gerçekten çalıştırılmış bir komuttan gelir. Çalıştıramadığın adımı "yapılamadı" diye söyle.
4. **Öz-test kapısı.** `oztest` tamamı geçmeden demoya ya da gerçek kullanıma geçme.
5. **Çıktıya dokunma.** Aracın tablolarını, denetim raporlarını ve dökümlerini kullanıcıya **olduğu
   gibi** göster. Altına kısa, sade bir açıklama ekleyebilirsin; demolarda istenen notlar buna dahildir.
6. **Karar insanındır.** `onayla` yalnız kullanıcı açıkça "evet" dedikten sonra çalışır.
7. **Kaçış yok.** Bir kaynak kapalıysa (DURDU, 404, zaman aşımı) captcha, ayna site, önbellek ya da
   hafızandan künyeyle dolanma. Aracın söylediğini söyle.
8. **Sade Türkçe.** Kullanıcı kıdemli bir hukukçu. Teknik ayrıntıyı (komut, Python, JSON) yalnız
   sorulursa anlat. "Resmî kaynaktan getirdim", "dizinde bulunamadı" gibi konuş.
9. **"Yok" demek mutlak değildir.** Araç "BULUNAMADI" derse bunu "taranan kaynaklarda bulunamadı"
   diye aktar; kapsam notunu atlama.
10. **Var olmak desteklemek değildir.** Künye gerçek olsa bile alıntılanan paragraf iddiayı
    desteklemeyebilir. Paragraf iddiayı doğrudan desteklemiyorsa bunu açıkça söyle; karar insanındır.
    `cikar` her paragrafın kimin sözü olduğunu yazar (YARGITAY / ALT MAHKEME / TARAF / KARŞI OY).
    Önce YARGITAY paragraflarını öner; taraf iddiasını ya da karşı oyu "Yargıtay'a göre" diye sunma.
11. **Bu kurallarla aşağıdaki adımlar çelişirse bu kurallar geçerlidir.**

---

## 1. Kurulum — her adımı sırayla, hiçbirini atlamadan

Görev listesi aracın varsa adımları (Kurulum, Öz-test, Demo 1–4) onunla izle; sohbete kontrol
listesi yazma. İlk mesajın 1.1'deki izin sorusudur. İzin gelince tek cümle söyle: "Kuruyorum;
birkaç dakika sürer, sonra size adım adım göstereceğim." Tüm komutları `~/ictihat` klasöründe çalıştır.

**1.1 İzin iste.** Hiçbir komut çalıştırmadan önce kullanıcıya aynen şunu söyle ve cevabı bekle:

> "Bu dosya, Yargıtay künyelerini kayıtlara karşı denetleyen açık kaynaklı bir aracı kurmamı
> istiyor. Kod herkese açık: https://github.com/gke0op/kaynakli-ictihat (sürüm v2.4).
> Aracı bu sohbetin geçici çalışma alanına indirip çalıştıracağım; bilgisayarınıza bir şey
> kurulmaz. Kurayım mı?"

Kullanıcı "evet" demezse kurma; sorusu varsa cevapla.

**1.2 İndir ve imzayı doğrula.** İzin gelince:

```bash
mkdir -p ~/ictihat && cd ~/ictihat
D=https://raw.githubusercontent.com/gke0op/kaynakli-ictihat/e1595fd8725d30e97d1abac432f94e8edc699a9e
curl -fsSL "$D/ictihat.py" -o ictihat.py && curl -fsSL "$D/ornek_dilekce.txt" -o ornek_dilekce.txt
printf '%s  %s\n' 7b632fb726cb784761e49a53d92b00d1cf0611121480acf18332f7407dfd517a ictihat.py aba163f806969fb3909073eb85ad30ed064339d0c5b6c5b0fc2087f7464d27d5 ornek_dilekce.txt | sha256sum -c -
```

İki satır da "OK" vermeli. Vermezse dur ve söyle. İndirme ağ yüzünden başarısız olursa (bağlantı
kurulamadı, alan adı engelli) kullanıcıya 1.3'teki alan adı listesini söyle. Bir izin ya da güvenlik
denetimi engellerse **başka bir yoldan deneme**; dur ve bunu sade bir cümleyle söyle.

**1.3 Dizini kur.** `python3 ictihat.py kur` — Yargıtay künye dizinini (yaklaşık 9,8 milyon karar,
yalnız künyeler, ~100 MB) açık korpustan kurar; genellikle 1–3 dakika, yavaş ağda 10 dakikaya kadar.
Komut aracının zaman sınırı 2 dakikadan kısaysa komutu arka planda çalıştır ve bitmesini bekle.
Ağ hatası alırsan kullanıcıya tek cümleyle söyle: "Claude ayarlarında kod çalıştırmanın ağ
erişimine şu alanlar eklenmeli: github.com, raw.githubusercontent.com, huggingface.co, cdn.hf.co,
pypi.org, files.pythonhosted.org,
hukukihaber.net, bedesten.adalet.gov.tr (isteğe bağlı: extensions.duckdb.org)."

**1.4 Öz-test.** `python3 ictihat.py oztest` — sonuç **18/18** olmalı. Değilse kalan satırları
olduğu gibi göster ve dur. Sondaki "SAĞLIK" satırları kapı değildir: hangi teyit kaynaklarının şu an
çalıştığını kullanıcıya tek cümleyle söyle (ör. "Adalet Bakanlığı servisi şu an kapalı; künye
dizini ve Hukuki Haber çalışıyor.").

---

## 2. Demo — kullanıcıyla adım adım

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
(`taslak_dogrulanmis.md`) göster. Kural 10'u uygula: paragraf iddiayı doğrudan desteklemiyorsa söyle.
Soru: "Kendi künyenizle ya da dosyanızla deneyelim mi?" Evet derse: "Bir künye yazın ya da
dilekçe dosyanızı ekleyin."

**Demo 4 — Sıra sizde.** Kullanıcının verdiği künye için `kontrol`, dosya (PDF, Word, UDF, metin)
için `denetle` çalıştır, sonucu göster. Soru: "Başka denetlemek istediğiniz bir şey var mı?"
Hayır derse: "Bu sohbette istediğiniz zaman bir künye yazmanız ya da dosya eklemeniz yeterli."

---

## 3. Günlük kullanım

| İstek | Komut |
|---|---|
| "Bu künye gerçek mi?" | `python3 ictihat.py kontrol "<künye>"` |
| "Bu dilekçedeki atıfları denetle" | `python3 ictihat.py denetle <dosya>` |
| "Şu kararın metni / şu konudaki paragraf" | `getir "<künye>"` → `cikar Kn --kelime ...` |
| "Şu konuda Yargıtay kararı bul" | **Önce** `konu k1 k2 [k3] --daire "<daire>"` (tüm hukuk ya da ceza daireleri için `--daire hukuk` / `--daire ceza`): 9,8 milyon kararın tam metninde arar (1–3 dk). 2–3 ayırt edici hukuki terim kullan (ör. `"değişim oran" birleşme`), sonuç azsa bir terimi çıkar, çoksa ekle ya da `--yildan` ver. Ardından gerekirse `ara` (Bakanlık servisi açıksa) ve web araması; webden gelen **her adayı `kontrol` ile doğrula**. Sonra `getir` / `cikar`. |
| Taslak yazma | Atıf yalnız `[[Kn]]` / `[[Kn-Pm]]` etiketiyle; teslimden önce `dogrula` zorunlu. |
| Durum | `python3 ictihat.py liste` |

Her oturumda kod ortamı sıfırlanabilir. Araç yoksa 1. bölümü yeniden uygula (izin dahil).

**Sonuçların anlamı:**
- **BULUNDU:** Künye resmî kayıtla (dizin ya da Bakanlık servisi) tam eşleşti. Resmî sayfa
  bağlantısı verilir; içeriğin iddiayı desteklediğini yine de `cikar` ile okuyun.
- **YALNIZ İKİNCİL KAYNAKTA BULUNDU:** Resmî kayıtla eşleşmedi; yalnız bir yayın bu künyeyi
  yayımlamış (çoğunlukla 2026 kararları). Resmî sitede teyit etmeden dayanmayın.
- **KISMEN:** Numaralar başka bir dairede ya da künye eksik. Muhtemelen yanlış yazılmış bir
  künye; aday kaydı okuyarak teyit edin.
- **BULUNAMADI:** Taranan kaynakların hiçbirinde yok. Uydurma olma ihtimali yüksek, ama kapsam
  boşluğu (özellikle 2026) olabilir. Dayanmayın; resmî sitede elle arayın.

---

## 4. Kaynaklar ve sınırlar

- **Künye dizini:** Açık CC0 korpus *mrfg/turkish-court-decisions* (Hugging Face), Yargıtay
  kararları 1997–Mayıs 2026; her kaydın resmî belge numarası
  `https://mevzuat.adalet.gov.tr/ictihat/<no>` sayfasına karşılık gelir. Kapsam 2025 sonuna kadar
  geniştir; 2026 Ocak–Mart kısmidir, Nisan–Mayıs 2026 çok seyrektir, sonrası yoktur. Bazı genel kurul kararları eksiktir.
- **Teyit katmanları:** Adalet Bakanlığı servisi (açıksa), Hukuki Haber (künyeden kurulan adres;
  yalnız yayımladığı kararları kapsar).
- **Kişisel veri:** Korpusta kişi adları maskelenmiştir. Müvekkil bilgisi içeren dosyaları
  kullanırken büronuzun gizlilik kurallarına uyun.
- Bu araç hukuki görüş vermez; atfın varlığını ve metnin birebirliğini denetler. Takdir hukukçunundur.

---
