import sqlite3

p = 'dataset/evidence/databases/customer_data_inventory_20260905.sql'
conn = sqlite3.connect(":memory:")
conn.executescript(open(p, encoding='utf-8', errors='ignore').read())
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print("Tables:", tables)
for t in tables:
    cnt = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {cnt} rows")
