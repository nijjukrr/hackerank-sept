import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

root_dir = Path(".").resolve()
zip_path = root_dir / "code.zip"
canonical_output = root_dir / "output.csv"
dataset_src = root_dir / "dataset"

print("=== CLEAN ENVIRONMENT EXTRACTION & EXECUTION AUDIT ===")
temp_dir = Path(tempfile.mkdtemp(prefix="orchestrate_audit_clean_"))
print(f"1. Created clean sandbox directory: {temp_dir}")

try:
    # 2. Extract code.zip
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(temp_dir)
    print(f"2. Extracted {len(z.namelist())} files from {zip_path.name}")

    # 3. Check for any forbidden files
    forbidden = ["__pycache__", ".pyc", ".venv", "venv", ".git", "output.csv", ".zip"]
    extracted_files = [p for p in temp_dir.rglob("*") if p.is_file()]
    for p in extracted_files:
        rel = p.relative_to(temp_dir)
        for f in forbidden:
            assert f not in str(rel), f"Forbidden artifact in code.zip: {rel}"
    print("3. Verified 0 forbidden artifacts, build caches, or virtualenvs in package.")

    # 4. Copy dataset to sandbox
    dataset_dest = temp_dir / "dataset"
    shutil.copytree(dataset_src, dataset_dest)
    print("4. Staged official dataset into clean sandbox.")

    # 5. Run the documented entry point: python code/main.py
    cmd = [sys.executable, "code/main.py"]
    print(f"5. Running documented entry point: {' '.join(cmd)} in sandbox...")
    res = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    assert res.returncode == 0, f"Execution failed with code {res.returncode}"

    # 6. Verify output.csv created at root of sandbox
    sandbox_output = temp_dir / "output.csv"
    assert sandbox_output.exists(), "output.csv was not created at sandbox root!"
    print(f"6. output.csv successfully created ({sandbox_output.stat().st_size} bytes)")

    # 7. Run validator in sandbox
    val_cmd = [sys.executable, "code/evaluation/main.py"]
    print("7. Running validator inside sandbox...")
    val_res = subprocess.run(val_cmd, cwd=temp_dir, capture_output=True, text=True)
    print(val_res.stdout)
    assert val_res.returncode == 0, f"Validator failed with code {val_res.returncode}"

    # 8. Compare SHA-256 digests between root output.csv and sandbox output.csv
    hash_canonical = sha256_file(canonical_output)
    hash_sandbox = sha256_file(sandbox_output)
    print(f"8. Canonical output SHA-256: {hash_canonical}")
    print(f"   Sandbox output SHA-256:   {hash_sandbox}")
    assert hash_canonical == hash_sandbox, "Hash mismatch between canonical output.csv and clean sandbox output.csv!"
    print("SUCCESS: Clean sandbox output is 100% BIT-FOR-BIT IDENTICAL to canonical output.csv!")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("Sandbox cleanup completed.")
