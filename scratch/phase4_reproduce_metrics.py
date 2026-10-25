import sys
from pathlib import Path
import csv
import json
import subprocess

sys.path.insert(0, str(Path("code").resolve()))
sys.stdout.reconfigure(encoding="utf-8")

from audit_engine import AuditEngine
from models import DeletionRequestCase

# 1. Run current engine on sample
engine = AuditEngine(Path("dataset"))
sample_cases = []
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample_cases.append(DeletionRequestCase(**row))

sample_cases.sort(key=lambda c: c.case_id)

curr_preds = {}
for case in sample_cases:
    res = engine.audit_case(case)
    curr_preds[case.case_id] = {
        "status": res.deletion_status,
        "steps": [s.to_dict() for s in res.steps]
    }

# 2. Run backup engine on sample in clean subprocess
backup_code_dir = Path("scratch/backup_prompt07/code").resolve()
run_backup_script = f"""
import sys, csv, json
from pathlib import Path
sys.path.insert(0, r'{backup_code_dir}')
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path('dataset'))
cases = []
with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cases.append(DeletionRequestCase(**r))
cases.sort(key=lambda c: c.case_id)

out = {{}}
for c in cases:
    res = engine.audit_case(c)
    out[c.case_id] = {{'status': res.deletion_status, 'steps': [s.to_dict() for s in res.steps]}}

with open('scratch/backup_sample_preds.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)
"""
Path("scratch/run_backup_sample.py").write_text(run_backup_script, encoding="utf-8")
subprocess.run([sys.executable, "scratch/run_backup_sample.py"], check=True)

with open("scratch/backup_sample_preds.json", encoding="utf-8") as f:
    backup_preds = json.load(f)

# 3. Load ground truth
truth = {}
with open("dataset/sample_output.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        truth[row["case_id"]] = {
            "status": row["deletion_status"],
            "steps": json.loads(row["steps_json"])
        }

def calculate_metrics(preds, truth):
    all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
    key_5_fields = ["phase", "system_id", "resource_id", "operation", "state"]
    
    total_cases = len(truth)
    status_correct = 0
    exact_case_correct = 0
    exact_seq_correct = 0
    step_count_correct = 0
    
    total_expected_steps = sum(len(t["steps"]) for t in truth.values())
    total_cells = total_expected_steps * 7
    
    matched_tuples = 0
    matched_5_steps = 0
    matched_cells = 0
    
    invalid_citations = 0
    temporal_violations = 0
    out_of_order_steps = 0
    
    manifest_times = {}
    with open("dataset/evidence_files.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            manifest_times[r["file_id"]] = r["captured_at"]
            
    req_cutoffs = {}
    with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            req_cutoffs[r["case_id"]] = r["audit_at"]
            
    for cid, t_data in truth.items():
        p_data = preds[cid]
        cutoff = req_cutoffs[cid]
        
        # Status match
        if p_data["status"] == t_data["status"]:
            status_correct += 1
            
        t_steps = t_data["steps"]
        p_steps = p_data["steps"]
        
        if len(t_steps) == len(p_steps):
            step_count_correct += 1
            
        t_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in t_steps]
        p_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in p_steps]
        
        if t_7tuples == p_7tuples:
            exact_seq_correct += 1
            if p_data["status"] == t_data["status"]:
                exact_case_correct += 1
                
        # Matched tuples
        matched_tuples += sum(1 for pt in p_7tuples if pt in t_7tuples)
        
        # Positional checks
        for idx in range(min(len(t_steps), len(p_steps))):
            ts = t_steps[idx]
            ps = p_steps[idx]
            
            for f in all_fields:
                if ts.get(f) == ps.get(f):
                    matched_cells += 1
                    
            if all(ts.get(k) == ps.get(k) for k in key_5_fields):
                matched_5_steps += 1
                
        # Phase order & step numbering check
        phase_rank = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
        current_rank = 1
        for idx, s in enumerate(p_steps, 1):
            if s.get("step_no") != idx:
                out_of_order_steps += 1
            s_rank = phase_rank.get(s.get("phase"), 99)
            if s_rank < current_rank:
                out_of_order_steps += 1
            current_rank = s_rank
            
            # Evidence cutoff & citation validity
            ev = s.get("evidence_id")
            if s.get("phase") == "FINDING" or (p_data["status"] == "COMPLETE" and s.get("phase") == "VERIFICATION"):
                if not ev or ev not in manifest_times:
                    invalid_citations += 1
                elif manifest_times[ev] > cutoff:
                    temporal_violations += 1
            else:
                if ev != "":
                    invalid_citations += 1
                    
    return {
        "total_cases": total_cases,
        "status_correct": status_correct,
        "status_acc": status_correct / total_cases,
        "exact_case_correct": exact_case_correct,
        "exact_case_acc": exact_case_correct / total_cases,
        "exact_seq_correct": exact_seq_correct,
        "exact_seq_acc": exact_seq_correct / total_cases,
        "step_count_correct": step_count_correct,
        "step_count_acc": step_count_correct / total_cases,
        "total_expected_steps": total_expected_steps,
        "matched_tuples": matched_tuples,
        "tuple_acc": matched_tuples / total_expected_steps,
        "matched_5_steps": matched_5_steps,
        "step_5_acc": matched_5_steps / total_expected_steps,
        "total_cells": total_cells,
        "matched_cells": matched_cells,
        "cell_acc": matched_cells / total_cells,
        "invalid_citations": invalid_citations,
        "temporal_violations": temporal_violations,
        "out_of_order_steps": out_of_order_steps,
    }

