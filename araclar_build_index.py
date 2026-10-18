"""Künye dizini: mrfg/turkish-court-decisions Yargıtay parçalarından yalnız künye
sütunlarını (metin hariç) uzaktan okuyup tek bir yerel parquet'e yazar.
Her satır: shard, court, esas_no, karar_no, karar_tarihi, document_id.
document_id = Adalet Bakanlığı belge no → https://mevzuat.adalet.gov.tr/ictihat/<id>
"""
import sys, time, duckdb

BASE = ("https://huggingface.co/datasets/mrfg/turkish-court-decisions/resolve/main/"
        "data/yargitay/train-{:05d}-of-00017.parquet")
OUT = sys.argv[1] if len(sys.argv) > 1 else "kunye_index.parquet"

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE TABLE idx (shard INT, court VARCHAR, esas_no VARCHAR, karar_no VARCHAR,"
            " karar_tarihi VARCHAR, document_id VARCHAR)")
t0 = time.time()
for i in range(17):
    t = time.time()
    for deneme in (1, 2):
        try:
            con.execute(f"INSERT INTO idx SELECT {i}, court, esas_no, karar_no, karar_tarihi, document_id "
                        f"FROM '{BASE.format(i)}'")
            break
        except Exception as e:
            if deneme == 2:
                print(f"shard {i} FAILED: {e}", flush=True); raise
            time.sleep(5)
    n = con.execute(f"SELECT count(*) FROM idx WHERE shard={i}").fetchone()[0]
    print(f"shard {i}: {n} rows in {time.time()-t:.1f}s", flush=True)
con.execute(f"COPY (SELECT * FROM idx ORDER BY esas_no, karar_no) TO '{OUT}' (FORMAT parquet, COMPRESSION zstd)")
tot = con.execute("SELECT count(*), min(karar_tarihi), max(karar_tarihi) FROM idx").fetchone()
print(f"DONE {tot} in {time.time()-t0:.0f}s -> {OUT}", flush=True)
