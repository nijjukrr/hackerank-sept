import os, sqlite3

for f in sorted(os.listdir('dataset/evidence/databases')):
    if f.startswith('customer_data_inventory'):
        p = os.path.join('dataset/evidence/databases', f)
        conn = sqlite3.connect(":memory:")
        conn.executescript(open(p, encoding='utf-8', errors='ignore').read())
        cp_cnt = conn.execute("SELECT count(*) FROM customer_profiles").fetchone()[0]
        scope = conn.execute("SELECT * FROM snapshot_scope").fetchone()
        print(f"{f}: customer_profiles={cp_cnt} | scope={scope}")
