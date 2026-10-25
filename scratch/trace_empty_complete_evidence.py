import csv
import os
import glob

targets = ["aarav.m2118@zoho.com", "user_131", "mateo.alvarez@gmail.com", "user_132", "case_133", "case_134"]

print("=== Checking system_activity.csv ===")
with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        for t in targets:
            if any(t.lower() in str(v).lower() for v in row.values()):
                print(f"system_activity: {row}")

print("=== Checking user_audit_log.csv ===")
with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        for t in targets:
            if any(t.lower() in str(v).lower() for v in row.values()):
                print(f"user_audit_log: {row}")

print("=== Checking evidence files for mentions ===")
for root, dirs, files in os.walk("dataset/evidence"):
    for file in files:
        path = os.path.join(root, file)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for t in targets:
                    if t.lower() in content.lower():
                        print(f"Found {t} in {path}")
        except Exception as e:
            pass
