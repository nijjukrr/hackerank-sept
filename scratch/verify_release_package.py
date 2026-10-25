import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

repo_root = Path(".").resolve()
zip_path = repo_root / "code.zip"

print(f"=== RELEASE GATE VERIFICATION ===")
print(f"1. Archive Existence: {zip_path.exists()} ({zip_path.stat().st_size} bytes)")

# 2. Inspect contents
with zipfile.ZipFile(zip_path, "r") as zf:
    namelist = zf.namelist()
    print(f"2. File Count: {len(namelist)}")
    for name in namelist:
        print(f"   - {name}")

    # Check forbidden contents
    forbidden = [n for n in namelist if "dataset" in n or "__pycache__" in n or ".venv" in n or ".git" in n or n.endswith(".zip")]
    if forbidden:
        print(f"   [FAIL] Forbidden files in archive: {forbidden}")
        sys.exit(1)
    else:
        print("   [PASS] No forbidden files in archive.")

# 3. Clean extraction and execution test
temp_dir = Path(tempfile.mkdtemp(prefix="orchestrate_verify_"))
try:
    print(f"\n3. Extracting to clean sandbox: {temp_dir}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(temp_dir)

    # Link or copy dataset for execution in sandbox
    sandbox_dataset = temp_dir / "dataset"
    shutil.copytree(repo_root / "dataset", sandbox_dataset)

    # Run clean execution on sample
    print("4. Running code/main.py --sample in clean sandbox...")
    res = subprocess.run(
        [sys.executable, str(temp_dir / "code" / "main.py"), "--sample"],
        cwd=temp_dir,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"   [FAIL] Sample execution failed: {res.stderr}")
        sys.exit(1)
    else:
        print("   [PASS] Sample execution succeeded cleanly.")

    # Run clean execution on full evaluation dataset
    print("5. Running code/main.py on full evaluation dataset in clean sandbox...")
    res = subprocess.run(
        [
            sys.executable,
            str(temp_dir / "code" / "main.py"),
            "--input",
            str(temp_dir / "dataset" / "deletion_requests.csv"),
            "--output",
            str(temp_dir / "output.csv"),
        ],
        cwd=temp_dir,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print(f"   [FAIL] Full execution failed: {res.stderr}")
        sys.exit(1)
    else:
        print("   [PASS] Full execution succeeded cleanly.")

    # Compare regenerated output with root output.csv
    root_out = repo_root / "output.csv"
    sandbox_out = temp_dir / "output.csv"
    match = filecmp.cmp(root_out, sandbox_out, shallow=False)
    print(f"6. Output bit-for-bit identical with root output.csv: {match}")
    if not match:
        print("   [FAIL] Output differ!")
        sys.exit(1)
    else:
        print("   [PASS] 100% bit-for-bit identical regenerated output!")

    # Validate output in sandbox
    res = subprocess.run(
        [sys.executable, str(temp_dir / "code" / "evaluation" / "main.py")],
        cwd=temp_dir,
        capture_output=True,
        text=True,
    )
    print(f"7. Evaluation script output:\n{res.stdout}")
    if res.returncode != 0:
        print(f"   [FAIL] Evaluation validation failed: {res.stderr}")
        sys.exit(1)
    else:
        print("   [PASS] Evaluation validation passed with 0 errors!")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("Cleanup completed.")
