import csv

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['case_id'] in ['case_27', 'case_28', 'case_29', 'case_30']:
            print(r['case_id'], r['email'], r['reported_at'], r['reported_status'], r['audit_at'])
