import csv, json

base_rows = {r['case_id']: r for r in csv.DictReader(open('scratch/backup_prompt11h/output.csv', encoding='utf-8'))}
new_rows = {r['case_id']: r for r in csv.DictReader(open('output.csv', encoding='utf-8'))}

changed_cases = []
for cid in sorted(base_rows.keys()):
    b = base_rows[cid]
    n = new_rows[cid]
    if b['deletion_status'] != n['deletion_status'] or b['steps_json'] != n['steps_json']:
        changed_cases.append((cid, b, n))

print(f"Total Changed Cases across all 518 requests: {len(changed_cases)}")
for cid, b, n in changed_cases:
    print(f"\n--- {cid} ---")
    print(f"Status: {b['deletion_status']} -> {n['deletion_status']}")
    b_steps = json.loads(b['steps_json'])
    n_steps = json.loads(n['steps_json'])
    print(f"Base Steps ({len(b_steps)}):")
    for s in b_steps:
        print(" ", s)
    print(f"New Steps ({len(n_steps)}):")
    for s in n_steps:
        print(" ", s)
