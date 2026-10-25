import sys
sys.path.insert(0, "code")
from evidence_loader import EvidenceLoader
from pathlib import Path

el = EvidenceLoader(Path("dataset"))
bad_rids = [o for o in el.all_observations if any(c in o.resource_id for c in ['"', "'", "\\"])]
bad_emails = [o for o in el.all_observations if o.email and any(c in o.email for c in ['"', "'", "\\"])]
bad_users = [o for o in el.all_observations if o.user_id and any(c in o.user_id for c in ['"', "'", "\\"])]

print(f"Total observations: {len(el.all_observations)}")
print(f"Total observations with polluted resource_id: {len(bad_rids)}")
print(f"Total observations with polluted email:       {len(bad_emails)}")
print(f"Total observations with polluted user_id:     {len(bad_users)}")

# Group polluted by evidence_id
polluted_files = set(o.evidence_id for o in bad_rids + bad_emails + bad_users)
print(f"Polluted evidence files ({len(polluted_files)}): {sorted(list(polluted_files))}")
