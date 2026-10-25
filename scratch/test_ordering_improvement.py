import sys
from pathlib import Path
sys.path.insert(0, "code")
from audit_engine import AuditEngine
from models import DeletionRequestCase, Step
import csv
import json

# Let's define the sorting keys for findings, remediations, and verifications
FINDING_ORDER = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

SYSTEM_FINDING_ORDER = {
    "account_service": 1,
    "export_service": 2,
    "search_service": 3,
    "analytics_platform": 4,
    "support_platform": 5,
    "identity_service": 6,
    "integration_service": 7,
    "backup_service": 8,
}

REMEDIATION_ORDER = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_SYSTEM_ORDER = {
    "account_service": 1,
    "export_service": 2,
    "search_service": 3,
    "security_service": 4,
    "support_platform": 5,
    "analytics_platform": 6,
    "identity_service": 7,
    "integration_service": 8,
    "backup_service": 9,
}

def sort_findings(steps):
    return sorted(steps, key=lambda s: (
        FINDING_ORDER.get(s.operation, 99),
        SYSTEM_FINDING_ORDER.get(s.system_id, 99),
        s.resource_id
    ))

def sort_remediations(steps):
    return sorted(steps, key=lambda s: (
        REMEDIATION_ORDER.get(s.operation, 99),
        s.system_id,
        s.resource_id
    ))

def sort_verifications(steps):
    return sorted(steps, key=lambda s: (
        VERIFICATION_SYSTEM_ORDER.get(s.system_id, 99),
        s.resource_id,
        s.operation
    ))

engine = AuditEngine(Path("dataset"))
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    cases = [DeletionRequestCase(**row) for row in csv.DictReader(f)]

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

original_exact = 0
reordered_exact = 0

diffs = []
for c in cases:
    cid = c.case_id
    res = engine.audit_case(c)
    exp_status, exp_steps = expected[cid]
    
    orig_steps = [s.to_dict() for s in res.steps]
    if res.deletion_status == exp_status and orig_steps == exp_steps:
        original_exact += 1
        
    # Reorder steps
    f_steps = [s for s in res.steps if s.phase == "FINDING"]
    r_steps = [s for s in res.steps if s.phase == "REMEDIATION"]
    v_steps = [s for s in res.steps if s.phase == "VERIFICATION"]
    
    f_sorted = sort_findings(f_steps)
    r_sorted = sort_remediations(r_steps)
    v_sorted = sort_verifications(v_steps)
    
    all_sorted = f_sorted + r_sorted + v_sorted
    for i, s in enumerate(all_sorted, 1):
        s.step_no = i
        
    reord_steps = [s.to_dict() for s in all_sorted]
    if res.deletion_status == exp_status and reord_steps == exp_steps:
        reordered_exact += 1
    else:
        diffs.append((cid, exp_steps, reord_steps))

print(f"Original exact: {original_exact}/32")
print(f"Reordered exact: {reordered_exact}/32")
print(f"Remaining mismatches: {len(diffs)}")
for cid, exp_s, reord_s in diffs:
    print(f"  {cid}: exp len={len(exp_s)}, got len={len(reord_s)}")
