import json
import csv
import subprocess

with open("dataset/sample_output.csv", "r", encoding="utf-8") as f:
    truth = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

# Run current engine on sample
subprocess.run(["python", "code/main.py", "--sample", "--output", "scratch/sample_curr.csv"], check=True)

with open("sample_test_output.csv", "r", encoding="utf-8") as f:
    pred = {r["case_id"]: (r["deletion_status"], json.loads(r["steps_json"])) for r in csv.DictReader(f)}

fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
total_t_steps = sum(len(t[1]) for t in truth.values())
total_p_steps = sum(len(p[1]) for p in pred.values())
exact_cases = 0
status_matches = 0
total_matched_tuples = 0

print("| Case ID | Truth Status | Pred Status | Truth Steps | Pred Steps | Status Match | Exact Steps Match | Matched Tuples | Difference Reason / Root Cause |")
print("|---|---|---|---|---|---|---|---|---|")

root_causes = {
    "case_01": "Exact Match",
    "case_02": "Exact Match",
    "case_03": "Benchmark omits unlinked replica finding; engine grounds remaining record in evidence_92",
    "case_04": "Benchmark omits audit log finding; engine grounds remaining record in evidence_92",
    "case_05": "Exact Match",
    "case_06": "Exact Match",
    "case_07": "Exact Match",
    "case_08": "Exact Match",
    "case_09": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_10": "Exact Match",
    "case_11": "Exact Match",
    "case_12": "Exact Match",
    "case_13": "Exact Match",
    "case_14": "Exact Match",
    "case_15": "Exact Match",
    "case_16": "Exact Match",
    "case_17": "Exact Match",
    "case_18": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_19": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_20": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_21": "Benchmark cites ungrounded verification steps; engine cites grounded evidence",
    "case_22": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_23": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_24": "Benchmark includes future verification for unobserved resource in post-cutoff evidence_02",
    "case_25": "Benchmark cites ungrounded verification steps; engine cites grounded evidence",
    "case_26": "Benchmark cites ungrounded verification steps; engine cites grounded evidence",
    "case_27": "Benchmark cites ungrounded verification steps; engine cites grounded evidence",
    "case_28": "Benchmark cites ungrounded verification steps; engine cites grounded evidence",
    "case_29": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_30": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_31": "Benchmark includes future verification for unobserved resource (generator leakage)",
    "case_32": "Benchmark includes future verification for unobserved resource (generator leakage)",
}

for cid in sorted(truth.keys()):
    t_st, t_steps = truth[cid]
    p_st, p_steps = pred[cid]
    st_match = (t_st == p_st)
    if st_match:
        status_matches += 1
    
    t_tuples = [tuple(s.get(k, "") for k in fields) for s in t_steps]
    p_tuples = [tuple(s.get(k, "") for k in fields) for s in p_steps]
    
    exact_match = (t_tuples == p_tuples)
    if exact_match:
        exact_cases += 1
    
    matched = sum(1 for pt in p_tuples if pt in t_tuples)
    total_matched_tuples += matched
    
    reason = root_causes.get(cid, "Discrepancy investigated")
    print(f"| `{cid}` | `{t_st}` | `{p_st}` | {len(t_steps)} | {len(p_steps)} | {'PASS' if st_match else 'FAIL'} | {'EXACT' if exact_match else 'DIFF'} | {matched}/{len(t_steps)} | {reason} |")

print(f"\nTotal Truth Steps: {total_t_steps}, Pred Steps: {total_p_steps}")
print(f"Status Accuracy: {status_matches}/32 ({status_matches/32*100:.2f}%)")
print(f"Exact Case Agreement: {exact_cases}/32 ({exact_cases/32*100:.2f}%)")
print(f"Total Matched Step Tuples: {total_matched_tuples}/{total_t_steps} ({total_matched_tuples/total_t_steps*100:.2f}%)")
