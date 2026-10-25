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

# For each case, check missing steps and find where resource_id appears in dataset/evidence/
missing_resources = []
for cid, case in sorted(sample_cases.items()):
    pred = engine.audit_case(case)
    exp_status, exp_steps = expected[cid]
    pred_steps = [s.to_dict() for s in pred.steps]
    
    if pred_steps == exp_steps:
        continue
    
    # Identify expected steps not matched in predicted (by 5 key fields)
    p_keys = {(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in pred_steps}
    t_keys = {(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) for s in exp_steps}
    
    missing_in_pred = [s for s in exp_steps if (s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) not in p_keys]
    extra_in_pred = [s for s in pred_steps if (s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"]) not in t_keys]
    
    print(f"\n==================== {cid} (audit_at: {case.audit_at}) ====================")
    print(f"User: email={case.email}, requested_at={case.requested_at}, reported={case.reported_status}")
    u_info = engine.identity_resolver.resolve_email(case.email)
    print(f"Resolved Identity: user_id={u_info.user_id if u_info else None}, emails={u_info.all_emails if u_info else None}, hashes={u_info.all_hashes if u_info else None}")
    
    print(f"--- Missing in Predicted ({len(missing_in_pred)} steps) ---")
    for s in missing_in_pred:
        print(f"   [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")
        missing_resources.append((cid, s['system_id'], s['resource_id'], s['evidence_id'], s))
        
    print(f"--- Extra in Predicted ({len(extra_in_pred)} steps) ---")
    for s in extra_in_pred:
        print(f"   [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")

print(f"\nTotal Missing Steps across sample: {len(missing_resources)}")
