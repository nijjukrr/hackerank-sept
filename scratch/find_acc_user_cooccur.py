import csv
import json
import glob
import os

print("=== CHECKING ALL EVIDENCE FILES FOR ACCOUNT -> USER LINKS ===")
for root, dirs, files in os.walk("dataset"):
    for f in files:
        fpath = os.path.join(root, f)
        if f.endswith(".json") or f.endswith(".sql") or f.endswith(".log") or f.endswith(".csv"):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                    # Check if both account_ and user_ appear on the same line or in the same object
                    for line in content.splitlines():
                        if "account_" in line and "user_" in line:
                            print(f"{fpath}: {line[:120]}")
                            break
            except Exception:
                pass
