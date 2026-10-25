import csv
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path

repo_root = Path(".").resolve()
sys.path.insert(0, str(repo_root / "code"))

from main import run_pipeline
from evaluation.main import evaluate_predictions, validate_csv

print("=== PHASE 3A: PUBLIC SAMPLE BENCHMARK REPRODUCTION ===")
sample_req = repo_root / "dataset" / "sample_deletion_requests.csv"
sample_out = repo_root / "sample_test_output.csv"
sample_truth = repo_root / "dataset" / "sample_output.csv"

# Run pipeline on sample
ret_sample = run_pipeline(
    input_path=sample_req,
    output_path=sample_out,
    dataset_dir=repo_root / "dataset",
    quiet=True
)
assert ret_sample == 0, "Sample pipeline execution failed!"

metrics = evaluate_predictions(sample_out, sample_truth)
print("\n[Sample Metrics Summary]:")
print(f"  Deletion Status Accuracy:     {metrics['correct_status']}/{metrics['total_cases']} ({metrics['status_accuracy']*100:.2f}%)")
print(f"  Exact Full-Case Agreement:    {metrics['exact_case_match']}/{metrics['total_cases']} ({metrics['exact_case_accuracy']*100:.2f}%)")
print(f"  Exact Step-Sequence Match:    {metrics['exact_step_seq_match']}/{metrics['total_cases']} ({metrics['exact_step_seq_match']/metrics['total_cases']*100:.2f}%)")
print(f"  Step-Count Agreement:         {metrics['step_count_match']}/{metrics['total_cases']} ({metrics['step_count_match']/metrics['total_cases']*100:.2f}%)")
print(f"  Exact 7-Field Step Tuples:    {metrics['matched_tuples']}/{metrics['total_expected_steps']} ({metrics['tuple_accuracy']*100:.2f}%)")
print(f"  Positional 5-Key-Field Match: {metrics['matched_steps']}/{metrics['total_expected_steps']} ({metrics['step_accuracy']*100:.2f}%)")
print(f"  Individual Field Accuracy:    {metrics['matched_cells']}/{metrics['total_cells']} ({metrics['field_cell_accuracy']*100:.2f}%)")

assert metrics['correct_status'] == 32, "Status accuracy regressed!"
assert metrics['exact_case_match'] == 15, "Exact case match regressed!"
assert metrics['matched_tuples'] == 126, "7-field tuple match regressed!"
assert metrics['matched_cells'] == 1016, "Individual field cells regressed!"
print(">>> Phase 3A PASS: Public sample metrics 100% verified.")

print("\n=== PHASE 3B: FULL EVALUATION OUTPUT VALIDATION ===")
eval_req = repo_root / "dataset" / "deletion_requests.csv"
root_out = repo_root / "output.csv"

# Run production pipeline on full dataset
ret_full = run_pipeline(
    input_path=eval_req,
    output_path=root_out,
    dataset_dir=repo_root / "dataset",
    quiet=True
)
assert ret_full == 0, "Full pipeline execution failed!"

# 1. Row coverage & header
with root_out.open("r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    assert header == ["case_id", "deletion_status", "steps_json"], f"Invalid header: {header}"
    rows = list(reader)

assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"
case_ids = [r[0] for r in rows]
assert case_ids == sorted(case_ids), "Case IDs not strictly sorted!"
assert set(case_ids) == {f"case_{i}" for i in range(33, 551)}, f"Missing or unexpected case IDs in dataset!"
assert case_ids == sorted(case_ids), "Case IDs must be strictly sorted by case_id!"

# 2. Schema validator
errors = validate_csv(root_out, expected_count=518)
assert len(errors) == 0, f"Validator errors: {errors}"
print("Schema Validator: PASSED (0 errors)")

# 3. Cutoff compliance and empty evidence ID rules
requests_map = {}
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        requests_map[row["case_id"]] = datetime.fromisoformat(row["audit_at"].replace("Z", "+00:00"))

manifest = {}
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        manifest[row["file_id"]] = datetime.fromisoformat(row["captured_at"].replace("Z", "+00:00"))

activity = {}
with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        activity[row["activity_id"]] = datetime.fromisoformat(row["event_time"].replace("Z", "+00:00"))

audit_log = {}
with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        audit_log[row["audit_id"]] = datetime.fromisoformat(row["event_time"].replace("Z", "+00:00"))

cutoff_violations = 0
empty_evidence_violations = 0
invalid_citations = 0

status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

for r in rows:
    cid, status, steps_raw = r
    status_counts[status] += 1
    audit_at = requests_map[cid]
    steps = json.loads(steps_raw)
    
    if status == "NOT_APPLICABLE":
        assert len(steps) == 0, f"NOT_APPLICABLE case {cid} has non-empty steps!"
        continue

    for s in steps:
        phase = s["phase"]
        ev_id = s["evidence_id"]
        if phase == "REMEDIATION" or (phase == "VERIFICATION" and status == "INCOMPLETE"):
            if ev_id != "":
                empty_evidence_violations += 1
        elif ev_id:
            ev_time = manifest.get(ev_id) or activity.get(ev_id) or audit_log.get(ev_id)
            if not ev_time:
                invalid_citations += 1
            elif ev_time > audit_at:
                cutoff_violations += 1

assert cutoff_violations == 0, f"Cutoff violations: {cutoff_violations}"
assert empty_evidence_violations == 0, f"Empty evidence violations: {empty_evidence_violations}"
assert invalid_citations == 0, f"Invalid citations: {invalid_citations}"

print(f"Status Distribution: {status_counts}")
print("Cutoff Violations: 0")
print("Citation Violations: 0")
print("Empty Evidence Rule: 100% compliant")

# 4. Determinism check
root_hash1 = hashlib.sha256(root_out.read_bytes()).hexdigest()
ret_full2 = run_pipeline(eval_req, root_out, repo_root / "dataset", quiet=True)
root_hash2 = hashlib.sha256(root_out.read_bytes()).hexdigest()
assert root_hash1 == root_hash2, "Determinism check failed across independent runs!"
print(f"Determinism: 100% byte-for-byte identical across runs (SHA-256: {root_hash1})")
print(">>> Phase 3B PASS: Full evaluation output 100% verified.")
