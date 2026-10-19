"""Tek ekranlık paylaşım sayfası: dokun → telefonun paylaşım listesi → uygulama seç → mesaj sohbette hazır."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
md = open(os.path.join(HERE, "..", "kutuphane", "planli-alanlar-imar-yonetmeligi", "madde-031.md"), encoding="utf-8").read()
fikra2 = re.search(r"^\(2\) .*?(?=^\(3\) )", md, re.S | re.M).group(0).strip()
bentler = "\n".join(p for p in fikra2.split("\n\n") if p.startswith(("(2)", "a)", "b)")))
KURAL = """Bu sohbet boyunca benimle şu kurallarla çalış:

1) Verdiğin her somut bilgiyi (sayı, ölçü, madde no, standart no, tarih, fiyat, isim) etiketle:
[BELGE] benim verdiğim belgeden; birebir alıntı ve sayfa/madde ile
[KAYNAK] şimdi açtığın resmî bir sayfadan; bağlantısıyla
[HAFIZA] doğrulamadığın bilgi; kullanmadan önce kontrol edilmeli
2) Bilmiyorsan ya da bulamıyorsan uydurma, "bilmiyorum" de.
3) Hesap yaparsan her adımı birimiyle göster.
4) Belge verirsem yalnız ona dayan; belgede olmayanı varmış gibi yazma.
5) Her cevabın sonuna "Kontrol etmem gerekenler" listesi koy."""
SORU = "Planlı Alanlar İmar Yönetmeliği'ne göre konutta ortak merdivenin rıht yüksekliği en fazla, basamak genişliği en az kaç cm? Hangi madde?"
tur1 = f"{KURAL}\n\nİlk soru: {SORU}"
tur2 = (f"{KURAL}\n\nAşağıda Planlı Alanlar İmar Yönetmeliği Madde 31'in resmî metninden bir bölüm var (mevzuat.gov.tr, 1 Temmuz 2026 değişikliği dahil güncel metin). "
        f"Soruyu YALNIZ bu metne dayanarak cevapla; birebir alıntı yap, fıkra ve bendi yaz.\n\n--- RESMÎ METİN: MADDE 31 ---\n{bentler}\n--- METİN SONU ---\n\nSoru: {SORU}")
html = open(os.path.join(HERE, "paylas_sablon.html"), encoding="utf-8").read()
html = html.replace("__TUR1__", json.dumps(tur1, ensure_ascii=False)).replace("__TUR2__", json.dumps(tur2, ensure_ascii=False))
assert "__TUR" not in html
open(os.path.join(HERE, "..", "paylas", "index.html"), "w", encoding="utf-8").write(html)
print("index.html", len(html), "bayt")
