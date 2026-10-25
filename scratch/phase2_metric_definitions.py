"""Phase 2 Metric Integrity Verification Script: Computes and validates all metric definitions."""

from __future__ import annotations

import csv
import json
from pathlib import Path

SAMPLE_TRUTH = Path("dataset/sample_output.csv")
SAMPLE_PRED = Path("sample_test_output.csv")

with SAMPLE_TRUTH.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with SAMPLE_PRED.open("r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
key_5_fields = ["phase", "system_id", "resource_id", "operation", "state"]

total_cases = len(truth)
status_matches = sum(1 for cid in truth if truth[cid][0] == pred[cid][0])
count_matches = sum(1 for cid in truth if len(truth[cid][1]) == len(pred[cid][1]))

exact_full_cases = 0
exact_seq_cases = 0
total_t_steps = sum(len(t[1]) for t in truth.values())
total_p_steps = sum(len(p[1]) for p in pred.values())

positional_key5_matches = 0
positional_cell_matches = {f: 0 for f in all_fields}
exact_7field_tuples = 0

# Check sequence invariant adherence
seq_invariant_pass_cases = 0

phase_order_map = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}

for cid in sorted(truth.keys()):
    t_st, t_steps = truth[cid]
    p_st, p_steps = pred[cid]

    t_tuples = [tuple(s.get(k, "") for k in all_fields) for s in t_steps]
    p_tuples = [tuple(s.get(k, "") for k in all_fields) for s in p_steps]

    # Full case match
    if t_st == p_st and t_tuples == p_tuples:
        exact_full_cases += 1
    if t_tuples == p_tuples:
        exact_seq_cases += 1

    # Exact tuple matches
    exact_7field_tuples += sum(1 for pt in p_tuples if pt in t_tuples)

    # Positional comparison
    for idx in range(min(len(t_steps), len(p_steps))):
        ts = t_steps[idx]
        ps = p_steps[idx]

        # Key 5 match at position idx
        if all(ts.get(k) == ps.get(k) for k in key_5_fields):
            positional_key5_matches += 1

        # Per field matches
        for f in all_fields:
            if ts.get(f) == ps.get(f):
                positional_cell_matches[f] += 1

    # Sequence invariant check on pred
    phases = [phase_order_map.get(s["phase"], 99) for s in p_steps]
    step_nos = [s["step_no"] for s in p_steps]
    is_phase_ordered = phases == sorted(phases)
    is_numbered = step_nos == list(range(1, len(p_steps) + 1))
    if is_phase_ordered and is_numbered:
        seq_invariant_pass_cases += 1

print("=" * 80)
print("PHASE 2: PRECISE METRIC CALCULATIONS & FORMULA VERIFICATION")
print("=" * 80)

print(f"\n1. Case-Level Status Accuracy:")
print(f"   Formula:     Count(pred_status == truth_status) / Total_Cases")
print(f"   Numerator:   {status_matches}")
print(f"   Denominator: {total_cases} cases")
print(f"   Value:       {status_matches / total_cases * 100:.2f}%\n")

print(f"2. Exact Full-Case Agreement:")
print(f"   Formula:     Count(pred_status == truth_status AND pred_steps == truth_steps on all 7 fields) / Total_Cases")
print(f"   Numerator:   {exact_full_cases}")
print(f"   Denominator: {total_cases} cases")
print(f"   Value:       {exact_full_cases / total_cases * 100:.2f}%\n")

print(f"3. Exact Ordered Step-Sequence Agreement:")
print(f"   Formula:     Count(pred_steps == truth_steps on all 7 fields in identical order) / Total_Cases")
print(f"   Numerator:   {exact_seq_cases}")
print(f"   Denominator: {total_cases} cases")
print(f"   Value:       {exact_seq_cases / total_cases * 100:.2f}%\n")

print(f"4. Step-Count Agreement:")
print(f"   Formula:     Count(len(pred_steps) == len(truth_steps)) / Total_Cases")
print(f"   Numerator:   {count_matches}")
print(f"   Denominator: {total_cases} cases")
print(f"   Value:       {count_matches / total_cases * 100:.2f}%\n")

print(f"5. Exact 7-Field Step-Tuple Agreement (Membership/Set Recall & Precision):")
print(f"   Recall (vs Expected Steps):     {exact_7field_tuples} / {total_t_steps} = {exact_7field_tuples / total_t_steps * 100:.2f}%")
print(f"   Precision (vs Predicted Steps):  {exact_7field_tuples} / {total_p_steps} = {exact_7field_tuples / total_p_steps * 100:.2f}%\n")

print(f"6. Positional 5-Key-Field Step Agreement Rate (Previously Mislabeled as Step-Field Accuracy):")
print(f"   Formula:     Count(ts[phase,sys,res,op,state] == ps[phase,sys,res,op,state] at position idx) / Total_Expected_Steps")
print(f"   Numerator:   {positional_key5_matches} step positions")
print(f"   Denominator: {total_t_steps} expected step rows")
print(f"   Value:       {positional_key5_matches / total_t_steps * 100:.2f}%\n")

print(f"7. True Individual Field-Level Accuracy (Cell-by-Cell):")
total_cells_7f = total_t_steps * 7
matched_cells_7f = sum(positional_cell_matches.values())
print(f"   All 7 Fields:  {matched_cells_7f} / {total_cells_7f} = {matched_cells_7f / total_cells_7f * 100:.2f}%")

total_cells_5f = total_t_steps * 5
matched_cells_5f = sum(positional_cell_matches[f] for f in key_5_fields)
print(f"   Key 5 Fields:  {matched_cells_5f} / {total_cells_5f} = {matched_cells_5f / total_cells_5f * 100:.2f}%")

print(f"\n   Field Breakdown (Numerator / {total_t_steps}):")
for f in all_fields:
    cnt = positional_cell_matches[f]
    print(f"     - {f:<15}: {cnt:>3} / {total_t_steps} ({cnt / total_t_steps * 100:.2f}%)")

print(f"\n8. Official Sequence Invariant Adherence:")
print(f"   Formula:     Count(FINDING -> REMEDIATION -> VERIFICATION, 1-indexed consecutive step_no) / Total_Cases")
print(f"   Value:       {seq_invariant_pass_cases} / {total_cases} = {seq_invariant_pass_cases / total_cases * 100:.2f}%")
