import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, "code")
sys.path.insert(0, "scratch")
from audit_engine import AuditEngine
from pathlib import Path
from models import DeletionRequestCase
import csv
import json
from test_details_enrichment import EnrichedEvidenceLoader

cases = [DeletionRequestCase(**r) for r in csv.DictReader(open("dataset/deletion_requests.csv", encoding="utf-8"))]
cases_by_id = {c.case_id: c for c in cases}
eng = AuditEngine(Path("dataset"))
eng.evidence_loader = EnrichedEvidenceLoader(Path("dataset"))
existing = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(open("output.csv", encoding="utf-8"))}

case_ids = ["case_156", "case_312", "case_360", "case_474", "case_478", "case_480", "case_504"]

for cid in case_ids:
    c = cases_by_id[cid]
    u = eng.identity_resolver.resolve_email(c.email)
    old_status, old_steps = existing[cid]
    res = eng.audit_case(c)
    new_status = res.deletion_status
    new_steps = json.loads(res.to_csv_row()[2])
    
    print(f"\n==================== {cid} ====================")
    print(f"Email: {c.email} | User ID: {u.user_id if u else None}")
    print(f"Requested: {c.requested_at} | Reported: {c.reported_status} ({c.reported_at}) | Audit At: {c.audit_at}")
    print(f"Request text: {c.request_text[:120]}...")
    print(f"STATUS CHANGE: {old_status} -> {new_status}")
    print(f"Old Step Count: {len(old_steps)} | New Step Count: {len(new_steps)}")
    
    print("OLD STEPS:")
    for s in old_steps:
        print(f"  {s['step_no']}: [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")
        
    print("NEW STEPS:")
    for s in new_steps:
        print(f"  {s['step_no']}: [{s['phase']}] {s['system_id']}:{s['resource_id']} | op={s['operation']} | st={s['state']} | ev={s['evidence_id']}")
