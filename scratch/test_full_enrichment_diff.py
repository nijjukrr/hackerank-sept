import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, "code")
from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from models import DeletionRequestCase
from evaluation.main import validate_csv

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

with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    eval_cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

eval_cases.sort(key=lambda c: c.case_id)

new_results = [engine.audit_case(c) for c in eval_cases]

# Read existing output.csv
existing_results = {}
with open("output.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        existing_results[row["case_id"]] = (row["deletion_status"], json.loads(row["steps_json"]))

diffs = []
for res in new_results:
    cid = res.case_id
    old_stat, old_steps = existing_results[cid]
    new_stat = res.deletion_status
    new_steps = [s.to_dict() for s in res.steps]
    
    if old_stat != new_stat or old_steps != new_steps:
        diffs.append((cid, old_stat, new_stat, len(old_steps), len(new_steps), old_steps, new_steps))

print(f"Total cases changed across 518 evaluation requests: {len(diffs)}")
for cid, old_stat, new_stat, old_len, new_len, old_s, new_s in diffs:
    print(f"\n--- {cid} ---")
    print(f"Status: {old_stat} -> {new_stat}")
    print(f"Step count: {old_len} -> {new_len}")
    print("Old steps:", old_s)
    print("New steps:", new_s)
