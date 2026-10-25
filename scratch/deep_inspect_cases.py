import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, "code")
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = {row["case_id"]: DeletionRequestCase(**row) for row in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

for cid in ["case_09", "case_18", "case_20", "case_21", "case_22", "case_23", "case_24", "case_25", "case_26", "case_27", "case_28", "case_29", "case_30"]:
    case = sample_cases[cid]
    u = engine.identity_resolver.resolve_email(case.email)
    uid = u.user_id if u else None
    emails = u.all_emails if u else ()
    hashes = u.all_hashes if u else ()
    
    exp_status, exp_steps = expected[cid]
    pred = engine.audit_case(case)
    pred_steps = [s.to_dict() for s in pred.steps]
    
    print(f"\n==================== {cid} (User: {uid}) ====================")
    print(f"Emails: {emails}")
    print(f"Hashes: {hashes}")
    print(f"Audit Cutoff: {case.audit_at}")
    print("Expected steps count:", len(exp_steps), "Predicted:", len(pred_steps))
    
    # Missing steps
    p_set = {(s["phase"], s["system_id"], s["resource_id"], s["operation"]) for s in pred_steps}
    missing = [s for s in exp_steps if (s["phase"], s["system_id"], s["resource_id"], s["operation"]) not in p_set]
    print("Missing in predicted:")
    for s in missing:
        print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | ev={s['evidence_id']}")
