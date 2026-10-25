import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260917.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

targets = ['analytics_5335', 'account_6440', 'analytics_1895', 'account_3136', 'account_5684', 'analytics_4566', 'account_3866', 'analytics_4574', 'account_5482', 'analytics_6077', 'audit_record_4128', 'audit_record_7095', 'audit_record_3954', 'audit_record_1707']

for snap in data['snapshots']:
    for r in snap['records']:
        for t in targets:
            if t in str(r):
                print(f"[{t}] in snap '{snap['data_store']}' / '{snap['collection']}' (snap_captured={snap['captured_at']}):")
                print('  Record:', json.dumps(r))
