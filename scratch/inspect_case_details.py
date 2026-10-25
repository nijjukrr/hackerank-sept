import sys
from pathlib import Path
import csv
import json

sys.path.insert(0, str(Path("code").resolve()))
sys.path.insert(0, str(Path("scratch").resolve()))

import test_loader_fix
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))

target_cases = ["case_263", "case_271", "case_522"]
cases = []
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["case_id"] in target_cases:
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

for case in cases:
    print(f"=== {case.case_id} ===")
    print(f"Email: {case.email}")
    print(f"Requested: {case.requested_at}")
    print(f"Reported: {case.reported_status} at {case.reported_at}")
    print(f"Audit Cutoff: {case.audit_at}")
    print(f"Request: {case.request_text[:100]}...")

    res = engine.audit_case(case)
    print(f"New Decision: {res.deletion_status}")
    print("Steps:")
    for s in res.steps:
        print(f"  Step {s.step_no}: phase={s.phase}, system={s.system_id}, resource={s.resource_id}, op={s.operation}, state={s.state}, ev={s.evidence_id}")
