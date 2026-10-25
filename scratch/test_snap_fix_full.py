import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json
from copy import deepcopy

from models import DeletionRequestCase
import evidence_loader
from evidence_loader import EvidenceLoader, EvidenceFileMeta, ObservedResource
from audit_engine import AuditEngine

# Monkeypatch EvidenceLoader._parse_json to use snap.get("captured_at")
orig_parse_json = EvidenceLoader._parse_json

def patched_parse_json(self, meta: EvidenceFileMeta) -> None:
    # Read data
    with meta.absolute_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # If not snapshots, run original
    if "snapshots" not in data:
        orig_parse_json(self, meta)
        return

    # Run original for any service_exports
    if "service_exports" in data:
        orig_parse_json(self, meta)
        return

    # Parse snapshots with internal captured_at
    for snap in data["snapshots"]:
        ds = snap.get("data_store", "")
        col = snap.get("collection", "")
        snap_cap = snap.get("captured_at") or meta.captured_at

        for rec in snap.get("records", []):
            rid = rec.get("resource_id")
            if ds == "account_service" or "profiles" in col:
                st = "PRESENT" if rec.get("account_status") == "ACTIVE" else "ABSENT"
                self._record_obs(
                    ObservedResource(
                        system_id="account_service",
                        resource_id=rid,
                        data_category="USER_PROFILE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("customer_reference") or rec.get("user_id"),
                        email=rec.get("email"),
                        phone=rec.get("phone"),
                        details=rec,
                    )
                )
            elif ds == "identity_service" or "deleted_customer_references" in col or "tombstone" in col:
                has_p = bool(rec.get("email") or rec.get("phone") or rec.get("email_hash") or rec.get("display_name") or rec.get("name"))
                st = "PRESENT" if has_p else "REDACTED"
                self._record_obs(
                    ObservedResource(
                        system_id="identity_service",
                        resource_id=rid,
                        data_category="ACCOUNT_TOMBSTONE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("subject_reference"),
                        email=rec.get("email"),
                        phone=rec.get("phone"),
                        is_tombstone=True,
                        has_exposed_pii=has_p,
                        details=rec,
                    )
                )
            elif ds == "security_service" or "security_audit" in col:
                self._record_obs(
                    ObservedResource(
                        system_id="security_service",
                        resource_id=rid,
                        data_category="SECURITY_AUDIT_LOG",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("subject_reference"),
                        is_retained_policy=True,
                        details=rec,
                    )
                )
            elif ds == "search_service" or "search_documents" in col:
                doc = rec.get("document", rec)
                self._record_obs(
                    ObservedResource(
                        system_id="search_service",
                        resource_id=rid,
                        data_category="SEARCH_INDEX_ENTRY",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=doc.get("customer_reference") or doc.get("user_id"),
                        email=doc.get("email"),
                        phone=doc.get("phone"),
                        details=rec,
                    )
                )
            elif ds == "analytics_platform" or "analytics_reports" in col:
                em = rec.get("email")
                uref = rec.get("user_id") or rec.get("customer_reference")
                is_anon = not (em or uref or rec.get("phone") or rec.get("email_hash"))
                st = "ANONYMIZED" if is_anon else "PRESENT"
                self._record_obs(
                    ObservedResource(
                        system_id="analytics_platform",
                        resource_id=rid,
                        data_category="ANALYTICS_PROFILE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=uref,
                        email=em,
                        phone=rec.get("phone"),
                        has_exposed_pii=(not is_anon),
                        details=rec,
                    )
                )
            elif ds in ("backup_service", "backup_restore_service") or "backup" in col:
                en = rec.get("restore_allowed", False)
                st = "ACTIVE" if en else "BLOCKED"
                self._record_obs(
                    ObservedResource(
                        system_id="backup_service",
                        resource_id=rid,
                        data_category="BACKUP_ARCHIVE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("customer_reference") or rec.get("user_id"),
                        email=rec.get("email"),
                        is_restore_risk=en,
                        details=rec,
                    )
                )
            elif ds == "integration_service" or "connector" in col:
                en = rec.get("enabled", False)
                st = "ACTIVE" if en else "DISABLED"
                self._record_obs(
                    ObservedResource(
                        system_id="integration_service",
                        resource_id=rid,
                        data_category="ACTIVE_DATA_FLOW",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("customer_reference") or rec.get("user_id"),
                        email=rec.get("customer_email") or rec.get("email"),
                        is_active_flow=en,
                        details=rec,
                    )
                )
            elif ds == "support_platform" or "support" in col or "ticket" in col:
                is_att = "attachment" in col
                cat = "SUPPORT_ATTACHMENT" if is_att else "SUPPORT_MESSAGE"
                has_p = bool(rec.get("customer_email") or rec.get("requester_email") or rec.get("requester_name") or rec.get("requester_phone") or rec.get("email") or rec.get("phone"))
                st = "PRESENT" if has_p else "REDACTED"
                self._record_obs(
                    ObservedResource(
                        system_id="support_platform",
                        resource_id=rid,
                        data_category=cat,
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("customer_reference") or rec.get("user_id"),
                        email=rec.get("customer_email") or rec.get("requester_email") or rec.get("email"),
                        has_exposed_pii=has_p,
                        details=rec,
                    )
                )
            elif ds == "export_service" or "export" in col:
                self._record_obs(
                    ObservedResource(
                        system_id="export_service",
                        resource_id=rid,
                        data_category="USER_EXPORT",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=snap_cap,
                        user_id=rec.get("customer_reference") or rec.get("user_id"),
                        email=rec.get("owner_email") or rec.get("email"),
                        details=rec,
                    )
                )

# Apply patch
EvidenceLoader._parse_json = patched_parse_json

# Now test on sample
engine = AuditEngine(Path("dataset"))
sample_cases = []
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        sample_cases.append(DeletionRequestCase(**r))
sample_cases.sort(key=lambda c: c.case_id)

with open("dataset/sample_output.csv", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

exact = 0
status_correct = 0
tuples_matched = 0
total_cells = 0
matched_cells = 0

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

for c in sample_cases:
    res = engine.audit_case(c)
    t_stat, t_steps = truth[c.case_id]
    p_steps = [s.to_dict() for s in res.steps]
    
    if res.deletion_status == t_stat:
        status_correct += 1
    if res.deletion_status == t_stat and p_steps == t_steps:
        exact += 1
        
    t_tuples = [tuple(s.get(k, "") for k in all_fields) for s in t_steps]
    p_tuples = [tuple(s.get(k, "") for k in all_fields) for s in p_steps]
    tuples_matched += sum(1 for pt in p_tuples if pt in t_tuples)
    
    for idx in range(min(len(t_steps), len(p_steps))):
        for f in all_fields:
            if t_steps[idx].get(f) == p_steps[idx].get(f):
                matched_cells += 1

print(f"Patched Sample Status Accuracy: {status_correct}/32")
print(f"Patched Sample Exact Agreement: {exact}/32")
print(f"Patched Matched Tuples: {tuples_matched}/193")
print(f"Patched Matched Cells: {matched_cells}/1351")

# Also test on 518 evaluation cases to see if any status regressions occur
eval_cases = []
with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        eval_cases.append(DeletionRequestCase(**r))
eval_cases.sort(key=lambda c: c.case_id)

eval_statuses = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}
for c in eval_cases:
    res = engine.audit_case(c)
    eval_statuses[res.deletion_status] += 1

print("Patched 518 Eval Statuses:", eval_statuses)
