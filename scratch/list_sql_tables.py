import os, re

print("=== CHECKING ALL SQL TABLES ===")
tables = set()
for root, dirs, files in os.walk('dataset/evidence/databases'):
    for f in files:
        if f.endswith('.sql'):
            p = os.path.join(root, f)
            for line in open(p, encoding='utf-8', errors='ignore'):
                m = re.search(r'CREATE TABLE (?:IF NOT EXISTS )?["\']?(\w+)["\']?', line, re.IGNORECASE)
                if m:
                    tables.add((f, m.group(1)))

for f, t in sorted(tables):
    print(f"{f}: {t}")
