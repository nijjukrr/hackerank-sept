import json
import csv
import copy
from pathlib import Path

# Load sample truth
with open('dataset/sample_output.csv', 'r', encoding='utf-8') as f:
    truth = {r['case_id']: json.loads(r['steps_json']) for r in csv.DictReader(f)}

# Let's inspect what happens to case_23, case_24, case_29, case_30
# if evidence_02 snapshots use snap.get('captured_at') instead of meta.captured_at
import sys
sys.path.insert(0, 'code')

from models import CaseAuditResult, DeletionRequestCase, Step, StepOperation, StepPhase, ResourceState, DeletionStatus
from evidence_loader import EvidenceLoader
from identity_resolver import IdentityResolver
from audit_engine import AuditEngine

dataset_dir = Path("dataset")
loader = EvidenceLoader(dataset_dir)

# Count how many observations in loader have captured_at changed if we use snap.get('captured_at')
print("Total observations before:", len(loader.all_observations))

# Let's see all observations for user_23, user_24, user_29, user_30
for uid in ['user_23', 'user_24', 'user_29', 'user_30']:
    obs_list = loader.resources_by_user.get(uid, [])
    print(f"\nUser {uid} observations currently in loader ({len(obs_list)}):")
    for o in obs_list:
        print(f"  {o.system_id} | {o.resource_id} | {o.data_category} | captured_at={o.captured_at} | ev={o.evidence_id}")
