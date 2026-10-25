import csv
import json

truth_path = "dataset/sample_output.csv"
preds_path = "sample_test_output.csv"

truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open(truth_path, encoding='utf-8'))}
preds = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(open(preds_path, encoding='utf-8'))}

all_fields = ['step_no', 'phase', 'system_id', 'resource_id', 'operation', 'state', 'evidence_id']

with open('scratch/discrepancies_report.txt', 'w', encoding='utf-8') as out:
    for cid in sorted(truth.keys()):
        t_steps = truth[cid]
        p_steps = preds.get(cid, [])
        if t_steps == p_steps:
            continue
        
        out.write("==============================\n")
        out.write(f"CASE: {cid} (Expected: {len(t_steps)} steps, Pred: {len(p_steps)} steps)\n")
        out.write("==============================\n")
        
        t_tuples = [tuple(s.get(k, '') for k in all_fields) for s in t_steps]
        p_tuples = [tuple(s.get(k, '') for k in all_fields) for s in p_steps]
        
        out.write("--- EXPECTED STEPS ---\n")
        for idx, s in enumerate(t_steps, 1):
            tup = tuple(s.get(k, '') for k in all_fields)
            matched = tup in p_tuples
            out.write(f"  [{idx}] {s.get('phase')} | {s.get('system_id')} | {s.get('resource_id')} | {s.get('operation')} | {s.get('state')} | ev={s.get('evidence_id')} -> in_pred={matched}\n")
            
        out.write("--- PREDICTED STEPS ---\n")
        for idx, s in enumerate(p_steps, 1):
            tup = tuple(s.get(k, '') for k in all_fields)
            matched = tup in t_tuples
            out.write(f"  [{idx}] {s.get('phase')} | {s.get('system_id')} | {s.get('resource_id')} | {s.get('operation')} | {s.get('state')} | ev={s.get('evidence_id')} -> in_truth={matched}\n")
        out.write("\n")

print("Generated scratch/discrepancies_report.txt successfully!")
