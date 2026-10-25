import glob, os

targets = ['account_3136', 'account_3866', 'account_5482', 'account_5684', 'account_6440']

for fpath in glob.glob('dataset/**', recursive=True):
    if os.path.isfile(fpath) and not fpath.endswith('.png') and not fpath.endswith('.pdf') and 'sample_output' not in fpath:
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                for target in targets:
                    if target in content:
                        print(f"{target} in {fpath}")
        except Exception:
            pass
