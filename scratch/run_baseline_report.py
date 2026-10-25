import csv
import json
import sys
from pathlib import Path

repo_root = Path(".").resolve()
sys.path.insert(0, str(repo_root / "code"))

from main import run_pipeline
from evaluation.main import evaluate_predictions

sample_req = repo_root / "dataset" / "sample_deletion_requests.csv"
sample_out = repo_root / "scratch" / "baseline_sample_output.csv"
sample_truth = repo_root / "dataset" / "sample_output.csv"

# Run pipeline
run_pipeline(sample_req, sample_out, repo_root / "dataset", quiet=True)

metrics = evaluate_predictions(sample_out, sample_truth)

# Generate detailed case-by-case step inventory
with sample_out.open("r", encoding="utf-8") as f:
    preds = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with sample_truth.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

print("\n=== COMPLETE CASE-BY-CASE STEP INVENTORY (ALL 32 CASES) ===")
print(f"{'Case ID':<10} {'Expected Steps':<16} {'Predicted Steps':<16} {'Match?':<8}")
print("-" * 52)
for cid in sorted(truth.keys()):
    t_len = len(truth[cid])
    p_len = len(preds.get(cid, []))
    matched = "YES" if t_len == p_len else "NO"
    print(f"{cid:<10} {t_len:<16} {p_len:<16} {matched:<8}")

# Save machine-readable baseline report
baseline_report = {
    "metrics": {
        "step_count_agreement": f"{metrics['step_count_match']}/{metrics['total_cases']} ({metrics['step_count_match']/metrics['total_cases']*100:.2f}%)",
        "exact_7_tuples": f"{metrics['matched_tuples']}/{metrics['total_expected_steps']} ({metrics['tuple_accuracy']*100:.2f}%)",
        "positional_5_key": f"{metrics['matched_steps']}/{metrics['total_expected_steps']} ({metrics['step_accuracy']*100:.2f}%)",
        "field_cell_accuracy": f"{metrics['matched_cells']}/{metrics['total_cells']} ({metrics['field_cell_accuracy']*100:.2f}%)",
        "exact_full_case": f"{metrics['exact_case_match']}/{metrics['total_cases']} ({metrics['exact_case_accuracy']*100:.2f}%)",
        "status_accuracy": f"{metrics['correct_status']}/{metrics['total_cases']} ({metrics['status_accuracy']*100:.2f}%)"
    },
    "case_step_counts": {cid: {"expected": len(truth[cid]), "predicted": len(preds.get(cid, []))} for cid in sorted(truth.keys())}
}

Path("scratch/baseline_evaluation_report.json").write_text(json.dumps(baseline_report, indent=2), encoding="utf-8")
print("\nSaved scratch/baseline_evaluation_report.json successfully.")
