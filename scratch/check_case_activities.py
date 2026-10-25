import csv
from datetime import datetime

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

# Group activities by time window
for req in requests[:10]:
    cid = req['case_id']
    req_at = req['requested_at']
    rep_at = req['reported_at']
    
    # Filter deletion_worker activities between req_at and rep_at
    acts = [
        a for a in activities
        if a['source_system'] == 'deletion_worker'
        and req_at <= a['event_time'] <= rep_at
    ]
    print(f"\n{cid} ({req['email']}) [{req_at} -> {rep_at}]:")
    for a in acts:
        print(f"  act: {a['activity_id']} {a['event_time']} {a['event_type']} {a['target_system']} {a['resource_id']}")
