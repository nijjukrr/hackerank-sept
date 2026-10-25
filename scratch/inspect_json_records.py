import json
import glob

files = [
    "dataset/evidence/records/connector_configurations_20260812.json",
    "dataset/evidence/records/security_audit_ledger_20261001.json",
    "dataset/evidence/records/customer_export_manifest_20260409.json",
    "dataset/evidence/records/customer_analytics_report_20260907.json",
    "dataset/evidence/records/customer_export_jobs_20260914.json"
]

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        recs = data.get("records", [])
        print(f"\n=== {fpath} (total {len(recs)} records) ===")
        if recs:
            print("First 2 records:", json.dumps(recs[:2], indent=2))
