with open("scratch/semantic_alignment_details.txt", encoding="utf-8") as f:
    lines = f.readlines()

current_case = ""
missing = []
for i, line in enumerate(lines):
    if line.startswith("--- Case:"):
        current_case = line.split()[2]
    if "Tier 5 MISSING" in line:
        exp_line = lines[i-1].strip()
        missing.append((current_case, exp_line))

print(f"Total Tier 5 Missing Steps: {len(missing)}")
for cid, s in missing:
    print(f"  {cid}: {s}")
