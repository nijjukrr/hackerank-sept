import os

audit_records = [
    'audit_record_6645', 'audit_record_5569', 'audit_record_4902',
    'audit_record_4128', 'audit_record_3954', 'audit_record_1707',
    'audit_record_7068', 'audit_record_3482', 'audit_record_7095',
    'audit_record_3737', 'audit_record_451', 'audit_record_5416',
    'audit_record_3830', 'audit_record_9265', 'audit_record_2016'
]

for root, dirs, files in os.walk('dataset'):
    for f in files:
        path = os.path.join(root, f)
        try:
            content = open(path, 'r', encoding='utf-8', errors='ignore').read()
            for r in audit_records:
                if r in content:
                    print(f"Found {r} in {path}")
        except Exception:
            pass
