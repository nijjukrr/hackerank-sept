import csv
import json
from datetime import datetime

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_out = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    activities = list(csv.DictReader(f))

acc_acts = [
    a for a in activities
    if a["source_system"] == "deletion_worker"
    and a["target_system"] == "account_service"
    and a["event_type"] == "DELETE_RECORD"
]

for cid, (stat, steps) in sample_out.items():
    req = sample_reqs[cid]
    req_at = req["requested_at"]
    rep_at = req["reported_at"]
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    if not acc_steps:
        continue
    exp_acc = acc_steps[0]["resource_id"]
    
    rep_dt = datetime.fromisoformat(rep_at.replace("Z", "+00:00"))
    
    # Check all candidate activities in [req_at, rep_at]
    cands = [a for a in acc_acts if req_at <= a["event_time"] <= rep_at]
    
    # Find matching candidate that equals exp_acc
    matched = [a for a in cands if a["resource_id"] == exp_acc]
    if matched:
        m = matched[0]
        ev_dt = datetime.fromisoformat(m["event_time"].replace("Z", "+00:00"))
        diff_hours = (rep_dt - ev_dt).total_seconds() / 3600.0
        # What is the rank of this activity by closest to reported_at?
        cands_by_diff = sorted(cands, key=lambda a: abs((rep_dt - datetime.fromisoformat(a["event_time"].replace("Z", "+00:00"))).total_seconds()))
        rank = [a["resource_id"] for a in cands_by_diff].index(exp_acc) + 1
        print(f"{cid} | exp: {exp_acc} | diff: {diff_hours:.2f}h | rank: {rank}/{len(cands)}")
    else:
        print(f"{cid} | exp: {exp_acc} | NOT IN CANDS! cands={len(cands)}")
