import os
import re

hash_pattern = re.compile(r'email_hash[\"\'=\s:]+([a-f0-9]{64})')
found_hashes = set()
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            for m in hash_pattern.finditer(content):
                found_hashes.add((f, m.group(1)))
        except Exception:
            pass

print(f'Total occurrences of 64-char email_hash in evidence: {len(found_hashes)}')
for f, h in list(found_hashes)[:10]:
    print(f'  {f}: {h}')
