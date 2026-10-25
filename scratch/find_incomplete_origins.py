import os

pairs = [
    ('case_09', 'account_3960', 'audit_record_4902'),
    ('case_18', 'account_5521', 'audit_record_6645'),
    ('case_20', 'account_5037', 'audit_record_5569'),
    ('case_22', 'account_4990', 'audit_record_3482'),
    ('case_23', 'account_410', 'audit_record_4128'),
    ('case_29', 'account_7012', 'audit_record_3954'),
    ('case_30', 'account_4163', 'audit_record_1707'),
    ('case_32', 'account_8858', 'audit_record_7068'),
]

for cid, acc, aud in pairs:
    print(f"\n--- {cid}: {acc}, {aud} ---")
    for root, dirs, files in os.walk('dataset'):
        for f in files:
            if f.endswith('.csv') or f.endswith('.json') or f.endswith('.log') or f.endswith('.sql'):
                p = os.path.join(root, f)
                try:
                    content = open(p, encoding='utf-8', errors='ignore').read()
                    if acc in content:
                        print(f"  {acc} found in {p}")
                    if aud in content:
                        print(f"  {aud} found in {p}")
                except:
                    pass
