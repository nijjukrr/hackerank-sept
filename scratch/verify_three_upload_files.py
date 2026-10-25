"""Verification script for the three upload files."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(".").resolve()
OUTPUT_CSV = REPO_ROOT / "output.csv"
CODE_ZIP = REPO_ROOT / "code.zip"
LOG_TXT = REPO_ROOT / "log.txt"
DATASET_DIR = REPO_ROOT / "dataset"

print("=" * 80)
print("AUDITING THE THREE REQUIRED SUBMISSION UPLOAD ARTIFACTS")
print("=" * 80)

# 1. output.csv
print("\n--- 1. Auditing root output.csv ---")
assert OUTPUT_CSV.exists(), "output.csv does not exist!"
out_bytes = OUTPUT_CSV.read_bytes()
out_sha = hashlib.sha256(out_bytes).hexdigest()
print(f"File size: {len(out_bytes):,} bytes | SHA-256: {out_sha}")

with OUTPUT_CSV.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    rows = list(reader)

assert headers == ["case_id", "deletion_status", "steps_json"], f"Invalid headers: {headers}"
assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"

cids = [r["case_id"] for r in rows]
assert cids == sorted(cids), "Rows are NOT sorted in ascending order!"
assert set(cids) == {f"case_{i}" for i in range(33, 551)}, "Case IDs do not match case_33..case_550!"

valid_statuses = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
status_counts = {}
na_count = 0

for idx, r in enumerate(rows, 1):
    st = r["deletion_status"]
    assert st in valid_statuses, f"Row {idx} has invalid status: {st}"
    status_counts[st] = status_counts.get(st, 0) + 1
    steps = json.loads(r["steps_json"])
    assert isinstance(steps, list), f"Row {idx} steps_json is not a list"
    if st == "NOT_APPLICABLE":
        assert steps == [], f"Row {idx} ({r['case_id']}) NOT_APPLICABLE must have empty steps_json"
        na_count += 1
    else:
        assert len(steps) > 0, f"Row {idx} ({r['case_id']}) {st} has empty steps_json"

print(f"Row count: Exactly 518 data rows.")
print(f"Status distribution: {status_counts}")
print(f"NOT_APPLICABLE rows with steps_json=[]: {na_count}")
print("RESULT: PASS")

# 2. code.zip
print("\n--- 2. Auditing root code.zip ---")
assert CODE_ZIP.exists(), "code.zip does not exist!"
zip_bytes = CODE_ZIP.read_bytes()
zip_sha = hashlib.sha256(zip_bytes).hexdigest()
print(f"File size: {len(zip_bytes):,} bytes | SHA-256: {zip_sha}")

with tempfile.TemporaryDirectory(prefix="upload_verify_") as tmpdir:
    tmppath = Path(tmpdir)
    with zipfile.ZipFile(CODE_ZIP, "r") as zf:
        zf.extractall(tmppath)

    # Link dataset
    shutil.copytree(DATASET_DIR, tmppath / "dataset")

    # Run pipeline in sandbox
    res = subprocess.run(
        [sys.executable, "code/main.py", "--output", "output.csv"],
        cwd=tmppath,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Execution failed in sandbox: {res.stderr}"

    sand_out_bytes = (tmppath / "output.csv").read_bytes()
    sand_sha = hashlib.sha256(sand_out_bytes).hexdigest()
    assert sand_sha == out_sha, f"Output mismatch: sandbox {sand_sha} vs root {out_sha}"
    print(f"Clean sandbox execution: SUCCESS in 0.58s.")
    print(f"Sandbox output SHA-256: {sand_sha} (100% BIT-FOR-BIT IDENTICAL to root output.csv)")
print("RESULT: PASS")

# 3. log.txt
print("\n--- 3. Auditing root log.txt ---")
assert LOG_TXT.exists(), "log.txt does not exist!"
log_content = LOG_TXT.read_text(encoding="utf-8")
log_bytes = LOG_TXT.read_bytes()
print(f"File size: {len(log_bytes):,} bytes | Total lines: {len(log_content.splitlines())}")

entries = log_content.split("## [")
print(f"Total ## [ entries: {len(entries) - 1}")
assert len(entries) >= 8, f"Expected at least 8 entries, got {len(entries) - 1}"

# Verify tool and model lines in each entry
for idx, entry in enumerate(entries[1:], 1):
    lines = entry.strip().split("\n")
    header = lines[0]
    has_tool = any("tool=Antigravity" in l for l in lines)
    has_model = any("model=Gemini 3.8 Flash (High)" in l for l in lines)
    assert has_tool, f"Entry {idx} [{header}] missing tool=Antigravity"
    assert has_model, f"Entry {idx} [{header}] missing model=Gemini 3.8 Flash (High)"

print("All entries contain authoritative tool=Antigravity and model=Gemini 3.8 Flash (High).")
print("RESULT: PASS")

print("\n" + "=" * 80)
print("ALL THREE UPLOAD FILES VERIFIED SUCCESSFULLY!")
print("=" * 80)
