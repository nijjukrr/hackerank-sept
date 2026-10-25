import hashlib
from pathlib import Path

actual = {}
for fn in ['output.csv', 'code.zip', 'log.txt']:
    p = Path(fn)
    actual[fn] = {
        'size': p.stat().st_size,
        'sha256': hashlib.sha256(p.read_bytes()).hexdigest()
    }

print("=== ACTUAL ARTIFACTS ON DISK ===")
for fn, data in actual.items():
    print(f"File: {fn}")
    print(f"  Exact Byte Size: {data['size']} bytes ({data['size']:,} bytes)")
    print(f"  SHA-256 Checksum: {data['sha256']}")

all_passed = True
for r in ['FINAL_RELEASE_REPORT.md', 'FINAL_UPLOAD_VERIFICATION.md']:
    txt = Path(r).read_text(encoding='utf-8')
    print(f"\n=== VALIDATION FOR {r} ===")
    for fn, data in actual.items():
        size_str = f"{data['size']:,} bytes"
        sha_str = data['sha256']
        size_pass = size_str in txt
        sha_pass = sha_str in txt
        print(f"  [{fn}] Size check ({size_str}): {'PASS' if size_pass else 'FAIL'}")
        print(f"  [{fn}] SHA-256 check ({sha_str}): {'PASS' if sha_pass else 'FAIL'}")
        if not (size_pass and sha_pass):
            all_passed = False
    
    # Check no retired hashes exist
    retired_hashes = [
        '6932c4e9adfa9305d604834ca3c5d02ae45449fd13477e517a2e01635dc282f6',
        '9640702fe79483d846e63d3f169e8811a3771e2935cb301619f5c1dd09b6b8ee'
    ]
    for rh in retired_hashes:
        rh_found = rh in txt
        print(f"  [Zero Stale Hash Check] '{rh[:8]}...': {'PASS (Absent)' if not rh_found else 'FAIL (Found)'}")
        if rh_found:
            all_passed = False

print(f"\nOVERALL DOCUMENTATION INTEGRITY STATUS: {'PASS' if all_passed else 'FAIL'}")
