import csv
import json

with open("sample_test_output.csv", encoding="utf-8") as f:
    preds = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", encoding="utf-8") as f:
    truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

for cid in ["case_05", "case_06", "case_07", "case_08", "case_12", "case_15"]:
    print(f"\n=== {cid} ===")
    print("TRUTH:")
    for s in truth[cid]:
        print(" ", s)
    print("PRED:")
    for s in preds[cid]:
        print(" ", s)
