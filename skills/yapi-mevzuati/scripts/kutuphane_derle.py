"""Resmî mevzuat PDF'ini madde madde ayırır; her maddeye değişiklik notlarını ve tarihini ekler.
Kullanım: python3 derle.py girdi/<dosya>.pdf "<Mevzuatın adı>" <kısa-ad>
Çıktı: cikti/<kısa-ad>/index.md, madde-XXX.md, maddeler.json
Metin kelimesi kelimesine korunur; yalnız PDF'in satır kırılmaları paragraf içinde birleştirilir."""
import hashlib, json, os, re, subprocess, sys, datetime as dt

pdf, ad, kisa = sys.argv[1], sys.argv[2], sys.argv[3]
KAYNAK = sys.argv[4] if len(sys.argv) > 4 else "resmî PDF (mevzuat.gov.tr)"
import pymupdf
DIP = "\u00a7DIPNOT\u00a7 "


def _norm(t):
    return " ".join(t.split())


def sayfa_satirlari(pdf_yolu):
    """Metin pdftotext'ten gelir (kelimesi kelimesine). Dipnotlar yalnız Word dipnot çizgisi
    (~144 pt, sol kenar) altında, küçük puntolu rakamla başlayan satırlardır; sayfa sonundan çıkarılıp
    ayrı tutulur. Gövdeye dokunulmaz (m² gibi küçük rakamlar korunur)."""
    ham = subprocess.run(["pdftotext", "-enc", "UTF-8", pdf_yolu, "-"], capture_output=True, text=True).stdout
    sayfalar = ham.split("\f")
    d = pymupdf.open(pdf_yolu)
    boy = {}
    for p in d:
        for b in p.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for sp in l["spans"]:
                    boy[round(sp["size"], 1)] = boy.get(round(sp["size"], 1), 0) + len(sp["text"])
    govde = max(boy, key=boy.get) if boy else 12
    out = []
    for pn, sayfa in enumerate(sayfalar):
        ss = [x.rstrip() for x in sayfa.splitlines()]
        dipler = []
        if pn < len(d):
            p = d[pn]
            cizgi = [dr["rect"] for dr in p.get_drawings()
                     if dr["rect"].height < 2 and 130 < dr["rect"].width < 160 and dr["rect"].x0 < 110
                     and dr["rect"].y0 > p.rect.height * 0.3]
            if cizgi:
                sinir = min(r.y0 for r in cizgi)
                alt = []
                for b in p.get_text("dict")["blocks"]:
                    for l in b.get("lines", []):
                        if l["bbox"][1] > sinir and "".join(sp["text"] for sp in l["spans"]).strip():
                            alt.append(l)
                alt.sort(key=lambda l: l["bbox"][1])
                if alt and alt[0]["spans"][0]["size"] < govde - 2 and alt[0]["spans"][0]["text"].strip().isdigit():
                    dipler = [_norm("".join(sp["text"] for sp in l["spans"])) for l in alt]
        if dipler:
            # pdftotext sayfasının sonundan, dipnot satırlarıyla eşleşen satırları çıkar
            dip_kume = set(dipler)
            dip_bas = [x for x in dipler]
            while ss and (not ss[-1].strip() or _norm(ss[-1]) in dip_kume
                          or any(_norm(ss[-1]) and (x.endswith(_norm(ss[-1])) or _norm(ss[-1]).endswith(x)) for x in dip_bas)):
                ss.pop()
            # dipnotları numarayla birleştir
            notlar = []
            for x in dipler:
                if re.match(r"^\d+\s", x) or not notlar: notlar.append(x)
                else: notlar[-1] += " " + x
            out += ss + [DIP + n for n in notlar] + [""]
        else:
            dolu = [i for i, x in enumerate(ss) if x.strip()]
            for uc in (dolu[:1] + dolu[-1:]):
                if re.fullmatch(r"\s*\d{1,4}\s*", ss[uc]): ss[uc] = ""
            out += ss + [""]
    return out


