import json
import csv

cases = ['case_18', 'case_20', 'case_22', 'case_23', 'case_29', 'case_30', 'case_31', 'case_32']

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('sample_test_output.csv', 'r', encoding='utf-8') as f:
    preds = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

for cid in cases:
    print(f"\n=================== {cid} ===================")
    print("--- TRUTH STEPS ---")
    for s in truth[cid]:
        print(f"  Step {s['step_no']:2d} | {s['phase']:12s} | {s['system_id']:16s} | {s['resource_id']:18s} | {s['operation']:26s} | {s['state']:10s} | ev: '{s['evidence_id']}'")
    print("--- PREDICTED STEPS ---")
    for s in preds.get(cid, []):
        print(f"  Step {s['step_no']:2d} | {s['phase']:12s} | {s['system_id']:16s} | {s['resource_id']:18s} | {s['operation']:26s} | {s['state']:10s} | ev: '{s['evidence_id']}'")
