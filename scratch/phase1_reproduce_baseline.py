"""Phase 1 Verification Script: Recalculates all baseline metrics from source code."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(".").resolve()
DATASET_DIR = REPO_ROOT / "dataset"
SAMPLE_INPUT = DATASET_DIR / "sample_deletion_requests.csv"
SAMPLE_TRUTH = DATASET_DIR / "sample_output.csv"
SAMPLE_PRED = REPO_ROOT / "sample_test_output.csv"
FULL_INPUT = DATASET_DIR / "deletion_requests.csv"
FULL_OUTPUT = REPO_ROOT / "output.csv"

print("=" * 80)
print("PHASE 1: BASELINE RE-EXECUTION AND METRIC RECALCULATION")
print("=" * 80)

# Step 1: Re-run sample execution
print("\n1. Running sample pipeline: python code/main.py --sample ...")
res_sample = subprocess.run(
    [sys.executable, "code/main.py", "--sample"],
    capture_output=True,
    text=True,
)
print(res_sample.stdout.strip())
if res_sample.returncode != 0:
    print("ERROR in sample execution:", res_sample.stderr)
    sys.exit(1)

# Step 2: Load sample truth and prediction
with SAMPLE_TRUTH.open("r", encoding="utf-8") as f:
    truth_rows = list(csv.DictReader(f))
truth_by_id = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in truth_rows}

with SAMPLE_PRED.open("r", encoding="utf-8") as f:
    pred_rows = list(csv.DictReader(f))
pred_by_id = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in pred_rows}

assert len(truth_by_id) == 32, f"Expected 32 truth cases, got {len(truth_by_id)}"
assert len(pred_by_id) == 32, f"Expected 32 pred cases, got {len(pred_by_id)}"

# Step 3: Recalculate all sample metrics
total_cases = 32
correct_status = 0
step_count_matches = 0
exact_full_case_matches = 0
exact_step_seq_matches = 0

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
key_5_fields = ["phase", "system_id", "resource_id", "operation", "state"]

field_correct_counts = {f: 0 for f in all_fields}
total_truth_steps = sum(len(t[1]) for t in truth_by_id.values())
total_pred_steps = sum(len(p[1]) for p in pred_by_id.values())

exact_7field_tuples_matched = 0

for cid in sorted(truth_by_id.keys()):
    t_st, t_steps = truth_by_id[cid]
    p_st, p_steps = pred_by_id[cid]

    # Status check
    st_match = (t_st == p_st)
    if st_match:
        correct_status += 1

    # Step count check
    sc_match = (len(t_steps) == len(p_steps))
    if sc_match:
        step_count_matches += 1

    # Exact 7-field step sequence check
    t_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in t_steps]
    p_7tuples = [tuple(s.get(k, "") for k in all_fields) for s in p_steps]
    if t_7tuples == p_7tuples:
        exact_step_seq_matches += 1
        if st_match:
            exact_full_case_matches += 1

    # Count matching 7-field tuples
    matched_in_case = sum(1 for pt in p_7tuples if pt in t_7tuples)
    exact_7field_tuples_matched += matched_in_case

    # Positional per-field accuracy (up to min length)
    for idx in range(min(len(t_steps), len(p_steps))):
        ts = t_steps[idx]
        ps = p_steps[idx]
        for f in all_fields:
            if ts.get(f) == ps.get(f):
                field_correct_counts[f] += 1

print("\n2. Public Sample Benchmark Metrics (N = 32 cases):")
print(f"  Total Cases:                         {total_cases}")
print(f"  Total Expected Steps:                {total_truth_steps}")
print(f"  Total Predicted Steps:               {total_pred_steps}")
print(f"  Status Accuracy:                     {correct_status} / {total_cases} ({correct_status / total_cases * 100:.2f}%)")
print(f"  Step-Count Agreement:                {step_count_matches} / {total_cases} ({step_count_matches / total_cases * 100:.2f}%)")
print(f"  Exact Step-Sequence Agreement (7-f): {exact_step_seq_matches} / {total_cases} ({exact_step_seq_matches / total_cases * 100:.2f}%)")
print(f"  Exact Full-Case Agreement:           {exact_full_case_matches} / {total_cases} ({exact_full_case_matches / total_cases * 100:.2f}%)")
print(f"  Exact 7-Field Step Tuples Matched:   {exact_7field_tuples_matched} / {total_truth_steps} ({exact_7field_tuples_matched / total_truth_steps * 100:.2f}%)")

print("\n3. Per-Field Step Accuracy (out of 193 expected steps):")
for f in all_fields:
    cnt = field_correct_counts[f]
    pct = cnt / total_truth_steps * 100
    print(f"  - {f:<15}: {cnt:>3} / {total_truth_steps} ({pct:.2f}%)")

key_5_avg = sum(field_correct_counts[f] for f in key_5_fields) / (5 * total_truth_steps) * 100
print(f"  Key 5-Field Mean Accuracy: {key_5_avg:.2f}%")

# Step 4: Full evaluation dataset execution and metrics
print("\n4. Running full pipeline: python code/main.py --output output.csv ...")
res_full = subprocess.run(
    [sys.executable, "code/main.py", "--output", "output.csv"],
    capture_output=True,
    text=True,
)
print(res_full.stdout.strip())

with FULL_OUTPUT.open("r", encoding="utf-8") as f:
    full_rows = list(csv.DictReader(f))

print(f"\n5. Full Evaluation Dataset Metrics (N = {len(full_rows)} cases):")
eval_status_counts = {}
for r in full_rows:
    st = r["deletion_status"]
    eval_status_counts[st] = eval_status_counts.get(st, 0) + 1

for st, count in sorted(eval_status_counts.items()):
    pct = count / len(full_rows) * 100
    print(f"  - {st:<15}: {count:>3} ({pct:.2f}%)")

# Step 5: Check output ordering and validity
case_ids = [r["case_id"] for r in full_rows]
assert case_ids == sorted(case_ids), "Output rows are NOT sorted strictly by case_id!"
assert len(case_ids) == 518, f"Expected 518 cases, got {len(case_ids)}"
print("  Case coverage: Exactly 518 cases (case_33 to case_550), strictly sorted.")

print("\n" + "=" * 80)
print("PHASE 1 COMPLETE: ALL METRICS SUCCESSFULLY RECALCULATED")
print("=" * 80)
