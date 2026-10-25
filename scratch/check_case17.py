import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path("code").resolve()))
from identity_resolver import IdentityResolver
from evidence_loader import EvidenceLoader, ObservedResource

dataset_dir = Path("dataset")
id_resolver = IdentityResolver(dataset_dir / "user_identities.csv", dataset_dir / "user_audit_log.csv")

with open(dataset_dir / "sample_output.csv", encoding="utf-8") as f:
    sample_outputs = {r["case_id"]: r for r in csv.DictReader(f)}

truth = json.loads(sample_outputs["case_17"]["steps_json"])
print("TRUTH STEPS:")
for s in truth:
    print(" ", s)
