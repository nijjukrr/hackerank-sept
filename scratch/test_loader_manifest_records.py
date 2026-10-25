import sys
from pathlib import Path
sys.path.insert(0, "code")

import json
import csv
from audit_engine import AuditEngine
from models import DeletionRequestCase
from evidence_loader import EvidenceLoader, ObservedResource

loader = EvidenceLoader(Path("dataset"))
initial_count = len(loader.all_observations)
print(f"Initial observations count: {initial_count}")

# Check observations for the empty complete cases
engine = AuditEngine(Path("dataset"))

with open("output.csv", "r", encoding="utf-8") as f:
    empty_complete_cids = [r["case_id"] for r in csv.DictReader(f) if r["deletion_status"] == "COMPLETE" and r["steps_json"] == "[]"]

print(f"Empty complete case IDs count: {len(empty_complete_cids)}")

# Test on case_133, case_134
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for req in csv.DictReader(f):
        if req["case_id"] in ("case_133", "case_134", "case_135", "case_140"):
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
                print(f"  step: {s.phase} {s.system_id} {s.resource_id} {s.operation} {s.state} ev={s.evidence_id}")
