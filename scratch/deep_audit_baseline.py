import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("code").resolve()))
from audit_engine import AuditEngine
from models import DeletionRequestCase

dataset_dir = Path("dataset")
engine = AuditEngine(dataset_dir)

with open(dataset_dir / "sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_requests = list(csv.DictReader(f))

with open(dataset_dir / "sample_output.csv", encoding="utf-8") as f:
    sample_outputs = {r["case_id"]: r for r in csv.DictReader(f)}

with open(dataset_dir / "evidence_files.csv", encoding="utf-8") as f:
    valid_evidence_ids = {r["file_id"] for r in csv.DictReader(f)}

total_cases = len(sample_requests)
status_matches = 0
step_count_matches = 0
exact_array_matches = 0

total_truth_steps = 0
total_pred_steps = 0
phase_matches = 0
op_matches = 0
sys_matches = 0
res_matches = 0
state_matches = 0
ev_matches = 0
order_matches = 0
invalid_evidence_citations = []

print(f"=== INDEPENDENT BASELINE AUDIT: {total_cases} SAMPLE CASES ===")

detailed_mismatches = []

for req in sample_requests:
    cid = req["case_id"]
    case_obj = DeletionRequestCase(
        case_id=cid,
        email=req["email"],
        requested_at=req["requested_at"],
        reported_status=req["reported_status"],
        reported_at=req["reported_at"],
        audit_at=req["audit_at"],
        request_text=req["request_text"],
    )
    res = engine.audit_case(case_obj)
    
    t_row = sample_outputs[cid]
    t_status = t_row["deletion_status"]
    t_steps = json.loads(t_row["steps_json"])
    p_status = res.deletion_status
    p_steps = [s.to_dict() for s in res.steps]
    
    # Status match
    st_match = (p_status == t_status)
    if st_match:
        status_matches += 1
        
    cnt_match = (len(p_steps) == len(t_steps))
    if cnt_match:
        step_count_matches += 1
        
    total_truth_steps += len(t_steps)
    total_pred_steps += len(p_steps)
    
    # Check invalid evidence citations
    for s in p_steps:
        ev_id = s.get("evidence_id")
        if ev_id:
            if ev_id not in valid_evidence_ids and not ev_id.startswith("activity_") and not ev_id.startswith("audit_"):
                invalid_evidence_citations.append((cid, s["step_no"], ev_id))
    
    # Detailed step comparison
    case_exact = st_match and cnt_match
    step_diffs = []
    
    for idx in range(max(len(t_steps), len(p_steps))):
        if idx >= len(t_steps):
            step_diffs.append(f"Extra pred step {idx+1}: {p_steps[idx]}")
            case_exact = False
            continue
        if idx >= len(p_steps):
            step_diffs.append(f"Missing pred step {idx+1}: {t_steps[idx]}")
            case_exact = False
            continue
            
        ts = t_steps[idx]
        ps = p_steps[idx]
        
        diff = []
        if ts.get("phase") == ps.get("phase"): phase_matches += 1
        else: diff.append(f"phase({ps.get('phase')}!=truth:{ts.get('phase')})")
        
        if ts.get("operation") == ps.get("operation"): op_matches += 1
        else: diff.append(f"op({ps.get('operation')}!=truth:{ts.get('operation')})")
        
        if ts.get("system_id") == ps.get("system_id"): sys_matches += 1
        else: diff.append(f"sys({ps.get('system_id')}!=truth:{ts.get('system_id')})")
        
        if ts.get("resource_id") == ps.get("resource_id"): res_matches += 1
        else: diff.append(f"res({ps.get('resource_id')}!=truth:{ts.get('resource_id')})")
        
        if ts.get("state") == ps.get("state"): state_matches += 1
        else: diff.append(f"state({ps.get('state')}!=truth:{ts.get('state')})")
        
        if ts.get("evidence_id") == ps.get("evidence_id"): ev_matches += 1
        else: diff.append(f"ev({ps.get('evidence_id')}!=truth:{ts.get('evidence_id')})")
        
        if diff:
            case_exact = False
            step_diffs.append(f"Step {idx+1} mismatch: {', '.join(diff)}")
            
    if case_exact:
        exact_array_matches += 1
    else:
        detailed_mismatches.append((cid, p_status, t_status, len(p_steps), len(t_steps), step_diffs))

print(f"\n--- RESULTS SUMMARY ---")
print(f"Total Cases: {total_cases}")
print(f"Status Agreement: {status_matches}/{total_cases} ({status_matches/total_cases*100:.2f}%)")
print(f"Step Count Agreement: {step_count_matches}/{total_cases} ({step_count_matches/total_cases*100:.2f}%)")
print(f"Exact Case Agreement: {exact_array_matches}/{total_cases} ({exact_array_matches/total_cases*100:.2f}%)")
print(f"Total Expected Steps: {total_truth_steps}, Total Predicted Steps: {total_pred_steps}")
print(f"Phase Matches: {phase_matches}/{total_truth_steps} ({phase_matches/total_truth_steps*100:.2f}%)")
print(f"Operation Matches: {op_matches}/{total_truth_steps} ({op_matches/total_truth_steps*100:.2f}%)")
print(f"System ID Matches: {sys_matches}/{total_truth_steps} ({sys_matches/total_truth_steps*100:.2f}%)")
print(f"Resource ID Matches: {res_matches}/{total_truth_steps} ({res_matches/total_truth_steps*100:.2f}%)")
print(f"State Matches: {state_matches}/{total_truth_steps} ({state_matches/total_truth_steps*100:.2f}%)")
print(f"Evidence ID Matches: {ev_matches}/{total_truth_steps} ({ev_matches/total_truth_steps*100:.2f}%)")
print(f"Invalid Evidence Citations: {len(invalid_evidence_citations)}")

print(f"\n--- DETAILED MISMATCHES ({len(detailed_mismatches)}) ---")
for cid, pst, tst, pcnt, tcnt, diffs in detailed_mismatches:
    print(f"\n[{cid}] Pred Status: {pst} | Truth Status: {tst} | Pred Steps: {pcnt} | Truth Steps: {tcnt}")
    for d in diffs[:5]:
        print(f"   {d}")
    if len(diffs) > 5:
        print(f"   ... and {len(diffs)-5} more diffs")
