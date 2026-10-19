"""Sağlama: her madde metni kaynak PDF'in kelime dizisinde AYNI SIRAYLA geçer mi; aradaki atlamalar yalnız dipnot mu."""
import json, re, subprocess, collections, sys
Z = "/home/claude/kutuphane/zip_ham/mevzuat_pdfs"
tum_ok = True
for satir in open("/home/claude/kutuphane/liste.txt", encoding="utf-8"):
    f, ad, kisa = satir.strip().split("|")
    ham = subprocess.run(["pdftotext", "-enc", "UTF-8", f"{Z}/{f}", "-"], capture_output=True, text=True).stdout
    H = re.findall(r"\w+", ham)
    j = json.load(open(f"cikti/{kisa}/maddeler.json", encoding="utf-8"))
    dip = " ".join(x for m in j["maddeler"] for x in m["dipnot"])
    D = collections.Counter(re.findall(r"\w+", dip))
    i, sorun, atlanan = 0, [], collections.Counter()
    for m in j["maddeler"]:
        W = re.findall(r"\w+", m["metin"])
        for w in W:
            k = i
            while k < len(H) and H[k] != w: k += 1
            if k == len(H): sorun.append(m["etiket"]); break
            atlanan.update(H[i:k]); i = k + 1
    # atlanan kelimelerden dipnotta olmayanlar (başlıklar, bölüm adları vb.)
    yabanci = sum(c for w, c in atlanan.items() if D[w] == 0 and not w.isdigit())
    et = [m["etiket"] for m in j["maddeler"]]
    tekrar = [k for k, v in collections.Counter(et).items() if v > 1]
    ok = not sorun
    tum_ok &= ok
    print(f"{kisa[:40]:40} madde={len(et):3} dipnot={sum(len(m['dipnot']) for m in j['maddeler']):3} sıra={'TAMAM' if ok else 'SORUN '+str(sorun[:3])} tekrar={tekrar} dipnot-dışı atlanan kelime={yabanci}")
print("HEPSİ SIRALI" if tum_ok else "SORUN VAR")