satirlar = sayfa_satirlari(pdf)
MADDE = re.compile(r"^\s*(?:(EK|Ek|GEÇİCİ|Geçici)\s+)?(?:MADDE|Madde)\s+(\d+)\s*(?:/\s*([A-Za-z]))?\s*[-–—]\s*(.*)$")
DEGISIK = re.compile(r"\((Değişik|Ek|Mülga|İptal)[^)]*?(?:RG[-–]\s*)?(\d{1,2})/(\d{1,2})/(\d{4})\s*[-–]?\s*(\d+)[^)]*\)")

def _yaz(t):
    y, a, g, sayi = t
    return f"RG {g}/{a}/{y}-{sayi}" if int(sayi) >= 10000 else f"{g}/{a}/{y} tarihli ve {sayi} sayılı Kanun"


def birlestir(satir_listesi):
    """Paragraf içi satır kırılmalarını birleştirir; fıkra (1) ve bent a) başlarını korur."""
    paras, cur = [], ""
    for s in satir_listesi:
        t = s.strip()
        if not t:
            if cur: paras.append(cur); cur = ""
            continue
        yeni = re.match(r"^(\(\d+\)|[a-zçğıöşü]{1,3}\)|\d+\)|\(Değişik|\(Ek|\(Mülga)", t)
        if cur and yeni:
            paras.append(cur); cur = t
        else:
            cur = f"{cur} {t}".strip() if cur else t
    if cur: paras.append(cur)
    return paras

maddeler, cur, baslik_aday = [], None, ""
islenemeyen, kaynak_etiket, son_no = False, "", 0
ISLENEMEYEN_KAYNAK = re.compile(r"^\s*\(?\d+\)\s*(.*?(?:sayılı|Sayılı).*?)\s*:?\s*$")
for i, s in enumerate(satirlar):
    if s.startswith(DIP):
        if cur: cur.setdefault("dipnot", []).append(s[len(DIP):])
        continue
    if "İŞLENEMEYEN" in s:
        # "... KANUNA/YÖNETMELİĞE İŞLENEMEYEN HÜKÜMLER": buradan sonrası değiştiren metinlerin kendi maddeleri
        if cur: maddeler.append(cur)
        cur, islenemeyen, kaynak_etiket, baslik_aday = None, True, "", ""
        continue
    if islenemeyen and not MADDE.match(s):
        k = ISLENEMEYEN_KAYNAK.match(s)
        if k and len(s) < 200:
            if cur: maddeler.append(cur)
            cur, kaynak_etiket, baslik_aday = None, k.group(1).rstrip(":").strip(), ""
            continue
    m = MADDE.match(s)
    if m:
        tur = (m.group(1) or "").strip(); tur = "GEÇİCİ" if tur.lower().startswith("geç") else ("EK" if tur else "")
        no = m.group(2) + (f"/{m.group(3)}" if m.group(3) else "")
        if not islenemeyen and not tur and int(m.group(2)) < son_no and cur:
            # ana bölümde numara geriye düştü: başka bir kanunun alıntılanan maddesi, madde metninin parçası
            cur["satirlar"].append(s)
            continue
        if cur: maddeler.append(cur)
        if not islenemeyen and not tur:
            son_no = int(m.group(2))
        cur = {"tur": tur, "no": no, "baslik": baslik_aday, "satirlar": [m.group(4)],
               "islenemeyen": (kaynak_etiket or "kaynağı belirtilmemiş") if islenemeyen else ""}
        baslik_aday = ""
        continue
    t = s.strip()
    # madde başlığı: MADDE satırından hemen önceki kısa, noktasız satır
    if t and len(t) < 90 and not t.endswith((".", ",", ";", ":")) and not re.match(r"^(\(\d+\)|[a-zçğıöşü]{1,3}\))", t):
        nxt = next((x for x in satirlar[i+1:i+3] if x.strip()), "")
        if MADDE.match(nxt):
            baslik_aday = t
            continue
    if cur: cur["satirlar"].append(s)
