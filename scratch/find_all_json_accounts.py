import os, json

print("=== CHECKING ALL JSON FILES FOR ACCOUNT RECORDS WITH USER_ID/EMAIL ===")
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.json'):
            p = os.path.join(root, f)
            try:
                data = json.load(open(p, encoding='utf-8'))
                s = json.dumps(data)
                if 'account_' in s:
                    # Look inside data
                    if 'snapshots' in data:
                        for snap in data['snapshots']:
                            for rec in snap.get('records', []):
                                rid = rec.get('resource_id', '')
                                if rid.startswith('account_'):
                                    print(f"{f} snap[{snap.get('captured_at')}] -> {rid} | user={rec.get('customer_reference') or rec.get('user_id')} | email={rec.get('email')}")
            except Exception as e:
                pass
