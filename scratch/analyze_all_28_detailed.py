import json
import csv

with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('sample_test_output.csv', 'r', encoding='utf-8') as f:
    preds = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    reqs = {r['case_id']: r for r in csv.DictReader(f)}

# Load 28 missing steps
with open('scratch/analyze_28_missing.py', 'r', encoding='utf-8') as f:
    pass

import subprocess
res = subprocess.run(['python', 'scratch/analyze_28_missing.py'], capture_output=True, text=True)
lines = res.stdout.splitlines()

# Extract missing steps list
missing_items = []
start = False
for line in lines:
    if "Total missing steps:" in line:
        start = True
        continue
    if start and line.strip() and line[0].isdigit():
        parts = [p.strip() for p in line.split('|')]
        num_case = parts[0].split('.')
        num = int(num_case[0])
        cid = num_case[1].strip()
        step_no = int(parts[1].replace('step', ''))
        phase = parts[2]
        sys_id = parts[3]
        res_id = parts[4]
        op = parts[5]
        state = parts[6]
        ev_id = parts[7].replace('ev:', '').strip().strip("'")
        missing_items.append({
            'num': num,
            'cid': cid,
            'step_no': step_no,
            'phase': phase,
            'sys_id': sys_id,
            'res_id': res_id,
            'op': op,
            'state': state,
            'ev_id': ev_id
        })

print(f"Loaded {len(missing_items)} missing items.")

# For each missing step, check if predicted steps contain something similar for that system
for item in missing_items:
    cid = item['cid']
    p_steps = preds.get(cid, [])
    # Find any predicted step with same system_id or resource_id
    sys_matches = [s for s in p_steps if s['system_id'] == item['sys_id']]
    res_matches = [s for s in p_steps if s['resource_id'] == item['res_id']]
    print(f"\n[{item['num']:2d}] {cid} | Expected Step {item['step_no']}: {item['sys_id']} / {item['res_id']} / {item['op']} / {item['state']} (ev: '{item['ev_id']}')")
    if res_matches:
        print(f"     -> MATCHED RESOURCE in predictions: {res_matches}")
    elif sys_matches:
        print(f"     -> Same system in predictions: {[s['resource_id'] + ' (' + s['operation'] + ')' for s in sys_matches]}")
    else:
        print(f"     -> NO predicted steps for system '{item['sys_id']}' in {cid}")
