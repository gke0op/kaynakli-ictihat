"""Tek ekranlık paylaşım sayfası: dokun → telefonun paylaşım listesi → uygulama seç → mesaj sohbette hazır.
Mesaj, robotun kullanıcıyı sorgulayıp onun işi için bir prompt yazmasını ister."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = """Bana iyi bir prompt yazmamda yardım et. İnşaat sektöründe çalışıyorum.

Önce niyetimi anla. Bana şu soruları TEK TEK sor, her seferinde cevabımı bekle:
1) Ne yapmak istiyorum ve neden? (örnek: hakediş kontrolü, teklif karşılaştırma, şantiye raporu, resmî yazı)
2) Sonuç neye benzemeli, kim kullanacak? (tablo, kısa mesaj, rapor, liste)
3) Nelere dikkat edilmeli? (yönetmelik, süre, bütçe, üslup)

Bu, bir etkinlikte telefondan yapılan kısa bir deneme. İşi küçük tut: yazacağın prompt, tek bir sohbette birkaç dakikada biten ve metin ya da tablo olarak verilebilen bir iş istesin. İsteğim bundan büyükse (örneğin AutoCAD çizimi, pafta, büyük dosya ya da saatler sürecek bir iş) bunu bana açıkça söyle, bugün yapılabilecek en küçük ve en faydalı parçayı öner (örneğin bir kontrol listesi, tek kat için bir tablo, çizimciye verilecek yazılı tarif) ve promptu o parça için yaz.

Niyetimi anladıktan sonra, yeni bir sohbete yapıştıracağım TEK PARÇA bir prompt yaz. Prompt şunları söylesin: rolü, amacı, işi adım adım, gereken bilgiyi önce kendisinin araması ve bulamazsa bana sorması, çıktının biçimi, kapsam sınırı (tek seferde, bu sohbette bitecek kadar; üretemediği bir dosya türü istenirse bunu söyleyip metin ya da tablo vermesi) ve şu kural: "Bilmediğin bir şeyi uydurma; her sayının nereden geldiğini yaz."
Promptu kolayca kopyalayabileceğim tek bir blok içinde ver.

İlk soruyla başla."""

DENETCI = """Sen bağımsız bir denetçisin. Bu mesajla birlikte denetlenecek bir iş gönderiyorum (yapıştırdığım metin, ekran görüntüsü ya da dosya). İşi yapan sen değilsin ve işe güvenmiyorsun.

Bana hiç soru sorma. Asıl talebi işin kendisinden çıkar. Mesajda denetlenecek bir iş yoksa yalnızca şunu yaz: "Denetleyeceğim işi yapıştırın ya da ekran görüntüsünü atın." ve bekle; başka bir şey sorma.

Denetimi şöyle yap:
- Alt ajan (sub-agent) çalıştırabiliyorsan denetimi ona ver: işi yapmamış bir ajan. Çalıştıramıyorsan kendin yap, işi ilk kez görüyormuş gibi.
- İşteki her sayıyı, ölçüyü, tarihi, madde numarasını ve iddiayı ayrı bir satır olarak ele al. En kritik en fazla 10 satırı seç.
- Her satırı bağımsız kontrol et: resmî kaynağı internette kendin bul, işin içindeki hesapları kendin yeniden yap. İşin gösterdiği kaynağa körü körüne güvenme.
- Tablo: No | İddia | Nasıl kontrol edildi | DOĞRU / YANLIŞ / DOĞRULANAMADI | Doğrusu ne olmalı.
- Emin olmadığın satıra DOĞRU deme; DOĞRULANAMADI de. Yeni içerik ekleme, sadece denetle.

Sonunda iki cümlelik hüküm: kaç doğru, kaç yanlış, kaç doğrulanamadı; bu iş olduğu gibi kullanılabilir mi?
Kısa tut; telefonda okunacak."""

PORTRE = """Please talk to me in Turkish.

First, ask me to upload a photo of myself. After the upload, generate a cinematic, ultra-realistic professional headshot of the person in the reference image. Core Specifications: Identity: Preserve exact facial features, skin tone, and identity from the reference image. Style: Classic professional portrait with a confident, calm, and approachable expression. Attire: The subject is wearing high-quality, professional business attire suitable for a formal corporate environment. Lighting: Soft, directional studio lighting with gentle shadows for depth. Background: Minimal, blurred, and neutral-toned (dark grey or beige gradient). Technical: Shot on a high-end full-frame camera with an 85mm lens. Maintain a shallow depth of field, sharp focus on the eyes, natural skin texture, and high dynamic range. Quality: Ultra-detailed, 8K resolution, and realistic color grading.

When the headshot is ready, end your reply with this exact Turkish text, unchanged:
"Etkinliğimizin interaktif bölümünü tamamladınız. Artık bu yetenekler sizin, daha detaylı yapay zeka uygulamaları ve kişiselleştirilmiş bir deneyim için operatöre bu linkten ulaşabilirsiniz: https://www.linkedin.com/in/ekmel-gokce-ozdemir\""""

