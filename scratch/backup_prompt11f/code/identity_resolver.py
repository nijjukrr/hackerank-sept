"""Identity resolution engine across current snapshots and historical audit logs."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Set

from models import SubjectIdentity


class IdentityResolver:
    """Resolves current and historical user identities, emails, phones, and email hashes."""

    def __init__(self, identities_path: Path, audit_log_path: Path):
        self.identities_path = identities_path
        self.audit_log_path = audit_log_path
        self.by_user_id: Dict[str, SubjectIdentity] = {}
        self.by_email: Dict[str, SubjectIdentity] = {}
        self.by_phone: Dict[str, SubjectIdentity] = {}
        self.by_hash: Dict[str, SubjectIdentity] = {}
        self._load()

    def _load(self) -> None:
        user_records: Dict[str, dict] = {}
        with self.identities_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row["user_id"]
                user_records[uid] = {
                    "user_id": uid,
                    "name": row["name"],
                    "current_email": row["email"],
                    "emails": {row["email"]} if row["email"] else set(),
                    "phones": {row["phone"]} if row["phone"] else set(),
                    "hashes": {row["email_hash"]} if row["email_hash"] else set(),
                }

        # Process audit log for historical changes
        if self.audit_log_path.exists():
            with self.audit_log_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    uid = row["user_id"]
                    if uid not in user_records:
                        user_records[uid] = {
                            "user_id": uid,
                            "name": "",
                            "current_email": "",
                            "emails": set(),
                            "phones": set(),
                            "hashes": set(),
                        }
                    field_name = row["field_name"]
                    old_val = row["old_value"].strip() if row.get("old_value") else ""
                    new_val = row["new_value"].strip() if row.get("new_value") else ""

                    target_set: Optional[Set[str]] = None
                    if field_name == "email":
                        target_set = user_records[uid]["emails"]
                    elif field_name == "phone":
                        target_set = user_records[uid]["phones"]
                    elif field_name == "email_hash":
                        target_set = user_records[uid]["hashes"]

                    if target_set is not None:
                        if old_val:
                            target_set.add(old_val)
                        if new_val:
                            target_set.add(new_val)

        # Build immutable SubjectIdentity instances and lookup indices
        for uid, data in user_records.items():
            identity = SubjectIdentity(
                user_id=uid,
                name=data["name"],
                current_email=data["current_email"],
                all_emails=tuple(sorted(data["emails"])),
                all_phones=tuple(sorted(data["phones"])),
                all_hashes=tuple(sorted(data["hashes"])),
            )
            self.by_user_id[uid] = identity
            for em in identity.all_emails:
                self.by_email[em.lower()] = identity
            for ph in identity.all_phones:
                self.by_phone[ph] = identity
            for h in identity.all_hashes:
                self.by_hash[h] = identity

    def resolve_email(self, email: str) -> Optional[SubjectIdentity]:
        if not email:
            return None
        return self.by_email.get(email.strip().lower())

    def resolve_user_id(self, user_id: str) -> Optional[SubjectIdentity]:
        if not user_id:
            return None
        return self.by_user_id.get(user_id.strip())

    def is_user_email(self, user_id: str, email: str) -> bool:
        ident = self.by_user_id.get(user_id)
        if not ident or not email:
            return False
        return email.strip().lower() in (e.lower() for e in ident.all_emails)
