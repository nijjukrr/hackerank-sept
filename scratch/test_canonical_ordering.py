import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json

from audit_engine import AuditEngine
from models import DeletionRequestCase, Step

FINDING_OP_ORDER = {
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
}

FINDING_SYS_ORDER = {
    "account_service": 1,
    "export_service": 2,
    "search_service": 3,
    "analytics_platform": 4,
    "support_platform": 5,
    "identity_service": 6,
    "integration_service": 7,
    "backup_service": 8,
}

REMEDIATION_OP_ORDER = {
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
}

VERIFICATION_SYS_ORDER = {
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

def sort_steps_canonically(steps):
    findings = [s for s in steps if s.phase == "FINDING"]
    remediations = [s for s in steps if s.phase == "REMEDIATION"]
    verifications = [s for s in steps if s.phase == "VERIFICATION"]

    sorted_findings = sorted(
        findings,
        key=lambda s: (
            FINDING_OP_ORDER.get(s.operation, 99),
            FINDING_SYS_ORDER.get(s.system_id, 99),
            s.resource_id,
        )
    )

    sorted_remediations = sorted(
        remediations,
        key=lambda s: (
            REMEDIATION_OP_ORDER.get(s.operation, 99),
            s.system_id,
            s.resource_id,
        )
    )

    sorted_verifications = sorted(
        verifications,
        key=lambda s: (
            VERIFICATION_SYS_ORDER.get(s.system_id, 99),
            s.resource_id,
            s.operation,
        )
    )

    all_sorted = sorted_findings + sorted_remediations + sorted_verifications
    for i, s in enumerate(all_sorted, 1):
        s.step_no = i
    return all_sorted

# Run comparison on sample
engine = AuditEngine(Path("dataset"))
sample_cases = []
with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        sample_cases.append(DeletionRequestCase(**r))
sample_cases.sort(key=lambda c: c.case_id)

with open("dataset/sample_output.csv", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

# Baseline metrics
base_exact = 0
base_tuples = 0
base_cells = 0

reord_exact = 0
reord_tuples = 0
reord_cells = 0

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

for c in sample_cases:
    res = engine.audit_case(c)
    t_stat, t_steps = truth[c.case_id]
    
    # Baseline
    b_steps = [s.to_dict() for s in res.steps]
    if res.deletion_status == t_stat and b_steps == t_steps:
        base_exact += 1
    t_tups = [tuple(s.get(k, "") for k in all_fields) for s in t_steps]
    b_tups = [tuple(s.get(k, "") for k in all_fields) for s in b_steps]
    base_tuples += sum(1 for pt in b_tups if pt in t_tups)
    for idx in range(min(len(t_steps), len(b_steps))):
        for f in all_fields:
            if t_steps[idx].get(f) == b_steps[idx].get(f):
                base_cells += 1
                
    # Reordered
    r_sorted_objs = sort_steps_canonically([Step(**s) for s in b_steps])
    r_steps = [s.to_dict() for s in r_sorted_objs]
    if res.deletion_status == t_stat and r_steps == t_steps:
        reord_exact += 1
    r_tups = [tuple(s.get(k, "") for k in all_fields) for s in r_steps]
    reord_tuples += sum(1 for pt in r_tups if pt in t_tups)
    for idx in range(min(len(t_steps), len(r_steps))):
        for f in all_fields:
            if t_steps[idx].get(f) == r_steps[idx].get(f):
                reord_cells += 1

print(f"Baseline exact: {base_exact}/32, tuples: {base_tuples}/193, cells: {base_cells}/1351")
print(f"Reordered exact: {reord_exact}/32, tuples: {reord_tuples}/193, cells: {reord_cells}/1351")
