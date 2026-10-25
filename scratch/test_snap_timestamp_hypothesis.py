import json
import csv
from pathlib import Path
import sys

sys.path.insert(0, "code")
from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from models import DeletionRequestCase

# Let's inspect all snapshot bundle files and see what snapshots they contain
loader = EvidenceLoader(Path("dataset"))

# Check case_26
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = {r["case_id"]: DeletionRequestCase(**r) for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

print("Loaded cases and expected.")
