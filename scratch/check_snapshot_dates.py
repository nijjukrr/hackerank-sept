import json
import glob

for fpath in glob.glob("dataset/evidence/records/customer_data_snapshot_bundle_*.json"):
    print(f"\nFile: {fpath}")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Top-level exported_at: {data.get('exported_at')}")
    for i, s in enumerate(data.get("snapshots", [])):
        print(f"  snap[{i}]: ds={s.get('data_store')}, col={s.get('collection')}, captured_at={s.get('captured_at')}, num_records={len(s.get('records', []))}")
