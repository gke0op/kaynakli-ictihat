#!/usr/bin/env python3
"""kaynakli-ictihat v2 — Yargıtay künyesini model değil kod doğrular.

Katmanlar (sırayla, hiçbiri tek başına güvenilmez):
  1. Yerel künye dizini: ~9,8 milyon Yargıtay kararı (1997–Mayıs 2026), açık CC0 korpustan
     (Hugging Face: mrfg/turkish-court-decisions). Her satırda resmî belge no var:
     https://mevzuat.adalet.gov.tr/ictihat/<belge_no>
  2. Adalet Bakanlığı servisi (bedesten.adalet.gov.tr) — açıksa canlı teyit ve yeni kararlar.
  3. Hukuki Haber — künyeden kurulan adres; gerçek künye 200, uydurma 404.
Tam metin: korpustan (belge no ile), olmazsa Bakanlık servisinden, olmazsa Hukuki Haber'den.

Komutlar:
  kur                              dizini indir ya da kur (bir kez)
  oztest                           kendi kendini dener; GEÇMEZSE kullanılmaz
  kontrol "<künye>" [...]          künye var mı? (BULUNDU / KISMEN / BULUNAMADI)
  denetle <dosya>                  dosyadaki (txt/md/pdf/docx/udf) tüm Yargıtay künyelerini denetler
  getir "<künye>"|<belge_no>       kararın tam metnini kayda alır (K1, K2 ...)
  cikar <Kn> --kelime k1 k2        ilgili paragrafları BİREBİR döker
  konu k1 k2 ... [--daire "11. HD"] [--yildan 2015]   korpusun TAM METNİNDE konu araması
  ara "<ifade>"                    Bakanlık servisi açıksa konu araması
  onayla <Kn> hepsi|P3 ...         insan "evet" dedikten sonra
  reddet <Kn>                      insan "hayır" dedikten sonra
  dogrula <taslak.md>              [[Kn]]/[[Kn-Pm]] etiketlerini yerleştirir, kaynaksız künyeyi yakalar
  liste
Yalnız standart kütüphane + duckdb (kur komutu yükler). PDF için pypdf ya da pdftotext.
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import html as _html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

SURUM = "2.3"
UA = f"kaynakli-ictihat/{SURUM}"
# Kendi aynamız (doluysa önce bu denenir); boşsa dizin asıl korpustan kurulur.
DIZIN_AYNA = os.environ.get("ICTIHAT_DIZIN_URL", "")
def _ayar(anahtar: str):
    """İsteğe bağlı yerel ayar: çalışma klasöründeki ictihat_ayar.json (ör. korpusun yerel kopyası)."""
    try:
        return json.load(open("ictihat_ayar.json", encoding="utf-8")).get(anahtar)
    except (OSError, ValueError):
        return None


KORPUS = (os.environ.get("ICTIHAT_KORPUS") or _ayar("korpus") or
          "https://huggingface.co/datasets/mrfg/turkish-court-decisions/resolve/main/data/yargitay/"
          "train-{:05d}-of-00017.parquet")
PARCA_SAYISI = 17
API = "https://bedesten.adalet.gov.tr/emsal-karar"
SAYFA = "https://mevzuat.adalet.gov.tr/ictihat"
HH = "https://www.hukukihaber.net"
DIZIN = os.environ.get("ICTIHAT_DIZIN", "kunye_index.parquet")
KAYIT = os.environ.get("ICTIHAT_KAYIT", "ictihat_kayit.json")
RAPOR = os.environ.get("ICTIHAT_RAPOR", "ictihat_raporu.md")
METIN_DIZIN = os.environ.get("ICTIHAT_METIN", "ictihat_metin")
KAPSAM = "dizin kapsamı: 1997–2025 geniş, Ocak–Mart 2026 kısmi, Nisan–Mayıs 2026 çok seyrek, sonrası yok"


class Dur(Exception):
    """Kaynağa ulaşılamadı ya da kaynak durdurdu."""


# ================= Türkçe metin =================

def tr_kucuk(s: str) -> str:
    s = s.replace("I", "ı").replace("İ", "i").lower().replace("̇", "")
    return s.translate(str.maketrans("âîû", "aiu"))


def _kok(w: str) -> str:
    w = tr_kucuk(w.strip())
    return w[:-1] if len(w) >= 5 and w[-1] in "pçtk" else w  # ihtiyaç -> ihtiyacı


def kalip(kelime: str) -> re.Pattern:
    parcalar = [re.escape(_kok(w)) + r"\w*" for w in kelime.split() if w.strip()]
    return re.compile(r"(?<!\w)" + r"\s+".join(parcalar))


# ================= Künye ayrıştırma =================

NO = r"(\d{4})\s*/\s*(\d{1,6}(?:\s*-\s*\d{1,6})?)"
_E = [re.compile(r"\b(?:E|Esas)\s*(?:No|Numarası|Sayısı)?\s*[.:]?\s*" + NO, re.I),
      re.compile(r"\b" + NO + r"\s*(?:E\b\.?|Esas\b)", re.I)]
_K = [re.compile(r"\b(?:K|Karar)\s*(?:No|Numarası|Sayısı)?\s*[.:]?\s*" + NO, re.I),
      re.compile(r"\b" + NO + r"\s*(?:K\b\.?|Karar\b)", re.I)]
_T = re.compile(r"\b(?:T|Tarih|Tarihi|Karar Tarihi)\s*[.:]?\s*(\d{1,2})[./](\d{1,2})[./](\d{4})", re.I)


def _no(yil: str, sira: str) -> str:
    sira = re.sub(r"\s", "", sira)
    return f"{yil}/" + "-".join(str(int(p)) for p in sira.split("-"))


def no_normal(s: str | None) -> str | None:
    if not s or "/" not in s:
        return None
    y, _, r = s.partition("/")
    try:
        return _no(y.strip(), r.strip())
    except ValueError:
        return None


def daire_bul(s: str) -> str | None:
    """'3. HD', '3. Hukuk Dairesi', 'HGK', 'CGK' ... -> dizindeki ad."""
    t = tr_kucuk(s)
    adaylar = []  # (bitiş konumu, ad): metinde EN SON geçen mahkeme adı kazanır
    for kp, ad in ((r"\bhgk\b|hukuk\s+genel\s+kurul", "Hukuk Genel Kurulu"),
                   (r"\bcgk\b|ceza\s+genel\s+kurul", "Ceza Genel Kurulu"),
                   (r"\by?ibk\b|içtihad\w*\s+birleştir|büyük\s+genel\s+kurul", "İBK")):
        adaylar += [(m.end(), ad) for m in re.finditer(kp, t)]
    for m in re.finditer(r"(\d{1,2})\s*\.\s*(?:(h)(?:ukuk)?|(c)(?:eza)?)\s*\.?\s*d(?:aire|\.|\b)", t):
        adaylar.append((m.end(), f"{int(m.group(1))}. {'Hukuk' if m.group(2) else 'Ceza'} Dairesi"))
    return max(adaylar)[1] if adaylar else None


def kunye_ayristir(s: str) -> dict:
    def ilk(kp):
        for k in kp:
            m = k.search(s)
            if m:
                return _no(m.group(1), m.group(2))
        return None
    t = _T.search(s)
    return {"daire": daire_bul(s), "esas": ilk(_E), "karar": ilk(_K),
            "tarih": f"{int(t.group(1)):02d}.{int(t.group(2)):02d}.{t.group(3)}" if t else None}


_MAHKEME_IZI = re.compile(
    r"yargıtay|\bhgk\b|\bcgk\b|\by?ibk\b|\d{1,2}\s*\.\s*(?:h|c|hukuk|ceza)\s*\.?\s*d"
    r"|bölge\s+adliye|\bbam\b|asliye|sulh|ağır\s+ceza|idare\s+mahkeme|vergi\s+mahkeme"
    r"|danıştay|anayasa\s+mahkeme|icra\s+(?:hukuk|ceza)|iş\s+mahkeme|aile\s+mahkeme", re.I)
_YARGITAY_IZI = re.compile(r"yargıtay|\bhgk\b|\bcgk\b|\by?ibk\b|\d{1,2}\s*\.\s*(?:h|c|hukuk|ceza)\s*\.?\s*d", re.I)


def kunyeleri_cikar(metin: str) -> list[dict]:
    """Serbest metindeki künye anılarını bulur. Her esas numarası bir adaydır; mahkemesi,
    önündeki en yakın mahkeme izine göre belirlenir (Yargıtay dışı olanlar ayrıca işaretlenir)."""
    bulunan, son_bitis = [], -1
    for kp in _E:
        for m in kp.finditer(metin):
            bulunan.append(m)
    bulunan.sort(key=lambda m: m.start())
    sonuc = []
    for m in bulunan:
        if m.start() < son_bitis:
            continue
        bas = max(0, m.start() - 160)
        pencere = metin[bas:min(len(metin), m.end() + 90)]
        geri = tr_kucuk(metin[bas:m.start()])
        izler = list(_MAHKEME_IZI.finditer(geri))
        yargitay = bool(izler) and bool(_YARGITAY_IZI.fullmatch(izler[-1].group(0)))
        if yargitay and len(izler) > 1 and re.match(r"\d", izler[-1].group(0)):
            # "Bölge Adliye Mahkemesi 54. Hukuk Dairesi": daire, hemen önündeki alt mahkemeye aittir
            onceki = izler[-2]
            if not _YARGITAY_IZI.fullmatch(onceki.group(0)) and izler[-1].start() - onceki.end() < 40:
                yargitay = False
        on = metin[m.start():min(len(metin), m.end() + 90)]
        k = None
        for kp in _K:
            km = kp.search(on)
            if km and km.start() > 0:
                k = km
                break
        bitis = m.start() + k.end() if k else m.end()
        tm = re.match(r"\s*,?\s*(?:T|Tarih|Tarihi)\s*[.:]?\s*\d{1,2}[./]\d{1,2}[./]\d{4}", metin[bitis:bitis + 30])
        if tm:  # künye tarihle bitiyorsa işaret tarihten sonra konur
            bitis += tm.end()
        son_bitis = bitis
        if izler:  # alıntı, künyeye ait mahkeme adından başlar ("İstanbul Bölge Adliye…", "Yargıtay 3. HD…")
            cap = izler[-2] if len(izler) > 1 and izler[-1].start() - izler[-2].end() < 40 else izler[-1]
            bas_a = bas + cap.start()
            onceki_sozcuk = metin.rfind(" ", max(0, bas_a - 25), max(0, bas_a - 1))
            if not _YARGITAY_IZI.fullmatch(cap.group(0)) and onceki_sozcuk >= 0:
                bas_a = onceki_sozcuk + 1  # şehir adı: "İstanbul Bölge Adliye…"
        else:
            bas_a = max(0, m.start() - 40)
        alinti = re.sub(r"\s+", " ", metin[bas_a:bitis]).strip().lstrip("(“\"'[ ")
        d = kunye_ayristir(pencere)
        d["daire"] = daire_bul(metin[bas:m.start()]) or daire_bul(metin[m.end():m.end() + 90])
        d.update(esas=_no(m.group(1), m.group(2)), karar=_no(k.group(1), k.group(2)) if k else None,
                 yargitay=yargitay, alinti=alinti, bitis=bitis)
        sonuc.append(d)
    return sonuc


# ================= HTTP =================

_son = {}


def _istek(url: str, veri: bytes | None = None, basliklar: dict | None = None,
           zaman: int = 30, beklenen_kod=(200,)) -> tuple[int, str, str]:
    host = url.split("/")[2]
    bekle = _son.get(host, 0) + 1.0 - time.monotonic()
    if bekle > 0:
        time.sleep(bekle)
    r = urllib.request.Request(url, data=veri, method="POST" if veri else "GET",
                               headers={"User-Agent": UA, **(basliklar or {})})
    try:
        for deneme in (1, 2):
            try:
                with urllib.request.urlopen(r, timeout=zaman) as y:
                    return y.status, y.headers.get("content-type", ""), y.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                if e.code in (403, 429):
                    raise Dur(f"{host} isteği durdurdu (HTTP {e.code}); yeniden denenmez.")
                return e.code, e.headers.get("content-type", ""), e.read().decode("utf-8", "replace")
            except (urllib.error.URLError, OSError) as e:
                if deneme == 2:
                    raise Dur(f"{host} ulaşılamadı: {getattr(e, 'reason', e)}")
                time.sleep(2)
    finally:
        _son[host] = time.monotonic()
    raise Dur(f"{host} ulaşılamadı")


def _bedesten(uc: str, veri: dict, sayfali=False) -> dict:
    govde = {"data": veri, **({"paging": True} if sayfali else {})}
    kod, tur, ham = _istek(f"{API}/{uc}", json.dumps(govde).encode(),
                           {"Content-Type": "application/json; charset=UTF-8",
                            "Accept": "application/json"}, zaman=45)
    if kod != 200 or "json" not in tur.lower():
        raise Dur(f"Bakanlık servisi yanıt vermiyor (HTTP {kod}).")
    j = json.loads(ham)
    if (j.get("metadata") or {}).get("FMTY") == "ERROR":
        raise Dur("Bakanlık servisi hata verdi: " + str(j["metadata"].get("FMTE")))
    return j.get("data") or {}


# ================= Dizin =================

def _duckdb():
    try:
        import duckdb  # type: ignore
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb"], check=False)
        try:
            import duckdb  # type: ignore
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--user",
                            "--break-system-packages", "duckdb"], check=False)
            import site, importlib
            sys.path.append(site.getusersitepackages())
            importlib.invalidate_caches()
            import duckdb  # type: ignore
    global HTTPFS
    con = duckdb.connect()
    if HTTPFS:
        try:
            con.execute("INSTALL httpfs; LOAD httpfs;")
        except Exception:
            HTTPFS = False  # eklenti indirilemedi (extensions.duckdb.org kapalı): pyarrow yoluna geç
    return con


HTTPFS = os.environ.get("ICTIHAT_HTTPFS", "1") != "0"


class _UzakDosya:
    """Uzak bir dosyayı HTTP Range istekleriyle okunan dosya gibi sunar (pyarrow için)."""

    def __init__(self, url: str, blok: int = 1 << 20):
        self.url, self.blok, self.konum, self._onbellek = url, blok, 0, {}
        r = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(r, timeout=60) as y:
            self.url = y.geturl()
            self.boy = int(y.headers["Content-Length"])
        self.closed = False

    def _blok(self, i: int) -> bytes:
        if i not in self._onbellek:
            a0, b0 = i * self.blok, min(self.boy, (i + 1) * self.blok) - 1
            r = urllib.request.Request(self.url, headers={"User-Agent": UA, "Range": f"bytes={a0}-{b0}"})
            for deneme in (1, 2, 3):
                try:
                    with urllib.request.urlopen(r, timeout=90) as y:
                        self._onbellek[i] = y.read()
                    break
                except (urllib.error.URLError, OSError):
                    if deneme == 3:
                        raise
                    time.sleep(2)
            if len(self._onbellek) > 64:
                self._onbellek.pop(next(iter(self._onbellek)))
        return self._onbellek[i]

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.boy - self.konum
        n = max(0, min(n, self.boy - self.konum))
        out, kalan = [], n
        while kalan > 0:
            i, ofs = divmod(self.konum, self.blok)
            parca = self._blok(i)[ofs:ofs + kalan]
            out.append(parca); self.konum += len(parca); kalan -= len(parca)
        return b"".join(out)

    def seek(self, ofs: int, nereden: int = 0) -> int:
        self.konum = ofs if nereden == 0 else self.konum + ofs if nereden == 1 else self.boy + ofs
        return self.konum

    def tell(self) -> int:
        return self.konum

    def seekable(self): return True
    def readable(self): return True
    def writable(self): return False
    def close(self): self.closed = True
    def size(self): return self.boy


def _pyarrow():
    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyarrow"], check=False)
        import pyarrow.parquet as pq  # type: ignore
    return pq


def _uzak_parquet(i: int):
    return _pyarrow().ParquetFile(_UzakDosya(KORPUS.format(i)))


def k_kur(a=None) -> int:
    if os.path.exists(DIZIN) and os.path.getsize(DIZIN) > 50_000_000:
        print(f"Dizin hazır: {DIZIN} ({os.path.getsize(DIZIN) // 1_000_000} MB).")
        return 0
    con = _duckdb()
    if DIZIN_AYNA:
        try:
            t = time.time()
            urllib.request.urlretrieve(DIZIN_AYNA, DIZIN)
            n = con.execute(f"SELECT count(*) FROM '{DIZIN}'").fetchone()[0]
            print(f"Dizin aynadan indirildi: {n} karar, {time.time() - t:.0f} sn.")
            return 0
        except Exception as e:
            print(f"Ayna kullanılamadı ({e}); dizin asıl korpustan kuruluyor.")
    t0 = time.time()
    con.execute("CREATE TABLE idx (shard INT, court VARCHAR, esas_no VARCHAR, karar_no VARCHAR,"
                " karar_tarihi VARCHAR, document_id VARCHAR)")
    sutunlar = ["court", "esas_no", "karar_no", "karar_tarihi", "document_id"]
    for i in range(PARCA_SAYISI):
        for deneme in (1, 2, 3):
            try:
                if HTTPFS:
                    con.execute(f"INSERT INTO idx SELECT {i}, court, esas_no, karar_no, karar_tarihi,"
                                f" document_id FROM '{KORPUS.format(i)}'")
                else:
                    tablo = _uzak_parquet(i).read(columns=sutunlar)  # yalnız künye sütunları indirilir
                    con.register("parca_t", tablo)
                    con.execute(f"INSERT INTO idx SELECT {i}, court, esas_no, karar_no, karar_tarihi,"
                                f" document_id FROM parca_t")
                    con.unregister("parca_t")
                break
            except Exception as e:
                if deneme == 3:
                    print(f"DURDU: korpus parçası {i} okunamadı: {e}")
                    return 3
                time.sleep(5)
        print(f"  parça {i + 1}/{PARCA_SAYISI} tamam", flush=True)
    con.execute(f"COPY (SELECT * FROM idx ORDER BY esas_no, karar_no) TO '{DIZIN}' "
                f"(FORMAT parquet, COMPRESSION zstd)")
    n = con.execute("SELECT count(*), min(karar_tarihi), max(karar_tarihi) FROM idx").fetchone()
    print(f"Dizin kuruldu: {n[0]} karar ({n[1]} – {n[2]}), {time.time() - t0:.0f} sn.")
    return 0


_con = None


def dizin():
    global _con
    if _con is None:
        if not os.path.exists(DIZIN):
            raise SystemExit("Dizin yok. Önce: ictihat.py kur")
        _con = _duckdb()
    return _con


def dizinde_ara(esas, karar):
    kosul, par = [], []
    if esas:
        kosul.append("esas_no = ?"); par.append(esas)
    if karar:
        kosul.append("karar_no = ?"); par.append(karar)
    if not kosul:
        return []
    rows = dizin().execute(
        f"SELECT court, esas_no, karar_no, karar_tarihi, document_id, shard FROM '{DIZIN}' "
        f"WHERE {' AND '.join(kosul)} LIMIT 25", par).fetchall()
    return [dict(zip(("daire", "esas", "karar", "tarih", "belge", "parca"), r)) for r in rows]


def _daire_uyar(istenen, kayit) -> bool:
    if not istenen:
        return True
    if istenen == "İBK":
        return "Birleştirme" in kayit or "Büyük" in kayit
    return istenen == (kayit or "").strip()


def _tarih(iso: str) -> str:
    try:
        y, m, d = iso[:10].split("-")
        return f"{d}.{m}.{y}"
    except ValueError:
        return iso


# ================= Katmanlar =================

def _hh_daire(daire: str) -> str | None:
    m = re.match(r"(\d+)\. (Hukuk|Ceza) Dairesi", daire or "")
    if m:
        return f"{m.group(1)}-{tr_kucuk(m.group(2)).replace('ı', 'i')}-dairesinin"
    return {"Hukuk Genel Kurulu": "hukuk-genel-kurulunun",
            "Ceza Genel Kurulu": "ceza-genel-kurulunun"}.get(daire)


def hukukihaber(daire, esas, karar) -> dict:
    d = _hh_daire(daire)
    if not (d and esas and karar):
        return {"durum": "denenmedi", "neden": "daire/esas/karar eksik"}
    slug = lambda n: n.replace("/", "")
    url = f"{HH}/yargitay-{d}-{slug(esas)}-e-{slug(karar)}-k-sayili-karari"
    kod, _, ham = _istek(url, zaman=25)
    if kod == 404:
        return {"durum": "yok", "url": url}
    if kod != 200:
        return {"durum": "denenemedi", "neden": f"HTTP {kod}"}
    baslik = re.search(r"<title>(.*?)</title>", ham, re.S | re.I)
    b = _html.unescape(baslik.group(1)) if baslik else ""
    tutar = esas in b.replace(" ", "") and karar in b.replace(" ", "")
    return {"durum": "var" if tutar else "uyuşmuyor", "url": url, "baslik": b.strip(), "ham": ham}


def bakanlik(esas, karar) -> dict:
    if not (esas and karar):
        return {"durum": "denenmedi", "neden": "esas/karar eksik"}
    sorgu = " ".join("+" + p for n in (esas, karar) for p in re.split(r"[/-]", n))
    v = _bedesten("searchDocuments", {"phrase": sorgu, "itemTypeList": ["YARGITAYKARARI"],
                                      "pageSize": 20, "pageNumber": 1}, sayfali=True)
    for d in v.get("emsalKararList") or []:
        if no_normal(d.get("esasNo")) == esas and no_normal(d.get("kararNo")) == karar:
            return {"durum": "var", "daire": d.get("birimAdi"), "tarih": d.get("kararTarihiStr"),
                    "belge": str(d.get("documentId"))}
    return {"durum": "yok"}


def kontrol_et(kunye: dict, cevrimici: bool = True) -> dict:
    esas, karar, daire = kunye.get("esas"), kunye.get("karar"), kunye.get("daire")
    s = {"istenen": kunye, "katmanlar": {}, "sonuc": None, "kayit": None, "notlar": []}
    if not esas and not karar:
        s["sonuc"] = "OKUNAMADI"
        return s
    tam = [r for r in dizinde_ara(esas, karar) if esas and karar]
    if not tam and esas and karar and re.fullmatch(r"\d{4}/\d+-\d+", esas):
        # Genel kurul yazımı: "2024/11-60" (dosyanın geldiği daire + sıra) — kayıtta "2024/60"
        kisa = f"{esas.split('/')[0]}/{esas.split('-')[-1]}"
        tam = dizinde_ara(kisa, karar)
        if tam:
            s["notlar"].append(f"Esas numarası genel kurul yazımıyla ({esas}) verilmiş; kayıtta {kisa} olarak geçiyor.")
    uyan = [r for r in tam if _daire_uyar(daire, r["daire"])]
    if uyan:
        s["kayit"] = uyan[0]
        s["katmanlar"]["dizin"] = "var"
    elif tam:
        s["katmanlar"]["dizin"] = f"numaralar başka dairede: {tam[0]['daire']}"
        s["yakin"] = tam
    elif esas and karar:
        s["katmanlar"]["dizin"] = "yok"
        # aynı dairede yalnız bir numarası tutan kararlar: ipucu, kanıt değil (tesadüf olabilir)
        s["ipucu"] = [r for r in dizinde_ara(esas, None) + dizinde_ara(None, karar)
                      if daire and _daire_uyar(daire, r["daire"])][:3]
    else:
        tek = [r for r in dizinde_ara(esas, karar) if _daire_uyar(daire, r["daire"])]
        s["katmanlar"]["dizin"] = f"yalnız {'esas' if esas else 'karar'} verildi; {len(tek)} aday"
        s["yakin"] = tek[:5]
    if cevrimici:
        try:
            s["katmanlar"]["bakanlik"] = bakanlik(esas, karar)["durum"]
        except Dur as e:
            s["katmanlar"]["bakanlik"] = f"ulaşılamadı ({str(e)[:60]})"
        try:
            dd = daire or (s["kayit"] or {}).get("daire")
            hh = hukukihaber(dd, esas, karar)
            s["katmanlar"]["hukukihaber"] = hh["durum"] + (f" — {hh['url']}" if hh.get("url") and hh["durum"] == "var" else "")
        except Dur as e:
            s["katmanlar"]["hukukihaber"] = f"ulaşılamadı ({str(e)[:60]})"
    teyit = sum(1 for v in s["katmanlar"].values() if str(v).startswith("var"))
    resmi = any(str(s["katmanlar"].get(x, "")).startswith("var") for x in ("dizin", "bakanlik"))
    if teyit and resmi:
        s["sonuc"] = "BULUNDU"
        s["teyit"] = teyit
    elif teyit:
        s["sonuc"] = "YALNIZ İKİNCİL KAYNAKTA BULUNDU"
        s["notlar"].append("Resmî kayıtla eşleşmedi; yalnız bir yayın (Hukuki Haber) bu künyeyi yayımlamış. "
                           "Resmî sitede teyit etmeden dayanmayın.")
    elif s.get("yakin") or str(s["katmanlar"].get("dizin", "")).startswith("numaralar"):
        s["sonuc"] = "KISMEN"
    else:
        s["sonuc"] = "BULUNAMADI"
        yil = int((karar or esas or "0/0").split("/")[0])
        if yil >= 2026:
            s["notlar"].append("2026 kararı: dizinde kapsam boşluğu var; bulunamamak uydurma olduğunu kanıtlamaz.")
    return s


def sonuc_yazi(s: dict) -> str:
    k = s["istenen"]
    ist = f"{k.get('daire') or 'daire ?'}, E. {k.get('esas') or '?'} K. {k.get('karar') or '?'}"
    satir = [f"■ {s['sonuc']} — istenen: {ist}"]
    if s["kayit"]:
        r = s["kayit"]
        satir.append(f"  kayıt: Yargıtay {r['daire']}, E. {r['esas']}, K. {r['karar']}, "
                     f"T. {_tarih(r['tarih'])} — resmî sayfa: {SAYFA}/{r['belge']}")
        if k.get("tarih") and k["tarih"] != _tarih(r["tarih"]):
            satir.append(f"  DİKKAT: istenen tarih {k['tarih']}, kayıttaki tarih {_tarih(r['tarih'])}.")
    for y in (s.get("yakin") or [])[:3]:
        satir.append(f"  aday kayıt: Yargıtay {y['daire']}, E. {y['esas']}, K. {y['karar']}, "
                     f"T. {_tarih(y['tarih'])} — {SAYFA}/{y['belge']}")
    for y in (s.get("ipucu") or [])[:3]:
        satir.append(f"  benzer numaralı BAŞKA karar (bu künye değildir; atıf yapmayın): Yargıtay {y['daire']}, "
                     f"E. {y['esas']}, K. {y['karar']}, T. {_tarih(y['tarih'])} — {SAYFA}/{y['belge']}")
    adlar = {"dizin": "Künye dizini", "bakanlik": "Adalet Bakanlığı servisi", "hukukihaber": "Hukuki Haber"}
    def _oku(v, a=""):
        v = str(v)
        return ("şu an yanıt vermiyor (geçici kesinti olabilir)" if v.startswith("ulaşılamadı") else
                "var" if v.startswith("var") else
                "bu kararı yayımlamamış (olağan; yalnız seçtiği kararları yayımlar)" if v == "yok" and a == "hukukihaber" else v)
    satir.append("  Bakılan kaynaklar: " + " · ".join(f"{adlar.get(a, a)}: {_oku(b, a)}" for a, b in s["katmanlar"].items()))
    if s["sonuc"] == "BULUNAMADI":
        satir.append(f"  Taranan kaynaklarda bulunamadı ({KAPSAM}). Bu künyeye dayanmayın; resmî sitede elle arayın.")
    if s["sonuc"] == "KISMEN":
        satir.append("  Künye eksik ya da daire tutmuyor: hatalı yazılmış olabilir. Aday kaydı okuyarak teyit edin.")
    satir += [f"  not: {n}" for n in s["notlar"]]
    return "\n".join(satir)


# ================= Metin =================

def html_metin(ham: str) -> str:
    s = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1>", "", ham)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</(p|div|tr|li|h[1-6])>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = _html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return re.sub(r"\n[ \t]+", "\n", s).strip()


def pdf_metin(yol: str) -> str:
    try:
        import pypdf  # type: ignore
        return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(yol).pages)
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        return subprocess.run(["pdftotext", yol, "-"], capture_output=True, text=True, check=True).stdout
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pypdf"], check=False)
    import pypdf  # type: ignore
    return "\n".join((p.extract_text() or "") for p in pypdf.PdfReader(yol).pages)


_KISALTMA = re.compile(r"(?:\b\d+|\b[A-ZÇĞİÖŞÜ]|\bmd|\bvd|\bbkz|\bs|\bNo|\bTic|\bHuk|\bCez|\bDai)\.$")


def pdf_paragraflastir(ham: str) -> str:
    out: list[str] = []
    for x in (s.strip() for s in ham.replace("\f", "\n").splitlines()):
        if not x:
            continue
        if out:
            o = out[-1]
            bitti = re.search(r"[.:;!?)\"”]$", o) and not _KISALTMA.search(o)
            if not bitti or x[:1].islower():
                out[-1] = (o[:-1] if o.endswith("-") and x[:1].islower() else o + " ") + x
                continue
        out.append(x)
    return "\n".join(out)


def dosya_metin(yol: str) -> str:
    u = yol.lower()
    if u.endswith(".pdf"):
        return pdf_paragraflastir(pdf_metin(yol))
    if u.endswith(".docx"):
        with zipfile.ZipFile(yol) as z:
            x = z.read("word/document.xml").decode("utf-8", "replace")
        x = re.sub(r"</w:p>", "\n", x)
        return _html.unescape(re.sub(r"<[^>]+>", "", x))
    if u.endswith(".udf"):  # UYAP: içinde content.xml olan zip (gerçek dosyayla test edilmeli)
        with zipfile.ZipFile(yol) as z:
            x = z.read("content.xml").decode("utf-8", "replace")
        m = re.search(r"<content>\s*<!\[CDATA\[(.*?)\]\]>", x, re.S)
        return m.group(1) if m else _html.unescape(re.sub(r"<[^>]+>", " ", x))
    if u.endswith((".html", ".htm")):
        return html_metin(open(yol, encoding="utf-8", errors="replace").read())
    return open(yol, encoding="utf-8", errors="replace").read()


def paragraflar(metin: str, hedef: int = 700) -> list[str]:
    cikti: list[str] = []
    for p in (x.strip() for x in metin.splitlines()):
        if not p:
            continue
        if len(p) <= hedef * 2:
            cikti.append(p)
            continue
        parca = ""
        for c in re.split(r"(?<=[.;:])\s+(?=[A-ZÇĞİÖŞÜ0-9])", p):
            if parca and len(parca) + len(c) > hedef:
                cikti.append(parca)
                parca = c
            else:
                parca = f"{parca} {c}".strip()
        if parca:
            cikti.append(parca)
    return cikti


_BASLIK = re.compile(r"^\s*([IVX]+)\s*[.\-]\s*(.{2,60})$")
_ALT = re.compile(r"^\s*([A-H]|\d{1,2})\s*[.\-)]\s*(.{2,70})$")
_KARSI_OY = re.compile(r"^\s*(K\s*A\s*R\s*Ş\s*I\s*O\s*Y|KARŞI\s+OY|MUHALEFET\s+ŞERHİ|AZLIK\s+OYU)", re.I)
_DUSUNULDU = re.compile(r"gereği\s+(?:görüşülüp\s+)?düşünüldü|gereği\s+görüşüldü", re.I)


def bolumle(ps: list[str]) -> list[str]:
    """Her paragrafın kimin sesi olduğunu kestirir: YARGITAY / ALT MAHKEME / TARAF / KARŞI OY /
    SONUÇ / BELİRSİZ. Yeni biçimde (I. DAVA … V. TEMYİZ) başlıklara, eski biçimde
    "gereği görüşülüp düşünüldü" ifadesine bakar. Kestirimdir; insan okur."""
    etiket = ["BELİRSİZ"] * len(ps)
    basliklar = [(i, m.group(2).upper()) for i, p in enumerate(ps) if (m := _BASLIK.match(p)) and len(p) < 80]
    if basliklar:
        durum, temyizde = "BELİRSİZ", False
        sira = dict(basliklar)
        for i, p in enumerate(ps):
            if i in sira:
                b = tr_kucuk(sira[i])
                temyizde = False
                if "dava" in b or "cevap" in b:
                    durum = "TARAF"
                elif "ilk derece" in b or "istinaf" in b or "bölge" in b:
                    durum = "ALT MAHKEME"
                elif "temyiz" in b or "gerekçe" in b or "değerlendirme" in b:
                    durum, temyizde = "YARGITAY", True
                elif "karar" in b or "hüküm" in b or "sonuç" in b:
                    durum = "SONUÇ"
            elif temyizde and (m := _ALT.match(p)) and len(p) < 90:
                a = tr_kucuk(m.group(2))
                durum = "TARAF" if ("sebep" in a or "başvuran" in a) else "YARGITAY"
            if re.match(r"^\s*[IVX]+\s*[.\-]\s*(SONUÇ|KARAR|HÜKÜM)", p):
                durum = "SONUÇ"
            if _KARSI_OY.match(p):
                durum = "KARŞI OY"
            etiket[i] = durum
        return _sonucla(ps, etiket)
    # eski biçim: "Kararı … temyiz etmiştir." cümlesinden sonrası Yargıtay'ın kendi değerlendirmesidir
    son = max((i for i, p in enumerate(ps)
               if len(p) < 400 and re.search(r"temyiz\s+(?:etmiş|edilmiş|edilmekle|olunmuş)", p, re.I)), default=None)
    durum = "BELİRSİZ"
    for i, p in enumerate(ps):
        if son is not None:
            if i > son:
                durum = "YARGITAY"
            elif re.match(r"^\s*(Davacı|Davalı|Müdahil|Sanık|Katılan|Şikayetçi|Alacaklı|Borçlu)", p):
                durum = "TARAF"
            elif re.match(r"^\s*(Mahkemece|İlk\s+derece|Bölge|Yerel\s+mahkeme)", p, re.I):
                durum = "ALT MAHKEME"
            elif i <= son and durum == "BELİRSİZ" and i > 1:
                durum = "ALT MAHKEME / TARAF"
        if re.match(r"^\s*(SONUÇ|HÜKÜM)\s*:?", p):
            durum = "SONUÇ"
        if _KARSI_OY.match(p):
            durum = "KARŞI OY"
        etiket[i] = durum
    return _sonucla(ps, etiket)


def _sonucla(ps: list[str], etiket: list[str]) -> list[str]:
    """Alt mahkeme paragraflarına Yargıtay'ın o kararı onayıp onaymadığını ekler."""
    tum = " ".join(ps[-4:])
    onay = re.search(r"ONANMASINA|esastan\s+reddine|itirazlarının\s+reddi", tum, re.I)
    bozma = re.search(r"BOZULMASINA|kaldırılmasına", tum, re.I)
    ek = " (Yargıtay onadı)" if onay and not bozma else " (Yargıtay bozdu)" if bozma and not onay else \
        " (kısmen onama/bozma)" if onay and bozma else ""
    return [e + ek if e.startswith("ALT MAHKEME") else e for e in etiket]


