import sqlite3

conn = sqlite3.connect(":memory:")
with open("dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql", "r", encoding="utf-8") as f:
    conn.executescript(f.read())

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
print("Tables in customer_accounts_failover_replica_20260902.sql:", tables)
for t in tables:
    cnt = conn.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
    print(f"  {t}: {cnt} rows")
conn.close()
