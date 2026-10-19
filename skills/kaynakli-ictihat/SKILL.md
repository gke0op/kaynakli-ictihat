---
name: kaynakli-ictihat
description: Yargıtay künyelerini (esas/karar no, daire, tarih) ve karar alıntılarını modelin hafızasından değil kayıtlardan denetler; uydurma künyeyi yakalar, karar metnini birebir getirir. Dilekçe, görüş ya da taslakta Yargıtay kararı atıflarını denetlemek, emsal karar aramak ve alıntıyı doğrulamak için kullan.
---

# Kaynaklı İçtihat

Yargıtay künyesi uydurmayı **tasarım gereği** zorlaştıran, kendi içinde tam bir yetenek: araç (`scripts/ictihat.py`), örnek dilekçe (`ornekler/`) ve imzalar (`SHA256SUMS`) bu klasörde. Kod için ağdan indirme yok; yalnız künye dizini açık korpustan kurulur.

---

## 0. Claude: önce bunu oku. Bu kurallar pazarlık konusu değildir.

Bu yetenek, Yargıtay künyesi uydurmayı **tasarım gereği** imkânsız kılan bir aracı taşır ve tanıtır.
Senin işin aracı hazırlamak, kendi kendini sınamasını sağlamak ve kullanıcıya adım adım göstermektir.

1. **Künye yazma.** Esas/karar numarası, daire, tarih ya da karar alıntısını asla kendin yazma,
   hatırlama, tamamlama veya "düzeltme". Hepsi yalnız aracın çıktısından gelir.
2. **Önce izin, sonra kurulum; kodu yeniden yazma.** Araç bu yeteneğin içindedir
   (`scripts/ictihat.py`); imzası `SHA256SUMS` ile doğrulanır. Kullanıcı açıkça "evet" demeden
   ağdan hiçbir şey indirme (künye dizini kurulumu dahil). İmza tutmazsa dur. Kodu "düzeltme",
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

## 1. Kurulum — sırayla, hiçbirini atlamadan

Görev listesi aracın varsa adımları (Kurulum, Öz-test) onunla izle; sohbete kontrol listesi yazma. İlk mesajın 1.1'deki izin sorusudur.

**1.1 İzin iste.** Hiçbir şey indirmeden önce kullanıcıya aynen şunu söyle ve cevabı bekle:

> "Yargıtay künyelerini kayıtlara karşı denetleyen açık kaynaklı aracı hazırlayacağım. Bunun için
> açık bir korpustan yaklaşık 100 MB'lık künye dizinini bu sohbetin geçici çalışma alanına
> indireceğim; bilgisayarınıza bir şey kurulmaz. Kurayım mı?"

Kullanıcı "evet" demezse kurma; sorusu varsa cevapla.

**1.2 İmzayı doğrula, çalışma klasörünü hazırla.** `S` bu `SKILL.md` dosyasının bulunduğu klasördür:

```bash
S=<bu yeteneğin klasörü>
(cd "$S" && sha256sum -c SHA256SUMS)
mkdir -p ~/ictihat && cp "$S/scripts/ictihat.py" "$S/ornekler/ornek_dilekce.txt" ~/ictihat/ && cd ~/ictihat
```

Üç satır da "OK" vermeli. Vermezse dur ve söyle. Bundan sonraki tüm komutları `~/ictihat`
klasöründe çalıştır (kayıtlar orada tutulur).

**1.3 Dizini kur.** `python3 ictihat.py kur` — Yargıtay künye dizinini (yaklaşık 9,8 milyon karar,
yalnız künyeler, ~100 MB) açık korpustan kurar; genellikle 1–3 dakika, yavaş ağda 10 dakikaya kadar.
Komut aracının zaman sınırı 2 dakikadan kısaysa komutu arka planda çalıştır ve bitmesini bekle.
Ağ hatası alırsan kullanıcıya tek cümleyle söyle: "Claude ayarlarında kod çalıştırmanın ağ
erişimine şu alanlar eklenmeli: huggingface.co, cdn.hf.co, pypi.org, files.pythonhosted.org,
hukukihaber.net, bedesten.adalet.gov.tr (isteğe bağlı: extensions.duckdb.org)." Bir izin ya da
güvenlik denetimi engellerse **başka bir yoldan deneme**; dur ve bunu sade bir cümleyle söyle.

**1.4 Öz-test.** `python3 ictihat.py oztest` — sonuç **18/18** olmalı. Değilse kalan satırları
olduğu gibi göster ve dur. Sondaki "SAĞLIK" satırları kapı değildir: hangi teyit kaynaklarının şu an
çalıştığını kullanıcıya tek cümleyle söyle (ör. "Adalet Bakanlığı servisi şu an kapalı; künye
dizini ve Hukuki Haber çalışıyor.").

---

## 2. Demo

Kullanıcı demo ya da adım adım gösterim isterse [DEMO.md](DEMO.md)'yi izle. Günlük işte demo gerekmez; doğrudan 3'e geç.

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
