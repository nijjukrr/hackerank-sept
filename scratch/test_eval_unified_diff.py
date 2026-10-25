import sys
from pathlib import Path
import csv
import json

sys.path.insert(0, str(Path("code").resolve()))
sys.path.insert(0, str(Path("scratch").resolve()))

import test_complete_log_integration
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))

cases = []
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cases.append(
            DeletionRequestCase(
                case_id=row["case_id"].strip(),
                email=row["email"].strip(),
                requested_at=row["requested_at"].strip(),
                reported_status=row["reported_status"].strip(),
                reported_at=row["reported_at"].strip(),
                audit_at=row["audit_at"].strip(),
                request_text=row["request_text"].strip(),
            )
        )

cases.sort(key=lambda c: c.case_id)

fixed_preds = {}
for case in cases:
    res = engine.audit_case(case)
    fixed_preds[case.case_id] = {
        "status": res.deletion_status,
        "steps": [s.to_dict() for s in res.steps]
    }

current_preds = {}
with open("output.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        current_preds[r["case_id"]] = {
            "status": r["deletion_status"],
            "steps": json.loads(r["steps_json"])
        }

status_diffs = []
step_diffs = []

for cid in fixed_preds:
    curr = current_preds.get(cid)
    fix = fixed_preds[cid]
    if not curr: continue
    if curr["status"] != fix["status"]:
        status_diffs.append((cid, curr["status"], fix["status"]))
    elif len(curr["steps"]) != len(fix["steps"]):
        step_diffs.append((cid, len(curr["steps"]), len(fix["steps"])))

print(f"Total evaluated cases: {len(fixed_preds)}")
print(f"Status differences: {len(status_diffs)}")
for cid, old_st, new_st in status_diffs:
    print(f"  {cid}: {old_st} -> {new_st}")

print(f"Step count differences with same status: {len(step_diffs)}")
for cid, old_sc, new_sc in step_diffs[:15]:
    print(f"  {cid}: {old_sc} -> {new_sc} steps")

# Check case_522 specifically
print("\n=== case_522 steps with unified parser ===")
for s in fixed_preds["case_522"]["steps"]:
    print(f"  Step {s['step_no']}: phase={s['phase']}, system={s['system_id']}, resource={s['resource_id']}, op={s['operation']}, state={s['state']}, ev={s['evidence_id']}")
