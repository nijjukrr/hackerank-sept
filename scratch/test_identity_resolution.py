from pathlib import Path
import sys

sys.path.insert(0, "code")
from identity_resolver import IdentityResolver

resolver = IdentityResolver(
    Path("dataset/user_identities.csv"),
    Path("dataset/user_audit_log.csv")
)

print(f"Total resolved users: {len(resolver.by_user_id)}")
print(f"Total indexed emails: {len(resolver.by_email)}")
print(f"Total indexed phones: {len(resolver.by_phone)}")
print(f"Total indexed hashes: {len(resolver.by_hash)}")

# Test 1: Historical email resolution
# Find a user with historical email change in user_audit_log.csv
import csv
historical_email_cases = []
with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["field_name"] == "email" and row["old_value"]:
            historical_email_cases.append((row["user_id"], row["old_value"], row["new_value"]))

print(f"\nHistorical email changes in audit log: {len(historical_email_cases)}")
success_count = 0
for uid, old_email, new_email in historical_email_cases:
    resolved_old = resolver.resolve_email(old_email)
    resolved_new = resolver.resolve_email(new_email)
    assert resolved_old is not None, f"Failed to resolve old email {old_email}"
    assert resolved_new is not None, f"Failed to resolve new email {new_email}"
    assert resolved_old.user_id == uid, f"Old email {old_email} resolved to {resolved_old.user_id}, expected {uid}"
    assert resolved_new.user_id == uid, f"New email {new_email} resolved to {resolved_new.user_id}, expected {uid}"
    success_count += 1
print(f"All {success_count} historical email changes correctly resolved to same user_id!")

# Test 2: Name collision test (Ensure names never cause false merges)
# Check multiple users with same or similar first/last name
names = {}
for u in resolver.by_user_id.values():
    first = u.name.split()[0] if u.name else ""
    if first:
        names.setdefault(first, []).append(u)

collisions = {k: v for k, v in names.items() if len(v) > 1}
print(f"\nCommon first names shared across distinct accounts: {len(collisions)}")
sample_first = list(collisions.keys())[0]
sample_users = collisions[sample_first]
print(f"Example: name '{sample_first}' shared by {len(sample_users)} distinct users:")
for u in sample_users[:3]:
    print(f"  {u.user_id}: {u.name} | {u.current_email}")

for u in sample_users:
    assert resolver.resolve_email(u.current_email).user_id == u.user_id
print("Verified: No cross-contamination across users sharing identical names!")

# Test 3: Partial string / substring rejection
assert resolver.resolve_email("fontaine") is None
assert resolver.resolve_email("@yahoo.com") is None
assert resolver.resolve_user_id("user") is None
print("Verified: Substring and domain-only lookups are strictly rejected!")
