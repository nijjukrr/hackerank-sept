import sys
from pathlib import Path
sys.path.insert(0, "code")

import json
import csv
from models import DeletionRequestCase
from evidence_loader import EvidenceLoader, ObservedResource
from audit_engine import AuditEngine

loader = EvidenceLoader(Path("dataset"))

# Check case_61
engine = AuditEngine(Path("dataset"))
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for req in csv.DictReader(f):
        if req["case_id"] == "case_61":
            case = DeletionRequestCase(
                case_id=req["case_id"],
                email=req["email"],
                requested_at=req["requested_at"],
                reported_status=req["reported_status"],
                reported_at=req["reported_at"],
                audit_at=req["audit_at"],
                request_text=req["request_text"],
            )
            res = engine.audit_case(case)
            print(f"{case.case_id}: status={res.deletion_status}, steps={len(res.steps)}")
            for s in res.steps:
                print(f"  step {s.step_no}: {s.phase} {s.system_id} {s.resource_id} {s.operation} {s.state} ev={s.evidence_id}")
