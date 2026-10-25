import json
import csv
import subprocess
from pathlib import Path

# Run sample prediction
subprocess.run(['python', 'code/main.py', '--dataset-dir', 'dataset', '--output', 'scratch/sample_pred.csv', '--sample'], check=True)

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('sample_test_output.csv', 'r', encoding='utf-8') as f:
    preds = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

all_fields = ['step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id']
key_fields = ['phase', 'system_id', 'resource_id', 'operation', 'state']

missing_steps = []
for cid in sorted(truth.keys()):
    t_steps = truth[cid]
    p_steps = preds.get(cid, [])
    p_keys = [tuple(s[k] for k in key_fields) for s in p_steps]
    p_tuples = [tuple(s[k] for k in all_fields) for s in p_steps]
    for ts in t_steps:
        t_key = tuple(ts[k] for k in key_fields)
        t_tuple = tuple(ts[k] for k in all_fields)
        if t_tuple not in p_tuples and t_key not in p_keys:
            missing_steps.append((cid, ts))

print(f"Total missing steps: {len(missing_steps)}")
for idx, (cid, s) in enumerate(missing_steps, 1):
    print(f"{idx:2d}. {cid:7s} | step {s['step_no']:2d} | {s['phase']:12s} | {s['system_id']:16s} | {s['resource_id']:18s} | {s['operation']:26s} | {s['state']:10s} | ev: '{s['evidence_id']}'")
