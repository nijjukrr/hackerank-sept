from pathlib import Path
import csv
import sys

sys.path.insert(0, "code")
from evidence_loader import EvidenceLoader
from identity_resolver import IdentityResolver

dataset_dir = Path("dataset")
resolver = IdentityResolver(dataset_dir / "user_identities.csv", dataset_dir / "user_audit_log.csv")
loader = EvidenceLoader(dataset_dir)

with open("dataset/sample_deletion_requests.csv", "r", encoding="utf-8") as f:
    sample_cases = {r["case_id"]: r for r in csv.DictReader(f)}

c3 = sample_cases["case_03"]
print("case_03:", c3)
ident3 = resolver.resolve_email(c3["email"])
print("ident3:", ident3)

cutoff3 = c3["audit_at"]
obs3 = [o for o in loader.all_observations if (ident3 and o.user_id == ident3.user_id) or (o.email and o.email.lower() == c3["email"].lower())]
print(f"Observations for case_03 (cutoff {cutoff3}):")
for o in obs3:
    print(f"  sys={o.system_id} res={o.resource_id} cat={o.data_category} st={o.state} ev={o.evidence_id} cap={o.captured_at} (<= cutoff: {o.captured_at <= cutoff3})")

c9 = sample_cases["case_09"]
print("\ncase_09:", c9)
ident9 = resolver.resolve_email(c9["email"])
print("ident9:", ident9)
cutoff9 = c9["audit_at"]
obs9 = [o for o in loader.all_observations if (ident9 and o.user_id == ident9.user_id) or (o.email and o.email.lower() == c9["email"].lower())]
print(f"Observations for case_09 (cutoff {cutoff9}):")
for o in obs9:
    print(f"  sys={o.system_id} res={o.resource_id} cat={o.data_category} st={o.state} ev={o.evidence_id} cap={o.captured_at} (<= cutoff: {o.captured_at <= cutoff9})")
