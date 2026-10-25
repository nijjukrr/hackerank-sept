import sqlite3

conn = sqlite3.connect(":memory:")
with open("dataset/evidence/databases/customer_data_read_replica_20260921.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print("Tables in evidence_05:", tables)
for t in tables:
    count = conn.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
    print(f"\n{t} ({count} rows):")
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
    print(f"  cols: {cols}")
    rows = conn.execute(f"SELECT * FROM {t};").fetchall()
    for r in rows:
        r_str = str(r)
        if "1007" in r_str or "8911" in r_str or "diya" in r_str or "seoyeon" in r_str:
            print("  MATCH:", r)
