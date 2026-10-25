p1 = 'dataset/evidence/logs/application_trace_eu_north_20260302.log'
for line in open(p1, encoding='utf-8', errors='ignore'):
    if '6645' in line:
        print(p1, line.strip())

p2 = 'dataset/evidence/logs/cloud_runtime_export_af_south_20260930.log'
for line in open(p2, encoding='utf-8', errors='ignore'):
    if '5569' in line:
        print(p2, line.strip())

p3 = 'dataset/evidence/logs/resource_lookup_trace_20260926_103856.log'
for line in open(p3, encoding='utf-8', errors='ignore'):
    if '5569' in line:
        print(p3, line.strip())
