import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260917.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)

for i, snap in enumerate(bundle.get('snapshots', [])):
    scap = snap.get('captured_at')
    ds = snap.get('data_store')
    for r in snap.get('records', []):
        sub = r.get('subject_reference') or r.get('customer_reference') or r.get('user_id')
        if sub in ['user_23', 'user_24', 'user_29', 'user_30']:
            rid = r.get('resource_id')
            print(f"snap {i} | ds={ds} | captured_at={scap} | {sub} -> {rid}")
