import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, "code")
from audit_engine import AuditEngine
from models import DeletionRequestCase, Step
from evaluation.main import evaluate_predictions, validate_csv

FINDING_OPS = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

REMEDIATION_OPS = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_OPS = {
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}

def official_sort_steps(steps: list[Step]) -> list[Step]:
    findings = [s for s in steps if s.phase == "FINDING"]
    remediations = [s for s in steps if s.phase == "REMEDIATION"]
    verifications = [s for s in steps if s.phase == "VERIFICATION"]

    findings.sort(key=lambda s: (FINDING_OPS.get(s.operation, 99), s.system_id, s.resource_id))
    remediations.sort(key=lambda s: (REMEDIATION_OPS.get(s.operation, 99), s.system_id, s.resource_id))
    verifications.sort(key=lambda s: (VERIFICATION_OPS.get(s.operation, 99), s.system_id, s.resource_id))

    all_sorted = findings + remediations + verifications
    for i, s in enumerate(all_sorted, 1):
        s.step_no = i
    return all_sorted

engine = AuditEngine(Path("dataset"))

# 1. Test on Sample
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

sample_truth = Path("dataset/sample_output.csv")
with open(sample_truth, "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

# Run baseline
baseline_exact = 0
for c in sample_cases:
    res = engine.audit_case(c)
    exp_status, exp_steps = expected[c.case_id]
    if res.deletion_status == exp_status and [s.to_dict() for s in res.steps] == exp_steps:
        baseline_exact += 1

# Run with official sorting
sorted_exact = 0
results_baseline = []
results_sorted = []
for c in sample_cases:
    res = engine.audit_case(c)
    results_baseline.append((res.case_id, res.deletion_status, json.dumps([s.to_dict() for s in res.steps])))
    
    sorted_steps = official_sort_steps(res.steps)
    results_sorted.append((res.case_id, res.deletion_status, json.dumps([s.to_dict() for s in sorted_steps])))
    
    exp_status, exp_steps = expected[c.case_id]
    if res.deletion_status == exp_status and [s.to_dict() for s in sorted_steps] == exp_steps:
        sorted_exact += 1

print(f"Sample exact matches: Baseline = {baseline_exact}/32, Official Ordered = {sorted_exact}/32")

# Write temporary files to evaluate full metrics
def write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "deletion_status", "steps_json"])
        w.writerows(rows)

write_csv("scratch/eval_baseline.csv", results_baseline)
write_csv("scratch/eval_sorted.csv", results_sorted)

print("\n--- BASELINE METRICS ---")
m_base = evaluate_predictions(Path("scratch/eval_baseline.csv"), sample_truth)

print("\n--- OFFICIAL ORDERED METRICS ---")
m_sort = evaluate_predictions(Path("scratch/eval_sorted.csv"), sample_truth)