def korpus_metin(belge: str, parca: int | None) -> str | None:
    con = dizin()
    parcalar = [parca] if parca is not None else range(PARCA_SAYISI)
    for i in parcalar:
        if HTTPFS:
            r = con.execute(f"SELECT text FROM '{KORPUS.format(int(i))}' WHERE document_id = ?",
                            [str(belge)]).fetchone()
            if r and r[0]:
                return r[0]
            continue
        pf = _uzak_parquet(int(i))
        for g in range(pf.num_row_groups):
            ids = pf.read_row_group(g, columns=["document_id"]).column(0).to_pylist()
            if str(belge) in ids:
                return pf.read_row_group(g, columns=["text"]).column(0)[ids.index(str(belge))].as_py()
    return None


def hh_govde(ham: str) -> str | None:
    """Hukuki Haber sayfasından yalnız karar gövdesini (art arda gelen <p> blokları) alır."""
    i = ham.find("İçtihat Metni")
    if i < 0:
        return None
    bas = ham.rfind("<p><strong>Yargıtay", 0, i)
    bas = bas if bas >= 0 and i - bas < 600 else ham.rfind("<p", 0, i)
    m = re.match(r"((?:\s*<p\b[^>]*>.*?</p>)+)", ham[bas:], re.S)
    return html_metin(m.group(1)) if m else None


