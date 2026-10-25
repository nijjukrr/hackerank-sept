import sys
from pathlib import Path
import csv
import json

sys.path.insert(0, str(Path("code").resolve()))
sys.stdout.reconfigure(encoding="utf-8")
from audit_engine import AuditEngine
from models import DeletionRequestCase
from identity_resolver import IdentityResolver

engine = AuditEngine(Path("dataset"))
resolver = engine.identity_resolver

target_cases = ["case_263", "case_268", "case_270", "case_271", "case_371", "case_414", "case_416", "case_420", "case_522"]

# Load deletion requests
requests_by_id = {}
with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] in target_cases:
            requests_by_id[r["case_id"]] = r

# Load evidence manifest
manifest = {}
with open("dataset/evidence_files.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        manifest[r["file_id"]] = r

# Load deletion rules
deletion_rules = {}
with open("dataset/deletion_rules.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        deletion_rules[r["data_category"]] = r

print("=" * 80)
print("PHASE 3: DETAILED INVESTIGATION OF ALL 9 STATUS TRANSITIONS")
print("=" * 80)

for cid in target_cases:
    req = requests_by_id[cid]
    case_obj = DeletionRequestCase(**req)
    audit_res = engine.audit_case(case_obj)
    
    email = req["email"]
    audit_at = req["audit_at"]
    reported_status = req["reported_status"]
    reported_at = req["reported_at"]
    
    # Resolve subject identity
    identity = resolver.resolve_email(email)
    
    print(f"\n--------------------------------------------------------------------------------")
    print(f"CASE: {cid} | Subject: {identity.user_id if identity else 'UNRESOLVED'} ({identity.name if identity else 'N/A'})")
    print(f"Request Email: {email} | Audit Cutoff: {audit_at}")
    print(f"Reported Workflow Status: {reported_status} at {reported_at}")
    print(f"Audited Decision: {audit_res.deletion_status}")
    print(f"All Identifiers: user_id={identity.user_id if identity else None}, emails={list(identity.all_emails) if identity else []}, hashes={len(identity.all_hashes) if identity else 0}")
    
    # Extract findings
    findings = [s for s in audit_res.steps if s.phase == "FINDING"]
    print(f"New Findings ({len(findings)}):")
    
    for f_idx, f in enumerate(findings, 1):
        ev_meta = manifest.get(f.evidence_id)
        captured_at = ev_meta["captured_at"] if ev_meta else "UNKNOWN"
        cutoff_ok = captured_at <= audit_at
        rule = deletion_rules.get(f.system_id) # check category or system
        
        # Find exact source log line in evidence file
        ev_file_path = Path("dataset") / ev_meta["file_path"]
        matching_lines = []
        if ev_file_path.exists():
            for line in ev_file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if f.resource_id in line:
                    matching_lines.append(line.strip())
                    
        print(f"  Finding {f_idx}:")
        print(f"    System:       {f.system_id}")
        print(f"    Resource ID:  {f.resource_id}")
        print(f"    Operation:    {f.operation}")
        print(f"    State:        {f.state}")
        print(f"    Evidence ID:  {f.evidence_id} ({ev_meta['file_path'] if ev_meta else 'N/A'})")
        print(f"    Captured At:  {captured_at} (<= audit_at {audit_at}: {cutoff_ok})")
        print(f"    Source Line:  {matching_lines[0] if matching_lines else 'NOT FOUND'}")
        
    # Check supporting / related verifications
    remediations = [s for s in audit_res.steps if s.phase == "REMEDIATION"]
    verifications = [s for s in audit_res.steps if s.phase == "VERIFICATION"]
    print(f"  Remediation Steps: {len(remediations)}")
    for r in remediations:
        print(f"    -> {r.system_id} / {r.resource_id}: {r.operation} -> {r.state}")
    print(f"  Verification Steps: {len(verifications)}")
    for v in verifications:
        print(f"    -> {v.system_id} / {v.resource_id}: {v.operation} -> {v.state}")
