import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_out = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["email"].lower(): r for r in csv.DictReader(f)}

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    activities = list(csv.DictReader(f))

# Map deletion_worker DELETE_RECORD on account_service to cases
for cid, (stat, steps) in sample_out.items():
    req = sample_reqs[cid]
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    if not acc_steps:
        continue
    expected_accs = list(dict.fromkeys(s["resource_id"] for s in acc_steps))

    # Find matching activities in window [req_at - delta, rep_at]
    matching_acts = [
        a for a in activities
        if a["source_system"] == "deletion_worker"
        and a["target_system"] == "account_service"
        and a["event_type"] == "DELETE_RECORD"
        and req_at <= a["event_time"] <= rep_at
    ]

    matched_accs = [a["resource_id"] for a in matching_acts]
    print(f"{cid} ({req_at} to {rep_at}):")
    print(f"   Expected accs: {expected_accs}")
    print(f"   Activities in window: {matched_accs}")
    for a in matching_acts:
        print(f"       -> {a['activity_id']} {a['event_time']} {a['resource_id']} {a['reported_result']} | {a['details']}")
