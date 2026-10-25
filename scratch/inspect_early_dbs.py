import sqlite3

for fpath in [
    "dataset/evidence/databases/customer_data_inventory_20260213.sql",
    "dataset/evidence/databases/customer_data_reporting_replica_20260208.sql"
]:
    conn = sqlite3.connect(":memory:")
    with open(fpath, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f"\n=== {fpath} ===")
    for t in tables:
        count = conn.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
        print(f"Table {t} ({count} rows): cols={cols}")
        rows = conn.execute(f"SELECT * FROM {t} LIMIT 3;").fetchall()
        print("Sample rows:", rows)
    conn.close()
