import os
import csv
import json
from pathlib import Path

target_resources = {
    # Cat 1 (5 404 accounts)
    "account_6440": "case_21",
    "account_3136": "case_25",
    "account_5684": "case_26",
    "account_3866": "case_27",
    "account_5482": "case_28",
    # Cat 2 (7 analytics)
    "analytics_9406": "case_03",
    "analytics_901": "case_04",
    "analytics_5335": "case_21",
    "analytics_1895": "case_25",
    "analytics_4566": "case_26",
    "analytics_4574": "case_27",
    "analytics_6077": "case_28",
    # Cat 4 (2 ungrounded security)
    "audit_record_6645": "case_18",
    "audit_record_5569": "case_20",
    # Cat 3 & 5 (accounts & audit records)
    "account_3960": "case_09",
    "audit_record_4902": "case_09",
    "account_5521": "case_18",
    "account_5037": "case_20",
    "account_4990": "case_22",
    "account_410": "case_23",
    "audit_record_4128": "case_23",
    "audit_record_7095": "case_24",
    "account_7012": "case_29",
    "audit_record_3954": "case_29",
    "account_4163": "case_30",
    "audit_record_1707": "case_30",
    "account_4857": "case_31",
    "account_8858": "case_32",
}

print(f"Total target resources: {len(target_resources)}")

dataset_dir = Path("dataset")

# Load evidence files manifest
manifest = {}
with open(dataset_dir / "evidence_files.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        manifest[row["file_id"]] = row

# We will scan:
# 1. system_activity.csv
# 2. user_identities.csv
# 3. user_audit_log.csv
# 4. all files in evidence/

matches = {res: [] for res in target_resources}

def search_text_file(path, label):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                for res in target_resources:
                    if res in line:
                        matches[res].append((label, line_no, line.strip()[:150]))
    except Exception as e:
        pass

# Check CSVs in dataset
for csv_name in ["system_activity.csv", "user_identities.csv", "user_audit_log.csv"]:
    p = dataset_dir / csv_name
    if p.exists():
        search_text_file(p, csv_name)

# Check all evidence files
for ev_id, info in manifest.items():
    p = dataset_dir / info["file_path"]
    if p.exists():
        search_text_file(p, f"{ev_id} ({info['file_path']}, captured={info['captured_at']})")

print("\n=== SEARCH RESULTS ACROSS ENTIRE PARTICIPANT DATASET ===")
for res, case_id in sorted(target_resources.items(), key=lambda x: (x[1], x[0])):
    hits = matches[res]
    print(f"\nResource: {res} (Expected in {case_id}) -> Found in {len(hits)} places:")
    if not hits:
        print("  [NOT FOUND IN ANY PARTICIPANT-VISIBLE FILE]")
    else:
        for loc, line_no, snippet in hits[:5]:
            print(f"  - {loc} [L{line_no}]: {snippet}")
        if len(hits) > 5:
            print(f"  ... and {len(hits) - 5} more")
