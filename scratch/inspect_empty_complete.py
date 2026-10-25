import csv
import json

with open("output.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

empty_complete = [r for r in rows if r["deletion_status"] == "COMPLETE" and r["steps_json"] == "[]"]
print(f"Total empty complete: {len(empty_complete)}")

# Load deletion requests
with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    del_reqs = {r["case_id"]: r for r in csv.DictReader(f)}

# Load user identities
with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    identities = {r["email"].lower(): r for r in csv.DictReader(f)}

print("\nSample 10 empty complete cases:")
for r in empty_complete[:10]:
    cid = r["case_id"]
    req = del_reqs.get(cid, {})
    email = req.get("email", "").lower()
    ident = identities.get(email, {})
    print(f"Case: {cid}, Email: {email}, Reported: {req.get('reported_status')}, AuditAt: {req.get('audit_at')}, UserID: {ident.get('user_id')}")
