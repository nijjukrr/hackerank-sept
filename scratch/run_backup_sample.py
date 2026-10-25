
import sys, csv, json
from pathlib import Path
sys.path.insert(0, r'C:\Users\nijju\.gemini\antigravity-ide\scratch\test-orchestrate-workspace\scratch\backup_prompt07\code')
from audit_engine import AuditEngine
from models import DeletionRequestCase

engine = AuditEngine(Path('dataset'))
cases = []
with open('dataset/sample_deletion_requests.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cases.append(DeletionRequestCase(**r))
cases.sort(key=lambda c: c.case_id)

out = {}
for c in cases:
    res = engine.audit_case(c)
    out[c.case_id] = {'status': res.deletion_status, 'steps': [s.to_dict() for s in res.steps]}

with open('scratch/backup_sample_preds.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)
