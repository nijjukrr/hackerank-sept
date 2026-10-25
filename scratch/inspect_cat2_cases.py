import csv
import json

print("=== CASE_03 & CASE_04 REQUESTS ===")
with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in ['case_03', 'case_04']:
            print(f"{r['case_id']}: email={r['email']}, req_at={r['requested_at']}, audit_at={r['audit_at']}")

print("\n=== EVIDENCE_94 for analytics_9406 ===")
with open('dataset/evidence/logs/resource_lookup_trace_20260926_103856.log', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'analytics_9406' in line:
            print(f"L{idx}: {line.strip()}")

print("\n=== EVIDENCE_56 for analytics_901 ===")
with open('dataset/evidence/records/customer_analytics_report_20260907.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2)[:500])
