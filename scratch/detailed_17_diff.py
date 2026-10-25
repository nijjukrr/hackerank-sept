import sys
from pathlib import Path
sys.path.insert(0, "code")
from audit_engine import AuditEngine
from models import DeletionRequestCase
import csv
import json

engine = AuditEngine(Path("dataset"))
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

mismatches = []
for c in cases:
    cid = c.case_id
    pred_res = engine.audit_case(c)
    exp_status, exp_steps = expected[cid]
    pred_steps = [s.to_dict() for s in pred_res.steps]
    
    # Check if exact match
    is_exact = (pred_res.deletion_status == exp_status and pred_steps == exp_steps)
    if not is_exact:
        mismatches.append((cid, c, exp_status, exp_steps, pred_res.deletion_status, pred_steps))

print(f"Total non-exact cases: {len(mismatches)} / {len(cases)}")
for cid, c, exp_stat, exp_s, pred_stat, pred_s in mismatches:
    print(f"\n==================== {cid} ====================")
    print(f"Status: Expected={exp_stat}, Predicted={pred_stat}")
    print("EXPECTED STEPS:")
    for s in exp_s:
        print(f"   [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")
    print("PREDICTED STEPS:")
    for s in pred_s:
        print(f"   [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")
