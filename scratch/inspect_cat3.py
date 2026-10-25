import csv
import json

cat3_cases = ['case_09', 'case_23', 'case_24', 'case_29', 'case_30']

print("=== CATEGORY 3 CASES: AUDIT_AT & EVIDENCE ===")
with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in cat3_cases:
            print(f"{r['case_id']}: email={r['email']}, req_at={r['requested_at']}, audit_at={r['audit_at']}")

with open('dataset/evidence_files.csv', 'r', encoding='utf-8') as f:
    manifest = {r['file_id']: r for r in csv.DictReader(f)}

print("\nManifest capture times for key evidence files:")
for ev_id in ['evidence_02', 'evidence_06', 'evidence_53', 'evidence_92']:
    print(f"  {ev_id}: path={manifest[ev_id]['file_path']}, captured_at={manifest[ev_id]['captured_at']}")
