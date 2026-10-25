import csv

cases = {
    'case_21': {'email': 'elena.rostova@yandex.ru', 'user_id': 'user_21'},
    'case_25': {'email': 'lucas.silva92@uol.com.br', 'user_id': 'user_25'},
    'case_26': {'email': 'almeida.mariana@gmail.com', 'user_id': 'user_26'},
    'case_27': {'email': 'ananya-nair@gmail.com', 'user_id': 'user_27'},
    'case_28': {'email': 'smartinez6461@gmail.com', 'user_id': 'user_28'},
}

# Let's search system_activity.csv for any mention of these emails or user_ids
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        for cid, info in cases.items():
            if info['user_id'] in str(row) or info['email'] in str(row):
                print(f"Direct match in system_activity: {cid} | {row}")
