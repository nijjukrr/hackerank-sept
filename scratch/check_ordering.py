import csv
import json
from collections import defaultdict

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

finding_systems = []
remediation_systems = []
verification_systems = []

for r in rows:
    steps = json.loads(r["steps_json"])
    for s in steps:
        p = s["phase"]
        sys = s["system_id"]
        op = s["operation"]
        if p == "FINDING":
            finding_systems.append((sys, op))
        elif p == "REMEDIATION":
            remediation_systems.append((sys, op))
        elif p == "VERIFICATION":
            verification_systems.append((sys, op))

print("Total cases in sample:", len(rows))
for r in rows:
    steps = json.loads(r["steps_json"])
    if not steps:
        continue
    cid = r["case_id"]
    stat = r["deletion_status"]
    v_sys = [f"{s['phase']}:{s['system_id']}:{s['operation']}" for s in steps]
    print(f"{cid} ({stat}):")
    for vs in v_sys:
        print(f"   {vs}")
