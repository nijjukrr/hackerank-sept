import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "code")

from models import DeletionRequestCase, CaseAuditResult
from audit_engine import AuditEngine
from evaluation.main import evaluate_predictions, validate_csv

dataset_dir = Path("dataset")
engine = AuditEngine(dataset_dir)

# Run on 32 public sample cases
sample_reqs = []
with open(dataset_dir / "sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample_reqs.append(DeletionRequestCase(
            case_id=row["case_id"].strip(),
            email=row["email"].strip(),
            requested_at=row["requested_at"].strip(),
            reported_status=row["reported_status"].strip(),
            reported_at=row["reported_at"].strip(),
            audit_at=row["audit_at"].strip(),
            request_text=row["request_text"].strip(),
        ))

pred_rows = []
for req in sample_reqs:
    res = engine.audit_case(req)
    steps_json = json.dumps([s.to_dict() for s in res.steps])
    pred_rows.append({
        "case_id": res.case_id,
        "deletion_status": res.deletion_status,
        "steps_json": steps_json
    })

temp_pred_path = Path("scratch/current_sample_pred.csv")
with open(temp_pred_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
    writer.writeheader()
    writer.writerows(pred_rows)

print("Validation errors on sample predictions:", validate_csv(temp_pred_path, expected_count=32))
print("\n--- EVALUATION AGAINST dataset/sample_output.csv ---")
metrics = evaluate_predictions(temp_pred_path, dataset_dir / "sample_output.csv")
