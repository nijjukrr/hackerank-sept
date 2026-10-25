import os, re

print("=== CHECKING ALL SQL FILES FOR ACCOUNT RECORDS ===")
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.sql'):
            p = os.path.join(root, f)
            try:
                for line in open(p, encoding='utf-8', errors='ignore'):
                    if 'account_' in line and ('user_' in line or '@' in line):
                        print(f"{f}: {line.strip()[:140]}")
            except Exception as e:
                pass
