import json
import csv

# Inspect evidence_02
with open('dataset/evidence/records/customer_data_snapshot_bundle_20260917.json', 'r', encoding='utf-8') as f:
    ev02 = json.load(f)

print("=== EVIDENCE_02 SNAPSHOTS ===")
for idx, snap in enumerate(ev02['snapshots']):
    ds = snap.get('data_store')
    col = snap.get('collection')
    snap_cap = snap.get('captured_at')
    recs = snap.get('records', [])
    print(f"Snap {idx}: data_store={ds}, collection={col}, snap_captured_at={snap_cap}, records={len(recs)}")
    for r in recs[:2]:
        print(f"   Rec: {json.dumps(r)[:120]}")

snap8 = ev02['snapshots'][8]
print(f"\nSnap 8 ({snap8['data_store']}, captured={snap8.get('captured_at')}):")
for r in snap8['records']:
    print('  ', r['resource_id'], r['subject_reference'], r['event_name'])
