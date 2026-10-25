import csv, json

manifest = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
print("evidence_54:", manifest.get('evidence_54'))
print("evidence_90:", manifest.get('evidence_90'))

for fid in ['evidence_54', 'evidence_90']:
    p = 'dataset/' + manifest[fid]['file_path']
    print(f"\n--- Checking {fid} ({p}) ---")
    c = open(p, encoding='utf-8', errors='ignore').read()
    if 'account_004' in c:
        print(f"  account_004 FOUND in {fid}")
    else:
        print(f"  account_004 NOT found in {fid}")
