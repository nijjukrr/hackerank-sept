import sqlite3

for f in ['customer_accounts_failover_replica_20260902.sql', 'customer_data_failover_replica_20260920.sql']:
    p = 'dataset/evidence/databases/' + f
    conn = sqlite3.connect(":memory:")
    conn.executescript(open(p, encoding='utf-8', errors='ignore').read())
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f, tables)
    for t in tables:
        cnt = conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {cnt} rows")
