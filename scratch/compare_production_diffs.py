import csv
import json

prev_rows = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(open("scratch/backup_prompt11f/output.csv", encoding="utf-8"))}
new_rows = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(open("output.csv", encoding="utf-8"))}

diffs = []
for cid in sorted(new_rows.keys()):
    old_status, old_steps = prev_rows[cid]
    new_status, new_steps = new_rows[cid]
    if old_status != new_status or old_steps != new_steps:
        diffs.append((cid, old_status, new_status, old_steps, new_steps))

print(f"Total changed cases between backup_prompt11f/output.csv and new output.csv: {len(diffs)}")
for cid, old_s, new_s, old_st, new_st in diffs:
    print(f"\n==================== {cid} ====================")
    print(f"Status: {old_s} -> {new_s}")
    print(f"Step Count: {len(old_st)} -> {len(new_st)}")
    
    # What was added/removed?
    old_tuples = {(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in old_st}
    new_tuples = {(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in new_st}
    
    added = [s for s in new_st if (s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) not in old_tuples]
    removed = [s for s in old_st if (s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) not in new_tuples]
    
    print(f"Added steps ({len(added)}):")
    for s in added:
        print(f"  + [{s['phase']}] {s['system_id']}:{s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
    print(f"Removed steps ({len(removed)}):")
    for s in removed:
        print(f"  - [{s['phase']}] {s['system_id']}:{s['resource_id']} {s['operation']} {s['state']} ev={s['evidence_id']}")
