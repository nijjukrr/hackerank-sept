import json
import csv
from pathlib import Path

# We can subclass or monkeypatch EvidenceLoader to use snap.get('captured_at')
import sys
sys.path.insert(0, 'code')

from models import DeletionRequestCase, Step, StepOperation, StepPhase, ResourceState, DeletionStatus
from evidence_loader import EvidenceLoader, ObservedResource, EvidenceFileMeta
from identity_resolver import IdentityResolver
from audit_engine import AuditEngine
from evaluation.main import evaluate_predictions

dataset_dir = Path("dataset")

# Let's inspect how _parse_json parses snapshots
orig_parse_json = EvidenceLoader._parse_json

def patched_parse_json(self, meta: EvidenceFileMeta):
    with meta.absolute_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. service_exports ...
    if "service_exports" in data:
        exports = data["service_exports"]
        if "account_service" in exports:
            for it in exports["account_service"].get("profile_lookups", []):
                rid = it.get("resource_id")
                st = "ABSENT" if it.get("status_code") == 404 or not it.get("profile") else "PRESENT"
                prof = it.get("profile") or {}
                self._record_obs(
                    ObservedResource(
                        system_id="account_service",
                        resource_id=rid,
                        data_category="USER_PROFILE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=prof.get("customer_reference"),
                        email=prof.get("email"),
                        phone=prof.get("phone"),
                        details=it,
                    )
                )

        if "analytics_platform" in exports:
            for it in exports["analytics_platform"].get("profiles", []):
                rid = it.get("resource_id")
                em = it.get("email")
                uref = it.get("customer_reference")
                is_anon = not (em or uref or it.get("phone") or it.get("email_hash"))
                st = "ANONYMIZED" if is_anon else "PRESENT"
                self._record_obs(
                    ObservedResource(
                        system_id="analytics_platform",
                        resource_id=rid,
                        data_category="ANALYTICS_PROFILE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=uref,
                        email=em,
                        phone=it.get("phone"),
                        has_exposed_pii=(not is_anon),
                        details=it,
                    )
                )

        if "support_platform" in exports:
            for it in exports["support_platform"].get("tickets", []):
                rid = it.get("resource_id")
                em = it.get("requester_email")
                uref = it.get("customer_reference")
                is_red = not (em or it.get("requester_name") or it.get("requester_phone"))
                st = "REDACTED" if is_red else "PRESENT"
                self._record_obs(
                    ObservedResource(
                        system_id="support_platform",
                        resource_id=rid,
                        data_category="SUPPORT_MESSAGE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=uref,
                        email=em,
                        phone=it.get("requester_phone"),
                        has_exposed_pii=(not is_red),
                        details=it,
                    )
                )

        if "security_service" in exports:
            for it in exports["security_service"].get("audit_records", []):
                rid = it.get("resource_id")
                sub = it.get("subject_reference")
                self._record_obs(
                    ObservedResource(
                        system_id="security_service",
                        resource_id=rid,
                        data_category="SECURITY_AUDIT_LOG",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=sub,
                        is_retained_policy=True,
                        details=it,
                    )
                )

        if "backup_service" in exports:
            for it in exports["backup_service"].get("restore_entries", []):
                rid = it.get("resource_id")
                en = it.get("restorable", False)
                self._record_obs(
                    ObservedResource(
                        system_id="backup_service",
                        resource_id=rid,
                        data_category="BACKUP_ARCHIVE",
                        state="ACTIVE" if en else "BLOCKED",
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=it.get("subject_reference"),
                        is_restore_risk=en,
                        details=it,
                    )
                )

        if "integration_service" in exports:
            for it in exports["integration_service"].get("connectors", []):
                rid = it.get("resource_id")
                st = it.get("sync_status", "ACTIVE")
                en = (st == "ACTIVE")
                self._record_obs(
                    ObservedResource(
                        system_id="integration_service",
                        resource_id=rid,
                        data_category="ACTIVE_DATA_FLOW",
                        state="ACTIVE" if en else "DISABLED",
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=it.get("customer_reference"),
                        is_active_flow=en,
                        details=it,
                    )
                )

        if "search_service" in exports:
            for it in exports["search_service"].get("index_queries", []):
                rid = it.get("resource_id")
                doc = it.get("document") or {}
                self._record_obs(
                    ObservedResource(
                        system_id="search_service",
                        resource_id=rid,
                        data_category="SEARCH_INDEX_ENTRY",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=it.get("observed_at") or meta.captured_at,
                        user_id=doc.get("customer_reference") or doc.get("user_id"),
                        email=doc.get("email"),
                        phone=doc.get("phone"),
                        details=it,
                    )
                )

    # 2. customer_data_snapshot_bundle_*.json
    if "snapshots" in data:
        for snap in data["snapshots"]:
            ds = snap.get("data_store", "")
            col = snap.get("collection", "")
            snap_time = snap.get("captured_at") or meta.captured_at
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
                            captured_at=snap_time,
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
                            captured_at=snap_time,
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
                            captured_at=snap_time,
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
                            captured_at=snap_time,
                            user_id=doc.get("customer_reference") or doc.get("user_id"),
                            email=doc.get("email"),
                            phone=doc.get("phone"),
                            details=rec,
                        )
                    )
                elif ds == "support_platform" or "support_conversations" in col:
                    em = rec.get("email")
                    uref = rec.get("customer_reference") or rec.get("subject_reference")
                    self._record_obs(
                        ObservedResource(
                            system_id="support_platform",
                            resource_id=rid,
                            data_category="SUPPORT_MESSAGE",
                            state="PRESENT",
                            evidence_id=meta.file_id,
                            captured_at=snap_time,
                            user_id=uref,
                            email=em,
                            has_exposed_pii=True,
                            details=rec,
                        )
                    )
                elif ds == "backup_service" or "backup_catalog" in col:
                    self._record_obs(
                        ObservedResource(
                            system_id="backup_service",
                            resource_id=rid,
                            data_category="BACKUP_ARCHIVE",
                            state="ACTIVE",
                            evidence_id=meta.file_id,
                            captured_at=snap_time,
                            user_id=rec.get("customer_reference") or rec.get("subject_reference"),
                            email=rec.get("customer_email"),
                            is_restore_risk=True,
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
                            captured_at=snap_time,
                            user_id=rec.get("customer_reference"),
                            email=rec.get("owner_email"),
                            details=rec,
                        )
                    )
                elif ds == "integration_service" or "connector" in col:
                    self._record_obs(
                        ObservedResource(
                            system_id="integration_service",
                            resource_id=rid,
                            data_category="ACTIVE_DATA_FLOW",
                            state="ACTIVE",
                            evidence_id=meta.file_id,
                            captured_at=snap_time,
                            user_id=rec.get("customer_reference"),
                            is_active_flow=True,
                            details=rec,
                        )
                    )

    # 3. Rest of json loading unchanged...
    # call orig for other types
    # Actually let's just run this and see

EvidenceLoader._parse_json = patched_parse_json

# Now build engine with patched loader
engine = AuditEngine(dataset_dir)

# Run on 32 sample cases
sample_reqs = []
with open(dataset_dir / "sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample_reqs.append(DeletionRequestCase(
            case_id=row["case_id"],
            email=row["email"],
            requested_at=row["requested_at"],
            reported_status=row["reported_status"],
            reported_at=row["reported_at"],
            audit_at=row["audit_at"],
            request_text=row["request_text"],
        ))

pred_rows = []
for req in sample_reqs:
    res = engine.audit_case(req)
    steps_json = json.dumps([s.to_dict() for s in res.steps])
    pred_rows.append({"case_id": res.case_id, "deletion_status": res.deletion_status, "steps_json": steps_json})

out_path = Path("scratch/simulated_sample_output.csv")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
    writer.writeheader()
    writer.writerows(pred_rows)

print("Running evaluation on simulated output:")
evaluate_predictions(out_path, dataset_dir / "sample_output.csv")
