import sys
sys.path.insert(0, "code")
from evidence_loader import EvidenceLoader

from pathlib import Path
loader = EvidenceLoader(Path("dataset"))
obs_46 = [o for o in loader.all_observations if o.evidence_id == "evidence_46"]
print(f"Observations from evidence_46: {len(obs_46)}")
for o in obs_46:
    print(o.system_id, o.resource_id, o.state, o.user_id, o.email)
