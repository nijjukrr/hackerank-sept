import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        steps = json.loads(row["steps_json"])
        for s in steps:
            if "account_" in s.get("resource_id", ""):
                print(f"Sample Case: {row['case_id']}, Resource: {s['resource_id']}, Op: {s['operation']}, Ev: {s['evidence_id']}")
