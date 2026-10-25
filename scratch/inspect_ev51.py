import json

with open('dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Keys in evidence_51:", list(data.keys()))
for k, v in data.items():
    if isinstance(v, list):
        print(f"Key '{k}': {len(v)} items")
        for item in v:
            text = json.dumps(item)
            if any(term in text for term in ['user_31', 'user_32', '4857', '8858', '6909', '7068', '440', '9178']):
                print(f"  [{k}] item:", text)
