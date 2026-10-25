import csv
import json
from pathlib import Path
import sys

# Load inputs
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    requests = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    evidence_manifest = {r["file_id"]: r for r in csv.DictReader(f)}

with open("output.csv", "r", encoding="utf-8") as f:
    rows = list(csv.reader(f))

header = rows[0]
data_rows = rows[1:]

print("=== DEEP AUDIT OF ALL OUTPUT ROWS ===")
print(f"Header: {header}")
assert header == ["case_id", "deletion_status", "steps_json"], f"Invalid header {header}"
print(f"Data rows count: {len(data_rows)}")
assert len(data_rows) == 518, f"Expected 518 rows, got {len(data_rows)}"

row_cids = [r[0] for r in data_rows]
req_cids = sorted(requests.keys())
assert row_cids == req_cids, "Row case_ids do not match sorted input deletion_requests case_ids!"
print("Coverage: Exactly 518 matching case_ids, perfectly sorted from case_33 to case_550.")

# Audit checks
status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
temporal_violations = []
invalid_evidence_ids = []
step_schema_errors = []
ordering_errors = []

for line_idx, (cid, status, steps_raw) in enumerate(data_rows, 2):
    status_counts[status] = status_counts.get(status, 0) + 1
    req = requests[cid]
    audit_cutoff = req["audit_at"]
    
    steps = json.loads(steps_raw)
    
    if status == "NOT_APPLICABLE":
        if len(steps) != 0:
            step_schema_errors.append(f"{cid}: NOT_APPLICABLE with non-empty steps")
        continue

    # Check consecutive numbering and phases
    for idx, step in enumerate(steps, 1):
        if step.get("step_no") != idx:
            step_schema_errors.append(f"{cid}: step {idx} has step_no {step.get('step_no')}")
            
        ev_id = step.get("evidence_id")
        
        # Check evidence citations
        if status == "COMPLETE":
            if not ev_id:
                invalid_evidence_ids.append(f"{cid} (COMPLETE): step {idx} missing evidence_id")
            elif ev_id not in evidence_manifest:
                invalid_evidence_ids.append(f"{cid} (COMPLETE): step {idx} cites nonexistent evidence_id '{ev_id}'")
            else:
                ev_meta = evidence_manifest[ev_id]
                if ev_meta["captured_at"] > audit_cutoff:
                    temporal_violations.append(f"{cid} (COMPLETE): step {idx} cites {ev_id} captured at {ev_meta['captured_at']} > audit_at {audit_cutoff}")
        elif status == "INCOMPLETE":
            phase = step.get("phase")
            if phase == "FINDING":
                if not ev_id:
                    invalid_evidence_ids.append(f"{cid} (INCOMPLETE FINDING): step {idx} missing evidence_id")
                elif ev_id not in evidence_manifest:
                    invalid_evidence_ids.append(f"{cid} (INCOMPLETE FINDING): step {idx} cites nonexistent evidence_id '{ev_id}'")
                else:
                    ev_meta = evidence_manifest[ev_id]
                    if ev_meta["captured_at"] > audit_cutoff:
                        temporal_violations.append(f"{cid} (INCOMPLETE FINDING): step {idx} cites {ev_id} captured at {ev_meta['captured_at']} > audit_at {audit_cutoff}")
            else:
                if ev_id != "":
                    invalid_evidence_ids.append(f"{cid} (INCOMPLETE {phase}): step {idx} has non-empty evidence_id '{ev_id}'")

print(f"\nStatus breakdown across 518 cases:")
for st, cnt in sorted(status_counts.items()):
    print(f"  {st}: {cnt} ({cnt/518*100:.2f}%)")

print(f"\nValidation Checks Results:")
print(f"  Temporal Cutoff Violations (captured_at > audit_at): {len(temporal_violations)}")
if temporal_violations:
    for tv in temporal_violations[:10]:
        print(f"    - {tv}")

print(f"  Invalid / Nonexistent Evidence IDs: {len(invalid_evidence_ids)}")
if invalid_evidence_ids:
    for ie in invalid_evidence_ids[:10]:
        print(f"    - {ie}")

print(f"  Step Schema / Numbering Errors: {len(step_schema_errors)}")
if step_schema_errors:
    for se in step_schema_errors[:10]:
        print(f"    - {se}")

print("=== AUDIT COMPLETE ===")
