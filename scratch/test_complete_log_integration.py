import sys
from pathlib import Path
import re
import json
import csv

sys.path.insert(0, str(Path("code").resolve()))
from evidence_loader import EvidenceLoader, ObservedResource, EvidenceFileMeta

def parse_log_line(line: str):
    line = line.strip()
    if not line:
        return None, None, None, {}

    # 1. JSON
    if line.startswith("{") or ('"severity"' in line and "{" in line):
        try:
            jstart = line.find("{")
            jd = json.loads(line[jstart:])
            srv = jd.get("service") or jd.get("logger") or jd.get("function")
            tid = jd.get("trace_id") or jd.get("requestId")
            ev = jd.get("event")
            return srv, tid, ev, jd
        except Exception:
            pass

    # 2. Pipe format: timestamp | level | service | trace_id | event | kv...
    if "|" in line:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6:
            srv = parts[2]
            tid = parts[3]
            ev = parts[4]
            rest = " | ".join(parts[5:])
            raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
            kv = {}
            for k, v in raw_pairs:
                cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                kv[k] = cleaned_v
            return srv, tid, ev, kv

    # 3. Bracket format: ts [level] [service] [trace_id] event: kv...
    m_bracket = re.match(r"^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+([^:]+):\s*(.*)$", line)
    if m_bracket:
        srv = m_bracket.group(3)
        tid = m_bracket.group(4)
        ev = m_bracket.group(5)
        rest = m_bracket.group(6)
        raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
        kv = {}
        for k, v in raw_pairs:
            cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
            kv[k] = cleaned_v
        return srv, tid, ev, kv

    # 4. Syslog RFC 5424 format: ts <pri> node service trace_id - - kv...
    m_syslog = re.match(r"^(\S+)\s+<[^>]+>\S*\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-\s+(.*)$", line)
    if m_syslog:
        srv = m_syslog.group(2)
        tid = m_syslog.group(3)
        rest = m_syslog.group(4)
        raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
        kv = {}
        for k, v in raw_pairs:
            cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
            kv[k] = cleaned_v
        ev = kv.get("event")
        return srv, tid, ev, kv

    # 5. Generic Key-Value format (including Cloud Runtime logs)
    raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', line)
    kv = {}
    for k, v in raw_pairs:
        cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
        kv[k] = cleaned_v
    srv = kv.get("service") or kv.get("source_system") or kv.get("function") or kv.get("logger")
    tid = kv.get("trace_id") or kv.get("requestId")
    ev = kv.get("event")
    return srv, tid, ev, kv

