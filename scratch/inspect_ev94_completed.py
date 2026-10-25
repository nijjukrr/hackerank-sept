p = 'dataset/evidence/logs/resource_lookup_trace_20260926_103856.log'
lines = open(p, encoding='utf-8', errors='ignore').readlines()
print(f"Total lines in evidence_94: {len(lines)}")
for line in lines:
    if 'completed' in line:
        print(" ", line.strip()[:140])
