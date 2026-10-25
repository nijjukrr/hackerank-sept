import csv

targets = {
    'account_6440': 'case_21', 'account_3136': 'case_25', 'account_5684': 'case_26', 
    'account_3866': 'case_27', 'account_5482': 'case_28',
    'analytics_5335': 'case_21', 'analytics_1895': 'case_25', 'analytics_4566': 'case_26',
    'analytics_4574': 'case_27', 'analytics_6077': 'case_28',
    'support_4715': 'case_26', 'data_flow_6244': 'case_26', 'backup_3120': 'case_26',
    'support_4707': 'case_27', 'data_flow_2295': 'case_27', 'backup_5970': 'case_27',
    'support_2351': 'case_28', 'data_flow_2337': 'case_28', 'backup_838': 'case_28',
}

print("=== SEARCHING system_activity.csv ===")
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for t, cid in targets.items():
            if t == row['resource_id'] or t in row['details']:
                print(f"{cid} | {t} | act={row['activity_id']} | src={row['source_system']} | tgt={row['target_system']} | ev_type={row['event_type']} | ts={row['event_time']} | det={row['details']}")
