import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, "code")
from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from models import DeletionRequestCase
from evaluation.main import evaluate_predictions, validate_csv

# Subclass EvidenceLoader with the proposed exact fix
class FixedEvidenceLoader(EvidenceLoader):
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

    def _parse_sql(self, meta) -> None:
        # Run original _parse_sql, then check if we need to refine SQL record parsing
        super()._parse_sql(meta)

# Run evaluation on public sample
engine = AuditEngine(Path("dataset"))
engine.evidence_loader = FixedEvidenceLoader(Path("dataset"))

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

sample_results = [engine.audit_case(c) for c in sample_cases]

sample_out_path = Path("scratch/sample_fixed_eval.csv")
with sample_out_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for r in sample_results:
        writer.writerow(r.to_csv_row())

print("=== PUBLIC SAMPLE EVALUATION ===")
m = evaluate_predictions(sample_out_path, Path("dataset/sample_output.csv"))

# Run on full 518 cases
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    eval_cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

eval_cases.sort(key=lambda c: c.case_id)
eval_results = [engine.audit_case(c) for c in eval_cases]

eval_out_path = Path("scratch/eval_518_fixed.csv")
with eval_out_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for r in eval_results:
        writer.writerow(r.to_csv_row())

# Validate CSV schema on 518
errors = validate_csv(eval_out_path, expected_count=518)
print(f"Validation errors on 518 cases: {len(errors)}")

# Compare against existing output.csv
existing = {}
with open("output.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        existing[row["case_id"]] = (row["deletion_status"], json.loads(row["steps_json"]))

changed_cases = []
for r in eval_results:
    cid = r.case_id
    old_status, old_steps = existing[cid]
    new_status = r.deletion_status
    new_steps = [s.to_dict() for s in r.steps]
    if old_status != new_status or old_steps != new_steps:
        changed_cases.append((cid, old_status, new_status, old_steps, new_steps))

print(f"\nTotal Changed Cases in Full 518 Dataset: {len(changed_cases)}")
for cid, old_s, new_s, old_st, new_st in changed_cases:
    print(f"\n--- Case {cid} ---")
    print(f"Status: {old_s} -> {new_s}")
    print(f"Old Step Count: {len(old_st)} | New Step Count: {len(new_st)}")
    print("Old steps:", old_st)
    print("New steps:", new_st)
