import csv

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        num = int(row['activity_id'].split('_')[1])
        if 3525 <= num <= 3545:
            print(f"{row['activity_id']} | {row['event_time']} | {row['source_system']} -> {row['target_system']} | {row['event_type']} | {row['resource_id']} | {row['details']}")
