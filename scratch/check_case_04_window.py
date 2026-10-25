import csv

with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        t = row['event_time']
        if '2026-08-27T08:30:00Z' <= t <= '2026-08-27T08:55:00Z':
            print(row)
