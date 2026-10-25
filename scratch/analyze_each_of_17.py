import csv
import json
from pathlib import Path

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    reqs = {r["case_id"]: r for r in csv.DictReader(f)}

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    manifest = {r["file_id"]: r for r in csv.DictReader(f)}

mismatches = ['case_03', 'case_04', 'case_09', 'case_18', 'case_20', 'case_21', 'case_22', 'case_23', 'case_24', 'case_25', 'case_26', 'case_27', 'case_28', 'case_29', 'case_30', 'case_31', 'case_32']

print(f"Total Mismatches: {len(mismatches)}")
for cid in mismatches:
    req = reqs[cid]
    t_stat, t_steps = truth[cid]
    p_stat, p_steps = pred[cid]
    cutoff = req["audit_at"]
    
    t_tuples = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in t_steps]
    p_tuples = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in p_steps]
    
    missing = [s for s in t_tuples if s not in p_tuples]
    extra = [s for s in p_tuples if s not in t_tuples]
    
    print(f"\n==================== {cid} ====================")
    print(f"Email: {req['email']} | ReqAt: {req['requested_at']} | RepStatus: {req['reported_status']} | RepAt: {req['reported_at']} | Cutoff: {cutoff}")
    print(f"Status: Truth={t_stat} vs Pred={p_stat}")
    print(f"Steps: Truth={len(t_steps)} vs Pred={len(p_steps)}")
    if missing:
        print("  MISSING IN PRED:")
        for m in missing:
            ev_id = m[5]
            ev_meta = manifest.get(ev_id, {})
            ev_time = ev_meta.get("captured_at", "N/A")
            is_post_cutoff = (ev_time > cutoff) if ev_time != "N/A" else "N/A"
            print(f"    - {m[0]} | {m[1]} | {m[2]} | {m[3]} | {m[4]} | ev={ev_id} (cap={ev_time}, post_cutoff={is_post_cutoff})")
    if extra:
        print("  EXTRA IN PRED:")
        for e in extra:
            print(f"    + {e[0]} | {e[1]} | {e[2]} | {e[3]} | {e[4]} | ev={e[5]}")
