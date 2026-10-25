import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json
from collections import defaultdict
from datetime import datetime

# Let's inspect how snap.get("captured_at") affects evidence observations
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = {r["file_id"]: r for r in csv.DictReader(f)}

print("Loaded evidence files:", len(ev_files))

# Check evidence_02
meta02 = ev_files.get("evidence_02")
print("evidence_02 meta captured_at:", meta02["captured_at"])
with open(f"dataset/{meta02['file_path']}", "r", encoding="utf-8") as f:
    data02 = json.load(f)

for i, snap in enumerate(data02.get("snapshots", [])):
    snap_cap = snap.get("captured_at")
    ds = snap.get("data_store")
    recs = snap.get("records", [])
    print(f"  snap {i}: ds={ds}, internal captured_at={snap_cap}, recs={len(recs)}")
