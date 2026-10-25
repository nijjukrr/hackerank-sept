import csv
import os

target = "priya.raman@gmail.com"
cutoff = "2026-02-14T10:00:00Z"

print(f"=== Activity for {target} before {cutoff} ===")
with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if target in str(r.values()) and r["event_time"] <= cutoff:
            print(r)

print(f"\n=== Evidence files mentioning {target} captured before {cutoff} ===")
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    meta = {r["file_id"]: r for r in csv.DictReader(f)}

for fid, m in meta.items():
    if m["captured_at"] <= cutoff:
        fpath = os.path.join("dataset", m["file_path"])
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                if target in f.read():
                    print(f"File {fid}: {m['file_path']}, captured {m['captured_at']}")
        except:
            pass
