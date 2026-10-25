import csv
import json
import glob
import os

cases_to_check = {
    "case_28": ["account_5482", "audit_record_9265"],
    "case_29": ["account_7012", "audit_record_3954"],
    "case_30": ["account_4163", "audit_record_1707"],
    "case_31": ["account_6440", "audit_record_8116"],
    "case_32": ["account_8858", "audit_record_7068", "tombstone_9178"]
}

print("=== SEARCHING IN DATASET CSVs ===")
for csv_file in glob.glob("dataset/*.csv"):
    with open(csv_file, "r", encoding="utf-8") as f:
        text = f.read()
    for cid, ids in cases_to_check.items():
        for res_id in ids:
            if res_id in text:
                print(f"[{cid}] {res_id} found in {csv_file}")

print("\n=== SEARCHING IN EVIDENCE FILES ===")
with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    ev_files = list(csv.DictReader(f))

for ef in ev_files:
    fpath = os.path.join("dataset", ef["file_path"])
    fid = ef["file_id"]
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for cid, ids in cases_to_check.items():
            for res_id in ids:
                if res_id in content:
                    print(f"[{cid}] {res_id} found in evidence {fid} ({ef['file_path']}) captured_at={ef['captured_at']}")
    except Exception as e:
        pass
