import csv, json
from datetime import datetime

# Load sample requests
requests = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

# Load worker account delete events
worker_events = []
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['source_system'] == 'deletion_worker' and r['target_system'] == 'account_service' and r['event_type'] == 'DELETE_RECORD':
            worker_events.append(r)

# Load expected sample output
sample_output = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case ID':<8} | {'Reported At':<20} | {'Expected Acc':<12} | {'Matched Activity':<15} | {'Matched Time':<20} | {'Delta (min)'}")
print("-" * 90)

for req in requests:
    cid = req['case_id']
    rep_at = req['reported_at']
    if not rep_at:
        continue
    dt_rep = datetime.fromisoformat(rep_at.replace('Z', '+00:00'))
    
    # Find expected account if any
    exp_acc = None
    for s in sample_output.get(cid, []):
        if s['system_id'] == 'account_service':
            exp_acc = s['resource_id']
            break
            
    # Find worker events within +/- 2 hours of reported_at
    candidates = []
    for ev in worker_events:
        dt_ev = datetime.fromisoformat(ev['event_time'].replace('Z', '+00:00'))
        delta_sec = (dt_rep - dt_ev).total_seconds()
        # Events happen before reported_at (or close to it)
        if 0 <= delta_sec <= 7200:
            candidates.append((delta_sec, ev))
            
    candidates.sort(key=lambda x: x[0])
    
    matched_ev = None
    if candidates:
        matched_ev = candidates[0][1]
        delta_min = candidates[0][0] / 60.0
        print(f"{cid:<8} | {rep_at:<20} | {str(exp_acc):<12} | {matched_ev['resource_id']:<15} | {matched_ev['event_time']:<20} | {delta_min:.1f}")
    else:
        print(f"{cid:<8} | {rep_at:<20} | {str(exp_acc):<12} | {'NONE':<15} | {'N/A':<20} | N/A")
