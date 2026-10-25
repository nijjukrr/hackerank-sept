import sys
from pathlib import Path
sys.path.insert(0, str(Path("code").resolve()))
import csv
import json
from datetime import datetime, timedelta

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = list(csv.DictReader(f))

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

# Map resource_id -> list of deletion_worker activities
worker_acts_by_res = {}
for a in acts:
    if a["source_system"] == "deletion_worker":
        rid = a["resource_id"]
        if rid:
            worker_acts_by_res.setdefault(rid, []).append(a)

from audit_engine import AuditEngine
from models import DeletionRequestCase
from pathlib import Path

engine = AuditEngine(Path("dataset"))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

print("=== Correlating Activity Workflows ===")
for c in sample_cases[20:]:
    cid = c["case_id"]
    case_obj = DeletionRequestCase(**c)
    res = engine.audit_case(case_obj)
    
    known_rids = set(s.resource_id for s in res.steps if s.resource_id)
    t_rids = set(s["resource_id"] for s in truth[cid] if s["resource_id"])
    
    # Find timestamps of activities for known_rids
    linked_act_times = []
    for rid in known_rids:
        for a in worker_acts_by_res.get(rid, []):
            linked_act_times.append(datetime.fromisoformat(a["event_time"].replace("Z", "+00:00")))
            
    if linked_act_times:
        min_t = min(linked_act_times)
        max_t = max(linked_act_times)
        # Search window [min_t - 2h, max_t + 2h]
        window_acts = [
            a for a in acts
            if a["source_system"] == "deletion_worker"
            and (min_t - timedelta(hours=2)) <= datetime.fromisoformat(a["event_time"].replace("Z", "+00:00")) <= (max_t + timedelta(hours=2))
        ]
        
        # Check what account_service and analytics_platform activities are in window
        cand_accs = [a["resource_id"] for a in window_acts if a["target_system"] == "account_service"]
        cand_anals = [a["resource_id"] for a in window_acts if a["target_system"] == "analytics_platform"]
        print(f"\n{cid}: known={known_rids}")
        print(f"  Activity window: {min_t.isoformat()} to {max_t.isoformat()} ({len(window_acts)} worker acts)")
        print(f"  Candidate accounts in window: {cand_accs}")
        print(f"  Candidate analytics in window: {cand_anals}")
        print(f"  Truth missing: {t_rids - known_rids}")
