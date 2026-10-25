import json
import glob

accounts_to_find = {
    "account_3136": "user_25",
    "account_3866": "user_27",
    "account_5334": "user_24",
    "account_5482": "user_28",
    "account_5684": "user_26",
    "account_6440": "user_21",
    "account_4857": "user_541",
    "account_8858": "user_542",
    "account_7012": "user_29",
    "account_4163": "user_30",
}

found = {}
for fpath in glob.glob("dataset/evidence/records/*.json"):
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        
        # Check snapshots
        for s in d.get("snapshots", []):
            for r in s.get("records", []):
                rid = r.get("resource_id")
                if rid in accounts_to_find:
                    uref = r.get("customer_reference") or r.get("user_id") or r.get("subject_reference")
                    em = r.get("email")
                    found[rid] = (fpath, uref, em)
    except Exception:
        pass

for acc, expected_u in accounts_to_find.items():
    if acc in found:
        print(f"FOUND {acc} -> user={found[acc][1]}, email={found[acc][2]} in {found[acc][0]}")
    else:
        print(f"NOT FOUND in snapshot records: {acc} (expected {expected_u})")
