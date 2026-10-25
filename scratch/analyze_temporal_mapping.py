import csv
from datetime import datetime

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = list(csv.DictReader(f))

with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    eval_cases = list(csv.DictReader(f))

all_cases = sample_cases + eval_cases

with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
    acts = list(csv.DictReader(f))

# Filter deletion worker activities targeting account_service with DELETE_RECORD
acc_acts = [
    a for a in acts
    if a["source_system"] == "deletion_worker"
    and a["target_system"] == "account_service"
    and a["event_type"] == "DELETE_RECORD"
]

print(f"Total cases: {len(all_cases)} (sample: {len(sample_cases)}, eval: {len(eval_cases)})")
print(f"Total account_service DELETE_RECORD activities: {len(acc_acts)}")

# Let's see if each case has a unique or closest activity before reported_at
matches = []
for c in all_cases:
    cid = c["case_id"]
    req_at = c["requested_at"]
    rep_at = c["reported_at"]
    
    # candidate activities in [req_at, rep_at]
    cands = [a for a in acc_acts if req_at <= a["event_time"] <= rep_at]
    matches.append((cid, len(cands), cands))

count_0 = sum(1 for cid, n, _ in matches if n == 0)
count_1 = sum(1 for cid, n, _ in matches if n == 1)
count_more = sum(1 for cid, n, _ in matches if n > 1)

print(f"Cases with 0 matching activities in [req_at, rep_at]: {count_0}")
print(f"Cases with 1 matching activity in [req_at, rep_at]: {count_1}")
print(f"Cases with >1 matching activities in [req_at, rep_at]: {count_more}")

# For the 32 sample cases, print the counts
print("\n--- Sample cases (1-32) ---")
for cid, n, cands in matches[:32]:
    print(f"{cid}: {n} candidate account activities: {[a['resource_id'] for a in cands]}")
