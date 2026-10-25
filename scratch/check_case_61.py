import csv

with open("dataset/deletion_requests.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["case_id"] == "case_61":
            print("case_61:", r)
            email = r["email"]

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["email"].lower() == email.lower():
            print("identity for case_61:", r)
