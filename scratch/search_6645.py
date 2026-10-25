import os

for root, dirs, files in os.walk('dataset'):
    for f in files:
        p = os.path.join(root, f)
        try:
            content = open(p, encoding='utf-8', errors='ignore').read()
            if '6645' in content:
                print(f"6645 in {p}")
            if '5569' in content:
                print(f"5569 in {p}")
        except:
            pass
