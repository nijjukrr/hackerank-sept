import csv

cases = ['case_21', 'case_25', 'case_26', 'case_27', 'case_28']

with open('dataset/sample_deletion_requests.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['case_id'] in cases:
            print(f"{row['case_id']}: email={row['email']}, requested_at={row['requested_at']}, reported_at={row['reported_at']}, audit_at={row['audit_at']}")
