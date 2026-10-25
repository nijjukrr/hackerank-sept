import hashlib
from pathlib import Path

def get_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

out_path = Path("output.csv")
zip_path = Path("code.zip")
log_path = Path("log.txt")

out_hash = get_hash(out_path)
zip_hash = get_hash(zip_path)
log_hash = get_hash(log_path)

out_size = out_path.stat().st_size
zip_size = zip_path.stat().st_size
log_size = log_path.stat().st_size

print(f"output.csv: {out_size} bytes, SHA-256: {out_hash}")
print(f"code.zip:   {zip_size} bytes, SHA-256: {zip_hash}")
print(f"log.txt:    {log_size} bytes, SHA-256: {log_hash}")

assert out_hash == "0b7ae604375e836d126dfdb51ff8bbe67195ecd8606e984a86a3b92b7930553d", f"Mismatch out_hash {out_hash}"
assert zip_hash == "1768ebd10919cb583d4bd122da4c4a9c1019b17bacc6d25ab9bb1ed48c4ef262", f"Mismatch zip_hash {zip_hash}"
assert log_hash == "c17db92b927473ba4d6870d57ad3dbd80dda040d52672b315ca3a17b8eb2e19e", f"Mismatch log_hash {log_hash}"

assert out_size == 474810, f"Mismatch out_size {out_size}"
assert zip_size == 48162, f"Mismatch zip_size {zip_size}"
assert log_size == 162116, f"Mismatch log_size {log_size}"

# Check markdown reports
for report_name in ["FINAL_RELEASE_REPORT.md", "FINAL_UPLOAD_VERIFICATION.md"]:
    content = Path(report_name).read_text(encoding="utf-8")
    assert out_hash in content, f"{out_hash} not found in {report_name}"
    assert zip_hash in content, f"{zip_hash} not found in {report_name}"
    assert log_hash in content, f"{log_hash} not found in {report_name}"
    assert "474,810" in content, f"474,810 not found in {report_name}"
    assert "48,162" in content, f"48,162 not found in {report_name}"
    assert "162,116" in content, f"162,116 not found in {report_name}"
    # Verify no stale log hash
    assert "b641cc90" not in content, f"Stale hash b641cc90 still found in {report_name}"
    assert "137,799" not in content, f"Stale size 137,799 still found in {report_name}"

print("\nALL CONSISTENCY ASSERTIONS PASSED WITH ZERO DISCREPANCIES!")
