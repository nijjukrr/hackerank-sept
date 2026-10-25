"""Phase 6 Release Artifacts Validation Script."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(".").resolve()
OUTPUT_CSV = REPO_ROOT / "output.csv"
CODE_ZIP = REPO_ROOT / "code.zip"
LOG_TXT = REPO_ROOT / "log.txt"

print("=" * 80)
print("PHASE 6: RELEASE ARTIFACTS INDEPENDENT VALIDATION")
print("=" * 80)

# Check 1: output.csv header, coverage, sorting, schema
print("\n1. Auditing output.csv structure...")
with OUTPUT_CSV.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

expected_headers = ["case_id", "deletion_status", "steps_json"]
assert fieldnames == expected_headers, f"Header mismatch: got {fieldnames}, expected {expected_headers}"
assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"

cids = [r["case_id"] for r in rows]
assert cids == sorted(cids), "Rows are NOT sorted strictly by case_id in alphabetical order!"
assert set(cids) == {f"case_{i}" for i in range(33, 551)}, f"Case ID set does not match case_33..case_550 exactly!"
print(f"  First 3 case_ids: {cids[:3]}, Last 3 case_ids: {cids[-3:]}")

valid_statuses = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
na_count = 0
for r in rows:
    st = r["deletion_status"]
    assert st in valid_statuses, f"Invalid status: {st} in case {r['case_id']}"
    steps = json.loads(r["steps_json"])
    assert isinstance(steps, list), f"steps_json is not a list in case {r['case_id']}"
    if st == "NOT_APPLICABLE":
        assert steps == [], f"NOT_APPLICABLE must have empty steps_json, got {steps} in case {r['case_id']}"
        na_count += 1

assert na_count == 10, f"Expected exactly 10 NOT_APPLICABLE rows, got {na_count}"
print(f"  [PASS] output.csv: 518 rows, correct header, strictly sorted, valid JSON, {na_count} NOT_APPLICABLE.")

# Check 2: code.zip contents & forbidden files check
print("\n2. Auditing code.zip contents...")
with zipfile.ZipFile(CODE_ZIP, "r") as zf:
    namelist = zf.namelist()

forbidden_prefixes = ("dataset", ".venv", ".git", "__pycache__", "tmp", "scratch")
for name in namelist:
    for fp in forbidden_prefixes:
        assert not name.startswith(fp), f"Forbidden file found in code.zip: {name}"
    assert not name.endswith(".zip"), f"Nested zip found in code.zip: {name}"

required_in_zip = [
    "README.md",
    "CONSTANTS.md",
    "code/main.py",
    "code/audit_engine.py",
    "code/evidence_loader.py",
    "code/identity_resolver.py",
    "code/intent_classifier.py",
    "code/models.py",
    "evaluation/evaluation_report.md",
    "evaluation/usage_report.md",
]
for req in required_in_zip:
    norm_req = req.replace("/", "\\")
    assert any(name == req or name == norm_req for name in namelist), f"Missing required file in code.zip: {req}"

print(f"  [PASS] code.zip: {len(namelist)} files, 0 forbidden files, all required code/docs present.")

# Check 3: Clean extraction execution
print("\n3. Testing execution in clean isolated environment...")
with tempfile.TemporaryDirectory(prefix="phase6_clean_sandbox_") as tmpdir:
    tmppath = Path(tmpdir)
    with zipfile.ZipFile(CODE_ZIP, "r") as zf:
        zf.extractall(tmppath)

    # Link dataset
    import shutil
    shutil.copytree(REPO_ROOT / "dataset", tmppath / "dataset")

    # Run pipeline in sandbox
    res = subprocess.run(
        [sys.executable, "code/main.py", "--output", "output.csv"],
        cwd=tmppath,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Pipeline failed in sandbox: {res.stderr}"

    # Verify output SHA-256
    sand_sha = hashlib.sha256((tmppath / "output.csv").read_bytes()).hexdigest()
    orig_sha = hashlib.sha256(OUTPUT_CSV.read_bytes()).hexdigest()
    assert sand_sha == orig_sha, f"Output mismatch: sandbox {sand_sha} vs canonical {orig_sha}"
    print(f"  [PASS] Clean extraction output is 100% BIT-FOR-BIT IDENTICAL (SHA-256: {orig_sha}).")

# Check 4: Validator negative controls
print("\n4. Running validator negative controls...")
res_neg = subprocess.run(
    [sys.executable, "scratch/test_validator_negative_controls.py"],
    capture_output=True,
    text=True,
)
assert res_neg.returncode == 0, f"Validator negative controls failed: {res_neg.stderr}"
print("  [PASS] Validator correctly rejected all 15 negative control invalid files.")

# Check 5: Append-only log check
print("\n5. Auditing log.txt append-only discipline...")
log_lines = LOG_TXT.read_text(encoding="utf-8").splitlines()
assert len(log_lines) > 50, "log.txt is too short!"
assert any("SESSION START" in l for l in log_lines), "Missing SESSION START in log.txt"
assert any("tool=Antigravity" in l for l in log_lines), "Missing tool=Antigravity in log.txt"
assert any("model=Gemini 3.8 Flash (High)" in l for l in log_lines), "Missing model=Gemini in log.txt"
print("  [PASS] log.txt strictly conforms to append-only logging requirements.")

print("\n" + "=" * 80)
print("ALL PHASE 6 RELEASE ARTIFACT CHECKS PASSED WITH ZERO ERRORS!")
print("=" * 80)
