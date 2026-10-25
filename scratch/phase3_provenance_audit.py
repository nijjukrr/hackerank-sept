"""Independent provenance and cutoff audit for all missing resources in mismatched cases."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

REPO_ROOT = Path(".").resolve()
DATASET_DIR = REPO_ROOT / "dataset"
EVIDENCE_FILES = DATASET_DIR / "evidence_files.csv"
SAMPLE_INPUT = DATASET_DIR / "sample_deletion_requests.csv"
SAMPLE_TRUTH = DATASET_DIR / "sample_output.csv"
SAMPLE_PRED = REPO_ROOT / "sample_test_output.csv"

with EVIDENCE_FILES.open("r", encoding="utf-8") as f:
    manifest = {r["file_id"]: r for r in csv.DictReader(f)}

with SAMPLE_INPUT.open("r", encoding="utf-8") as f:
    requests = {r["case_id"]: r for r in csv.DictReader(f)}

with SAMPLE_TRUTH.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with SAMPLE_PRED.open("r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

# Find all missing steps in pred
missing_resources_by_case = {}
for cid in sorted(truth.keys()):
    t_st, t_steps = truth[cid]
    p_st, p_steps = pred[cid]
    t_tuples = [tuple(s.get(k, "") for k in fields) for s in t_steps]
    p_tuples = [tuple(s.get(k, "") for k in fields) for s in p_steps]
    missing = [s for s, tup in zip(t_steps, t_tuples) if tup not in p_tuples]
    if missing:
        missing_resources_by_case[cid] = missing

print(f"Total cases with missing steps: {len(missing_resources_by_case)}")

# Search for provenance of each missing resource
for cid, missing_steps in missing_resources_by_case.items():
    req = requests[cid]
    audit_at = req["audit_at"]
    print(f"\n=======================================================")
    print(f"CASE {cid} | Email: {req['email']} | Audit Cutoff: {audit_at}")
    print(f"Missing steps in prediction: {len(missing_steps)}")
    print(f"=======================================================")

    for ms in missing_steps:
        rid = ms["resource_id"]
        phase = ms["phase"]
        op = ms["operation"]
        sys_id = ms["system_id"]
        ev_id = ms["evidence_id"]

        print(f"\n- Missing Step: {phase} | {sys_id} | {rid} | {op} | evidence_id: '{ev_id}'")

        # Find all occurrences of rid in dataset/
        occurrences = []
        for file_id, meta in manifest.items():
            fpath = DATASET_DIR / meta["file_path"]
            if not fpath.exists():
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if rid in content:
                    occurrences.append({
                        "file_id": file_id,
                        "file_path": meta["file_path"],
                        "captured_at": meta["captured_at"],
                        "is_before_cutoff": meta["captured_at"] <= audit_at,
                    })
            except Exception:
                pass

        # Check system_activity.csv
        in_activity = False
        with (DATASET_DIR / "system_activity.csv").open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("resource_id") == rid:
                    in_activity = True
                    break

        print(f"  In system_activity.csv: {in_activity}")
        print(f"  Occurrences in evidence files ({len(occurrences)}):")
        for occ in occurrences:
            status_str = "LEGAL (<= cutoff)" if occ["is_before_cutoff"] else "ILLEGAL (> cutoff / TEMPORAL LEAK)"
            print(f"    * {occ['file_id']} ({occ['file_path']}) | captured_at: {occ['captured_at']} | {status_str}")

        if not occurrences:
            print(f"    * ZERO occurrences found in any evidence file across dataset/evidence/!")
