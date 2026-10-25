import csv
import json

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    cases = list(csv.DictReader(f))

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    expected = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

print("=== Checking Activity Correlation with Expected Steps ===")
for c in cases[20:]:
    cid = c["case_id"]
    req_at = c["requested_at"]
    rep_at = c["reported_at"]
    exp_steps = expected[cid]
    
    # Collect all resource_ids in expected steps
    exp_rids = set(s["resource_id"] for s in exp_steps if s["resource_id"])
    
    # Find all activities in system_activity that mention any of these resource_ids
    matched_acts = [a for a in acts if a["resource_id"] in exp_rids]
    
    print(f"\n{cid} (req: {req_at}, rep: {rep_at}):")
    print(f"  Expected resources ({len(exp_rids)}): {exp_rids}")
    print(f"  Matched activities ({len(matched_acts)}):")
    for a in matched_acts:
        print(f"    act: {a['activity_id']} | time: {a['event_time']} | type: {a['event_type']} | sys: {a['target_system']} | res: {a['resource_id']} | res_res: {a['reported_result']}")
