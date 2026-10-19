"""Tek ekranlık paylaşım sayfası: dokun → telefonun paylaşım listesi → uygulama seç → mesaj sohbette hazır.
Mesaj, robotun kullanıcıyı sorgulayıp onun işi için bir prompt yazmasını ister."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
MESAJ = """Bana iyi bir prompt yazmamda yardım et. İnşaat sektöründe çalışıyorum.

Önce bana şu soruları TEK TEK sor, her seferinde cevabımı bekle:
1) Yapay zekâya hangi işi yaptırmak istiyorum? (örnek: hakediş kontrolü, şartname özeti, teklif karşılaştırma, şantiye raporu, resmî yazı)
2) Sonuç neye benzemeli? (tablo, kısa mesaj, rapor, madde madde liste)
3) Elimde hangi belgeler var? (PDF, fotoğraf, Excel)
4) Nelere dikkat edilmeli? (yönetmelik, süre, bütçe, kim okuyacak)

Cevaplarımı aldıktan sonra, yeni bir sohbete yapıştıracağım TEK PARÇA bir prompt yaz. Prompt şunları söylesin: rolü, işi adım adım, belgeleri nasıl kullanacağını, çıktının biçimini ve şu kuralı: "Bilmediğin ya da belgede olmayan bir şeyi uydurma; her sayının nereden geldiğini yaz."
Promptu kolayca kopyalayabileceğim tek bir blok içinde ver.

İlk soruyla başla."""
html = open(os.path.join(HERE, "paylas_sablon.html"), encoding="utf-8").read()
html = html.replace("__MESAJ__", json.dumps(MESAJ, ensure_ascii=False))
assert "__MESAJ__" not in html
open(os.path.join(HERE, "..", "paylas", "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html), "bayt; mesaj", len(MESAJ), "karakter")
