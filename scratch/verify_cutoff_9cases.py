import sys
from pathlib import Path
import csv

sys.path.insert(0, str(Path("code").resolve()))
sys.path.insert(0, str(Path("scratch").resolve()))
import test_complete_log_integration
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))
target_cases = ["case_263", "case_268", "case_270", "case_271", "case_371", "case_414", "case_416", "case_420", "case_522"]

manifest = {}
with open("dataset/evidence_files.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        manifest[r["file_id"]] = r["captured_at"]

all_valid = True
with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in target_cases:
            res = engine.audit_case(DeletionRequestCase(**r))
            print(f"=== {r['case_id']} (audit_at={r['audit_at']}) ===")
            for s in res.steps:
                if s.phase == "FINDING":
                    ev_time = manifest.get(s.evidence_id)
                    is_ok = ev_time <= r["audit_at"]
                    if not is_ok: all_valid = False
                    print(f"  Finding on {s.system_id}/{s.resource_id}: ev={s.evidence_id} (captured={ev_time}) <= audit_at: {is_ok}")

print("\nALL FINDINGS STRICTLY COMPLY WITH TEMPORAL CUTOFF:", all_valid)
