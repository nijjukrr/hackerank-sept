p = 'dataset/evidence/logs/resource_lookup_trace_20260926_103856.log'
lines = open(p, encoding='utf-8', errors='ignore').readlines()
for line in lines:
    if 'completed' in line and 'readback_collector' not in line:
        print(line.strip())
