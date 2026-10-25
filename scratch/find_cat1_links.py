import csv
import json

cases = {
    'case_21': {'email': 'amara-okeke@proton.me', 'acc': 'account_6440', 'ana': 'analytics_5335'},
    'case_25': {'email': 's.yoon04@gmail.com', 'acc': 'account_3136', 'ana': 'analytics_1895'},
    'case_26': {'email': 'almeida.mariana@gmail.com', 'acc': 'account_5684', 'ana': 'analytics_4566'},
    'case_27': {'email': 'ananya-nair@gmail.com', 'acc': 'account_3866', 'ana': 'analytics_4574'},
    'case_28': {'email': 'smartinez6461@gmail.com', 'acc': 'account_5482', 'ana': 'analytics_6077'},
}

# Find user_id for each email
user_ids = {}
with open('dataset/user_identities.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        for cid, info in cases.items():
            if r['email'] == info['email']:
                user_ids[cid] = r['user_id']
                info['user_id'] = r['user_id']
                info['phone'] = r['phone']
                info['email_hash'] = r['email_hash']

print("Identities for 5 cases:")
for cid, info in cases.items():
    print(f"  {cid}: user_id={info.get('user_id')}, email={info['email']}, acc={info['acc']}, ana={info['ana']}")

print("\nSearching system_activity.csv for user_id, email, acc, or ana:")
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        for cid, info in cases.items():
            u_match = info.get('user_id') and info['user_id'] in r['details']
            e_match = info['email'] in r['details']
            a_match = r['resource_id'] == info['acc'] or r['resource_id'] == info['ana']
            if u_match or e_match or a_match:
                print(f"[{cid}] Activity {r['activity_id']} ({r['event_time']}): res={r['resource_id']}, type={r['event_type']}, res_stat={r['reported_result']}, details={r['details']}")
