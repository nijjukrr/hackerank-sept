import csv

with open('output.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cid_num = int(r['case_id'].split('_')[1])
        if 530 <= cid_num <= 545:
            print(f"{r['case_id']}: {r['deletion_status']} -> {r['steps_json']}")
