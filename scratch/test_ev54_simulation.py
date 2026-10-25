import csv, json
from pathlib import Path

# Load sample_test_output.csv and change case_04 evidence_id to evidence_54
rows = list(csv.DictReader(open('sample_test_output.csv', encoding='utf-8')))
for r in rows:
    if r['case_id'] == 'case_04':
        steps = json.loads(r['steps_json'])
        for s in steps:
            if s['resource_id'] == 'account_004':
                s['evidence_id'] = 'evidence_54'
        r['steps_json'] = json.dumps(steps)

with open('scratch/sample_sim_output.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['case_id', 'deletion_status', 'steps_json'])
    for r in rows:
        writer.writerow([r['case_id'], r['deletion_status'], r['steps_json']])

# Evaluate with code/evaluation/main.py
import sys
sys.path.insert(0, 'code')
from evaluation.main import evaluate_predictions

print("--- EVALUATION WITH SIMULATED EVIDENCE_54 ON CASE_04 ---")
metrics = evaluate_predictions(Path('scratch/sample_sim_output.csv'), Path('dataset/sample_output.csv'))
