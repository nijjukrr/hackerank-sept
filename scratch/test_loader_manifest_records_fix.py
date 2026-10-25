import sys
from pathlib import Path
sys.path.insert(0, "code")

import json
import csv
from models import DeletionRequestCase, StepPhase, StepOperation, ResourceState
from evidence_loader import EvidenceLoader, ObservedResource
from audit_engine import AuditEngine

loader = EvidenceLoader(Path("dataset"))
print(f"Before fix: {len(loader.all_observations)} observations")

# Now let's manually parse the unparsed files into loader
for meta in loader.files_by_id.values():
    if not meta.file_path.endswith(".json"):
        continue
    with meta.absolute_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            continue
    
    # 1. Manifest / records
    if "records" in data and ("connector" in meta.file_path or "manifest" in meta.file_path or "ledger" in meta.file_path):
        for rec in data["records"]:
            sys_id = rec.get("system")
            rec_type = rec.get("record_type")
            res_id = rec.get("resource_id")
            sub_ref = rec.get("subject_reference") or rec.get("customer_reference") or rec.get("user_id")
            result = rec.get("result", "")
            
            srv = sys_id or "account_service"
            cat = rec_type or "USER_PROFILE"
            if cat == "DATA_FLOW":
                cat = "ACTIVE_DATA_FLOW"
                srv = "integration_service"

            em = sub_ref if sub_ref and "@" in sub_ref else None
            uref = sub_ref if sub_ref and sub_ref.startswith("user_") else None
            eh = sub_ref if sub_ref and len(sub_ref) == 64 and all(c in "0123456789abcdefABCDEF" for c in sub_ref) else None

            st = "PRESENT"
            has_p = False
            is_r = False
            is_f = False
            is_ret = False

            if cat == "LEGAL_HOLD_RECORD":
                continue

            if cat == "SECURITY_AUDIT_LOG":
                st = "PRESENT"
                is_ret = True
            elif cat == "ACTIVE_DATA_FLOW":
                if result == "DISABLED":
                    st = "DISABLED"
                else:
                    st = "ACTIVE"
                    is_f = True
            elif cat == "BACKUP_ARCHIVE":
                if result == "BLOCKED":
                    st = "BLOCKED"
                else:
                    st = "ACTIVE"
                    is_r = True
            elif cat == "ANALYTICS_PROFILE":
                if result == "ANONYMIZED":
                    st = "ANONYMIZED"
                else:
                    st = "PRESENT"
                    has_p = True
            elif cat in ("SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT"):
                if result == "REDACTED":
                    st = "REDACTED"
                else:
                    st = "PRESENT"
                    has_p = True
            elif cat in ("USER_PROFILE", "SEARCH_INDEX_ENTRY", "USER_EXPORT"):
                if result == "NOT_FOUND":
                    st = "ABSENT"
                else:
                    st = "PRESENT"

            loader._record_obs(
                ObservedResource(
                    system_id=srv,
                    resource_id=res_id,
                    data_category=cat,
                    state=st,
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    user_id=uref,
                    email=em,
                    email_hash=eh,
                    has_exposed_pii=has_p,
                    is_retained_policy=is_ret,
                    is_active_flow=is_f,
                    is_restore_risk=is_r,
                    details=rec,
                )
            )

    # 2. customer_analytics_report_*.json
    if "customer_analytics" in meta.file_path and "records" in data:
        for prof in data.get("records", []):
            rid = prof.get("resource_id")
            em = prof.get("email")
            uref = prof.get("user_id") or prof.get("customer_reference")
            is_anon = not (em or uref or prof.get("phone") or prof.get("email_hash"))
            st = "ANONYMIZED" if is_anon else "PRESENT"
            loader._record_obs(
                ObservedResource(
                    system_id="analytics_platform",
                    resource_id=rid,
                    data_category="ANALYTICS_PROFILE",
                    state=st,
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    user_id=uref,
                    email=em,
                    phone=prof.get("phone"),
                    has_exposed_pii=(not is_anon),
                    details=prof,
                )
            )

print(f"After fix: {len(loader.all_observations)} observations")

# Now re-audit case_133, case_134, case_135, case_140
from identity_resolver import IdentityResolver
from intent_classifier import IntentClassifier

engine = AuditEngine(Path("dataset"))
engine.evidence_loader = loader

test_cids = ["case_133", "case_134", "case_135", "case_136", "case_137", "case_140", "case_141", "case_142"]

with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for req in csv.DictReader(f):
        if req["case_id"] in test_cids:
            case = DeletionRequestCase(
                case_id=req["case_id"],
                email=req["email"],
                requested_at=req["requested_at"],
                reported_status=req["reported_status"],
                reported_at=req["reported_at"],
                audit_at=req["audit_at"],
                request_text=req["request_text"],
            )
            res = engine.audit_case(case)
            print(f"\n{case.case_id}: status={res.deletion_status}, steps={len(res.steps)}")
            for s in res.steps:
                print(f"  step {s.step_no}: {s.phase} {s.system_id} {s.resource_id} {s.operation} {s.state} ev={s.evidence_id}")