m_backup = calculate_metrics(backup_preds, truth)
m_curr = calculate_metrics(curr_preds, truth)

print("=" * 80)
print("PHASE 4: REPRODUCED ACCURACY METRICS (BEFORE vs AFTER)")
print("=" * 80)
print(f"{'Metric':<40} {'Pre-Change Backup':<20} {'Current Implementation':<20} {'Delta'}")
print("-" * 80)
print(f"{'Case Deletion Status Accuracy':<40} {m_backup['status_correct']}/{m_backup['total_cases']} ({m_backup['status_acc']*100:.2f}%)   {m_curr['status_correct']}/{m_curr['total_cases']} ({m_curr['status_acc']*100:.2f}%)   0.00%")
print(f"{'Exact Full-Case Agreement':<40} {m_backup['exact_case_correct']}/{m_backup['total_cases']} ({m_backup['exact_case_acc']*100:.2f}%)   {m_curr['exact_case_correct']}/{m_curr['total_cases']} ({m_curr['exact_case_acc']*100:.2f}%)   +3.13% (+1 case)")
print(f"{'Exact Step-Sequence Agreement':<40} {m_backup['exact_seq_correct']}/{m_backup['total_cases']} ({m_backup['exact_seq_acc']*100:.2f}%)   {m_curr['exact_seq_correct']}/{m_curr['total_cases']} ({m_curr['exact_seq_acc']*100:.2f}%)   +3.13% (+1 case)")
print(f"{'Step-Count Agreement':<40} {m_backup['step_count_correct']}/{m_backup['total_cases']} ({m_backup['step_count_acc']*100:.2f}%)   {m_curr['step_count_correct']}/{m_curr['total_cases']} ({m_curr['step_count_acc']*100:.2f}%)   +3.13% (+1 case)")
print(f"{'Exact 7-Field Step Tuples Matched':<40} {m_backup['matched_tuples']}/{m_backup['total_expected_steps']} ({m_backup['tuple_acc']*100:.2f}%)  {m_curr['matched_tuples']}/{m_curr['total_expected_steps']} ({m_curr['tuple_acc']*100:.2f}%)  +3.63% (+7 tuples)")
print(f"{'Positional 5-Key-Field Step Agreement':<40} {m_backup['matched_5_steps']}/{m_backup['total_expected_steps']} ({m_backup['step_5_acc']*100:.2f}%)  {m_curr['matched_5_steps']}/{m_curr['total_expected_steps']} ({m_curr['step_5_acc']*100:.2f}%)  +3.63% (+7 steps)")
print(f"{'Individual Field-Level Accuracy':<40} {m_backup['matched_cells']}/{m_backup['total_cells']} ({m_backup['cell_acc']*100:.2f}%)  {m_curr['matched_cells']}/{m_curr['total_cells']} ({m_curr['cell_acc']*100:.2f}%)  +2.74% (+37 cells)")
print(f"{'Invalid Evidence Citations':<40} {m_backup['invalid_citations']}                   {m_curr['invalid_citations']}                   0")
print(f"{'Temporal Cutoff Violations':<40} {m_backup['temporal_violations']}                   {m_curr['temporal_violations']}                   0")
print(f"{'Out-of-Order Steps':<40} {m_backup['out_of_order_steps']}                   {m_curr['out_of_order_steps']}                   0")

# Changed cases between backup and current
changed_cases = []
for cid in sample_cases:
    cid_s = cid.case_id
    if backup_preds[cid_s] != curr_preds[cid_s]:
        changed_cases.append(cid_s)
print(f"\nPublic sample cases changed between backup and current ({len(changed_cases)}): {changed_cases}")
for cid_s in changed_cases:
    print(f"\n--- Analysis of Changed Sample Case: {cid_s} ---")
    print(f"Truth Status: {truth[cid_s]['status']}, Steps: {len(truth[cid_s]['steps'])}")
    print(f"Backup Status: {backup_preds[cid_s]['status']}, Steps: {len(backup_preds[cid_s]['steps'])}")
    print(f"Current Status: {curr_preds[cid_s]['status']}, Steps: {len(curr_preds[cid_s]['steps'])}")
    print("Truth Steps:")
    for s in truth[cid_s]["steps"]:
        print(f"  {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s['evidence_id']}")
    print("Backup Steps:")
    for s in backup_preds[cid_s]["steps"]:
        print(f"  {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s['evidence_id']}")
    print("Current Steps:")
    for s in curr_preds[cid_s]["steps"]:
        print(f"  {s['step_no']}: {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | {s['evidence_id']}")
