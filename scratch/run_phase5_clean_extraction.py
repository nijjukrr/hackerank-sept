import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

repo_root = Path(".").resolve()
zip_path = repo_root / "code.zip"
root_output = repo_root / "output.csv"
scratch_dir = repo_root / "scratch" / "clean_extraction_test"

print("=== PHASE 5: CLEAN EXTRACTION AND REPRODUCIBILITY AUDIT ===")

# 1. Inspect every ZIP member
print("\n--- Step 1: Inspecting ZIP Members ---")
assert zip_path.exists(), "code.zip does not exist!"
zip_members = []
with zipfile.ZipFile(zip_path, "r") as zf:
    for info in zf.infolist():
        zip_members.append(info.filename)
        print(f"  {info.filename} ({info.file_size} bytes)")
        # Check forbidden patterns
        assert not any(p in info.filename for p in ["dataset", "__pycache__", ".venv", "venv", ".git", ".zip", ".tar"]), \
            f"Forbidden member found in zip: {info.filename}"

# Check required members
required_paths = [
    "README.md",
    "code/main.py",
    "code/evaluation/evaluation_report.md",
    "code/evaluation/usage_report.md",
    "evaluation/evaluation_report.md",
    "evaluation/usage_report.md",
]
for rp in required_paths:
    # Normalize forward/back slashes
    found = any(m.replace("\\", "/") == rp for m in zip_members)
    assert found, f"Required member {rp} NOT found in code.zip!"
print("All required members present; zero forbidden artifacts found.")

# 2. Extract into isolated temporary directory
print("\n--- Step 2: Extracting to Isolated Temporary Directory ---")
if scratch_dir.exists():
    shutil.rmtree(scratch_dir)
scratch_dir.mkdir(parents=True)

with zipfile.ZipFile(zip_path, "r") as zf:
    zf.extractall(scratch_dir)
print(f"Extracted to {scratch_dir}")

# In an evaluation environment, dataset/ is mounted at repository root.
# We copy dataset/ into scratch_dir to verify zero dependence on the original dev workspace.
print("Copying dataset/ into extraction directory to test standalone execution...")
shutil.copytree(repo_root / "dataset", scratch_dir / "dataset")

# 3. Run the documented command: python code/main.py
print("\n--- Step 3: Executing Documented Command in Isolated Dir ---")
cmd = [sys.executable, "code/main.py"]
proc = subprocess.run(cmd, cwd=scratch_dir, capture_output=True, text=True)
print("STDOUT:\n" + proc.stdout)
if proc.stderr:
    print("STDERR:\n" + proc.stderr)
assert proc.returncode == 0, f"Execution failed with return code {proc.returncode}"

extracted_output = scratch_dir / "output.csv"
assert extracted_output.exists(), "Clean execution did not generate output.csv!"

# 4 & 5. Byte-for-byte comparison
print("\n--- Step 4 & 5: Comparing Extracted output.csv with Root output.csv ---")
root_bytes = root_output.read_bytes()
extracted_bytes = extracted_output.read_bytes()

root_sha = hashlib.sha256(root_bytes).hexdigest()
extracted_sha = hashlib.sha256(extracted_bytes).hexdigest()

print(f"Root output.csv SHA-256:      {root_sha}")
print(f"Extracted output.csv SHA-256: {extracted_sha}")
assert root_sha == extracted_sha, "Extracted output.csv differs from root output.csv!"
print("Byte-for-byte match: 100% identical!")

# 6, 7, 8, 9. Run validator and specification constraints
print("\n--- Steps 6, 7, 8, 9: Validating Output Specification Constraints ---")
sys.path.insert(0, str(repo_root / "code"))
from evaluation.main import validate_csv

errors = validate_csv(extracted_output, expected_count=518)
assert len(errors) == 0, f"Validation errors found: {errors}"
print(f"Schema validator: PASSED with 0 errors on all 518 cases.")

# 10. Record final sizes and SHA-256 hashes
zip_size = zip_path.stat().st_size
zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
out_size = root_output.stat().st_size

print("\n--- Step 10: Final Checksums and File Properties ---")
print(f"code.zip:   {zip_size:,} bytes | SHA-256: {zip_sha}")
print(f"output.csv: {out_size:,} bytes | SHA-256: {root_sha}")

print("\n=== PHASE 5 VERIFICATION COMPLETE: ALL CHECKS PASSED ===")
