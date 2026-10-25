import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json
from collections import defaultdict
from datetime import datetime

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = list(csv.DictReader(f))

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    baseline_pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

print("Evaluating trace correlation potential...")

# For each case, what known resources do we have from evidence?
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path("dataset"))

for c in sample_cases[20:]:
    cid = c["case_id"]
    t_stat, t_steps = truth[cid]
    
    # Get current predicted steps
    case_obj = DeletionRequestCase(**c)
    res = engine.audit_case(case_obj)
    p_rids = set(s.resource_id for s in res.steps if s.resource_id)
    t_rids = set(s["resource_id"] for s in t_steps if s["resource_id"])
    
    # Check what activities share resources with p_rids in [req_at, rep_at + 2h]
    req_at = c["requested_at"]
    rep_at = c["reported_at"]
    
    # Filter worker activities in window
    w_acts = [
        a for a in acts
        if a["source_system"] == "deletion_worker"
        and req_at <= a["event_time"] <= "2026-09-20"  # or before audit cutoff
    ]
    
    print(f"\n{cid} (Truth: {t_stat}):")
    print(f"  Truth resources: {t_rids}")
    print(f"  Pred resources:  {p_rids}")
    print(f"  Missing resources: {t_rids - p_rids}")
