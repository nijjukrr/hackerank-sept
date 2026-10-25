import csv
import json
from pathlib import Path

# Load sample requests
with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

# Load sample truth
with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

# Load sample pred
with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    sample_pred = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

# Load system activities
with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    activities = list(csv.DictReader(f))

# Filter deletion worker activities
del_worker_acts = [a for a in activities if a["source_system"] == "deletion_worker"]
print(f"Total system activities: {len(activities)}")
print(f"Deletion worker activities: {len(del_worker_acts)}")

# For each case, check activities between requested_at and reported_at
print("\n--- TRACING DELETION WORKER ACTIVITIES PER SAMPLE CASE ---")

for cid, req in sorted(sample_reqs.items()):
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    t_steps = sample_truth[cid]
    p_steps = sample_pred[cid]
    t_res = {s["resource_id"] for s in t_steps}
    p_res = {s["resource_id"] for s in p_steps}
    missing = t_res - p_res

    # Find deletion worker activities around requested_at and reported_at
    # Let's look for activities in window [req_at - 1h, rep_at + 1h]
    window_acts = [a for a in del_worker_acts if req_at <= a["event_time"] <= rep_at]

    if missing:
        print(f"\n[{cid}] ({req['email']}) req={req_at} rep={rep_at} | Missing {len(missing)}: {sorted(missing)}")
        print(f"  Activities in window [requested_at, reported_at] ({len(window_acts)}):")
        for a in window_acts:
            matches_missing = a["resource_id"] in missing
            flag = "==> MISSING RES!" if matches_missing else ""
            print(f"    {a['event_time']} | {a['event_type']:18} | tgt={a['target_system']:18} | res={a['resource_id']} | {a['reported_result']} {flag}")
