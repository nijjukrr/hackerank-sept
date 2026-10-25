import sys
from pathlib import Path
import csv
import json

sys.path.insert(0, str(Path("code").resolve()))
sys.stdout.reconfigure(encoding="utf-8")

from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))
sample_cases = []
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample_cases.append(DeletionRequestCase(**row))

sample_cases.sort(key=lambda c: c.case_id)

preds = {}
for case in sample_cases:
    res = engine.audit_case(case)
    preds[case.case_id] = {
        "status": res.deletion_status,
        "steps": [s.to_dict() for s in res.steps]
    }

truth = {}
with open("dataset/sample_output.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        truth[row["case_id"]] = {
            "status": row["deletion_status"],
            "steps": json.loads(row["steps_json"])
        }

manifest = {}
with open("dataset/evidence_files.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        manifest[r["file_id"]] = r

cutoffs = {}
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cutoffs[r["case_id"]] = r["audit_at"]

mismatches = []
exact_matches = []

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

for cid in sorted(truth.keys()):
    t = truth[cid]
    p = preds[cid]
    
    t_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in t["steps"]]
    p_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in p["steps"]]
    
    is_exact = (t["status"] == p["status"]) and (t_7tuples == p_7tuples)
    if is_exact:
        exact_matches.append(cid)
    else:
        mismatches.append(cid)

print(f"Total Public Cases: {len(truth)}")
print(f"Exact Matches: {len(exact_matches)} ({len(exact_matches)/len(truth)*100:.2f}%) -> {exact_matches}")
print(f"Mismatches: {len(mismatches)} ({len(mismatches)/len(truth)*100:.2f}%) -> {mismatches}\n")

print("=" * 80)
print("PHASE 1: DETAILED STEP-BY-STEP COMPARISON OF ALL 17 MISMATCHED PUBLIC CASES")
print("=" * 80)

for cid in mismatches:
    t = truth[cid]
    p = preds[cid]
    cutoff = cutoffs[cid]
    
    print(f"\n--------------------------------------------------------------------------------")
    print(f"CASE: {cid} | Status: Truth={t['status']} vs Pred={p['status']} | Cutoff={cutoff}")
    print(f"Step counts: Truth={len(t['steps'])} vs Pred={len(p['steps'])}")
    
    t_steps = t["steps"]
    p_steps = p["steps"]
    
    print("Truth Steps:")
    for s in t_steps:
        ev = s.get("evidence_id", "")
        ev_time = manifest.get(ev, {}).get("captured_at", "") if ev else ""
        print(f"  {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {ev} ({ev_time})")
        
    print("Pred Steps:")
    for s in p_steps:
        ev = s.get("evidence_id", "")
        ev_time = manifest.get(ev, {}).get("captured_at", "") if ev else ""
        print(f"  {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {ev} ({ev_time})")
        
    # Analyze difference
    missing_in_pred = [s for s in t_steps if tuple(s.get(k, "") for k in all_fields[1:]) not in [tuple(ps.get(k, "") for k in all_fields[1:]) for ps in p_steps]]
    extra_in_pred = [ps for ps in p_steps if tuple(ps.get(k, "") for k in all_fields[1:]) not in [tuple(s.get(k, "") for k in all_fields[1:]) for s in t_steps]]
    
    print("Analysis:")
    if missing_in_pred:
        print("  Missing in Pred:")
        for m in missing_in_pred:
            print(f"    - {m['phase']} | {m['system_id']} | {m['resource_id']} | {m['operation']} | {m['state']} | {m['evidence_id']}")
    if extra_in_pred:
        print("  Extra in Pred:")
        for e in extra_in_pred:
            print(f"    + {e['phase']} | {e['system_id']} | {e['resource_id']} | {e['operation']} | {e['state']} | {e['evidence_id']}")
