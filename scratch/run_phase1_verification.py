import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path("code").resolve()))
from main import run_pipeline
from evaluation.main import evaluate_predictions, validate_csv

print("Running pipeline on sample...")
run_pipeline(
    input_path=Path("dataset/sample_deletion_requests.csv"),
    output_path=Path("sample_test_output.csv"),
    dataset_dir=Path("dataset"),
)

metrics = evaluate_predictions(Path("sample_test_output.csv"), Path("dataset/sample_output.csv"))
print("Sample Metrics:")
print(f"  Status Accuracy: {metrics['correct_status']}/{metrics['total_cases']} ({metrics['status_accuracy']*100:.2f}%)")
print(f"  Exact Full-Case Match: {metrics['exact_case_match']}/{metrics['total_cases']} ({metrics['exact_case_accuracy']*100:.2f}%)")
print(f"  Exact Step Sequence: {metrics['exact_step_seq_match']}/{metrics['total_cases']}")
print(f"  Matched 7-field Tuples: {metrics['matched_tuples']}/{metrics['total_expected_steps']}")
print(f"  Matched Field Cells: {metrics['matched_cells']}/{metrics['total_cells']}")

errors = validate_csv(Path("output.csv"), expected_count=518)
print(f"\nRoot output.csv validation errors: {len(errors)}")

# Check status distribution in root output.csv
with open("output.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    statuses = {}
    for r in reader:
        statuses[r["deletion_status"]] = statuses.get(r["deletion_status"], 0) + 1
print(f"Root output.csv status distribution: {statuses}")
