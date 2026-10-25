import csv
import json
from pathlib import Path
import subprocess
import sys

# 1. Run pipeline on sample
cmd = [sys.executable, "code/main.py", "--sample"]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Pipeline run return code:", res.returncode)

# 2. Load expected and predicted
truth_path = Path("dataset/sample_output.csv")
pred_path = Path("sample_test_output.csv")

with truth_path.open("r", encoding="utf-8") as f:
    truth_rows = list(csv.DictReader(f))
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in truth_rows}

with pred_path.open("r", encoding="utf-8") as f:
    pred_rows = list(csv.DictReader(f))
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in pred_rows}

total_cases = len(truth)
assert total_cases == 32
assert set(truth.keys()) == set(pred.keys()), "Case IDs do not match!"

correct_status = 0
exact_seq_match = 0
exact_case_match = 0
step_count_match = 0

cases_complete_step_agreement = 0
cases_partial_step_agreement = 0
cases_zero_step_agreement = 0

total_expected_steps = sum(len(steps) for _, steps in truth.values())
total_pred_steps = sum(len(steps) for _, steps in pred.values())

field_counts = {
    "step_no": 0,
    "phase": 0,
    "system_id": 0,
    "resource_id": 0,
    "operation": 0,
    "state": 0,
    "evidence_id": 0,
}
exact_step_tuples_matched = 0

missing_steps_count = 0
extra_steps_count = 0
reordered_steps_count = 0
mismatched_steps_count = 0

for cid in sorted(truth.keys()):
    t_status, t_steps = truth[cid]
    p_status, p_steps = pred[cid]

    status_match = (t_status == p_status)
    if status_match:
        correct_status += 1

    if len(t_steps) == len(p_steps):
        step_count_match += 1

    seq_match = (t_steps == p_steps)
    if seq_match:
        exact_seq_match += 1

    if status_match and seq_match:
        exact_case_match += 1

    # Compare steps aligned by position up to min len
    min_len = min(len(t_steps), len(p_steps))
    case_matched_steps = 0
    for idx in range(min_len):
        ts = t_steps[idx]
        ps = p_steps[idx]

        for k in field_counts:
            if ts.get(k) == ps.get(k):
                field_counts[k] += 1

        if (
            ts.get("phase") == ps.get("phase")
            and ts.get("system_id") == ps.get("system_id")
            and ts.get("resource_id") == ps.get("resource_id")
            and ts.get("operation") == ps.get("operation")
            and ts.get("state") == ps.get("state")
            and ts.get("evidence_id") == ps.get("evidence_id")
        ):
            case_matched_steps += 1
            exact_step_tuples_matched += 1
        else:
            mismatched_steps_count += 1

    if len(t_steps) > len(p_steps):
        missing_steps_count += (len(t_steps) - len(p_steps))
    elif len(p_steps) > len(t_steps):
        extra_steps_count += (len(p_steps) - len(t_steps))

    # Check unaligned set overlap (to detect reordering)
    t_set = {
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id"))
        for s in t_steps
    }
    p_set = {
        (s.get("phase"), s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("state"), s.get("evidence_id"))
        for s in p_steps
    }
    common_set = t_set.intersection(p_set)
    if len(common_set) > case_matched_steps:
        reordered_steps_count += (len(common_set) - case_matched_steps)

    if case_matched_steps == len(t_steps) and len(t_steps) == len(p_steps):
        cases_complete_step_agreement += 1
    elif case_matched_steps > 0 or len(common_set) > 0:
        cases_partial_step_agreement += 1
    else:
        cases_zero_step_agreement += 1

print("="*60)
print("PHASE 1: REPRODUCED BENCHMARK METRICS")
print("="*60)
print(f"Total Sample Cases: {total_cases}")
print(f"Total Expected Steps: {total_expected_steps}")
print(f"Total Predicted Steps: {total_pred_steps}")
print(f"Case-Level Status Accuracy: {correct_status}/{total_cases} ({correct_status/total_cases*100:.2f}%)")
print(f"Exact Full-Case Agreement (Status + All Steps): {exact_case_match}/{total_cases} ({exact_case_match/total_cases*100:.2f}%)")
print(f"Exact Step-Sequence Agreement: {exact_seq_match}/{total_cases} ({exact_seq_match/total_cases*100:.2f}%)")
print(f"Step-Count Agreement: {step_count_match}/{total_cases} ({step_count_match/total_cases*100:.2f}%)")
print()
print("Cases by Step Agreement Level:")
print(f"  Complete step agreement: {cases_complete_step_agreement}/{total_cases} ({cases_complete_step_agreement/total_cases*100:.2f}%)")
print(f"  Partial step agreement:  {cases_partial_step_agreement}/{total_cases} ({cases_partial_step_agreement/total_cases*100:.2f}%)")
print(f"  Zero step agreement:     {cases_zero_step_agreement}/{total_cases} ({cases_zero_step_agreement/total_cases*100:.2f}%)")
print()
print("Per-Field Accuracy (out of total 193 expected steps):")
for f_name, f_cnt in field_counts.items():
    print(f"  {f_name:12}: {f_cnt}/{total_expected_steps} ({f_cnt/total_expected_steps*100:.2f}%)")
print(f"  Exact Step Tuples Matched (all 7 fields): {exact_step_tuples_matched}/{total_expected_steps} ({exact_step_tuples_matched/total_expected_steps*100:.2f}%)")
print()
print(f"Step Differences Summary:")
print(f"  Missing steps (expected > predicted): {missing_steps_count}")
print(f"  Extra steps (predicted > expected):   {extra_steps_count}")
print(f"  Positional mismatched steps:          {mismatched_steps_count}")
print(f"  Reordered steps (set match but misaligned): {reordered_steps_count}")
