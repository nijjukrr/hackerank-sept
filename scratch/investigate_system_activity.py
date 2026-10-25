import csv
import json
import sys

def main():
    with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
        identities = {r["email"].lower(): r for r in csv.DictReader(f)}

    with open("dataset/system_activity.csv", "r", encoding="utf-8") as f:
        activities = list(csv.DictReader(f))

    with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
        expected = {r["case_id"]: json.loads(r["steps_json"]) for r in csv.DictReader(f)}

    print(f"Loaded {len(cases)} cases, {len(activities)} activities.")

    # Let's inspect cases 25 to 32
    for c in cases[24:]:
        cid = c["case_id"]
        email = c["email"].lower()
        ident = identities.get(email, {})
        uid = ident.get("user_id", "")
        req_at = c["requested_at"]
        rep_at = c["reported_at"]
        aud_at = c["audit_at"]

        exp_steps = expected.get(cid, [])
        exp_resources = [(s.get("system_id"), s.get("resource_id"), s.get("operation"), s.get("evidence_id")) for s in exp_steps]

        # Find activities matching uid, email, or in time window [req_at, rep_at]
        matching_acts = []
        for a in activities:
            det = a.get("details", "")
            res_id = a.get("resource_id", "")
            # check if details or resource_id mentions uid or email
            if (uid and uid in det) or (email in det) or (uid and uid in res_id):
                matching_acts.append(a)
            elif req_at <= a["event_time"] <= rep_at and a["source_system"] == "deletion_worker":
                # check if target is account_service
                matching_acts.append(a)

        print(f"\n--- {cid} (User: {uid}, Email: {email}) ---")
        print(f"Requested: {req_at}, Reported: {rep_at}, Audit: {aud_at}")
        print("Expected Steps Resources:")
        for er in exp_resources:
            print(f"  {er}")

        print("Candidate Activities:")
        for ma in matching_acts:
            print(f"  {ma['activity_id']} | {ma['event_time']} | {ma['event_type']} | {ma['source_system']} -> {ma['target_system']} | res: {ma['resource_id']} | res_res: {ma['reported_result']} | det: {ma['details']}")

if __name__ == "__main__":
    main()
