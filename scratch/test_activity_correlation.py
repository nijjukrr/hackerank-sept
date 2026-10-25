import csv
import json
from collections import defaultdict

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = list(csv.DictReader(f))

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

print(f"Total sample cases: {len(sample_cases)}")

# Let's inspect cases 21 to 32
for c in sample_cases[20:]:
    cid = c["case_id"]
    req_at = c["requested_at"]
    rep_at = c["reported_at"]
    aud_at = c["audit_at"]
    stat = c["reported_status"]
    
    # Expected resources
    exp_steps = expected[cid]
    exp_res = [(s["system_id"], s["resource_id"], s["operation"]) for s in exp_steps]
    
    # Find deletion_worker activities in [req_at, rep_at]
    worker_acts = [
        a for a in acts
        if a["source_system"] == "deletion_worker"
        and req_at <= a["event_time"] <= rep_at
    ]
    
    print(f"\n=== {cid} ({stat}) ===")
    print(f"Window: {req_at} -> {rep_at}")
    print("Expected resources:")
    for er in exp_res:
        print(f"   {er}")
    print(f"Worker activities in window ({len(worker_acts)}):")
    for wa in worker_acts:
        print(f"   {wa['activity_id']} | {wa['event_time']} | {wa['event_type']} | {wa['target_system']}:{wa['resource_id']} | {wa['reported_result']}")
