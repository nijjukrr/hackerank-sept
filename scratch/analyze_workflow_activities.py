import csv
from datetime import datetime, timezone

# Load deletion requests
sample_requests = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

# Load system activity
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

print(f"Loaded {len(sample_requests)} sample requests and {len(activities)} activities.")

def parse_iso(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

# For each sample request, find deletion_worker activities between requested_at and reported_at
for req in sample_requests[:10]:
    cid = req['case_id']
    t_req = parse_iso(req['requested_at'])
    t_rep = parse_iso(req['reported_at'])
    
    # Filter deletion_worker activities around t_rep (e.g. within 2 hours before t_rep)
    window_acts = []
    for a in activities:
        if a['source_system'] == 'deletion_worker':
            t_act = parse_iso(a['event_time'])
            if t_req <= t_act <= t_rep:
                window_acts.append(a)
    
    print(f"\n--- {cid} ({req['email']}) req={req['requested_at']} -> rep={req['reported_at']} (status={req['reported_status']}) ---")
    print(f"Activities in [req, rep] window: {len(window_acts)}")
    for a in window_acts:
        print(f"  {a['activity_id']} @ {a['event_time']}: {a['event_type']} -> {a['target_system']}/{a['resource_id']} ({a['reported_result']})")
