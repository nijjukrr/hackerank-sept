import sys
from pathlib import Path
sys.path.insert(0, "code")
from audit_engine import AuditEngine
from models import DeletionRequestCase
import csv, json

engine = AuditEngine(Path("dataset"))
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    cases = {row["case_id"]: DeletionRequestCase(**row) for row in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

early_cases = [
    "case_03", "case_04", "case_09", "case_18", "case_20", "case_21"
]

for cid in early_cases:
    c = cases[cid]
    pred_res = engine.audit_case(c)
    exp_status, exp_steps = expected[cid]
    pred_steps = [s.to_dict() for s in pred_res.steps]
    if pred_res.deletion_status != exp_status or pred_steps != exp_steps:
        print(f"=== {cid} === Exp={exp_status}, Pred={pred_res.deletion_status}")
        print("  EXP:")
        for s in exp_steps:
            print(f"    [{s['phase']}] {s['system_id']}:{s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
        print("  PRED:")
        for s in pred_steps:
            print(f"    [{s['phase']}] {s['system_id']}:{s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
