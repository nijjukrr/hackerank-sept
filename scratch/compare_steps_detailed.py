import csv
import json

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

total = len(truth)
status_matches = 0
exact_matches = 0
step_count_matches = 0

diff_by_case = {}

for cid in sorted(truth.keys()):
    t_status, t_steps = truth[cid]
    p_status, p_steps = pred[cid]
    
    if t_status == p_status:
        status_matches += 1
    if len(t_steps) == len(p_steps):
        step_count_matches += 1
    if t_status == p_status and t_steps == p_steps:
        exact_matches += 1
    else:
        diff_by_case[cid] = {
            "status": (t_status, p_status),
            "t_len": len(t_steps),
            "p_len": len(p_steps),
            "t_steps": t_steps,
            "p_steps": p_steps
        }

print(f"Sample Cases: {total}")
print(f"Status Agreement: {status_matches}/{total} ({status_matches/total*100:.2f}%)")
print(f"Step Count Agreement: {step_count_matches}/{total} ({step_count_matches/total*100:.2f}%)")
print(f"Exact Agreement: {exact_matches}/{total} ({exact_matches/total*100:.2f}%)")
print(f"Mismatched cases count: {len(diff_by_case)}")

# Let's inspect some sample mismatches
for cid in list(diff_by_case.keys())[:5]:
    d = diff_by_case[cid]
    print(f"\n--- {cid} (Truth: {d['status'][0]} ({d['t_len']} steps) vs Pred: {d['status'][1]} ({d['p_len']} steps)) ---")
    print("Truth:")
    for s in d["t_steps"]:
        print(f"  [{s['phase']}] {s['operation']} | sys={s['system_id']} res={s['resource_id']} st={s['state']} ev={s['evidence_id']}")
    print("Pred:")
    for s in d["p_steps"]:
        print(f"  [{s['phase']}] {s['operation']} | sys={s['system_id']} res={s['resource_id']} st={s['state']} ev={s['evidence_id']}")
