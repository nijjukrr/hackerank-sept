import sys
sys.path.insert(0, "code")
from evidence_loader import EvidenceLoader
from pathlib import Path

el = EvidenceLoader(Path("dataset"))
quoted_obs = [o for o in el.all_observations if '"' in o.resource_id or '\\' in o.resource_id]
print(f"Total observations with quotes or backslashes in resource_id: {len(quoted_obs)}")

for o in quoted_obs[:10]:
    print(f"File: {o.evidence_id} | res_id: {repr(o.resource_id)} | sys: {o.system_id} | cat: {o.data_category} | user: {o.user_id} | email: {o.email}")
