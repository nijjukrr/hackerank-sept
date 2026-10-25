import csv, json
from pathlib import Path
from collections import defaultdict

pred_path = Path("sample_test_output.csv")
truth_path = Path("dataset/sample_output.csv")

with pred_path.open("r", encoding="utf-8") as f:
    preds = {r["case_id"]: [json.loads(s) for s in [r["steps_json"]]][0] for r in csv.DictReader(f)}

with truth_path.open("r", encoding="utf-8") as f:
    truth = {r["case_id"]: [json.loads(s) for s in [r["steps_json"]]][0] for r in csv.DictReader(f)}

all_fields = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
core_5_fields = ["phase", "system_id", "resource_id", "operation", "state"]

# Hierarchy levels
# 1. Exact 7-field match
# 2. Same 5 core fields (phase, system_id, resource_id, operation, state)
# 3. Same system_id, resource_id, operation
# 4. Same resource_id and phase
# 5. Missing

alignments = {} # cid -> list of (exp_step, pred_step, tier, diff_fields)
tier_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0} # 5 is missing
extra_predicted = []

semantic_field_mismatches = defaultdict(int)
positional_field_mismatches = defaultdict(int)

total_exp_steps = 0
total_pred_steps = 0

for cid in sorted(truth.keys()):
    t_steps = truth[cid]
    p_steps = preds.get(cid, [])
    total_exp_steps += len(t_steps)
    total_pred_steps += len(p_steps)
    
    # Track used pred step indices
    used_pred_indices = set()
    case_alignments = []
    
    # Pass 1: Exact 7-field match
    for e_idx, es in enumerate(t_steps):
        matched_p_idx = None
        for p_idx, ps in enumerate(p_steps):
            if p_idx in used_pred_indices:
                continue
            if all(es.get(k) == ps.get(k) for k in all_fields):
                matched_p_idx = p_idx
                break
        if matched_p_idx is not None:
            used_pred_indices.add(matched_p_idx)
            case_alignments.append((es, p_steps[matched_p_idx], 1, []))
        else:
            case_alignments.append((es, None, 0, [])) # unresolved
            
    # Pass 2: Same 5 core fields
    for idx, (es, ps, tier, diffs) in enumerate(case_alignments):
        if tier != 0:
            continue
        matched_p_idx = None
        for p_idx, candidate in enumerate(p_steps):
            if p_idx in used_pred_indices:
                continue
            if all(es.get(k) == candidate.get(k) for k in core_5_fields):
                matched_p_idx = p_idx
                break
        if matched_p_idx is not None:
            used_pred_indices.add(matched_p_idx)
            diff = [k for k in all_fields if es.get(k) != p_steps[matched_p_idx].get(k)]
            case_alignments[idx] = (es, p_steps[matched_p_idx], 2, diff)
            
    # Pass 3: Same system_id, resource_id, operation
    for idx, (es, ps, tier, diffs) in enumerate(case_alignments):
        if tier != 0:
            continue
        matched_p_idx = None
        for p_idx, candidate in enumerate(p_steps):
            if p_idx in used_pred_indices:
                continue
            if (es.get("system_id") == candidate.get("system_id") and
                es.get("resource_id") == candidate.get("resource_id") and
                es.get("operation") == candidate.get("operation")):
                matched_p_idx = p_idx
                break
        if matched_p_idx is not None:
            used_pred_indices.add(matched_p_idx)
            diff = [k for k in all_fields if es.get(k) != p_steps[matched_p_idx].get(k)]
            case_alignments[idx] = (es, p_steps[matched_p_idx], 3, diff)

    # Pass 4: Same resource_id and phase
    for idx, (es, ps, tier, diffs) in enumerate(case_alignments):
        if tier != 0:
            continue
        matched_p_idx = None
        for p_idx, candidate in enumerate(p_steps):
            if p_idx in used_pred_indices:
                continue
            if (es.get("resource_id") == candidate.get("resource_id") and
                es.get("phase") == candidate.get("phase")):
                matched_p_idx = p_idx
                break
        if matched_p_idx is not None:
            used_pred_indices.add(matched_p_idx)
            diff = [k for k in all_fields if es.get(k) != p_steps[matched_p_idx].get(k)]
            case_alignments[idx] = (es, p_steps[matched_p_idx], 4, diff)

    # Pass 5: Remaining unresolved are Tier 5 (Missing)
    for idx, (es, ps, tier, diffs) in enumerate(case_alignments):
        if tier == 0:
            case_alignments[idx] = (es, None, 5, all_fields[:])
            
    # Check for Extra predicted steps
    for p_idx, ps in enumerate(p_steps):
        if p_idx not in used_pred_indices:
            extra_predicted.append((cid, ps))
            
    alignments[cid] = case_alignments

