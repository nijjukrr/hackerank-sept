import csv

analytics_ids = ['analytics_1895', 'analytics_4566', 'analytics_4574', 'analytics_5335', 'analytics_6077']

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['resource_id'] in analytics_ids:
            print(row)
