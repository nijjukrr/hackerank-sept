import os

accounts = ['account_5482', 'account_3866', 'account_7012', 'account_6440', 'account_3136', 'account_5684']

print("=== SEARCHING ALL DATASET FILES FOR ACCOUNT IDS ===")
for root, dirs, files in os.walk('dataset'):
    for f in files:
        if f.endswith('.csv') or f.endswith('.json') or f.endswith('.log') or f.endswith('.txt') or f.endswith('.sql'):
            p = os.path.join(root, f)
            try:
                content = open(p, encoding='utf-8', errors='ignore').read()
                for acc in accounts:
                    if acc in content:
                        print(f"FOUND {acc} in {p}")
            except Exception as e:
                pass
