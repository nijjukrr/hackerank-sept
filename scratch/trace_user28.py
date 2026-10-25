import csv

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

print("=== All activities mentioning user_28 ===")
for a in acts:
    if "user_28" in str(a):
        print(a)

print("\n=== Activities between 2026-08-28 and 2026-08-31 for deletion_worker ===")
for a in acts:
    if a["source_system"] == "deletion_worker" and "2026-08-28" <= a["event_time"] <= "2026-08-31":
        print(f"{a['activity_id']} | {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']} | {a['details']}")
