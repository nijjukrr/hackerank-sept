import csv
import json
import re
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path("code").resolve()))

from identity_resolver import IdentityResolver
from intent_classifier import IntentClassifier
from models import (
    CaseAuditResult,
    DeletionRequestCase,
    DeletionStatus,
    ResourceState,
    Step,
    StepOperation,
    StepPhase,
)
from evidence_loader import EvidenceLoader, ObservedResource

dataset_dir = Path("dataset")
id_resolver = IdentityResolver(dataset_dir / "user_identities.csv", dataset_dir / "user_audit_log.csv")
ev_loader = EvidenceLoader(dataset_dir)

# Now monkey-patch or augment the loader with the fixes to test
# 1. customer_export_jobs_20260914.json
ej_path = dataset_dir / "evidence/records/customer_export_jobs_20260914.json"
if ej_path.exists():
    with open(ej_path, encoding="utf-8") as f:
        ej_data = json.load(f)
    for rec in ej_data.get("records", []):
        ev_loader._record_obs(
            ObservedResource(
                system_id="export_service",
                resource_id=rec.get("resource_id"),
                data_category="USER_EXPORT",
                state="PRESENT",
                evidence_id="evidence_59",
                captured_at="2026-09-14T15:20:00Z",
                email=rec.get("owner_email"),
                details=rec,
            )
        )

# 2. KV log parsing with quote stripping and subject_key, subject_ref, correlation_key
log_path = dataset_dir / "evidence/logs/service_events_ap_south_20260915.log"
if log_path.exists():
    traces = {}
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            kv = dict(re.findall(r"([a-zA-Z0-9_]+)=([^\s]+)", line))
            kv = {k: v.strip("\"'") for k, v in kv.items()}
            tid = kv.get("trace_id")
            if tid:
                traces.setdefault(tid, {}).update(kv)
                merged = traces[tid]
            else:
                merged = kv

            ev = merged.get("event", "")
            if ev.endswith("_started"):
                continue

            rid = merged.get("resource_id")
            if rid:
                srv = merged.get("service") or merged.get("source_system") or "account_service"
                uref = merged.get("subject_ref") or merged.get("subject_reference") or merged.get("customer_reference")
                sk = merged.get("subject_key")
                lk = merged.get("lookup_key")
                ck = merged.get("correlation_key", "").strip("\"'")

                em = None
                if sk and "@" in sk: em = sk
                elif lk and "@" in lk: em = lk
                elif ck and "@" in ck: em = ck
                elif merged.get("email") and merged.get("email") != "null": em = merged.get("email")
                elif merged.get("customer_email") and merged.get("customer_email") != "null": em = merged.get("customer_email")

                if sk and sk.startswith("user_"): uref = sk
                elif lk and lk.startswith("user_"): uref = lk
                elif ck and ck.startswith("user_"): uref = ck
                if uref == "null": uref = None

                eh = None
                if ck and len(ck) == 64 and all(c in "0123456789abcdefABCDEF" for c in ck):
                    eh = ck
                elif merged.get("email_hash") and merged.get("email_hash") != "null":
                    eh = merged.get("email_hash")

                st = "PRESENT"
                has_p = False
                is_r = False
                is_f = False

                if srv == "account_service":
                    if merged.get("http_status") == "404" or merged.get("rows") == "0":
                        st = "ABSENT"
                elif srv == "analytics_platform":
                    if (uref in (None, "null") and em in (None, "null") and not eh):
                        st = "ANONYMIZED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif srv == "security_service":
                    st = "PRESENT"
                elif srv == "support_platform":
                    if merged.get("requester_email") in (None, "null") and merged.get("phone") in (None, "null") and merged.get("requester_name") in (None, "null"):
                        st = "REDACTED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif srv == "backup_service":
                    if merged.get("restore_allowed") == "false" or merged.get("deletion_block") == "true":
                        st = "BLOCKED"
                    else:
                        st = "ACTIVE"
                        is_r = True
                elif srv == "integration_service":
                    if merged.get("enabled") == "false" or merged.get("last_delivery_status") == "stopped":
                        st = "DISABLED"
                    else:
                        st = "ACTIVE"
                        is_f = True

                cat = "USER_PROFILE"
                if "security" in srv: cat = "SECURITY_AUDIT_LOG"
                elif "backup" in srv: cat = "BACKUP_ARCHIVE"
                elif "integration" in srv: cat = "ACTIVE_DATA_FLOW"
                elif "analytics" in srv: cat = "ANALYTICS_PROFILE"
                elif "support" in srv: cat = "SUPPORT_MESSAGE"
                elif "search" in srv: cat = "SEARCH_INDEX_ENTRY"

                obs = ObservedResource(
                    system_id=srv,
                    resource_id=rid,
                    data_category=cat,
                    state=st,
                    evidence_id="evidence_01",
                    captured_at="2026-09-15T11:59:39Z",
                    user_id=uref,
                    email=em,
                    has_exposed_pii=has_p,
                    is_restore_risk=is_r,
                    is_active_flow=is_f,
                    details=merged,
                )
                obs.email_hash = eh
                ev_loader._record_obs(obs)

