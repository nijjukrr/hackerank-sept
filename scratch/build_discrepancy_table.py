import csv
import json
from pathlib import Path

truth_path = Path("dataset/sample_output.csv")
pred_path = Path("sample_test_output.csv")

with truth_path.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

with pred_path.open("r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

table_rows = []

for cid in sorted(truth.keys()):
    t_status, t_steps = truth[cid]
    p_status, p_steps = pred[cid]

    exact_seq = (t_steps == p_steps)
    exact_case = (t_status == p_status and exact_seq)

    first_mismatch_idx = None
    first_mismatch_field = None
    t_ev = ""
    p_ev = ""

    min_len = min(len(t_steps), len(p_steps))
    for idx in range(min_len):
        ts = t_steps[idx]
        ps = p_steps[idx]
        diffs = []
        for k in ["phase", "operation", "system_id", "resource_id", "state", "evidence_id"]:
            if ts.get(k) != ps.get(k):
                diffs.append(k)
        if diffs:
            first_mismatch_idx = idx + 1
            first_mismatch_field = ", ".join(diffs)
            t_ev = ts.get("evidence_id", "")
            p_ev = ps.get("evidence_id", "")
            break

    if first_mismatch_idx is None and len(t_steps) != len(p_steps):
        first_mismatch_idx = min_len + 1
        first_mismatch_field = "step_count_truncation" if len(p_steps) < len(t_steps) else "extra_steps"
        if len(t_steps) > min_len:
            t_ev = t_steps[min_len].get("evidence_id", "")
        if len(p_steps) > min_len:
            p_ev = p_steps[min_len].get("evidence_id", "")

    # Category determination
    category = "Exact Match"
    if not exact_seq:
        t_res_set = {s["resource_id"] for s in t_steps}
        p_res_set = {s["resource_id"] for s in p_steps}

        missing_res = t_res_set - p_res_set
        extra_res = p_res_set - t_res_set

        if missing_res and extra_res:
            category = f"Missing ({len(missing_res)}) & Extra ({len(extra_res)}) resources"
        elif missing_res:
            category = f"Missing resource discovery ({', '.join(sorted(missing_res))})"
        elif extra_res:
            category = f"Extra resource discovery ({', '.join(sorted(extra_res))})"
        else:
            # All resources match, check operations or ordering
            t_tuples = [(s["phase"], s["operation"], s["system_id"], s["resource_id"], s["state"]) for s in t_steps]
            p_tuples = [(s["phase"], s["operation"], s["system_id"], s["resource_id"], s["state"]) for s in p_steps]
            if sorted(t_tuples) == sorted(p_tuples):
                category = "Step Ordering discrepancy"
            else:
                category = "Operation/State discrepancy on same resources"

    table_rows.append({
        "case_id": cid,
        "expected_status": t_status,
        "predicted_status": p_status,
        "expected_steps": len(t_steps),
        "predicted_steps": len(p_steps),
        "exact_seq": "YES" if exact_seq else "NO",
        "first_mismatch": f"Step {first_mismatch_idx}: {first_mismatch_field}" if first_mismatch_idx else "-",
        "t_ev": t_ev,
        "p_ev": p_ev,
        "category": category,
    })

print("| Case ID | Status (Exp / Pred) | Steps (Exp / Pred) | Match? | First Mismatch | Category |")
print("|---|---|---|---|---|---|")
for r in table_rows:
    print(f"| `{r['case_id']}` | {r['expected_status']} / {r['predicted_status']} | {r['expected_steps']} / {r['predicted_steps']} | **{r['exact_seq']}** | {r['first_mismatch']} | {r['category']} |")
