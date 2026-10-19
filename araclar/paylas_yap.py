"""Tek ekranlık paylaşım sayfası: dokun → telefonun paylaşım listesi → uygulama seç → mesaj sohbette hazır.
Mesaj, robotun kullanıcıyı sorgulayıp onun işi için bir prompt yazmasını ister."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = """Bana iyi bir prompt yazmamda yardım et. İnşaat sektöründe çalışıyorum.

Önce niyetimi anla. Bana şu soruları TEK TEK sor, her seferinde cevabımı bekle:
1) Ne yapmak istiyorum ve neden? (örnek: hakediş kontrolü, teklif karşılaştırma, şantiye raporu, resmî yazı)
2) Sonuç neye benzemeli, kim kullanacak? (tablo, kısa mesaj, rapor, liste)
3) Nelere dikkat edilmeli? (yönetmelik, süre, bütçe, üslup)

Niyetimi anladıktan sonra, yeni bir sohbete yapıştıracağım TEK PARÇA bir prompt yaz. Prompt şunları söylesin: rolü, amacı, işi adım adım, gereken bilgiyi önce kendisinin araması ve bulamazsa bana sorması, çıktının biçimi ve şu kural: "Bilmediğin bir şeyi uydurma; her sayının nereden geldiğini yaz."
Promptu kolayca kopyalayabileceğim tek bir blok içinde ver.

İlk soruyla başla."""

DENETCI = """Sen bağımsız bir denetçisin. Bir işi kontrol edeceğiz; işi yapan sen değilsin ve işe güvenmiyorsun.

Önce benden şu üçünü iste ve hepsi gelmeden başlama:
1) Asıl talep: robottan ne istemiştim, niyetim neydi?
2) Yapılan iş: çıkan cevabın, tablonun ya da belgenin tamamı (yapıştırırım ya da dosya eklerim).
3) Kaynaklar: işte kullanılan belgeler veya bağlantılar (varsa).

Sonra denetimi şöyle yap:
- Alt ajan (sub-agent) çalıştırabiliyorsan denetimi ona ver: işi yapmamış, önceki sohbeti görmemiş bir ajan. Çalıştıramıyorsan kendin yap, ama işi ilk kez görüyormuş gibi.
- İşi satır satır böl. Her sayı, ölçü, tarih, madde numarası, isim ve iddia ayrı bir satır olsun.
- Her satırı bağımsız kontrol et: verdiğim belgede ara ya da resmî kaynağı internette kendin bul. İşin kendi gösterdiği kaynağa körü körüne güvenme; açıp bak.
- Her satır için tablo: No | İddia | Nasıl kontrol edildi (belge, madde ya da bağlantı) | Sonuç: DOĞRU / YANLIŞ / DOĞRULANAMADI | Doğrusu ne olmalı.
- Ayrıca işin asıl talebe uyup uymadığını kontrol et: istenen ama yapılmayan, istenmeyen ama eklenen ne var?

Sonunda kısa bir hüküm yaz: kaç satır, kaçı doğru, kaçı yanlış, kaçı doğrulanamadı; bu iş olduğu gibi kullanılabilir mi, yoksa neyin düzeltilmesi gerekir?
Kurallar: yeni içerik ekleme, sadece denetle. Emin olmadığın satıra DOĞRU deme; DOĞRULANAMADI de.

Hadi, ilk olarak asıl talebi sor."""

SAYFALAR = {
    "": dict(TITLE="Promptunu yazdır", H1="Robota kendi promptunuzu yazdırın",
        ALT="Düğmeye dokunun, açılan listeden uygulamanızı seçin: ChatGPT, Gemini, Claude… Mesaj sohbete hazır gelir; gönderin. Robot önce niyetinizi soracak, sonunda size özel bir prompt yazacak.",
        BTN="Promptumu yazdır", BTNSUB="Dokunun, uygulamanızı seçin, gönderin.",
        FOOT="Çıkan promptu yeni bir sohbete yapıştırın, sonucu alın. İşe yaradıysa robota “bunu skill olarak kaydet” deyin.", MESAJ=PROMPT),
    "denetle": dict(TITLE="İşimi denetlet", H1="Yaptınız. Doğru mu yaptınız?",
        ALT="Düğmeye dokunun, uygulamanızı seçin, gönderin. Denetçi sizden üç şey isteyecek: asıl talebiniz, yapılan iş, kaynaklar. Sonra her satırı tek tek kontrol edip rapor verecek.",
        BTN="İşimi denetlet", BTNSUB="Dokunun, uygulamanızı seçin, gönderin.",
        FOOT="Denetimi yeni bir sohbette yaptırın: işi yapan göz, kendi hatasını zor görür.", MESAJ=DENETCI),
}
sablon = open(os.path.join(HERE, "paylas_sablon.html"), encoding="utf-8").read()
for yol, d in SAYFALAR.items():
    html = sablon
    for k, v in d.items():
        html = html.replace("__" + k + "__", json.dumps(v, ensure_ascii=False) if k == "MESAJ" else v)
    assert "__" not in re.sub(r"__(?![A-Z])", "", html) or "__MESAJ__" not in html
    hedef = os.path.join(HERE, "..", "paylas", yol); os.makedirs(hedef, exist_ok=True)
    open(os.path.join(hedef, "index.html"), "w", encoding="utf-8").write(html)
    print("paylas/" + (yol + "/" if yol else "") + "index.html", len(html), "bayt; mesaj", len(d["MESAJ"]), "karakter")
