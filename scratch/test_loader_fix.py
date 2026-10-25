import sys
from pathlib import Path

sys.path.insert(0, "code")
import re
from evidence_loader import EvidenceLoader, ObservedResource, EvidenceFileMeta

def new_parse_log(self, meta: EvidenceFileMeta) -> None:
    traces = {}
    with meta.absolute_path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 1. JSON formatted log lines
            if "{" in line and "}" in line:
                try:
                    import json
                    jstart = line.find("{")
                    jd = json.loads(line[jstart:])
                    tid = jd.get("trace_id") or jd.get("requestId")
                    if tid:
                        traces.setdefault(tid, {}).update(jd)
                        merged = traces[tid]
                    else:
                        merged = jd

                    ev = merged.get("event", "")
                    if ev.endswith("_started") or ev.endswith("_check_started"):
                        continue

                    rid = merged.get("resource_id")
                    if rid:
                        rid = str(rid).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                        srv = self._normalize_system_id(merged.get("service") or merged.get("logger") or merged.get("function") or "account_service")
                        uref = merged.get("subject_ref") or merged.get("subject_reference") or merged.get("customer_reference")
                        sk = merged.get("subject_key") or merged.get("lookup_key")
                        ck = str(merged.get("correlation_key", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()

                        em = None
                        if sk and "@" in sk: em = sk
                        elif ck and "@" in ck: em = ck
                        elif merged.get("email") and merged.get("email") != "null": em = merged.get("email")
                        elif merged.get("customer_email") and merged.get("customer_email") != "null": em = merged.get("customer_email")

                        if sk and sk.startswith("user_"): uref = sk
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
                        if str(merged.get("http_status")) == "404" or str(merged.get("rows")) == "0":
                            st = "ABSENT"
                        if merged.get("eligible") in (True, "true") and merged.get("deletion_block") in (False, "false"):
                            st = "ACTIVE"
                            is_r = True
                        if merged.get("enabled") in (True, "true"):
                            st = "ACTIVE"
                            is_f = True

                        cat = "USER_PROFILE"
                        if ev == "contact_lookup_completed": cat = "SECONDARY_IDENTIFIER"
                        elif "security" in srv: cat = "SECURITY_AUDIT_LOG"
                        elif "backup" in srv: cat = "BACKUP_ARCHIVE"
                        elif "integration" in srv: cat = "ACTIVE_DATA_FLOW"
                        elif "analytics" in srv: cat = "ANALYTICS_PROFILE"
                        elif "support" in srv: cat = "SUPPORT_MESSAGE"
                        elif "search" in srv: cat = "SEARCH_INDEX_ENTRY"

                        self._record_obs(
                            ObservedResource(
                                system_id=srv,
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
                except Exception:
                    pass
            else:
                # 2. Key-value formatted log lines
                raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', line)
                kv = {}
                for k, v in raw_pairs:
                    cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    kv[k] = cleaned_v

                tid = kv.get("trace_id") or kv.get("requestId")
                if tid:
                    traces.setdefault(tid, {}).update(kv)
                    merged = traces[tid]
                else:
                    merged = kv

                ev = merged.get("event", "")
                if ev.endswith("_started") or ev.endswith("_check_started"):
                    continue

                rid = merged.get("resource_id")
                if rid:
                    rid = str(rid).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    srv = self._normalize_system_id(merged.get("service") or merged.get("source_system") or merged.get("function") or merged.get("logger") or "account_service")
                    uref = merged.get("subject_ref") or merged.get("subject_reference") or merged.get("customer_reference")
                    sk = merged.get("subject_key")
                    lk = merged.get("lookup_key")
                    ck = merged.get("correlation_key", "").strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    mv = merged.get("matched_value", "").strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    req_em = merged.get("requester_email", "").strip("'\"\\").replace('\\"', '').replace('"', '').strip()

                    em = None
                    if sk and "@" in sk: em = sk
                    elif lk and "@" in lk: em = lk
                    elif ck and "@" in ck: em = ck
                    elif mv and "@" in mv: em = mv
                    elif req_em and "@" in req_em: em = req_em
                    elif merged.get("email") and merged.get("email") != "null": em = merged.get("email")
                    elif merged.get("customer_email") and merged.get("customer_email") != "null": em = merged.get("customer_email")

                    if sk and sk.startswith("user_"): uref = sk
                    elif lk and lk.startswith("user_"): uref = lk
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
                    if srv == "account_service":
                        if merged.get("http_status") == "404" or merged.get("rows") == "0":
                            st = "ABSENT"
                    elif srv == "search_service":
                        if merged.get("result") == "miss" or str(merged.get("rows")) == "0":
                            st = "ABSENT"
                        else:
                            st = "PRESENT"
                    elif srv == "analytics_platform":
                        if uref in (None, "null") and em in (None, "null") and not eh:
                            st = "ANONYMIZED"
                        else:
                            st = "PRESENT"
                            has_p = True
                    elif srv == "security_service":
                        st = "PRESENT"
                    elif srv == "support_platform":
                        if merged.get("marker_found") in (False, "false") or merged.get("source") == "legacy_contact_index":
                            st = "PRESENT"
                            has_p = False
                            cat = "SUPPORT_ATTACHMENT"
                        elif merged.get("requester_email") in (None, "null") and merged.get("phone") in (None, "null") and merged.get("requester_name") in (None, "null"):
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
                    if ev == "contact_lookup_completed":
                        cat = "SECONDARY_IDENTIFIER"
                        has_p = False
                    elif "security" in srv: cat = "SECURITY_AUDIT_LOG"
                    elif "backup" in srv: cat = "BACKUP_ARCHIVE"
                    elif "integration" in srv: cat = "ACTIVE_DATA_FLOW"
                    elif "analytics" in srv: cat = "ANALYTICS_PROFILE"
                    elif "support" in srv: cat = "SUPPORT_MESSAGE"
                    elif "search" in srv: cat = "SEARCH_INDEX_ENTRY"

                    self._record_obs(
                        ObservedResource(
                            system_id=srv,
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

EvidenceLoader._parse_log = new_parse_log
el = EvidenceLoader(Path("dataset"))
bad_rids = [o for o in el.all_observations if any(c in o.resource_id for c in ["'", '"', '\\'])]
bad_emails = [o for o in el.all_observations if o.email and any(c in o.email for c in ["'", '"', '\\'])]
bad_users = [o for o in el.all_observations if o.user_id and any(c in o.user_id for c in ["'", '"', '\\'])]
print(f"Total observations with fix: {len(el.all_observations)}")
print(f"Polluted resource_ids: {len(bad_rids)}")
print(f"Polluted emails:       {len(bad_emails)}")
print(f"Polluted users:        {len(bad_users)}")
