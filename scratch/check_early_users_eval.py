import csv

users = set()
with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        # check user_identities
        pass

identities = {r['email']: r['user_id'] for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}

eval_early_users = []
with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        em = r['email'].strip().lower()
        uid = identities.get(em)
        if uid and uid.startswith('user_'):
            try:
                num = int(uid.split('_')[1])
                if 1 <= num <= 10:
                    eval_early_users.append((r['case_id'], uid, em, r['audit_at']))
            except:
                pass

print(f"Total cases in deletion_requests.csv with user_01..user_10: {len(eval_early_users)}")
for item in eval_early_users:
    print(" ", item)
