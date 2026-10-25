import csv, json

with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/sample_output.csv", encoding="utf-8") as f:
    truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

with open("sample_test_output.csv", encoding="utf-8") as f:
    pred = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

req = sample_reqs["case_11"]
print("case_11 request:", req)

print("\nExpected steps in sample_output.csv:")
for s in truth["case_11"]:
    print(f"  [{s['phase']:12}] {s['operation']:25} | sys={s['system_id']:18} | res={s['resource_id']:18} | st={s['state']:10} | ev={s['evidence_id']}")

print("\nPredicted steps:")
for s in pred["case_11"]:
    print(f"  [{s['phase']:12}] {s['operation']:25} | sys={s['system_id']:18} | res={s['resource_id']:18} | st={s['state']:10} | ev={s['evidence_id']}")
