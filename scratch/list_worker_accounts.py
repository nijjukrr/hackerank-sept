import csv

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    worker_accounts = []
    for r in csv.DictReader(f):
        if r['source_system'] == 'deletion_worker' and r['target_system'] == 'account_service' and r['event_type'] == 'DELETE_RECORD':
            worker_accounts.append((r['activity_id'], r['event_time'], r['resource_id'], r['details']))

print(f"Total deletion_worker account DELETE_RECORD events: {len(worker_accounts)}")
for act_id, t, rid, det in worker_accounts[:30]:
    print(f"  {act_id} | {t} | {rid} | {det}")
