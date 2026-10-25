import csv
import json

sample_truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
requests = {r['case_id']: r for r in csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8'))}

# Load system_activity deletion_worker rows for account_service
acc_activities = []
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['target_system'] == 'account_service' and row['source_system'] == 'deletion_worker':
            acc_activities.append(row)

print(f"Total deletion_worker account_service activities: {len(acc_activities)}")

for cid in sorted(sample_truth.keys()):
    req = requests[cid]
    steps = sample_truth[cid]
    acc_steps = [s for s in steps if s['system_id'] == 'account_service']
    acc_id = acc_steps[0]['resource_id'] if acc_steps else "NONE"
    
    # Check if acc_id is in acc_activities
    matches = [a for a in acc_activities if a['resource_id'] == acc_id]
    match_info = f"Found in activity: {matches[0]['activity_id']} at {matches[0]['event_time']} (res={matches[0]['reported_result']})" if matches else "NOT in activity"
    
    print(f"{cid} (req={req['requested_at']}, rep={req['reported_at']}): {acc_id} -> {match_info}")
