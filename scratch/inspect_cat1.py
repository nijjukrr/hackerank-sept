import json
import csv

cases = ['case_21', 'case_25', 'case_26', 'case_27', 'case_28']
print("=== SAMPLE DELETION REQUESTS ===")
with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in cases:
            print(f"{r['case_id']}: email={r['email']}, req_at={r['requested_at']}, audit_at={r['audit_at']}")

with open('dataset/evidence/records/service_resource_export_20260915_114455.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

se = data.get('service_exports', {})
for svc, records in se.items():
    print(f"\nService '{svc}': {len(records)} records")
    for rec in records:
        print('  Rec:', json.dumps(rec))
