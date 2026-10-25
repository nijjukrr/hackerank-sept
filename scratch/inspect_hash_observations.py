import csv
import json
import sys
from pathlib import Path

repo_root = Path(".").resolve()
sys.path.insert(0, str(repo_root / "code"))

from evidence_loader import EvidenceLoader
from identity_resolver import IdentityResolver

loader = EvidenceLoader(repo_root / "dataset")
resolver = IdentityResolver(repo_root / "dataset" / "user_identities.csv", repo_root / "dataset" / "user_audit_log.csv")

with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    users = list(csv.DictReader(f))

hashes_to_user = {u["email_hash"]: u for u in users}

matched_users = []
for obs in loader.all_observations:
    d = obs.details
    if isinstance(d, dict):
        eh = d.get("email_hash") or d.get("hash")
        if eh and isinstance(eh, str) and len(eh) == 64:
            matched_u = hashes_to_user.get(eh)
            matched_users.append((obs.system_id, obs.resource_id, obs.evidence_id, matched_u["user_id"] if matched_u else None, eh))

print(f"Total observations with raw 64-char hash: {len(matched_users)}")
print("Sample matched observations:")
for sys_id, res_id, ev_id, uid, eh in matched_users[:15]:
    print(f"  {sys_id} | res: {res_id} | ev: {ev_id} | user: {uid} | hash: {eh[:12]}...")