# Collect tier counts and semantic field diffs
for cid, c_align in alignments.items():
    for es, ps, tier, diffs in c_align:
        tier_counts[tier] += 1
        if ps is not None:
            for d in diffs:
                semantic_field_mismatches[d] += 1
        else:
            # missing step: all 7 fields missing
            for f in all_fields:
                semantic_field_mismatches[f"missing_{f}"] += 1

# Collect positional field diffs (from official evaluator logic)
for cid in sorted(truth.keys()):
    t_steps = truth[cid]
    p_steps = preds.get(cid, [])
    for idx in range(max(len(t_steps), len(p_steps))):
        if idx >= len(t_steps):
            # extra step
            continue
        if idx >= len(p_steps):
            # missing step positionally
            for f in all_fields:
                positional_field_mismatches[f] += 1
            continue
        ts = t_steps[idx]
        ps = p_steps[idx]
        for f in all_fields:
            if ts.get(f) != ps.get(f):
                positional_field_mismatches[f] += 1

print("================================================================================")
print("PHASE 2 & 3: EVALUATION & STEP ALIGNMENT ANALYSIS")
print("================================================================================")
print(f"Total Public Cases: {len(truth)}")
print(f"Total Expected Steps: {total_exp_steps}")
print(f"Total Expected Field Cells: {total_exp_steps * 7}")
print(f"Total Predicted Steps: {total_pred_steps}")
print(f"\n--- 5-Tier Semantic Alignment Breakdown ---")
print(f"Tier 1 (Exact 7-Field Tuple Match):               {tier_counts[1]:>3} / {total_exp_steps} ({tier_counts[1]/total_exp_steps*100:.2f}%)")
print(f"Tier 2 (Same 5 Core Fields, StepNo/Ev Differ):    {tier_counts[2]:>3} / {total_exp_steps} ({tier_counts[2]/total_exp_steps*100:.2f}%)")
print(f"Tier 3 (Same Sys/Res/Op, Phase/State/Ev Differ):  {tier_counts[3]:>3} / {total_exp_steps} ({tier_counts[3]/total_exp_steps*100:.2f}%)")
print(f"Tier 4 (Same Res/Phase, Op/State Differ):         {tier_counts[4]:>3} / {total_exp_steps} ({tier_counts[4]/total_exp_steps*100:.2f}%)")
print(f"Tier 5 (Truly Missing Counterpart):               {tier_counts[5]:>3} / {total_exp_steps} ({tier_counts[5]/total_exp_steps*100:.2f}%)")
print(f"Extra Predicted Steps (No Expected Counterpart):  {len(extra_predicted):>3}")

print(f"\n--- Positional Field Mismatches (Evaluator's Raw View) ---")
for f in all_fields:
    print(f"  {f:<15}: {positional_field_mismatches[f]:>3} mismatches (Match: {total_exp_steps - positional_field_mismatches[f]}/{total_exp_steps})")
total_pos_matched = sum(total_exp_steps - positional_field_mismatches[f] for f in all_fields)
print(f"Total Positional Matched Field Cells: {total_pos_matched} / {total_exp_steps * 7} ({total_pos_matched / (total_exp_steps * 7) * 100:.2f}%)")

print(f"\n--- Semantic 1-to-1 Step-Level Field Differences (Matched Steps: Tier 1-4 = {sum(tier_counts[t] for t in [1,2,3,4])}) ---")
for f in all_fields:
    print(f"  {f:<15}: {semantic_field_mismatches[f]:>3} differing fields among identified counterpart steps")

with open("scratch/semantic_alignment_details.txt", "w", encoding="utf-8") as out:
    out.write("=== SEMANTIC 1-TO-1 ALIGNMENT DETAILS ===\n\n")
    for cid in sorted(alignments.keys()):
        out.write(f"--- Case: {cid} ---\n")
        for es, ps, tier, diffs in alignments[cid]:
            out.write(f"  Expected Step {es['step_no']}: ({es['phase']}, {es['system_id']}, {es['resource_id']}, {es['operation']}, {es['state']}, '{es['evidence_id']}')\n")
            if ps is not None:
                out.write(f"    -> Tier {tier} Matched Pred Step {ps['step_no']}: ({ps['phase']}, {ps['system_id']}, {ps['resource_id']}, {ps['operation']}, {ps['state']}, '{ps['evidence_id']}')\n")
                if diffs:
                    out.write(f"       Differing Fields: {diffs}\n")
            else:
                out.write(f"    -> Tier 5 MISSING (No predicted counterpart found)\n")
        out.write("\n")

print("\nDetailed alignment output saved to scratch/semantic_alignment_details.txt")
