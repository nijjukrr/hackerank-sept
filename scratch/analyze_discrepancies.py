import csv
import json
from pathlib import Path

truth_path = Path("dataset/sample_output.csv")
pred_path = Path("sample_test_output.csv")

with truth_path.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with pred_path.open("r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

cases = sorted(truth.keys())
print(f"Total cases: {len(cases)}")
print("=" * 80)

for cid in cases:
    t_status, t_steps = truth[cid]
    p_status, p_steps = pred[cid]

    exp_res = {(s["system_id"], s["resource_id"], s["phase"]): s for s in t_steps}
    pred_res = {(s["system_id"], s["resource_id"], s["phase"]): s for s in p_steps}

    missing = set(exp_res.keys()) - set(pred_res.keys())
    extra = set(pred_res.keys()) - set(exp_res.keys())
    common = set(exp_res.keys()) & set(pred_res.keys())

    is_exact = (t_steps == p_steps and t_status == p_status)
    if not is_exact:
        print(f"\n--- {cid} (Status: {t_status} vs {p_status}) ---")
        print(f"  Exp count: {len(t_steps)} | Pred count: {len(p_steps)}")
        if missing:
            print(f"  MISSING ({len(missing)}):")
            for sys_id, rid, phase in sorted(missing):
                s = exp_res[(sys_id, rid, phase)]
                print(f"    - {phase:12} | {sys_id:20} | {rid:18} | {s['operation']:26} | {s['state']:10} | ev={s['evidence_id']}")
        if extra:
            print(f"  EXTRA ({len(extra)}):")
            for sys_id, rid, phase in sorted(extra):
                s = pred_res[(sys_id, rid, phase)]
                print(f"    + {phase:12} | {sys_id:20} | {rid:18} | {s['operation']:26} | {s['state']:10} | ev={s['evidence_id']}")
        if common:
            diffs = []
            for k in sorted(common):
                es = exp_res[k]
                ps = pred_res[k]
                if es["operation"] != ps["operation"] or es["state"] != ps["state"] or es["evidence_id"] != ps["evidence_id"]:
                    diffs.append((k, es, ps))
            if diffs:
                print(f"  FIELD MISMATCHES on common resources ({len(diffs)}):")
                for k, es, ps in diffs:
                    print(f"    * {k}:")
                    print(f"       Exp: op={es['operation']}, st={es['state']}, ev='{es['evidence_id']}'")
                    print(f"       Pred: op={ps['operation']}, st={ps['state']}, ev='{ps['evidence_id']}'")
