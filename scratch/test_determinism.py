import filecmp
import hashlib
import subprocess
import sys
from pathlib import Path

repo_root = Path(".").resolve()
out1 = repo_root / "scratch" / "run1_output.csv"
out2 = repo_root / "scratch" / "run2_output.csv"

print("Running pass 1...")
res1 = subprocess.run(
    [sys.executable, "code/main.py", "--input", "dataset/deletion_requests.csv", "--output", str(out1)],
    capture_output=True,
    text=True,
)
assert res1.returncode == 0, f"Pass 1 failed: {res1.stderr}"

print("Running pass 2...")
res2 = subprocess.run(
    [sys.executable, "code/main.py", "--input", "dataset/deletion_requests.csv", "--output", str(out2)],
    capture_output=True,
    text=True,
)
assert res2.returncode == 0, f"Pass 2 failed: {res2.stderr}"

h1 = hashlib.sha256(out1.read_bytes()).hexdigest()
h2 = hashlib.sha256(out2.read_bytes()).hexdigest()
h_root = hashlib.sha256((repo_root / "output.csv").read_bytes()).hexdigest()

print(f"SHA256 Run 1: {h1}")
print(f"SHA256 Run 2: {h2}")
print(f"SHA256 Root:  {h_root}")

assert h1 == h2 == h_root, "Outputs are not byte-for-byte identical!"
print("[PASS] 100% Deterministic & byte-for-byte identical across runs!")
