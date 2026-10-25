"""Phase 5 Status Transition Audit: Auditing all 34 evaluation cases that shifted from COMPLETE to INCOMPLETE."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(".").resolve()
DATASET_DIR = REPO_ROOT / "dataset"
BACKUP_OUTPUT = REPO_ROOT / "scratch" / "backup_output.csv"
CURRENT_OUTPUT = REPO_ROOT / "output.csv"
REQUESTS_FILE = DATASET_DIR / "deletion_requests.csv"
RULES_FILE = DATASET_DIR / "deletion_rules.csv"
EVIDENCE_FILES = DATASET_DIR / "evidence_files.csv"

# Load requests
with REQUESTS_FILE.open("r", encoding="utf-8") as f:
    requests = {r["case_id"]: r for r in csv.DictReader(f)}

# Load manifest
with EVIDENCE_FILES.open("r", encoding="utf-8") as f:
    manifest = {r["file_id"]: r for r in csv.DictReader(f)}

# Load rules
with RULES_FILE.open("r", encoding="utf-8") as f:
    rules = list(csv.DictReader(f))

# Load outputs
with BACKUP_OUTPUT.open("r", encoding="utf-8") as f:
    orig = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with CURRENT_OUTPUT.open("r", encoding="utf-8") as f:
    curr = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

transitions = []
for cid in sorted(curr.keys()):
    orig_st, orig_steps = orig[cid]
    curr_st, curr_steps = curr[cid]
    if orig_st == "COMPLETE" and curr_st == "INCOMPLETE":
        transitions.append(cid)

print(f"Total COMPLETE -> INCOMPLETE transitions: {len(transitions)}")
assert len(transitions) == 34, f"Expected 34 transitions, got {len(transitions)}"

transition_audit_records = []

for cid in transitions:
    req = requests[cid]
    audit_at = req["audit_at"]
    orig_st, orig_steps = orig[cid]
    curr_st, curr_steps = curr[cid]

    # Findings in current prediction
    findings = [s for s in curr_steps if s["phase"] == "FINDING"]
    remediations = [s for s in curr_steps if s["phase"] == "REMEDIATION"]

    # Identify the specific finding(s) that caused INCOMPLETE
    new_risks = []
    for f in findings:
        ev_id = f["evidence_id"]
        ev_meta = manifest.get(ev_id, {})
        cap_at = ev_meta.get("captured_at", "UNKNOWN")
        is_legal = (cap_at <= audit_at) if cap_at != "UNKNOWN" else False

        new_risks.append({
            "system_id": f["system_id"],
            "resource_id": f["resource_id"],
            "operation": f["operation"],
            "state": f["state"],
            "evidence_id": ev_id,
            "file_path": ev_meta.get("file_path", "UNKNOWN"),
            "captured_at": cap_at,
            "audit_at": audit_at,
            "cutoff_valid": is_legal,
        })

    record = {
        "case_id": cid,
        "email": req["email"],
        "audit_at": audit_at,
        "findings_count": len(findings),
        "remediations_count": len(remediations),
        "new_risks": new_risks,
    }
    transition_audit_records.append(record)

# Save to scratch
with open("scratch/transition_audit_details.json", "w", encoding="utf-8") as f:
    json.dump(transition_audit_records, f, indent=2)

print("Saved transition audit details to scratch/transition_audit_details.json\n")

# Print summary table of transitions
print("| Case ID | Subject Email | Newly Discovered Resource | System | Operation | Evidence File | Cutoff Valid |")
print("|---|---|---|---|---|---|---|")
for r in transition_audit_records:
    cid = r["case_id"]
    email = r["email"]
    for nr in r["new_risks"]:
        print(f"| `{cid}` | `{email}` | `{nr['resource_id']}` | `{nr['system_id']}` | `{nr['operation']}` | `{nr['evidence_id']}` | {'PASS' if nr['cutoff_valid'] else 'FAIL'} |")
