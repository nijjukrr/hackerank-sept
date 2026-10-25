import csv

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

# Let's inspect all activities where target_system is account_service or resource_id is account_XXXX
# Or where details mention user or email or account
users_to_check = {
    "user_28": "account_5482",
    "user_29": "account_7012",
    "user_30": "account_4163",
    "user_541": "account_4857",
    "user_542": "account_8858"
}

for uid, acc in users_to_check.items():
    print(f"\n=== Inspecting for {uid} ({acc}) ===")
    for a in acts:
        if acc in str(a) or uid in str(a):
            print(f"  {a['activity_id']} | {a['event_time']} | {a['event_type']} | {a['source_system']} -> {a['target_system']} | res: {a['resource_id']} | {a['reported_result']} | {a['details']}")