def bakanlik_metin(belge: str) -> str | None:
    v = _bedesten("getDocumentContent", {"documentId": str(belge)})
    if not v.get("content"):
        return None
    ham = base64.b64decode(v["content"])
    if "pdf" in (v.get("mimeType") or ""):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t:
            t.write(ham)
        try:
            return pdf_paragraflastir(pdf_metin(t.name))
        finally:
            os.unlink(t.name)
    return html_metin(ham.decode("utf-8", "replace"))


# ================= Kayıt =================

def kayit_oku() -> dict:
    if os.path.exists(KAYIT):
        return json.load(open(KAYIT, encoding="utf-8"))
    return {"sayac": 0, "kararlar": {}}


def kayit_yaz(k: dict) -> None:
    json.dump(k, open(KAYIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def atif(d: dict) -> str:
    p = [d.get("mahkeme") or ""]
    p += [f"E. {d['esas']}"] if d.get("esas") else []
    p += [f"K. {d['karar']}"] if d.get("karar") else []
    p += [f"T. {d['tarih']}"] if d.get("tarih") else []
    return ", ".join(x for x in p if x)


def _kaydet(k: dict, kunye: dict, metin: str) -> str:
    for kno, d in k["kararlar"].items():
        if kunye.get("belge") and d.get("belge") == kunye["belge"]:
            return kno
    k["sayac"] += 1
    kno = f"K{k['sayac']}"
    os.makedirs(METIN_DIZIN, exist_ok=True)
    open(os.path.join(METIN_DIZIN, f"{kno}.txt"), "w", encoding="utf-8").write(metin)
    k["kararlar"][kno] = {**kunye, "durum": "incelenmedi", "onayli_paragraflar": [], "gosterilen": [],
                          "alinma": _dt.datetime.now().strftime("%d.%m.%Y %H:%M")}
    return kno


def _metin(kno: str) -> str:
    return open(os.path.join(METIN_DIZIN, f"{kno}.txt"), encoding="utf-8").read()


# ================= Komutlar =================

def k_kontrol(a) -> int:
    kod = 0
    for s in a.kunye:
        r = kontrol_et(kunye_ayristir(s), not a.cevrimdisi)
        print(sonuc_yazi(r))
        print()
        kod = kod or (0 if r["sonuc"] == "BULUNDU" else 2)
    return kod


def k_denetle(a) -> int:
    metin = dosya_metin(a.dosya)
    adaylar = kunyeleri_cikar(metin)
    satirlar = [f"# Künye denetimi — {os.path.basename(a.dosya)}",
                f"Tarih: {_dt.datetime.now():%d.%m.%Y %H:%M} · {KAPSAM}", ""]
    say = {}
    for i, c in enumerate(adaylar, 1):
        if not c["yargitay"]:
            satirlar.append(f"{i}. “{c['alinti']}” — Yargıtay dışı bir mahkeme; denetlenmedi.")
            say["Yargıtay dışı (denetlenmedi)"] = say.get("Yargıtay dışı (denetlenmedi)", 0) + 1
            continue
        s = kontrol_et(c, not a.cevrimdisi)
        say[s["sonuc"]] = say.get(s["sonuc"], 0) + 1
        satirlar.append(f"{i}. Metindeki ifade: “{c['alinti']}”")
        satirlar.append(sonuc_yazi(s))
        satirlar.append("")
    ozet = ", ".join(f"{v} {k}" for k, v in say.items()) or "künye bulunamadı"
    satirlar.insert(2, f"Özet: {len(adaylar)} künye — {ozet}")
    cikti = re.sub(r"(\.\w+)?$", "_kunye_denetimi.md", a.dosya, count=1)
    open(cikti, "w", encoding="utf-8").write("\n".join(satirlar))
    print("\n".join(satirlar))
    print(f"\nRapor: {cikti}")
    return 0


def k_getir(a) -> int:
    k = kayit_oku()
    hedef = a.hedef.strip()
    if re.fullmatch(r"\d{5,}", hedef):
        aday = dizin().execute(f"SELECT court, esas_no, karar_no, karar_tarihi, document_id, shard "
                               f"FROM '{DIZIN}' WHERE document_id = ?", [hedef]).fetchall()
        kayit = dict(zip(("daire", "esas", "karar", "tarih", "belge", "parca"), aday[0])) if aday else \
            {"daire": "", "esas": "", "karar": "", "tarih": "", "belge": hedef, "parca": None}
    else:
        ky = kunye_ayristir(hedef)
        s = kontrol_et(ky, cevrimici=False)
        if s["kayit"]:
            kayit = s["kayit"]
        else:  # dizinde yok (ör. 2026): yalnız künyeden kurulan resmî olmayan kaynakları dene
            kayit = {"daire": ky.get("daire") or "", "esas": ky.get("esas"), "karar": ky.get("karar"),
                     "tarih": "", "belge": "", "parca": None}
            if not (kayit["esas"] and kayit["karar"]):
                print(sonuc_yazi(s)); return 2
    metin, kaynak, sayfa = None, None, f"{SAYFA}/{kayit['belge']}" if kayit["belge"] else ""
    if kayit["belge"]:
        try:
            metin = korpus_metin(kayit["belge"], kayit.get("parca"))
            kaynak = "açık korpus (resmî belge kopyası)"
        except Exception as e:
            print(f"korpus okunamadı: {e}")
        if not metin:
            try:
                metin = bakanlik_metin(kayit["belge"])
                kaynak = "Adalet Bakanlığı servisi"
            except Dur as e:
                print(f"Bakanlık servisi: {e}")
    if not metin and kayit.get("esas"):
        try:
            hh = hukukihaber(kayit["daire"], kayit["esas"], kayit["karar"])
            if hh["durum"] == "var":
                metin, kaynak = hh_govde(hh["ham"]), "Hukuki Haber (ikincil yayın)"
                sayfa = sayfa or hh["url"]
        except Dur:
            pass
    if not metin:
        print("Metin hiçbir kaynakta bulunamadı." +
              (f" Künye kayıtlı; metni resmî sayfadan okuyun: {sayfa}" if sayfa else ""))
        return 2
    kno = _kaydet(k, {"mahkeme": f"Yargıtay {kayit['daire']}".strip(), "esas": kayit["esas"],
                      "karar": kayit["karar"], "tarih": _tarih(kayit["tarih"]) if kayit["tarih"] else "",
                      "belge": kayit["belge"], "kaynak": sayfa, "metin_kaynagi": kaynak}, metin)
    kayit_yaz(k)
    d = k["kararlar"][kno]
    print(f"{kno} kayda alındı: {atif(d)} — {len(paragraflar(metin))} paragraf. "
          f"Metin kaynağı: {kaynak}. {'Resmî' if SAYFA in sayfa else 'Kaynak'} sayfa: {d['kaynak']}")
    return 0


def puanla(ps: list[str], kelimeler: list[str]):
    kps = [kalip(w) for w in kelimeler]
    sonuc = []
    for i, p in enumerate(ps):
        n = tr_kucuk(p)
        isabet = [len(kp.findall(n)) for kp in kps]
        f = sum(1 for x in isabet if x)
        if f:
            sonuc.append((i, f, sum(isabet)))
    return sonuc


def _vurgula(p: str, kelimeler: list[str]) -> str:
    n = tr_kucuk(p)
    if len(n) != len(p):
        return p
    ar = sorted((m.start(), m.end()) for w in kelimeler for m in kalip(w).finditer(n))
    out, son = [], 0
    for a0, b0 in ar:
        if a0 >= son:
            out += [p[son:a0], "**", p[a0:b0], "**"]
            son = b0
    return "".join(out + [p[son:]])


def k_cikar(a) -> int:
    k = kayit_oku()
    if a.kno not in k["kararlar"]:
        raise SystemExit(f"{a.kno} kayıtta yok. Önce: getir")
    d = k["kararlar"][a.kno]
    ps = paragraflar(_metin(a.kno))
    ses = bolumle(ps)
    def oncelik(e: str) -> int:
        return 0 if e == "YARGITAY" else 1 if e == "SONUÇ" else 2 if e == "BELİRSİZ" else \
            3 if "onadı" in e else 4 if e.startswith("ALT MAHKEME") else 5 if e == "TARAF" else 6
    secim = sorted(sorted(puanla(ps, a.kelime),
                          key=lambda t: (oncelik(ses[t[0]]), -t[1], -t[2], t[0]))[:a.en_fazla])
    etiket = "Resmî sayfa" if SAYFA in (d["kaynak"] or "") else "Kaynak sayfa"
    out = [f"## {a.kno} — {atif(d)}", f"{etiket}: {d['kaynak']} · Metin kaynağı: {d.get('metin_kaynagi')}",
           f"Aranan: {', '.join(a.kelime)} · Gösterilen: {len(secim)} / {len(ps)} paragraf", ""]
    if not secim:
        out.append("Bu kararda aranan kelimelerin geçtiği paragraf yok.")
    for i, f, _ in secim:
        out += [f"**{a.kno}-P{i + 1}**  [{ses[i]}{' GEREKÇESİ' if ses[i] == 'YARGITAY' else ''}]  ({f}/{len(a.kelime)} kelime)",
                "> " + _vurgula(ps[i], a.kelime), ""]
    blok = "\n".join(out)
    print(blok)
    open(RAPOR, "a", encoding="utf-8").write(blok + "\n\n")
    d["gosterilen"] = sorted(set(d.get("gosterilen", [])) | {f"P{i + 1}" for i, _, _ in secim},
                             key=lambda x: int(x[1:]))
    kayit_yaz(k)
    print("— Metin kaynağından birebir alınmıştır; kalın yazılar yalnız vurgudur. "
          "Köşeli parantez, paragrafın kimin sesi olduğunu gösterir (kestirim). "
          "Hangi paragrafları kullanmak istersiniz? (ör. K1-P7) Hiçbiri uygun değilse: hayır.")
    return 0


def _desen(k: str) -> str:
    """Bir anahtar kelimeyi ILIKE desenine çevirir (kök; sert ünsüz yumuşaması)."""
    k = tr_kucuk(k.strip())
    k = k[:-1] if len(k) >= 5 and k[-1] in "pçtk" else k
    return "%" + k.replace("%", "").replace("_", "") + "%"


def _konu_sql(kaynak: str, kosul: list[str], kelimeler: list[str], ilk: str, adet: int) -> str:
    """Kelimelerin hepsinin geçtiği kararları, kelimelerin metinde geçme sıklığına göre sıralar."""
    kokler = [_desen(k).strip("%").replace("'", "") for k in kelimeler]
    puan = " + ".join(f"(length(lt) - length(replace(lt, '{k}', ''))) / {max(1, len(k))}" for k in kokler)
    kosul_lt = [c.replace("lower(replace(replace(text, 'İ', 'i'), 'I', 'ı'))", "lt") for c in kosul]
    return (f"SELECT court, esas_no, karar_no, karar_tarihi, document_id, "
            f"regexp_extract(lt, '.{{0,140}}{ilk}.{{0,140}}'), {puan} AS puan FROM ("
            f"SELECT court, esas_no, karar_no, karar_tarihi, document_id, "
            f"lower(replace(replace(text, 'İ', 'i'), 'I', 'ı')) AS lt FROM {kaynak}) "
            f"WHERE {' AND '.join(kosul_lt)} ORDER BY puan DESC, karar_tarihi DESC LIMIT {int(adet)}")


def k_konu(a) -> int:
    """Korpusun tam metninde, kararın kendi metnine göre arar. Sonuç künyeleri resmî belge
    numarasıyla verir; hiçbir künye model tarafından yazılmaz."""
    if not os.path.exists(DIZIN):
        raise SystemExit("Dizin yok. Önce: ictihat.py kur")
    con = dizin()
    daire = daire_bul(a.daire) if a.daire else None
    if a.daire and not daire:
        raise SystemExit(f"Daire okunamadı: {a.daire}")
    yil = str(a.yildan) if a.yildan else "1900"
    parcalar = [r[0] for r in con.execute(
        f"SELECT DISTINCT shard FROM '{DIZIN}' WHERE karar_tarihi >= ? ORDER BY 1", [yil]).fetchall()]
    if not HTTPFS and not a.yildan:  # eklentisiz yolda tam tarama çok yavaş: son yıllara sınırla
        parcalar = parcalar[-4:]
        print("Not: hızlı uzak okuma yok; arama son dört parçayla (yaklaşık son yıllar) sınırlandı.")
    kosul, par = ["1=1"], []
    if daire == "İBK":
        kosul.append("(court ILIKE '%Birleştirme%' OR court ILIKE '%Büyük Genel%')")
    elif daire:
        kosul.append("court = ?"); par.append(daire)
    if a.yildan:
        kosul.append("karar_tarihi >= ?"); par.append(yil)
    for k in a.kelime:
        kosul.append("lower(replace(replace(text, 'İ', 'i'), 'I', 'ı')) LIKE ?"); par.append(_desen(k))
    ilk = re.escape(_desen(a.kelime[0]).strip("%"))
    t0 = time.time()
    print(f"Korpusta aranıyor: {', '.join(a.kelime)}"
          + (f" · {daire}" if daire else "") + (f" · {a.yildan}+" if a.yildan else "")
          + f" · {len(parcalar)} parça (bir-iki dakika sürebilir)…", flush=True)
    sonuc = []
    if HTTPFS:
        dosyalar = "[" + ",".join(f"'{KORPUS.format(int(i))}'" for i in parcalar) + "]"
        sonuc = con.execute(_konu_sql(f"read_parquet({dosyalar})", kosul, a.kelime, ilk, a.en_fazla), par).fetchall()
    else:
        import pyarrow as pa  # noqa: F401
        for i in reversed(parcalar):
            pf = _uzak_parquet(int(i))
            for g in range(pf.num_row_groups):
                t = pf.read_row_group(g, columns=["court", "esas_no", "karar_no", "karar_tarihi",
                                                    "document_id", "text"])
                con.register("rg", t)
                sonuc += con.execute(_konu_sql("rg", kosul, a.kelime, ilk, a.en_fazla), par).fetchall()
                con.unregister("rg")
            if len(sonuc) >= a.en_fazla:
                break
        sonuc = sorted(sonuc, key=lambda r: (r[6], r[3]), reverse=True)[:a.en_fazla]
    print(f"{len(sonuc)} karar bulundu ({time.time() - t0:.0f} sn). Künyeler kayıttan; metni okumadan "
          f"kullanmayın.\n")
    if not sonuc:
        print("Bu kelimelerin hepsinin geçtiği karar yok. Daha az ya da farklı kelimeyle deneyin.")
        return 2
    print("| Künye | Kararın içinden | Resmî sayfa |\n|---|---|---|")
    for court, e, k, t, belge, parca, _puan in sonuc:
        parca = re.sub(r"\s+", " ", parca or "").strip().replace("|", "/")
        print(f"| Yargıtay {court}, E. {e}, K. {k}, T. {_tarih(t)} | …{parca}… | {SAYFA}/{belge} |")
    print("\nSıradaki adım: uygun olanı `getir \"<künye>\"` ile kayda alın, `cikar` ile okuyun.")
    return 0


def k_ara(a) -> int:
    try:
        v = _bedesten("searchDocuments", {
            "phrase": " ".join("+" + w for w in re.findall(r"\w+", a.ifade)),
            "itemTypeList": ["YARGITAYKARARI"], "pageSize": max(1, min(a.adet, 50)), "pageNumber": 1,
            "sortFields": ["KARAR_TARIHI"], "sortDirection": "desc"}, sayfali=True)
    except Dur as e:
        print(f"Bakanlık servisi kapalı ({e}). Konu araması için web aramasıyla aday künye bulun, "
              f"her adayı 'kontrol' ile doğrulayın ve 'getir' ile metne geçin.")
        return 3
    print(f"| Künye | Resmî sayfa |\n|---|---|")
    for d in v.get("emsalKararList") or []:
        print(f"| Yargıtay {d.get('birimAdi')}, E. {d.get('esasNo')}, K. {d.get('kararNo')}, "
              f"T. {d.get('kararTarihiStr')} | {SAYFA}/{d.get('documentId')} |")
    return 0


def k_onayla(a) -> int:
    k = kayit_oku()
    d = k["kararlar"].get(a.kno) or sys.exit(f"{a.kno} kayıtta yok.")
    gos = set(d.get("gosterilen", []))
    if [p.lower() for p in a.paragraf] == ["hepsi"]:
        a.paragraf = sorted(gos, key=lambda x: int(x[1:]))
        if not a.paragraf:
            sys.exit(f"{a.kno} için insana henüz paragraf gösterilmedi.")
    eksik = [p for p in a.paragraf if p not in gos]
    if eksik:
        sys.exit(f"Bu paragraflar insana gösterilmedi, onaylanamaz: {', '.join(eksik)}")
    d["durum"] = "onaylandı"
    d["onayli_paragraflar"] = sorted(set(d["onayli_paragraflar"]) | set(a.paragraf), key=lambda x: int(x[1:]))
    kayit_yaz(k)
    print(f"{a.kno} onaylandı: {', '.join(d['onayli_paragraflar'])}.")
    return 0


def k_reddet(a) -> int:
    k = kayit_oku()
    if a.kno not in k["kararlar"]:
        sys.exit(f"{a.kno} kayıtta yok.")
    k["kararlar"][a.kno]["durum"] = "reddedildi"
    kayit_yaz(k)
    print(f"{a.kno} reddedildi.")
    return 0


ETIKET = re.compile(r"\[\[(K\d+)(?:-(P\d+))?\]\]")


def k_dogrula(a) -> int:
    taslak = open(a.taslak, encoding="utf-8").read()
    k = kayit_oku()
    sorun = []
    adaylar = kunyeleri_cikar(ETIKET.sub(lambda m: " " * len(m.group(0)), taslak))  # konumlar korunur
    for c in sorted(adaylar, key=lambda c: -c["bitis"]):
        taslak = taslak[:c["bitis"]] + " ⟦DOĞRULANMADI — kullanmayın⟧" + taslak[c["bitis"]:]
    for c in adaylar:
        satir = f"DOĞRULANMADI — taslakta etiketsiz künye: “{c['alinti']}”"
        if c["yargitay"]:
            try:
                s = kontrol_et(c, not a.cevrimdisi)
                satir += "\n" + sonuc_yazi(s)
            except Exception as e:
                satir += f"\n  denetlenemedi: {e}"
        sorun.append(satir)

    def degistir(m):
        kno, p = m.group(1), m.group(2)
        d = k["kararlar"].get(kno)
        if not d:
            sorun.append(f"KAYITSIZ — {m.group(0)}"); return m.group(0)
        if d["durum"] != "onaylandı":
            sorun.append(f"ONAYSIZ — {m.group(0)} insan tarafından onaylanmadı"); return m.group(0)
        if not p:
            return f"({atif(d)}; {d['kaynak']})"
        if p not in d["onayli_paragraflar"]:
            sorun.append(f"ONAYSIZ — {m.group(0)} paragrafı onaylanmadı"); return m.group(0)
        ps = paragraflar(_metin(kno))
        i = int(p[1:]) - 1
        ses = bolumle(ps)[i]
        not_ = "" if ses == "YARGITAY" else f"; kararda aktarılan {ses.lower()} metni"
        return f"“{ps[i]}” ({atif(d)}; {d['kaynak']}{not_})"

    son = ETIKET.sub(degistir, taslak)
    cikti = a.cikti or re.sub(r"(\.\w+)?$", "_SORUNLU.md" if sorun else "_dogrulanmis.md", a.taslak, count=1)
    open(cikti, "w", encoding="utf-8").write(son)
    if sorun:
        print("SORUNLAR:")
        for s in dict.fromkeys(sorun):
            print(" - " + s)
    else:
        print("Temiz: her atıf insan onaylı ve kaynağından birebir yerleştirildi.")
    print(f"Çıktı: {cikti}")
    return 2 if sorun else 0


def k_liste(a) -> int:
    k = kayit_oku()
    for kno, d in k["kararlar"].items():
        print(f"{kno}: {atif(d)} — {d['durum']} {d['onayli_paragraflar'] or ''} — {d['kaynak']}")
    if not k["kararlar"]:
        print("Kayıt boş.")
    return 0


def k_oztest(a) -> int:
    sonuclar = []

    def test(ad, kosul):
        sonuclar.append((ad, bool(kosul)))
        print(("GEÇTİ  " if kosul else "KALDI  ") + ad, flush=True)

    # ayrıştırma (çevrimdışı)
    for metin, beklenen in [
        ("Yargıtay 3. HD, E. 2023/4567 K. 2024/1234", ("3. Hukuk Dairesi", "2023/4567", "2024/1234")),
        ("Yargıtay 12. Hukuk Dairesi'nin 2019/0345 E., 2020/112 K. sayılı ilamı", ("12. Hukuk Dairesi", "2019/345", "2020/112")),
        ("HGK, Esas No: 2003/4-184 Karar No: 2003/201", ("Hukuk Genel Kurulu", "2003/4-184", "2003/201")),
        ("Yargıtay CGK'nın 2023/131 Esas, 2025/593 Karar sayılı kararı", ("Ceza Genel Kurulu", "2023/131", "2025/593")),
    ]:
        c = kunyeleri_cikar(metin)
        test(f"ayrıştırma: {metin[:40]}…", c and (c[0]["daire"], c[0]["esas"], c[0]["karar"]) == beklenen and c[0]["yargitay"])
    c = kunyeleri_cikar("İstanbul Bölge Adliye Mahkemesi 54. Hukuk Dairesi 2024/1915 E., 2024/2842 K.")
    test("ayrıştırma: BAM kararı Yargıtay sayılmaz", c and not c[0]["yargitay"])
    test("Türkçe eşleşme: ihtiyaç ~ İHTİYACIN", kalip("ihtiyaç").search(tr_kucuk("İHTİYACIN SAMİMİ")))
    # dizin
    for kunye, beklenen, belge in [
        ("21. HD E. 2014/24839 K. 2015/9497", "BULUNDU", "210988800"),
        ("HGK 2024/11-60 E., 2025/588 K.", "BULUNDU", "1180504600"),
        ("3. HD E. 2025/927 K. 2025/6060", "BULUNDU", "1205482000"),
        ("3. HD E. 2023/4567 K. 2024/1234", "BULUNAMADI", None),
        ("3. HD E. 2025/927 K. 2025/9999", "BULUNAMADI", None),
        ("5. HD E. 2025/927 K. 2025/6060", "KISMEN", None),
    ]:
        s = kontrol_et(kunye_ayristir(kunye), cevrimici=False)
        ok = s["sonuc"] == beklenen and (belge is None or (s["kayit"] or {}).get("belge") == belge)
        test(f"dizin: {kunye} → {beklenen}", ok)
    # metin
    try:
        m = korpus_metin("1205482000", None)
        test("metin: korpustan 3. HD 2025/927 tam metni", m and "temyiz sınırı" in m)
    except Exception as e:
        test(f"metin: korpus okunamadı ({e})", False)
    # konu araması (korpusun tam metni)
    eski = sys.stdout
    sys.stdout = io_ = __import__("io").StringIO()
    try:
        k_konu(argparse.Namespace(kelime=["denkleştirme", "birleşme"], daire="11. HD", yildan=2025, en_fazla=20))
    except Exception as e:
        print(f"HATA {e}")
    finally:
        sys.stdout = eski
    test("konu: korpusta 11. HD 2025 'denkleştirme birleşme' → 2023/6190", "2023/6190" in io_.getvalue())
    # taslak denetimi (çevrimdışı)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    tmp.write("Nitekim Yargıtay 3. HD, E. 2023/4567 K. 2024/1234 sayılı kararında...")
    tmp.close()
    eski = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        kod = k_dogrula(argparse.Namespace(taslak=tmp.name, cikti=tmp.name + ".out", cevrimdisi=True))
    finally:
        sys.stdout.close(); sys.stdout = eski
    test("taslak: uydurma künye yakalanır", kod == 2)
    eski_bicim = ["Taraflar arasındaki davanın yapılan yargılaması sonunda ... okunup, incelendikten sonra işin "
                  "gereği görüşülüp, düşünüldü:", "Davacı vekili, birleşmenin geçersiz olduğunu ileri sürmüştür.",
                  "Mahkemece davanın reddine karar verilmiştir.", "Kararı, davacı vekili temyiz etmiştir.",
                  "Dosyadaki yazılara göre temyiz itirazları yerinde değildir.",
                  "SONUÇ: Hükmün ONANMASINA oybirliğiyle karar verildi."]
    yeni_bicim = ["I. DAVA", "Davacı vekili dava dilekçesinde ...", "IV. İSTİNAF", "Bölge Adliye Mahkemesince ...",
                  "V. TEMYİZ", "B. Değerlendirme ve Gerekçe", "Somut olayda ... yerinde değildir.",
                  "VI. SONUÇ: Yukarıda açıklanan nedenlerle kararın ONANMASINA ...", "K A R Ş I O Y", "Çoğunluk ..."]
    e1, e2 = bolumle(eski_bicim), bolumle(yeni_bicim)
    test("ses: eski biçimde gerekçe Yargıtay'ın, taraf/alt mahkeme ayrı",
         e1[4] == "YARGITAY" and e1[1] == "TARAF" and e1[2].startswith("ALT MAHKEME") and e1[5] == "SONUÇ")
    test("ses: yeni biçimde gerekçe Yargıtay'ın, karşı oy ayrı",
         e2[6] == "YARGITAY" and e2[1] == "TARAF" and e2[3].startswith("ALT MAHKEME") and e2[7] == "SONUÇ"
         and e2[9] == "KARŞI OY")
    print("\nSAĞLIK (bilgi içindir, kapı değildir) — teyit katmanları şu an:")
    for ad, f in [("Adalet Bakanlığı servisi", lambda: bakanlik("2025/927", "2025/6060")["durum"]),
                  ("Hukuki Haber", lambda: hukukihaber("1. Ceza Dairesi", "2025/7342", "2026/4000")["durum"])]:
        try:
            durum = f()
        except Exception as e:
            durum = "şu an yanıt vermiyor (geçici kesinti olabilir)"
        print(f"  {ad}: {'çalışıyor' if durum == 'var' else durum}")
    kalan = [a for a, ok in sonuclar if not ok]
    print(f"\nÖZ-TEST: {len(sonuclar) - len(kalan)}/{len(sonuclar)} geçti.")
    if kalan:
        print("ARAÇ KULLANILAMAZ. Kalan testleri kullanıcıya olduğu gibi bildirin; aracı değiştirmeyin.")
        return 1
    print("Araç hazır.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ictihat")
    alt = ap.add_subparsers(dest="komut", required=True)
    alt.add_parser("kur").set_defaults(f=k_kur)
    alt.add_parser("oztest").set_defaults(f=k_oztest)
    s = alt.add_parser("kontrol"); s.add_argument("kunye", nargs="+"); s.add_argument("--cevrimdisi", action="store_true"); s.set_defaults(f=k_kontrol)
    s = alt.add_parser("denetle"); s.add_argument("dosya"); s.add_argument("--cevrimdisi", action="store_true"); s.set_defaults(f=k_denetle)
    s = alt.add_parser("getir"); s.add_argument("hedef"); s.set_defaults(f=k_getir)
    s = alt.add_parser("cikar"); s.add_argument("kno"); s.add_argument("--kelime", nargs="+", required=True)
    s.add_argument("--en-fazla", dest="en_fazla", type=int, default=6); s.set_defaults(f=k_cikar)
    s = alt.add_parser("ara"); s.add_argument("ifade"); s.add_argument("--adet", type=int, default=10); s.set_defaults(f=k_ara)
    s = alt.add_parser("konu"); s.add_argument("kelime", nargs="+"); s.add_argument("--daire")
    s.add_argument("--yildan", type=int); s.add_argument("--en-fazla", dest="en_fazla", type=int, default=15)
    s.set_defaults(f=k_konu)
    s = alt.add_parser("onayla"); s.add_argument("kno"); s.add_argument("paragraf", nargs="+"); s.set_defaults(f=k_onayla)
    s = alt.add_parser("reddet"); s.add_argument("kno"); s.set_defaults(f=k_reddet)
    s = alt.add_parser("dogrula"); s.add_argument("taslak"); s.add_argument("--cikti")
    s.add_argument("--cevrimdisi", action="store_true"); s.set_defaults(f=k_dogrula)
    alt.add_parser("liste").set_defaults(f=k_liste)
    a = ap.parse_args(argv)
    try:
        return a.f(a)
    except Dur as e:
        print(f"DURDU: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
