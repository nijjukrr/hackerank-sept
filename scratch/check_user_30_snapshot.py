import json

with open("dataset/evidence/records/customer_data_snapshot_bundle_20260917.json", encoding="utf-8") as f:
    d = json.load(f)

for snap in d["snapshots"]:
    for rec in snap.get("records", []):
        txt = json.dumps(rec)
        if '"user_30"' in txt or "camille.bernard" in txt:
            print("Found in", snap.get("data_store"), snap.get("collection"))
            print(" ", rec)
