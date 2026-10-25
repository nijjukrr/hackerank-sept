import sys
from pathlib import Path
sys.path.insert(0, "code")

import csv
import json
from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from models import DeletionRequestCase
from evaluation.main import evaluate_predictions

# Subclass EvidenceLoader to auto-enrich obs from details
class EnrichedEvidenceLoader(EvidenceLoader):
    def _record_obs(self, obs: ObservedResource) -> None:
        if isinstance(obs.details, dict):
            d = obs.details
            # 1. email_hash
            if not obs.email_hash:
                eh = d.get("email_hash") or d.get("hash")
                if eh and isinstance(eh, str) and len(eh) == 64 and all(c in "0123456789abcdefABCDEF" for c in eh):
                    obs.email_hash = eh.lower().strip()
            
            # 2. user_id
            if not obs.user_id:
                uid = d.get("customer_reference") or d.get("subject_reference") or d.get("user_id")
                if uid and isinstance(uid, str) and uid.startswith("user_"):
                    obs.user_id = uid.strip()
            
            # 3. email
            if not obs.email:
                em = d.get("email") or d.get("requester_email") or d.get("customer_email") or d.get("owner_email")
                if em and isinstance(em, str) and "@" in em:
                    obs.email = em.lower().strip()

        super()._record_obs(obs)

engine = AuditEngine(Path("dataset"))
engine.evidence_loader = EnrichedEvidenceLoader(Path("dataset"))

# Audit sample cases
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

results = [engine.audit_case(c) for c in sample_cases]

# Write to temp file and evaluate
out_path = Path("scratch/test_enrichment_output.csv")
with out_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for r in results:
        writer.writerow(r.to_csv_row())

truth_path = Path("dataset/sample_output.csv")
metrics = evaluate_predictions(out_path, truth_path)
