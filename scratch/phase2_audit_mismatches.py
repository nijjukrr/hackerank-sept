"""Phase 2 Deep Mismatch Audit: Detailed step-by-step audit of all 18 mismatched cases."""

from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(".").resolve()
DATASET_DIR = REPO_ROOT / "dataset"
SAMPLE_INPUT = DATASET_DIR / "sample_deletion_requests.csv"
SAMPLE_TRUTH = DATASET_DIR / "sample_output.csv"
SAMPLE_PRED = REPO_ROOT / "sample_test_output.csv"
RULES_FILE = DATASET_DIR / "deletion_rules.csv"
EVIDENCE_FILES = DATASET_DIR / "evidence_files.csv"

# Load rules
with RULES_FILE.open("r", encoding="utf-8") as f:
    rules = list(csv.DictReader(f))

# Load evidence manifest
with EVIDENCE_FILES.open("r", encoding="utf-8") as f:
    ev_manifest = {r["file_id"]: r for r in csv.DictReader(f)}

# Load sample requests
with SAMPLE_INPUT.open("r", encoding="utf-8") as f:
    requests = {r["case_id"]: r for r in csv.DictReader(f)}

# Load truth and pred
with SAMPLE_TRUTH.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with SAMPLE_PRED.open("r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

mismatched_cids = []
for cid in sorted(truth.keys()):
    t_st, t_steps = truth[cid]
    p_st, p_steps = pred[cid]
    t_7t = [tuple(s.get(k, "") for k in fields) for s in t_steps]
    p_7t = [tuple(s.get(k, "") for k in fields) for s in p_steps]
    if t_st != p_st or t_7t != p_7t:
        mismatched_cids.append(cid)

print(f"Total mismatched cases: {len(mismatched_cids)} out of 32")
print(f"Mismatched Case IDs: {mismatched_cids}\n")

case_analysis_results = []

for cid in mismatched_cids:
    req = requests[cid]
    t_st, t_steps = truth[cid]
    p_st, p_steps = pred[cid]

    t_tuples = [tuple(s.get(k, "") for k in fields) for s in t_steps]
    p_tuples = [tuple(s.get(k, "") for k in fields) for s in p_steps]

    missing_steps = [s for s, tup in zip(t_steps, t_tuples) if tup not in p_tuples]
    extra_steps = [s for s, tup in zip(p_steps, p_tuples) if tup not in t_tuples]

    # Collect cited evidence files in truth vs pred
    t_evs = {s["evidence_id"] for s in t_steps if s.get("evidence_id")}
    p_evs = {s["evidence_id"] for s in p_steps if s.get("evidence_id")}

    case_info = {
        "case_id": cid,
        "email": req["email"],
        "requested_at": req["requested_at"],
        "reported_status": req["reported_status"],
        "audit_at": req["audit_at"],
        "truth_status": t_st,
        "pred_status": p_st,
        "truth_step_count": len(t_steps),
        "pred_step_count": len(p_steps),
        "missing_steps": missing_steps,
        "extra_steps": extra_steps,
        "truth_evidence_ids": list(t_evs),
        "pred_evidence_ids": list(p_evs),
        "truth_steps": t_steps,
        "pred_steps": p_steps,
    }
    case_analysis_results.append(case_info)

# Write analysis to JSON for programmatic inspection
with open("scratch/mismatch_audit_data.json", "w", encoding="utf-8") as f:
    json.dump(case_analysis_results, f, indent=2)

print("Saved detailed mismatch data to scratch/mismatch_audit_data.json")

# Print summary table
for item in case_analysis_results:
    cid = item["case_id"]
    print(f"--- Case {cid} ---")
    print(f"  Email: {item['email']} | Audit At: {item['audit_at']}")
    print(f"  Truth: {item['truth_status']} ({item['truth_step_count']} steps) | Pred: {item['pred_status']} ({item['pred_step_count']} steps)")
    print(f"  Missing in Pred ({len(item['missing_steps'])}):")
    for ms in item["missing_steps"]:
        print(f"    - Step {ms['step_no']}: {ms['phase']} | {ms['system_id']} | {ms['resource_id']} | {ms['operation']} | {ms['state']} | ev:{ms['evidence_id']}")
    print(f"  Extra in Pred ({len(item['extra_steps'])}):")
    for es in item["extra_steps"]:
        print(f"    - Step {es['step_no']}: {es['phase']} | {es['system_id']} | {es['resource_id']} | {es['operation']} | {es['state']} | ev:{es['evidence_id']}")
    print()
