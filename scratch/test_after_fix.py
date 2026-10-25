import sys
from pathlib import Path
import csv

sys.path.insert(0, str(Path("code").resolve()))
sys.path.insert(0, str(Path("scratch").resolve()))

import test_loader_fix
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))

cases = []
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cases.append(
            DeletionRequestCase(
                case_id=row["case_id"].strip(),
                email=row["email"].strip(),
                requested_at=row["requested_at"].strip(),
                reported_status=row["reported_status"].strip(),
                reported_at=row["reported_at"].strip(),
                audit_at=row["audit_at"].strip(),
                request_text=row["request_text"].strip(),
            )
        )

cases.sort(key=lambda c: c.case_id)

sample_out = Path("scratch/sample_after_fix.csv")
with sample_out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for case in cases:
        record = engine.audit_case(case)
        writer.writerow(record.to_csv_row())

print(f"Generated {sample_out} successfully.")

# Now evaluate against dataset/sample_output.csv
from evaluation.main import evaluate_predictions
metrics = evaluate_predictions(sample_out, Path("dataset/sample_output.csv"))