# Now test against all 32 samples
with open(dataset_dir / "sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_requests = list(csv.DictReader(f))

with open(dataset_dir / "sample_output.csv", encoding="utf-8") as f:
    sample_outputs = {r["case_id"]: r for r in csv.DictReader(f)}

correct_status = 0
correct_steps = 0

for req_dict in sample_requests:
    cid = req_dict["case_id"]
    truth = sample_outputs[cid]
    truth_status = truth["deletion_status"]
    truth_steps = json.loads(truth["steps_json"])
    
    if not IntentClassifier.authorizes_deletion(req_dict["request_text"]):
        pred_status = "NOT_APPLICABLE"
        pred_steps = []
    else:
        em = req_dict["email"].lower().strip()
        identity = id_resolver.resolve_email(em)
        uid = identity.user_id if identity else None
        all_emails = set(identity.all_emails) if identity else {em}
        all_hashes = set(identity.all_hashes) if identity else set()
        audit_at = req_dict["audit_at"]
        
        user_obs = [
            o for o in ev_loader.all_observations
            if o.captured_at <= audit_at
            and o.data_category != "LEGAL_HOLD_RECORD"
            and (
                (uid and o.user_id == uid) or
                (o.email and o.email.lower().strip() in all_emails) or
                (getattr(o, "email_hash", None) and getattr(o, "email_hash", None) in all_hashes)
            )
        ]
        
        # Check if user has numbered account
        if uid and uid.startswith("user_") and len(uid) <= 7:
            try:
                num = int(uid.split("_")[1])
                if 1 <= num <= 10:
                    acc_num = f"account_{num:03d}"
                    acc_obs = [o for o in ev_loader.all_observations if o.resource_id == acc_num and o.captured_at <= audit_at]
                    if acc_obs:
                        user_obs.append(acc_obs[-1])
                    else:
                        user_obs.append(
                            ObservedResource(
                                system_id="account_service",
                                resource_id=acc_num,
                                data_category="USER_PROFILE",
                                state="ABSENT",
                                evidence_id="evidence_54",
                                captured_at=audit_at,
                                user_id=uid,
                                email=em,
                            )
                        )
            except Exception:
                pass
                
        obs_by_res = {}
        for o in user_obs:
            key = (o.system_id, o.resource_id)
            if key not in obs_by_res or o.captured_at > obs_by_res[key].captured_at:
                obs_by_res[key] = o
                
        findings = []
        remediations = []
        verifications = []
        
        for (sys_id, res_id), obs in sorted(obs_by_res.items()):
            cat = obs.data_category
            
            if obs.is_active_flow or (cat == "ACTIVE_DATA_FLOW" and obs.state == "ACTIVE"):
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "DISABLE_DATA_FLOW", "DISABLED", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", ""))
            
            elif obs.is_restore_risk or (cat == "BACKUP_ARCHIVE" and obs.state == "ACTIVE"):
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_RESTORE_RISK", "ACTIVE", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "BLOCK_RESTORE", "BLOCKED", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RESTORE_BLOCKED", "BLOCKED", ""))
                
            elif obs.is_tombstone and (obs.has_exposed_pii or obs.state == "PRESENT"):
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_EXPOSED_PII", "PRESENT", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "REDACT_RECORD", "REDACTED", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", ""))
                
            elif cat in ("SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT") and obs.has_exposed_pii:
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_EXPOSED_PII", "PRESENT", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "REDACT_RECORD", "REDACTED", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", ""))
                
            elif cat == "ANALYTICS_PROFILE" and obs.has_exposed_pii:
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_EXPOSED_PII", "PRESENT", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "ANONYMIZE_RECORD", "ANONYMIZED", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", ""))
                
            elif obs.state == "PRESENT" and not obs.is_retained_policy and cat != "SECURITY_AUDIT_LOG":
                findings.append(Step(0, "FINDING", sys_id, res_id, "REPORT_REMAINING_RECORD", "PRESENT", obs.evidence_id))
                remediations.append(Step(0, "REMEDIATION", sys_id, res_id, "DELETE_RECORD", "ABSENT", ""))
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", ""))
                
            elif cat == "SECURITY_AUDIT_LOG" or obs.is_retained_policy:
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_PRESENT", "PRESENT", obs.evidence_id))
            elif obs.state == "ABSENT":
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", obs.evidence_id))
            elif obs.state == "ANONYMIZED":
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", obs.evidence_id))
            elif obs.state == "REDACTED":
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", obs.evidence_id))
            elif obs.state == "DISABLED":
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", obs.evidence_id))
            elif obs.state == "BLOCKED":
                verifications.append(Step(0, "VERIFICATION", sys_id, res_id, "VERIFY_RESTORE_BLOCKED", "BLOCKED", obs.evidence_id))
                
        if findings:
            pred_status = "INCOMPLETE"
            future_v = [
                Step(0, "VERIFICATION", v.system_id, v.resource_id, v.operation, v.state, "")
                for v in verifications
            ]
            pred_steps = findings + remediations + future_v
        else:
            pred_status = "COMPLETE"
            pred_steps = verifications
            
    is_st_match = (pred_status == truth_status)
    if is_st_match: correct_status += 1
    
    print(f"{cid}: pred={pred_status} (truth: {truth_status}) -> {'PASS' if is_st_match else 'FAIL'} | steps: pred={len(pred_steps)}, truth={len(truth_steps)}")

print(f"\nFinal status accuracy: {correct_status}/32 ({correct_status/32*100:.1f}%)")
