import csv
import json
import sys
from pathlib import Path

repo_root = Path(".").resolve()
sys.path.insert(0, str(repo_root / "code"))

from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from models import DeletionRequestCase
from evaluation.main import evaluate_predictions

# Let's inspect where email_hash exists in raw evidence records
loader = EvidenceLoader(repo_root / "dataset")

# Check all observations and see how many raw details have email_hash
records_with_raw_hash = 0
for obs in loader.all_observations:
    d = obs.details
    if isinstance(d, dict):
        eh = d.get("email_hash") or d.get("hash")
        if eh and isinstance(eh, str) and len(eh) == 64:
            records_with_raw_hash += 1

print(f"Total observations in loader: {len(loader.all_observations)}")
print(f"Observations where details contains 64-char email_hash: {records_with_raw_hash}")
print(f"Observations where obs.email_hash is currently populated: {sum(1 for o in loader.all_observations if o.email_hash)}")
