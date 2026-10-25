import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("code").resolve()))
from evaluation.main import validate_csv

out_path = Path("output.csv")
req_path = Path("dataset/deletion_requests.csv")
ev_path = Path("dataset/evidence_files.csv")

with open(req_path, encoding="utf-8") as f:
    eval_requests = {r["case_id"]: r for r in csv.DictReader(f)}

with open(ev_path, encoding="utf-8") as f:
    evidence_manifest = {r["file_id"]: r for r in csv.DictReader(f)}

with open(out_path, encoding="utf-8") as f:
    out_rows = list(csv.DictReader(f))

print(f"=== AUDITING FULL 518 EVALUATION OUTPUTS ===")
print(f"Total Rows in output.csv: {len(out_rows)}")
print(f"Total Input Requests: {len(eval_requests)}")

# 1. Base schema validation
schema_errors = validate_csv(out_path, expected_count=518)
print(f"1. Schema Validation Errors: {len(schema_errors)}")
for e in schema_errors[:5]:
    print(f"   - {e}")

# 2. Case coverage check
out_cids = [r["case_id"] for r in out_rows]
req_cids = sorted(list(eval_requests.keys()))
print(f"2. Case Coverage Check:")
print(f"   Missing IDs: {set(req_cids) - set(out_cids)}")
print(f"   Extra IDs: {set(out_cids) - set(req_cids)}")
print(f"   Strict Sort Order Match: {out_cids == req_cids}")

# 3. Temporal Cutoff & Evidence Existence Check for all cited evidence_ids
temporal_violations = []
nonexistent_evidence = []
status_distribution = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

for line_idx, r in enumerate(out_rows, 1):
    cid = r["case_id"]
    status = r["deletion_status"]
    status_distribution[status] = status_distribution.get(status, 0) + 1
    req = eval_requests[cid]
    audit_at = req["audit_at"]
    
    steps = json.loads(r["steps_json"])
    for s in steps:
        ev_id = s.get("evidence_id")
        if ev_id:
            # Check manifest existence
            if ev_id not in evidence_manifest:
                nonexistent_evidence.append((cid, s["step_no"], ev_id))
            else:
                ev_meta = evidence_manifest[ev_id]
                cap_at = ev_meta["captured_at"]
                if cap_at > audit_at:
                    temporal_violations.append((cid, s["step_no"], ev_id, cap_at, audit_at))

print(f"\n3. Status Distribution: {status_distribution}")
print(f"4. Nonexistent Evidence Citations: {len(nonexistent_evidence)}")
for ne in nonexistent_evidence[:5]:
    print(f"   - Case {ne[0]} step {ne[1]}: {ne[2]}")
print(f"5. Temporal Cutoff Violations (captured_at > audit_at): {len(temporal_violations)}")
for tv in temporal_violations[:5]:
    print(f"   - Case {tv[0]} step {tv[1]}: {tv[2]} (captured {tv[3]} > audit cutoff {tv[4]})")

# 6. Risk-based sampling trace
print(f"\n6. Risk-based Case Sampling Traces:")
sample_check_ids = ["case_33", "case_100", "case_250", "case_500", "case_533", "case_538", "case_542", "case_550"]
for cid in sample_check_ids:
    row = [r for r in out_rows if r["case_id"] == cid][0]
    req = eval_requests[cid]
    print(f"\n[{cid}] Status: {row['deletion_status']}")
    print(f"   Request: {req['request_text'][:80]}...")
    steps = json.loads(row["steps_json"])
    print(f"   Steps Count: {len(steps)}")
    for s in steps[:3]:
        print(f"     Step {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev={s['evidence_id']}")
    if len(steps) > 3:
        print(f"     ... and {len(steps)-3} more steps")
