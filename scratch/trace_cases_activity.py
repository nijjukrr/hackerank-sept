import csv

cases = ['case_30', 'case_29', 'case_22', 'case_23', 'case_32', 'case_09', 'case_18', 'case_20']

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['case_id'] in cases:
            print(f"{row['case_id']}: email={row['email']}, requested_at={row['requested_at']}, reported_at={row['reported_at']}, audit_at={row['audit_at']}")
