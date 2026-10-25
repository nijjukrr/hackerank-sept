import os

accounts = ['account_6440', 'account_3136', 'account_5684', 'account_3866', 'account_5482']

for root, dirs, files in os.walk('dataset'):
    for f in files:
        path = os.path.join(root, f)
        try:
            content = open(path, 'r', encoding='utf-8', errors='ignore').read()
            for a in accounts:
                if a in content:
                    print(f"Found {a} in {path}")
        except Exception:
            pass
