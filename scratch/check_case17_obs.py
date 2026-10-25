import csv, json, re
from pathlib import Path
import sys
sys.path.insert(0, str(Path("code").resolve()))
from evidence_loader import EvidenceLoader, ObservedResource
from identity_resolver import IdentityResolver

dataset_dir = Path("dataset")
id_resolver = IdentityResolver(dataset_dir / "user_identities.csv", dataset_dir / "user_audit_log.csv")
ev = EvidenceLoader(dataset_dir)

# Add the parsed KV log lines
traces = {}
with open(dataset_dir / "evidence/logs/service_events_ap_south_20260915.log", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        kv = {k: v.strip("\"'") for k, v in dict(re.findall(r"([a-zA-Z0-9_]+)=([^\s]+)", line)).items()}
        tid = kv.get("trace_id")
        if tid: traces.setdefault(tid, {}).update(kv); m = traces[tid]
        else: m = kv
        if m.get("event", "").endswith("_started"): continue
        rid = m.get("resource_id")
        if not rid: continue
        srv = m.get("service") or "account_service"
        sk = m.get("subject_key")
        lk = m.get("lookup_key")
        ck = m.get("correlation_key", "").strip("\"'")
        em = sk if (sk and "@" in sk) else (lk if (lk and "@" in lk) else (ck if (ck and "@" in ck) else None))
        uref = sk if (sk and sk.startswith("user_")) else (lk if (lk and lk.startswith("user_")) else (ck if (ck and ck.startswith("user_")) else None))
        eh = ck if (ck and len(ck) == 64) else None
        st = "PRESENT"
        is_r = False
        if srv == "account_service" and (m.get("http_status") == "404" or m.get("rows") == "0"): st = "ABSENT"
        elif srv == "backup_service" and (m.get("restore_allowed") != "false" and m.get("deletion_block") != "true"): st = "ACTIVE"; is_r = True
        elif srv == "integration_service" and m.get("enabled") == "true": st = "ACTIVE"
        cat = "USER_PROFILE"
        if "security" in srv: cat = "SECURITY_AUDIT_LOG"
        elif "backup" in srv: cat = "BACKUP_ARCHIVE"
        elif "integration" in srv: cat = "ACTIVE_DATA_FLOW"
        elif "analytics" in srv: cat = "ANALYTICS_PROFILE"
        o = ObservedResource(srv, rid, cat, st, "evidence_01", "2026-09-15T11:59:39Z", user_id=uref, email=em, is_restore_risk=is_r)
        o.email_hash = eh
        ev._record_obs(o)

ident = id_resolver.resolve_email("leonie.g9352@outlook.com")
user_obs = [o for o in ev.all_observations if (o.email and o.email.lower() == "leonie.g9352@outlook.com") or (o.user_id == "user_17")]
obs_by_res = {}
for o in user_obs:
    obs_by_res[(o.system_id, o.resource_id)] = o

print("Observed resources for case_17:")
for k, v in obs_by_res.items():
    print(" ", k, "state:", v.state, "cat:", v.data_category, "risk:", v.is_restore_risk)
