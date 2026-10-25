import csv, json

incomplete_cases = ['case_09', 'case_18', 'case_20', 'case_22', 'case_23', 'case_29', 'case_30', 'case_32']

exp_data = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
pred_data = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('sample_test_output.csv', encoding='utf-8'))}

for cid in incomplete_cases:
    exp = exp_data[cid]
    pred = pred_data[cid]
    print(f"\n==================== {cid} ====================")
    print(f"EXPECTED ({len(exp)} steps):")
    for s in exp:
        print(f"  {s['step_no']} | {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev='{s['evidence_id']}'")
    print(f"PREDICTED ({len(pred)} steps):")
    for s in pred:
        print(f"  {s['step_no']} | {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | {s['state']} | ev='{s['evidence_id']}'")
