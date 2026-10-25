import sys
sys.path.insert(0, "code")
from audit_engine import AuditEngine
from pathlib import Path
from models import DeletionRequestCase
import csv

row = [r for r in csv.DictReader(open("dataset/deletion_requests.csv", encoding="utf-8")) if r["case_id"] == "case_95"][0]
c = DeletionRequestCase(**row)
eng = AuditEngine(Path("dataset"))
res = eng.audit_case(c)
print("case_95 baseline steps:")
for s in res.steps:
    print(f"  {s.step_no}: [{s.phase}] {s.system_id}:{s.resource_id} {s.operation}")
