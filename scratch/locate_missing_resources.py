import csv
import json
import os
from pathlib import Path

# Load all sample truth steps
with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    sample_pred = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

# Find all missing (case_id, resource_id)
missing_resources_by_case = {}
for cid in sorted(sample_truth.keys()):
    t_res = {s["resource_id"] for s in sample_truth[cid]}
    p_res = {s["resource_id"] for s in sample_pred[cid]}
    diff = t_res - p_res
    if diff:
        missing_resources_by_case[cid] = sorted(diff)

print(f"Total cases with missing resources: {len(missing_resources_by_case)}")

# Manifest
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    manifest = {r["file_path"]: (r["file_id"], r["captured_at"]) for r in csv.DictReader(f)}

# Now locate each missing resource across dataset/
# We want to know:
# 1. Which file contains it?
# 2. What is the file's file_id and captured_at?
# 3. What is the line/event timestamp inside the file?
# 4. What is the case's audit_at timestamp?

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

print("\n--- LOCATING MISSING RESOURCES ---")
for cid, res_list in sorted(missing_resources_by_case.items()):
    req = sample_reqs[cid]
    audit_at = req["audit_at"]
    print(f"\n[{cid}] (user={req['email']}, audit_at={audit_at}): Missing {res_list}")
    for rid in res_list:
        locations = []
        for root, dirs, files in os.walk("dataset"):
            for fname in files:
                if fname in ("sample_output.csv", "output.csv"):
                    continue
                fpath = Path(root) / fname
                rel_fpath = fpath.relative_to(Path("dataset")).as_posix()
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        for lno, line in enumerate(fp, 1):
                            if rid in line:
                                locations.append((rel_fpath, lno, line.strip()))
                except Exception:
                    pass
        print(f"  Resource {rid}: found in {len(locations)} locations:")
        for rel_p, lno, ltxt in locations[:3]:
            # Check if this file is in manifest
            file_info = manifest.get(rel_p, ("not_in_manifest", "unknown"))
            print(f"    - {rel_p} (file_id={file_info[0]}, captured_at={file_info[1]}): L{lno} -> {ltxt[:110]}")
