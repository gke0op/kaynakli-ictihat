"""Tek ekranlık paylaşım sayfası: dokun → telefonun paylaşım listesi → uygulama seç → mesaj sohbette hazır.
Mesaj, robotun kullanıcıyı sorgulayıp onun işi için bir prompt yazmasını ister."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
MESAJ = """Bana iyi bir prompt yazmamda yardım et. İnşaat sektöründe çalışıyorum.

Önce niyetimi anla. Bana şu soruları TEK TEK sor, her seferinde cevabımı bekle:
1) Ne yapmak istiyorum ve neden? (örnek: hakediş kontrolü, teklif karşılaştırma, şantiye raporu, resmî yazı)
2) Sonuç neye benzemeli, kim kullanacak? (tablo, kısa mesaj, rapor, liste)
3) Nelere dikkat edilmeli? (yönetmelik, süre, bütçe, üslup)

Niyetimi anladıktan sonra, yeni bir sohbete yapıştıracağım TEK PARÇA bir prompt yaz. Prompt şunları söylesin: rolü, amacı, işi adım adım, gereken bilgiyi önce kendisinin araması ve bulamazsa bana sorması, çıktının biçimi ve şu kural: "Bilmediğin bir şeyi uydurma; her sayının nereden geldiğini yaz."
Promptu kolayca kopyalayabileceğim tek bir blok içinde ver.

İlk soruyla başla."""
html = open(os.path.join(HERE, "paylas_sablon.html"), encoding="utf-8").read()
html = html.replace("__MESAJ__", json.dumps(MESAJ, ensure_ascii=False))
assert "__MESAJ__" not in html
open(os.path.join(HERE, "..", "paylas", "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html), "bayt; mesaj", len(MESAJ), "karakter")
