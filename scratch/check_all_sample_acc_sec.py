import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    sample_out = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["email"].lower(): r for r in csv.DictReader(f)}

for cid, (stat, steps) in sample_out.items():
    req = sample_reqs.get(cid, {})
    email = req.get("email", "").lower()
    uid = identities.get(email, {}).get("user_id", "")
    acc_steps = [s for s in steps if s["system_id"] == "account_service"]
    sec_steps = [s for s in steps if s["system_id"] == "security_service"]
    acc_ids = [s["resource_id"] for s in acc_steps]
    sec_ids = [s["resource_id"] for s in sec_steps]
    print(f"{cid} | user: {uid} | email: {email} | stat: {stat} | acc: {acc_ids} | sec: {sec_ids}")
