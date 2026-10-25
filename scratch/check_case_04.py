import csv

with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['case_id'] == 'case_04':
            print("case_04 request:", row)

with open('dataset/sample_output.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['case_id'] == 'case_04':
            print("case_04 expected output:", row)

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if '901' in str(row) or 'account_004' in str(row):
            print("system_activity:", row)