def unified_parse_log(self, meta: EvidenceFileMeta) -> None:
    traces = {}
    with meta.absolute_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            srv, tid, ev, kv = parse_log_line(line)
            if not kv and not srv:
                continue

            if tid:
                traces.setdefault(tid, {}).update(kv)
                if srv: traces[tid]["_service"] = srv
                if ev: traces[tid]["_event"] = ev
                merged = traces[tid]
                srv = merged.get("_service") or srv
                ev = merged.get("_event") or ev
            else:
                merged = kv

            ev_str = str(ev or merged.get("event") or "")
            if ev_str.endswith("_started") or ev_str.endswith("_check_started"):
                continue

            rid = merged.get("resource_id")
            if rid:
                rid = str(rid).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                srv_resolved = self._normalize_system_id(
                    srv or merged.get("service") or merged.get("source_system") or merged.get("function") or merged.get("logger") or "account_service"
                )
                uref = merged.get("subject_ref") or merged.get("subject_reference") or merged.get("customer_reference")
                sk = merged.get("subject_key") or merged.get("lookup_key")
                ck = str(merged.get("correlation_key", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                mv = str(merged.get("matched_value", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                req_em = str(merged.get("requester_email", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()

                em = None
                if sk and "@" in sk: em = sk
                elif ck and "@" in ck: em = ck
                elif mv and "@" in mv: em = mv
                elif req_em and "@" in req_em: em = req_em
                elif merged.get("email") and merged.get("email") != "null": em = merged.get("email")
                elif merged.get("customer_email") and merged.get("customer_email") != "null": em = merged.get("customer_email")

                if sk and sk.startswith("user_"): uref = sk
                elif ck and ck.startswith("user_"): uref = ck
                elif mv and mv.startswith("user_"): uref = mv
                if uref == "null": uref = None

                eh = None
                if ck and len(ck) == 64 and all(c in "0123456789abcdefABCDEF" for c in ck):
                    eh = ck
                elif mv and len(mv) == 64 and all(c in "0123456789abcdefABCDEF" for c in mv):
                    eh = mv
                elif merged.get("email_hash") and merged.get("email_hash") != "null":
                    eh = merged.get("email_hash")

                st = "PRESENT"
                has_p = False
                is_r = False
                is_f = False

                if srv_resolved == "account_service":
                    if str(merged.get("http_status")) == "404" or str(merged.get("rows")) == "0":
                        st = "ABSENT"
                elif srv_resolved == "search_service":
                    if merged.get("result") == "miss" or str(merged.get("rows")) == "0":
                        st = "ABSENT"
                    else:
                        st = "PRESENT"
                elif srv_resolved == "analytics_platform":
                    if uref in (None, "null") and em in (None, "null") and not eh:
                        st = "ANONYMIZED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif srv_resolved == "security_service":
                    st = "PRESENT"
                elif srv_resolved == "support_platform":
                    if merged.get("marker_found") in (False, "false") or merged.get("source") == "legacy_contact_index":
                        st = "PRESENT"
                        has_p = False
                        cat = "SUPPORT_ATTACHMENT"
                    elif ev_str == "message_pii_scan" or (merged.get("detector") == "direct_identifier" and mv):
                        st = "PRESENT"
                        has_p = True
                        cat = "SUPPORT_MESSAGE"
                    elif merged.get("requester_email") in (None, "null") and merged.get("phone") in (None, "null") and merged.get("requester_name") in (None, "null"):
                        st = "REDACTED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif srv_resolved == "backup_service":
                    if merged.get("restore_allowed") in ("false", False) or merged.get("deletion_block") in ("true", True):
                        st = "BLOCKED"
                    else:
                        st = "ACTIVE"
                        is_r = True
                elif srv_resolved == "integration_service":
                    if merged.get("enabled") in ("false", False) or merged.get("last_delivery_status") == "stopped":
                        st = "DISABLED"
                    else:
                        st = "ACTIVE"
                        is_f = True

                cat = "USER_PROFILE"
                if ev_str == "contact_lookup_completed": cat = "SECONDARY_IDENTIFIER"
                elif "security" in srv_resolved: cat = "SECURITY_AUDIT_LOG"
                elif "backup" in srv_resolved: cat = "BACKUP_ARCHIVE"
                elif "integration" in srv_resolved: cat = "ACTIVE_DATA_FLOW"
                elif "analytics" in srv_resolved: cat = "ANALYTICS_PROFILE"
                elif "support" in srv_resolved:
                    if merged.get("marker_found") in (False, "false") or merged.get("source") == "legacy_contact_index":
                        cat = "SUPPORT_ATTACHMENT"
                    else:
                        cat = "SUPPORT_MESSAGE"
                elif "search" in srv_resolved: cat = "SEARCH_INDEX_ENTRY"

                self._record_obs(
                    ObservedResource(
                        system_id=srv_resolved,
                        resource_id=rid,
                        data_category=cat,
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=uref,
                        email=em,
                        email_hash=eh,
                        has_exposed_pii=has_p,
                        is_restore_risk=is_r,
                        is_active_flow=is_f,
                        details=merged,
                    )
                )

EvidenceLoader._parse_log = unified_parse_log

el = EvidenceLoader(Path("dataset"))
bad_rids = [o for o in el.all_observations if any(c in o.resource_id for c in ["'", '"', '\\'])]
bad_emails = [o for o in el.all_observations if o.email and any(c in o.email for c in ["'", '"', '\\'])]
bad_users = [o for o in el.all_observations if o.user_id and any(c in o.user_id for c in ["'", '"', '\\'])]

print(f"Total observations: {len(el.all_observations)}")
print(f"Polluted resource_ids: {len(bad_rids)}")
print(f"Polluted emails:       {len(bad_emails)}")
print(f"Polluted users:        {len(bad_users)}")

# Now run sample test
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))
sample_cases = []
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample_cases.append(
            DeletionRequestCase(
                case_id=row["case_id"].strip(),
                email=row["email"].strip(),
                requested_at=row["requested_at"].strip(),
                reported_status=row["reported_status"].strip(),
                reported_at=row["reported_at"].strip(),
                audit_at=row["audit_at"].strip(),
                request_text=row["request_text"].strip(),
            )
        )
sample_cases.sort(key=lambda c: c.case_id)

sample_out = Path("scratch/sample_unified_out.csv")
with sample_out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["case_id", "deletion_status", "steps_json"])
    for case in sample_cases:
        writer.writerow(engine.audit_case(case).to_csv_row())

from evaluation.main import evaluate_predictions
print("=== Sample Evaluation Results ===")
metrics = evaluate_predictions(sample_out, Path("dataset/sample_output.csv"))
