import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json

# Let's inspect all snapshot bundle files and their snapshots
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = {r["file_id"]: r for r in csv.DictReader(f)}

bundle_files = [m for m in ev_files.values() if "customer_data_snapshot_bundle" in m["file_path"]]
print(f"Total bundle files: {len(bundle_files)}")

for m in bundle_files:
    fpath = Path("dataset") / m["file_path"]
    with fpath.open("r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n{m['file_id']} ({m['file_path']}): meta.captured_at = {m['captured_at']}")
    for s in data.get("snapshots", []):
        scap = s.get("captured_at")
        ds = s.get("data_store")
        col = s.get("collection")
        print(f"   snap: ds={ds}, col={col}, snap.captured_at={scap}")
