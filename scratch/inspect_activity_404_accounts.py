import csv

accounts = ['account_6440', 'account_3136', 'account_5684', 'account_3866', 'account_5482']

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['resource_id'] in accounts:
            print(row)