SAYFALAR = {
    "": dict(TITLE="Promptunu yazdır", H1="Robota kendi promptunuzu yazdırın",
        ALT="Düğmeye dokunun, açılan listeden uygulamanızı seçin: ChatGPT, Gemini, Claude… Mesaj sohbete hazır gelir; gönderin. Robot önce niyetinizi soracak, sonunda size özel bir prompt yazacak.",
        BTN="Promptumu yazdır", BTNSUB="Dokunun, uygulamanızı seçin, gönderin.",
        FOOT="Çıkan promptu yeni bir sohbete yapıştırın, sonucu alın. İşe yaradıysa robota “bunu skill olarak kaydet” deyin.", MESAJ=PROMPT),
    "denetle": dict(TITLE="İşimi denetlet", H1="Yaptınız. Doğru mu yaptınız?",
        ALT="Düğmeye dokunun, uygulamanızı seçin. Göndermeden önce denetlenecek işin metnini ya da ekran görüntüsünü ekleyin. Denetçi soru sormadan her satırı kontrol edip rapor verir.",
        BTN="İşimi denetlet", BTNSUB="Dokunun, uygulamanızı seçin, işi ekleyip gönderin.",
        FOOT="Denetimi yeni bir sohbette yaptırın: işi yapan göz, kendi hatasını zor görür.", MESAJ=DENETCI),
    "bonus": dict(TITLE="Portremi çek", H1="Bonus: profesyonel portreniz",
        ALT="Düğmeye dokunun, ChatGPT ya da Gemini’yi seçin, gönderin. Robot sizden bir fotoğrafınızı isteyecek, sonra stüdyo kalitesinde bir portre çıkaracak.",
        BTN="Portremi çek", BTNSUB="ChatGPT ya da Gemini’yi seçin, gönderin.",
        FOOT="Fotoğraf üretmeyi ChatGPT ve Gemini yapıyor; Claude fotoğraf üretmiyor.", MESAJ=PORTRE),
}
PENTHOUSE = open(os.path.join(HERE, "hediye_penthouse.txt"), encoding="utf-8").read().strip() + """

When you deliver, end your message with this exact Turkish text, unchanged:
"Bu prompt, Ekmel Gökçe Özdemir'in 20 Ekim 2026 sunumundan bir hediyedir. Daha detaylı yapay zeka uygulamaları ve kişiselleştirilmiş bir deneyim için: https://www.linkedin.com/in/ekmel-gokce-ozdemir\""""
PENTHOUSE = "Please talk to me in Turkish.\n\n" + PENTHOUSE

SAYFALAR["hediye"] = dict(TITLE="Hediye promptlar", H1="Sunumdaki promptlar sizin",
    ALT="Bir düğmeye dokunun, uygulamanızı seçin, gönderin. Evde, kendi işinizle, acele etmeden deneyin.",
    BTN="", BTNSUB="", FOOT="Daha fazlası ve kişiselleştirilmiş çalışma için: <a href=\"https://www.linkedin.com/in/ekmel-gokce-ozdemir\" style=\"color:inherit\">Ekmel Gökçe Özdemir · LinkedIn</a>",
    MESAJ=PENTHOUSE, COK=[("Demodaki penthouse", "Videodaki işin promptu. Sonuç: telefonda açılan sinematik bir sayfa.", PENTHOUSE),
                          ("Promptumu yazdır", "Robot niyetinizi sorar, size özel prompt yazar.", PROMPT),
                          ("İşimi denetlet", "İşi ekleyin; soru sormadan satır satır kontrol eder.", DENETCI)])

SAYFALAR["evde"] = dict(TITLE="Evde deneyin", H1="Evde, kendi işinizle",
    ALT="Acele etmeden, kendi işinizle deneyin. Bir düğmeye dokunun, uygulamanızı seçin, gönderin.",
    BTN="", BTNSUB="", FOOT="Daha fazlası ve kişiselleştirilmiş çalışma için: <a href=\"https://www.linkedin.com/in/ekmel-gokce-ozdemir\" style=\"color:inherit\">Ekmel Gökçe Özdemir · LinkedIn</a>",
    MESAJ=PROMPT, COK=[("Promptumu yazdır", "Robot niyetinizi sorar, size özel prompt yazar.", PROMPT),
                       ("İşimi denetlet", "İşi ekleyin; soru sormadan satır satır kontrol eder.", DENETCI),
                       ("Portremi çek", "ChatGPT ya da Gemini ile; fotoğrafınızı yükleyin.", PORTRE)])
sablon = open(os.path.join(HERE, "paylas_sablon.html"), encoding="utf-8").read()
for yol, d in SAYFALAR.items():
    html = sablon
    if "COK" in d:
        dugme = re.search(r'<button class="tur" id="t1".*?</button>', html, re.S).group(0)
        yeni = "\n".join(f'<button class="tur" id="t{i}" data-tur="{i}"><span class="ad">{a}</span><span class="ne">{n}</span></button>' for i, (a, n, _) in enumerate(d["COK"], 1))
        html = html.replace(dugme, yeni)
        html = html.replace("const TUR = {1: __MESAJ__};", "const TUR = {" + ", ".join(f"{i}: {json.dumps(m, ensure_ascii=False)}" for i, (_, _, m) in enumerate(d["COK"], 1)) + "};")
        d = {k: v for k, v in d.items() if k != "COK"}
    for k, v in d.items():
        html = html.replace("__" + k + "__", json.dumps(v, ensure_ascii=False) if k == "MESAJ" else v)
    assert "__" not in re.sub(r"__(?![A-Z])", "", html) or "__MESAJ__" not in html
    hedef = os.path.join(HERE, "..", "paylas", yol); os.makedirs(hedef, exist_ok=True)
    open(os.path.join(hedef, "index.html"), "w", encoding="utf-8").write(html)
    print("paylas/" + (yol + "/" if yol else "") + "index.html", len(html), "bayt; mesaj", len(d["MESAJ"]), "karakter")