if cur: maddeler.append(cur)

out = os.path.join("cikti", kisa); os.makedirs(out, exist_ok=True)
imza = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
tumu, en_son, kullanilan_dosya = [], None, set()
for md in maddeler:
    paras = birlestir(md["satirlar"])
    metin = "\n\n".join(paras)
    def _sayisal(p):
        tok = p.split(); say = sum(1 for t in tok if re.fullmatch(r"[\d.,%/≤<>=-]+", t))
        return say >= 8 and say / max(len(tok), 1) > 0.3
    tablo = sum(1 for p in paras if re.fullmatch(r"[\d.,\s%/-]+", p)) >= 4 or any(_sayisal(p) for p in paras)
    degisiklikler = sorted({(int(y), int(a), int(g), sayi, tur) for tur, g, a, y, sayi in DEGISIK.findall(metin)})
    son = max(((y, a, g, sayi) for y, a, g, sayi, _ in degisiklikler), default=None)
    if son and (en_son is None or son > en_son): en_son = son
    kimlik = (md["tur"].lower().replace("geçici", "gecici") + "-" if md["tur"] else "") + md["no"].replace("/", "-")
    dosya = f"madde-{kimlik.zfill(3) if kimlik.isdigit() else kimlik}.md"
    etiket = f"{md['tur'] + ' ' if md['tur'] else ''}MADDE {md['no']}"
    if md.get("islenemeyen"):
        etiket = f"İşlenemeyen hüküm · {md['islenemeyen']} · {etiket}"
        dosya = "islenemeyen-" + dosya
    taban, sira = dosya[:-3], 2
    while dosya in kullanilan_dosya:
        dosya, sira = f"{taban}-{sira}.md", sira + 1
    kullanilan_dosya.add(dosya)
    son_yazi = _yaz(son) if son else "yayımdan beri değişiklik notu yok"
    with open(os.path.join(out, dosya), "w", encoding="utf-8") as f:
        f.write(f"# {ad} — {etiket}{' · ' + md['baslik'] if md['baslik'] else ''}\n\n")
        f.write(f"> Kaynak: {KAYNAK}, SHA-256 `{imza[:16]}…` · Bu maddedeki son değişiklik notu: {son_yazi}\n\n")
        if tablo:
            f.write("> ⚠ Bu madde tablo içeriyor; metne çevirirken tablo düzeni bozulmuş olabilir. Sayıları resmî PDF'teki tablodan okuyun.\n\n")
        f.write(metin + "\n")
        if md.get("dipnot"):
            f.write("\n---\n\n**Dipnotlar** (mevzuat.gov.tr'nin sayfa altı notları; madde metnine dahil değil):\n\n")
            for dn in md["dipnot"]:
                f.write(f"- {dn}\n")
    tumu.append({"dipnot": md.get("dipnot", []), "tablo": tablo, "etiket": etiket, "baslik": md["baslik"], "dosya": dosya, "son_degisiklik": son_yazi, "metin": metin})
with open(os.path.join(out, "maddeler.json"), "w", encoding="utf-8") as f:
    json.dump({"ad": ad, "sha256": imza, "derlendi": dt.date.today().isoformat(), "maddeler": tumu}, f, ensure_ascii=False, indent=1)
with open(os.path.join(out, "index.md"), "w", encoding="utf-8") as f:
    son_yazi = _yaz(en_son) if en_son else "—"
    f.write(f"# {ad}\n\nKaynak: {KAYNAK}. Madde madde, kelimesi kelimesine. En son değişiklik notu: **{son_yazi}** · derlendi: {dt.date.today():%d.%m.%Y}\n\n")
    for t in tumu:
        f.write(f"- [{t['etiket']}{' — ' + t['baslik'] if t['baslik'] else ''}]({t['dosya']}) · {t['son_degisiklik']}\n")
print(f"{ad}: {len(tumu)} madde, en son değişiklik {son_yazi}")
