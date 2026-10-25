import csv
import json
from collections import defaultdict
from pathlib import Path

truth_path = Path("dataset/sample_output.csv")
pred_path = Path("scratch/baseline_sample_output.csv")

with truth_path.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with pred_path.open("r", encoding="utf-8") as f:
    preds = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = {r["case_id"]: r for r in csv.DictReader(f)}

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

diff_summary = []
for cid in sorted(truth.keys()):
    t_status, t_steps = truth[cid]
    p_status, p_steps = preds[cid]
    
    t_tuples = [tuple(s[k] for k in all_fields) for s in t_steps]
    p_tuples = [tuple(s[k] for k in all_fields) for s in p_steps]
    
    if t_tuples == p_tuples and t_status == p_status:
        continue
    
    t_set = set(t_tuples)
    p_set = set(p_tuples)
    
    missing_tuples = [s for s in t_steps if tuple(s[k] for k in all_fields) not in p_set]
    extra_tuples = [s for s in p_steps if tuple(s[k] for k in all_fields) not in t_set]
    
    diff_summary.append({
        "case_id": cid,
        "req": reqs[cid],
        "truth_status": t_status,
        "pred_status": p_status,
        "truth_count": len(t_steps),
        "pred_count": len(p_steps),
        "missing": missing_tuples,
        "extra": extra_tuples
    })

print(f"Total non-matching cases: {len(diff_summary)}")
for d in diff_summary:
    print(f"\n==========================================")
    print(f"CASE: {d['case_id']} | Status: Truth={d['truth_status']}, Pred={d['pred_status']} | Steps: Truth={d['truth_count']}, Pred={d['pred_count']}")
    print(f"Requested: {d['req']['requested_at']} | Audit Cutoff: {d['req']['audit_at']}")
    print(f"Request Email: {d['req']['email']}")
    print(f"MISSING STEPS ({len(d['missing'])}):")
    for s in d['missing']:
        print(f"  [-] {s['phase']:<12} {s['system_id']:<18} {s['resource_id']:<18} {s['operation']:<24} {s['state']:<10} ev={s['evidence_id']}")
    print(f"EXTRA STEPS ({len(d['extra'])}):")
    for s in d['extra']:
        print(f"  [+] {s['phase']:<12} {s['system_id']:<18} {s['resource_id']:<18} {s['operation']:<24} {s['state']:<10} ev={s['evidence_id']}")
