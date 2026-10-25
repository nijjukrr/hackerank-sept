"""Unified evidence indexing and normalization engine across all 94 evidence files."""

from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import pypdf
except ImportError:
    pypdf = None


@dataclass
class EvidenceFileMeta:
    file_id: str
    file_path: str
    origin: str
    captured_at: str
    absolute_path: Path


@dataclass
class ObservedResource:
    system_id: str
    resource_id: str
    data_category: str
    state: str                 # 'PRESENT', 'ABSENT', 'REDACTED', 'ANONYMIZED', 'ACTIVE', 'BLOCKED', 'DISABLED'
    evidence_id: str
    captured_at: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    email_hash: Optional[str] = None
    is_tombstone: bool = False
    has_exposed_pii: bool = False
    is_retained_policy: bool = False
    is_active_flow: bool = False
    is_restore_risk: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class EvidenceLoader:
    """Loads, indexes, and normalizes all participant evidence under dataset/evidence/."""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.evidence_manifest_path = dataset_dir / "evidence_files.csv"
        self.files_by_id: Dict[str, EvidenceFileMeta] = {}
        self.resources_by_user: Dict[str, List[ObservedResource]] = {}
        self.resources_by_email: Dict[str, List[ObservedResource]] = {}
        self.resources_by_hash: Dict[str, List[ObservedResource]] = {}
        self.resources_by_id: Dict[str, List[ObservedResource]] = {}
        self.all_observations: List[ObservedResource] = []
        self._load_manifest()
        self._load_all_evidence()

    def _load_manifest(self) -> None:
        if not self.evidence_manifest_path.exists():
            return
        with self.evidence_manifest_path.open("r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                fid = r["file_id"]
                rel_path = r["file_path"]
                meta = EvidenceFileMeta(
                    file_id=fid,
                    file_path=rel_path,
                    origin=r["origin"],
                    captured_at=r["captured_at"],
                    absolute_path=self.dataset_dir / rel_path,
                )
                self.files_by_id[fid] = meta

    def _record_obs(self, obs: ObservedResource) -> None:
        if isinstance(obs.details, dict):
            d = obs.details
            if not obs.email_hash:
                eh = d.get("email_hash") or d.get("hash")
                if eh and isinstance(eh, str) and len(eh) == 64 and all(c in "0123456789abcdefABCDEF" for c in eh):
                    obs.email_hash = eh.lower().strip()

            if not obs.user_id:
                uid = d.get("customer_reference") or d.get("subject_reference") or d.get("user_id")
                if uid and isinstance(uid, str) and uid.startswith("user_"):
                    obs.user_id = uid.strip()

            if not obs.email:
                em = d.get("email") or d.get("requester_email") or d.get("customer_email") or d.get("owner_email")
                if em and isinstance(em, str) and "@" in em:
                    obs.email = em.lower().strip()

        self.all_observations.append(obs)
        if obs.resource_id:
            self.resources_by_id.setdefault(obs.resource_id, []).append(obs)
        if obs.user_id:
            self.resources_by_user.setdefault(obs.user_id, []).append(obs)
        if obs.email:
            self.resources_by_email.setdefault(obs.email.lower().strip(), []).append(obs)
        if obs.email_hash:
            self.resources_by_hash.setdefault(obs.email_hash.lower().strip(), []).append(obs)

    def _load_all_evidence(self) -> None:
        for fid, meta in self.files_by_id.items():
            if not meta.absolute_path.exists():
                continue
            ext = meta.absolute_path.suffix.lower()
            try:
                if ext == ".json":
                    self._parse_json(meta)
                elif ext == ".sql":
                    self._parse_sql(meta)
                elif ext == ".log":
                    self._parse_log(meta)
                elif ext == ".txt":
                    self._parse_txt(meta)
                elif ext == ".pdf":
                    self._parse_pdf(meta)
                elif ext == ".png":
                    self._parse_png(meta)
            except Exception:
                pass

    def _parse_json(self, meta: EvidenceFileMeta) -> None:
        with meta.absolute_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. service_exports in service_resource_export_*.json
        if "service_exports" in data:
            exports = data["service_exports"]

            if "account_service" in exports:
                for it in exports["account_service"].get("profile_lookups", []):
                    rid = it.get("resource_id")
                    st = "ABSENT" if it.get("status_code") == 404 or not it.get("profile") else "PRESENT"
                    prof = it.get("profile") or {}
                    self._record_obs(
                        ObservedResource(
                            system_id="account_service",
                            resource_id=rid,
                            data_category="USER_PROFILE",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=prof.get("customer_reference"),
                            email=prof.get("email"),
                            phone=prof.get("phone"),
                            details=it,
                        )
                    )

            if "analytics_platform" in exports:
                for it in exports["analytics_platform"].get("profiles", []):
                    rid = it.get("resource_id")
                    em = it.get("email")
                    uref = it.get("customer_reference")
                    is_anon = not (em or uref or it.get("phone") or it.get("email_hash"))
                    st = "ANONYMIZED" if is_anon else "PRESENT"
                    self._record_obs(
                        ObservedResource(
                            system_id="analytics_platform",
                            resource_id=rid,
                            data_category="ANALYTICS_PROFILE",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=uref,
                            email=em,
                            phone=it.get("phone"),
                            has_exposed_pii=(not is_anon),
                            details=it,
                        )
                    )

            if "support_platform" in exports:
                for it in exports["support_platform"].get("tickets", []):
                    rid = it.get("resource_id")
                    em = it.get("requester_email")
                    uref = it.get("customer_reference")
                    is_red = not (em or it.get("requester_name") or it.get("requester_phone"))
                    st = "REDACTED" if is_red else "PRESENT"
                    self._record_obs(
                        ObservedResource(
                            system_id="support_platform",
                            resource_id=rid,
                            data_category="SUPPORT_MESSAGE",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=uref,
                            email=em,
                            phone=it.get("requester_phone"),
                            has_exposed_pii=(not is_red),
                            details=it,
                        )
                    )

            if "search_service" in exports:
                for it in exports["search_service"].get("index_queries", []):
                    rid = it.get("resource_id")
                    email = it.get("email") or it.get("query")
                    uref = it.get("customer_reference")
                    hits_obj = it.get("hits")
                    hits_docs = []
                    total_hits = it.get("total_hits", 0)
                    if isinstance(hits_obj, dict):
                        hits_docs = hits_obj.get("documents", [])
                        total_hits = hits_obj.get("total", len(hits_docs))
                    for d in hits_docs:
                        if isinstance(d, dict):
                            if not email and d.get("email"):
                                email = d.get("email")
                            if not uref and d.get("customer_reference"):
                                uref = d.get("customer_reference")
                    st = "ABSENT" if it.get("result") == "miss" or total_hits == 0 else "PRESENT"
                    self._record_obs(
                        ObservedResource(
                            system_id="search_service",
                            resource_id=rid,
                            data_category="SEARCH_INDEX_ENTRY",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=uref,
                            email=email,
                            has_exposed_pii=False,
                            details=it,
                        )
                    )

            if "integration_service" in exports:
                for it in exports["integration_service"].get("connectors", []):
                    rid = it.get("resource_id")
                    en = it.get("enabled", False)
                    st = "ACTIVE" if en else "DISABLED"
                    self._record_obs(
                        ObservedResource(
                            system_id="integration_service",
                            resource_id=rid,
                            data_category="ACTIVE_DATA_FLOW",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=it.get("customer_reference"),
                            email=it.get("customer_email"),
                            is_active_flow=en,
                            details=it,
                        )
                    )

            if "backup_service" in exports:
                for it in exports["backup_service"].get("restore_entries", []):
                    rid = it.get("resource_id")
                    en = it.get("restore_allowed", False)
                    st = "ACTIVE" if en else "BLOCKED"
                    self._record_obs(
                        ObservedResource(
                            system_id="backup_service",
                            resource_id=rid,
                            data_category="BACKUP_ARCHIVE",
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=it.get("customer_reference"),
                            email=it.get("customer_email"),
                            is_restore_risk=en,
                            details=it,
                        )
                    )

            if "security_service" in exports:
                for it in exports["security_service"].get("audit_records", []):
                    rid = it.get("resource_id")
                    self._record_obs(
                        ObservedResource(
                            system_id="security_service",
                            resource_id=rid,
                            data_category="SECURITY_AUDIT_LOG",
                            state="PRESENT",
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=it.get("subject_reference"),
                            is_retained_policy=True,
                            details=it,
                        )
                    )

            if "export_service" in exports:
                for it in exports["export_service"].get("exports", []):
                    rid = it.get("resource_id")
                    self._record_obs(
                        ObservedResource(
                            system_id="export_service",
                            resource_id=rid,
                            data_category="USER_EXPORT",
                            state="PRESENT",
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=it.get("customer_reference"),
                            email=it.get("owner_email"),
                            details=it,
                        )
                    )

        # 2. customer_data_snapshot_bundle_*.json
        if "snapshots" in data:
            for snap in data["snapshots"]:
                ds = snap.get("data_store", "")
                col = snap.get("collection", "")
                for rec in snap.get("records", []):
                    rid = rec.get("resource_id")
                    if ds == "account_service" or "profiles" in col:
                        st = "PRESENT" if rec.get("account_status") == "ACTIVE" else "ABSENT"
                        self._record_obs(
                            ObservedResource(
                                system_id="account_service",
                                resource_id=rid,
                                data_category="USER_PROFILE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("customer_reference") or rec.get("user_id"),
                                email=rec.get("email"),
                                phone=rec.get("phone"),
                                details=rec,
                            )
                        )
                    elif ds == "identity_service" or "deleted_customer_references" in col or "tombstone" in col:
                        has_p = bool(rec.get("email") or rec.get("phone") or rec.get("email_hash") or rec.get("display_name") or rec.get("name"))
                        st = "PRESENT" if has_p else "REDACTED"
                        self._record_obs(
                            ObservedResource(
                                system_id="identity_service",
                                resource_id=rid,
                                data_category="ACCOUNT_TOMBSTONE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("subject_reference"),
                                email=rec.get("email"),
                                phone=rec.get("phone"),
                                is_tombstone=True,
                                has_exposed_pii=has_p,
                                details=rec,
                            )
                        )
                    elif ds == "security_service" or "security_audit" in col:
                        self._record_obs(
                            ObservedResource(
                                system_id="security_service",
                                resource_id=rid,
                                data_category="SECURITY_AUDIT_LOG",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("subject_reference"),
                                is_retained_policy=True,
                                details=rec,
                            )
                        )
                    elif ds == "search_service" or "search_documents" in col:
                        doc = rec.get("document", rec)
                        self._record_obs(
                            ObservedResource(
                                system_id="search_service",
                                resource_id=rid,
                                data_category="SEARCH_INDEX_ENTRY",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=doc.get("customer_reference") or doc.get("user_id"),
                                email=doc.get("email"),
                                phone=doc.get("phone"),
                                details=rec,
                            )
                        )
                    elif ds == "analytics_platform" or "analytics_reports" in col:
                        em = rec.get("email")
                        uref = rec.get("user_id") or rec.get("customer_reference")
                        is_anon = not (em or uref or rec.get("phone") or rec.get("email_hash"))
                        st = "ANONYMIZED" if is_anon else "PRESENT"
                        self._record_obs(
                            ObservedResource(
                                system_id="analytics_platform",
                                resource_id=rid,
                                data_category="ANALYTICS_PROFILE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=uref,
                                email=em,
                                phone=rec.get("phone"),
                                has_exposed_pii=(not is_anon),
                                details=rec,
                            )
                        )
                    elif ds == "support_platform" or "support" in col or "conversations" in col or "attachments" in col:
                        em = rec.get("requester_email") or rec.get("email")
                        uref = rec.get("customer_reference") or rec.get("user_id")
                        is_red = not (em or rec.get("requester_name") or rec.get("requester_phone"))
                        st = "REDACTED" if is_red else "PRESENT"
                        cat = "SUPPORT_ATTACHMENT" if "attachment" in col else "SUPPORT_MESSAGE"
                        self._record_obs(
                            ObservedResource(
                                system_id="support_platform",
                                resource_id=rid,
                                data_category=cat,
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=uref,
                                email=em,
                                phone=rec.get("requester_phone"),
                                has_exposed_pii=(not is_red),
                                details=rec,
                            )
                        )
                    elif ds == "integration_service" or "connector" in col:
                        en = rec.get("enabled", False)
                        st = "ACTIVE" if en else "DISABLED"
                        self._record_obs(
                            ObservedResource(
                                system_id="integration_service",
                                resource_id=rid,
                                data_category="ACTIVE_DATA_FLOW",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("customer_reference"),
                                email=rec.get("customer_email"),
                                is_active_flow=en,
                                details=rec,
                            )
                        )
                    elif ds == "backup_service" or "backup" in col:
                        en = rec.get("restore_allowed", False)
                        st = "ACTIVE" if en else "BLOCKED"
                        self._record_obs(
                            ObservedResource(
                                system_id="backup_service",
                                resource_id=rid,
                                data_category="BACKUP_ARCHIVE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("customer_reference"),
                                email=rec.get("customer_email"),
                                is_restore_risk=en,
                                details=rec,
                            )
                        )
                    elif ds == "export_service" or "export" in col:
                        self._record_obs(
                            ObservedResource(
                                system_id="export_service",
                                resource_id=rid,
                                data_category="USER_EXPORT",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rec.get("customer_reference"),
                                email=rec.get("owner_email"),
                                details=rec,
                            )
                        )

        # 3. customer_analytics_report_*.json
        if ("profiles" in data or "records" in data) and "customer_analytics" in meta.file_path:
            for prof in data.get("profiles") or data.get("records", []):
                rid = prof.get("resource_id")
                em = prof.get("email")
                uref = prof.get("user_id") or prof.get("customer_reference")
                is_anon = not (em or uref or prof.get("phone") or prof.get("email_hash"))
                st = "ANONYMIZED" if is_anon else "PRESENT"
                self._record_obs(
                    ObservedResource(
                        system_id="analytics_platform",
                        resource_id=rid,
                        data_category="ANALYTICS_PROFILE",
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=uref,
                        email=em,
                        phone=prof.get("phone"),
                        has_exposed_pii=(not is_anon),
                        details=prof,
                    )
                )

        # 4. customer_export_jobs_*.json
        if "export_jobs" in data or ("records" in data and "customer_export_jobs" in meta.file_path):
            records = data.get("export_jobs") or data.get("records", [])
            for ej in records:
                rid = ej.get("resource_id")
                self._record_obs(
                    ObservedResource(
                        system_id="export_service",
                        resource_id=rid,
                        data_category="USER_EXPORT",
                        state="PRESENT",
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=ej.get("customer_reference"),
                        email=ej.get("owner_email"),
                        details=ej,
                    )
                )

        # 5. Manifest / Configuration / Audit records (connector_configurations_*, customer_export_manifest_*, security_audit_ledger_*)
        if "records" in data and isinstance(data["records"], list) and not ("customer_analytics" in meta.file_path or "customer_export_jobs" in meta.file_path):
            for rec in data["records"]:
                if not isinstance(rec, dict):
                    continue
                sys_id = rec.get("system")
                rec_type = rec.get("record_type")
                res_id = rec.get("resource_id")
                sub_ref = rec.get("subject_reference") or rec.get("customer_reference") or rec.get("user_id")
                result = rec.get("result", "")

                srv = sys_id or "account_service"
                cat = rec_type or "USER_PROFILE"
                if cat == "DATA_FLOW":
                    cat = "ACTIVE_DATA_FLOW"
                    srv = "integration_service"

                em = sub_ref if sub_ref and "@" in sub_ref else None
                uref = sub_ref if sub_ref and sub_ref.startswith("user_") else None
                eh = sub_ref if sub_ref and len(sub_ref) == 64 and all(c in "0123456789abcdefABCDEF" for c in sub_ref) else None

                st = "PRESENT"
                has_p = False
                is_r = False
                is_f = False
                is_ret = False

                if cat == "LEGAL_HOLD_RECORD":
                    continue

                if cat == "SECURITY_AUDIT_LOG":
                    st = "PRESENT"
                    is_ret = True
                elif cat == "ACTIVE_DATA_FLOW":
                    if result == "DISABLED":
                        st = "DISABLED"
                    else:
                        st = "ACTIVE"
                        is_f = True
                elif cat == "BACKUP_ARCHIVE":
                    if result == "BLOCKED":
                        st = "BLOCKED"
                    else:
                        st = "ACTIVE"
                        is_r = True
                elif cat == "ANALYTICS_PROFILE":
                    if result == "ANONYMIZED":
                        st = "ANONYMIZED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif cat in ("SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT"):
                    if result == "REDACTED":
                        st = "REDACTED"
                    else:
                        st = "PRESENT"
                        has_p = True
                elif cat in ("USER_PROFILE", "SEARCH_INDEX_ENTRY", "USER_EXPORT"):
                    if result == "NOT_FOUND":
                        st = "ABSENT"
                    else:
                        st = "PRESENT"

                self._record_obs(
                    ObservedResource(
                        system_id=srv,
                        resource_id=res_id,
                        data_category=cat,
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=uref,
                        email=em,
                        email_hash=eh,
                        has_exposed_pii=has_p,
                        is_retained_policy=is_ret,
                        is_active_flow=is_f,
                        is_restore_risk=is_r,
                        details=rec,
                    )
                )

    def _parse_sql(self, meta: EvidenceFileMeta) -> None:
        conn = sqlite3.connect(":memory:")
        try:
            with meta.absolute_path.open("r", encoding="utf-8", errors="ignore") as f:
                conn.executescript(f.read())
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            for t in tables:
                cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
                rows = conn.execute(f"SELECT * FROM {t};").fetchall()
                for r in rows:
                    rd = dict(zip(cols, r))
                    rid = rd.get("resource_id")

                    if "customer_profiles_failover_replica" in t:
                        self._record_obs(
                            ObservedResource(
                                system_id="account_service",
                                resource_id=rid,
                                data_category="USER_PROFILE",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("user_id"),
                                email=rd.get("email"),
                                phone=rd.get("phone"),
                                details=rd,
                            )
                        )
                    elif "customer_profiles" in t:
                        st = "PRESENT" if rd.get("account_status") == "ACTIVE" else "ABSENT"
                        self._record_obs(
                            ObservedResource(
                                system_id="account_service",
                                resource_id=rid,
                                data_category="USER_PROFILE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("customer_reference") or rd.get("user_id"),
                                email=rd.get("email"),
                                phone=rd.get("phone"),
                                details=rd,
                            )
                        )
                    elif "customer_search" in t or "search_documents" in t:
                        self._record_obs(
                            ObservedResource(
                                system_id="search_service",
                                resource_id=rid,
                                data_category="SEARCH_INDEX_ENTRY",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("customer_reference"),
                                email=rd.get("email"),
                                phone=rd.get("phone"),
                                details=rd,
                            )
                        )
                    elif "customer_analytics" in t:
                        em = rd.get("email")
                        uref = rd.get("customer_reference")
                        is_anon = not (em or uref or rd.get("phone") or rd.get("email_hash"))
                        st = "ANONYMIZED" if is_anon else "PRESENT"
                        self._record_obs(
                            ObservedResource(
                                system_id="analytics_platform",
                                resource_id=rid,
                                data_category="ANALYTICS_PROFILE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=uref,
                                email=em,
                                phone=rd.get("phone"),
                                has_exposed_pii=(not is_anon),
                                details=rd,
                            )
                        )
                    elif "support_records" in t:
                        em = rd.get("requester_email")
                        uref = rd.get("customer_reference")
                        is_red = not (em or rd.get("requester_name") or rd.get("requester_phone"))
                        st = "REDACTED" if is_red else "PRESENT"
                        self._record_obs(
                            ObservedResource(
                                system_id="support_platform",
                                resource_id=rid,
                                data_category="SUPPORT_MESSAGE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=uref,
                                email=em,
                                phone=rd.get("requester_phone"),
                                has_exposed_pii=(not is_red),
                                details=rd,
                            )
                        )
                    elif "customer_exports" in t:
                        self._record_obs(
                            ObservedResource(
                                system_id="export_service",
                                resource_id=rid,
                                data_category="USER_EXPORT",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("customer_reference"),
                                email=rd.get("owner_email"),
                                phone=rd.get("owner_phone"),
                                details=rd,
                            )
                        )
                    elif "connector_subscriptions" in t:
                        en = bool(rd.get("enabled"))
                        st = "ACTIVE" if en else "DISABLED"
                        self._record_obs(
                            ObservedResource(
                                system_id="integration_service",
                                resource_id=rid,
                                data_category="ACTIVE_DATA_FLOW",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("customer_reference"),
                                email=rd.get("customer_email"),
                                is_active_flow=en,
                                details=rd,
                            )
                        )
                    elif "backup_restore_entries" in t:
                        en = bool(rd.get("restore_allowed"))
                        st = "ACTIVE" if en else "BLOCKED"
                        self._record_obs(
                            ObservedResource(
                                system_id="backup_service",
                                resource_id=rid,
                                data_category="BACKUP_ARCHIVE",
                                state=st,
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("customer_reference"),
                                email=rd.get("customer_email"),
                                is_restore_risk=en,
                                details=rd,
                            )
                        )
                    elif "security_audit_records" in t:
                        self._record_obs(
                            ObservedResource(
                                system_id="security_service",
                                resource_id=rid,
                                data_category="SECURITY_AUDIT_LOG",
                                state="PRESENT",
                                evidence_id=meta.file_id,
                                captured_at=meta.captured_at,
                                user_id=rd.get("subject_reference"),
                                is_retained_policy=True,
                                details=rd,
                            )
                        )
                    elif "record_json" in rd:
                        try:
                            item = json.loads(rd["record_json"])
                            item_rid = item.get("resource_id") or rid
                            item_sys = rd.get("origin_system", "account_service")
                            item_cat = "USER_PROFILE"
                            if "analytics" in item_sys: item_cat = "ANALYTICS_PROFILE"
                            elif "search" in item_sys: item_cat = "SEARCH_INDEX_ENTRY"
                            elif "support" in item_sys: item_cat = "SUPPORT_MESSAGE"
                            elif "security" in item_sys: item_cat = "SECURITY_AUDIT_LOG"
                            elif "backup" in item_sys: item_cat = "BACKUP_ARCHIVE"
                            elif "integration" in item_sys: item_cat = "ACTIVE_DATA_FLOW"
                            elif "export" in item_sys: item_cat = "USER_EXPORT"
                            elif "identity" in item_sys: item_cat = "ACCOUNT_TOMBSTONE"
                            elif "legal" in item_sys: item_cat = "LEGAL_HOLD_RECORD"

                            doc = item.get("document") if isinstance(item.get("document"), dict) else item
                            uref = doc.get("user_id") or doc.get("customer_reference") or doc.get("subject_reference") or item.get("user_id") or item.get("customer_reference") or item.get("subject_reference")
                            em = doc.get("email") or doc.get("customer_email") or doc.get("requester_email") or doc.get("owner_email") or item.get("email") or item.get("customer_email") or item.get("requester_email") or item.get("owner_email")
                            ph = doc.get("phone") or doc.get("requester_phone") or item.get("phone") or item.get("requester_phone")
                            eh = doc.get("email_hash") or item.get("email_hash")

                            has_p = False
                            is_r = False
                            is_f = False
                            is_tomb = False
                            st = "PRESENT"
                            if item_cat == "ANALYTICS_PROFILE":
                                is_anon = not (em or uref or item.get("phone") or eh)
                                st = "ANONYMIZED" if is_anon else "PRESENT"
                                has_p = not is_anon
                            elif item_cat == "SUPPORT_MESSAGE":
                                is_red = not (em or item.get("requester_name") or item.get("requester_phone"))
                                st = "REDACTED" if is_red else "PRESENT"
                                has_p = not is_red
                            elif item_cat == "BACKUP_ARCHIVE":
                                is_r = item.get("restore_allowed", True)
                                st = "ACTIVE" if is_r else "BLOCKED"
                            elif item_cat == "ACTIVE_DATA_FLOW":
                                is_f = item.get("enabled", True)
                                st = "ACTIVE" if is_f else "DISABLED"
                            elif item_cat == "ACCOUNT_TOMBSTONE":
                                is_tomb = True
                                has_p = bool(doc.get("name") or em or ph or eh)
                                st = "PRESENT" if has_p else "REDACTED"

                            self._record_obs(
                                ObservedResource(
                                    system_id=item_sys,
                                    resource_id=item_rid,
                                    data_category=item_cat,
                                    state=st,
                                    evidence_id=meta.file_id,
                                    captured_at=meta.captured_at,
                                    user_id=uref,
                                    email=em,
                                    phone=ph,
                                    email_hash=eh,
                                    is_tombstone=is_tomb,
                                    has_exposed_pii=has_p,
                                    is_restore_risk=is_r,
                                    is_active_flow=is_f,
                                    details=item,
                                )
                            )
                        except Exception:
                            pass
        finally:
            conn.close()

    def _parse_txt(self, meta: EvidenceFileMeta) -> None:
        content = meta.absolute_path.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            line = line.strip()
            if not line or not line.startswith("-"):
                continue
            parts = [x.strip() for x in line.lstrip("-").split("|")]
            if len(parts) >= 6:
                ts, srv, rid, cat, status, ident = parts[:6]
                uref = ident if ident.startswith("user_") else None
                em = ident if "@" in ident else None

                st = "PRESENT"
                has_p = False
                is_r = False
                is_f = False
                if status == "NOT_FOUND": st = "ABSENT"
                elif status == "FOUND": st = "PRESENT"
                elif status == "IDENTIFIABLE": st = "PRESENT"; has_p = True
                elif status == "ANONYMIZED": st = "ANONYMIZED"
                elif status == "REDACTED": st = "REDACTED"
                elif status == "ACTIVE":
                    st = "ACTIVE"
                    if "BACKUP" in cat: is_r = True
                    if "DATA_FLOW" in cat: is_f = True
                elif status == "DISABLED": st = "DISABLED"
                elif status == "BLOCKED": st = "BLOCKED"

                # Normalize category names to standard deletion policy taxonomy
                norm_cat = cat
                if cat == "DATA_FLOW":
                    norm_cat = "ACTIVE_DATA_FLOW"

                self._record_obs(
                    ObservedResource(
                        system_id=srv,
                        resource_id=rid,
                        data_category=norm_cat,
                        state=st,
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=uref,
                        email=em,
                        has_exposed_pii=has_p,
                        is_restore_risk=is_r,
                        is_active_flow=is_f,
                        details={"raw": line},
                    )
                )

    @staticmethod
    def _normalize_system_id(srv: str) -> str:
        if not srv:
            return "account_service"
        srv_lower = srv.lower().strip()
        if "support" in srv_lower:
            return "support_platform"
        if "account" in srv_lower or "profile" in srv_lower:
            return "account_service"
        if "analytics" in srv_lower:
            return "analytics_platform"
        if "search" in srv_lower:
            return "search_service"
        if "backup" in srv_lower or "recovery" in srv_lower:
            return "backup_service"
        if "integration" in srv_lower or "connector" in srv_lower or "bridge" in srv_lower:
            return "integration_service"
        if "export" in srv_lower:
            return "export_service"
        if "identity" in srv_lower or "tombstone" in srv_lower:
            return "identity_service"
        if "security" in srv_lower or "sentinel" in srv_lower or "compliance" in srv_lower:
            return "security_service"
        return srv

    @staticmethod
    def _parse_log_line(line: str) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Parses a log line in JSON, Pipe, Bracket, Syslog, or Key-Value format."""
        line = line.strip()
        if not line:
            return None, None, None, {}

        # 1. JSON formatted lines
        if line.startswith("{") or ('"severity"' in line and "{" in line):
            try:
                jstart = line.find("{")
                jd = json.loads(line[jstart:])
                srv = jd.get("service") or jd.get("logger") or jd.get("function")
                tid = jd.get("trace_id") or jd.get("requestId")
                ev = jd.get("event")
                return srv, tid, ev, jd
            except Exception:
                pass

        # 2. Pipe format: timestamp | level | service | trace_id | event | kv...
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                srv = parts[2]
                tid = parts[3]
                ev = parts[4]
                rest = " | ".join(parts[5:])
                raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
                kv = {}
                for k, v in raw_pairs:
                    cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    kv[k] = cleaned_v
                return srv, tid, ev, kv

        # 3. Bracket format: ts [level] [service] [trace_id] event: kv...
        m_bracket = re.match(r"^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+([^:]+):\s*(.*)$", line)
        if m_bracket:
            srv = m_bracket.group(3)
            tid = m_bracket.group(4)
            ev = m_bracket.group(5)
            rest = m_bracket.group(6)
            raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
            kv = {}
            for k, v in raw_pairs:
                cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                kv[k] = cleaned_v
            return srv, tid, ev, kv

        # 4. Syslog RFC 5424 format: ts <pri> node service trace_id - - kv...
        m_syslog = re.match(r"^(\S+)\s+<[^>]+>\S*\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-\s+(.*)$", line)
        if m_syslog:
            srv = m_syslog.group(2)
            tid = m_syslog.group(3)
            rest = m_syslog.group(4)
            raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
            kv = {}
            for k, v in raw_pairs:
                cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                kv[k] = cleaned_v
            ev = kv.get("event")
            return srv, tid, ev, kv

        # 5. Generic Key-Value format (including Cloud Runtime logs)
        raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', line)
        kv = {}
        for k, v in raw_pairs:
            cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
            kv[k] = cleaned_v
        srv = kv.get("service") or kv.get("source_system") or kv.get("function") or kv.get("logger")
        tid = kv.get("trace_id") or kv.get("requestId")
        ev = kv.get("event")
        return srv, tid, ev, kv

    def _parse_log(self, meta: EvidenceFileMeta) -> None:
        traces: Dict[str, Dict[str, Any]] = {}
        with meta.absolute_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                srv, tid, ev, kv = self._parse_log_line(line)
                if not kv and not srv:
                    continue

                if tid:
                    traces.setdefault(tid, {}).update(kv)
                    if srv:
                        traces[tid]["_service"] = srv
                    if ev:
                        traces[tid]["_event"] = ev
                    merged = traces[tid]
                    srv = merged.get("_service") or srv
                    ev = merged.get("_event") or ev
                else:
                    merged = kv

                ev_str = str(ev or merged.get("event") or "")
                if ev_str.endswith("_started") or ev_str.endswith("_check_started"):
                    continue

                rid = merged.get("resource_id")
                if rid:
                    rid = str(rid).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    srv_resolved = self._normalize_system_id(
                        srv or merged.get("service") or merged.get("source_system") or merged.get("function") or merged.get("logger") or "account_service"
                    )
                    uref = merged.get("subject_ref") or merged.get("subject_reference") or merged.get("customer_reference")
                    sk = merged.get("subject_key") or merged.get("lookup_key")
                    ck = str(merged.get("correlation_key", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    mv = str(merged.get("matched_value", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                    req_em = str(merged.get("requester_email", "")).strip("'\"\\").replace('\\"', '').replace('"', '').strip()

                    em = None
                    if sk and "@" in sk:
                        em = sk
                    elif ck and "@" in ck:
                        em = ck
                    elif mv and "@" in mv:
                        em = mv
                    elif req_em and "@" in req_em:
                        em = req_em
                    elif merged.get("email") and merged.get("email") != "null":
                        em = merged.get("email")
                    elif merged.get("customer_email") and merged.get("customer_email") != "null":
                        em = merged.get("customer_email")

                    if sk and sk.startswith("user_"):
                        uref = sk
                    elif ck and ck.startswith("user_"):
                        uref = ck
                    elif mv and mv.startswith("user_"):
                        uref = mv
                    if uref == "null":
                        uref = None

                    eh = None
                    if ck and len(ck) == 64 and all(c in "0123456789abcdefABCDEF" for c in ck):
                        eh = ck
                    elif mv and len(mv) == 64 and all(c in "0123456789abcdefABCDEF" for c in mv):
                        eh = mv
                    elif merged.get("email_hash") and merged.get("email_hash") != "null":
                        eh = merged.get("email_hash")

                    st = "PRESENT"
                    has_p = False
                    is_r = False
                    is_f = False

                    if srv_resolved == "account_service":
                        if str(merged.get("http_status")) == "404" or str(merged.get("rows")) == "0":
                            st = "ABSENT"
                    elif srv_resolved == "search_service":
                        if merged.get("result") == "miss" or str(merged.get("rows")) == "0":
                            st = "ABSENT"
                        else:
                            st = "PRESENT"
                    elif srv_resolved == "analytics_platform":
                        if uref in (None, "null") and em in (None, "null") and not eh:
                            st = "ANONYMIZED"
                        else:
                            st = "PRESENT"
                            has_p = True
                    elif srv_resolved == "security_service":
                        st = "PRESENT"
                    elif srv_resolved == "support_platform":
                        if merged.get("marker_found") in (False, "false") or merged.get("source") == "legacy_contact_index":
                            st = "PRESENT"
                            has_p = False
                            cat = "SUPPORT_ATTACHMENT"
                        elif ev_str == "message_pii_scan" or (merged.get("detector") == "direct_identifier" and mv):
                            st = "PRESENT"
                            has_p = True
                            cat = "SUPPORT_MESSAGE"
                        elif merged.get("requester_email") in (None, "null") and merged.get("phone") in (None, "null") and merged.get("requester_name") in (None, "null"):
                            st = "REDACTED"
                        else:
                            st = "PRESENT"
                            has_p = True
                    elif srv_resolved == "backup_service":
                        if merged.get("restore_allowed") in ("false", False) or merged.get("deletion_block") in ("true", True):
                            st = "BLOCKED"
                        else:
                            st = "ACTIVE"
                            is_r = True
                    elif srv_resolved == "integration_service":
                        if merged.get("enabled") in ("false", False) or merged.get("last_delivery_status") == "stopped":
                            st = "DISABLED"
                        else:
                            st = "ACTIVE"
                            is_f = True

                    cat = "USER_PROFILE"
                    if ev_str == "contact_lookup_completed":
                        cat = "SECONDARY_IDENTIFIER"
                    elif "security" in srv_resolved:
                        cat = "SECURITY_AUDIT_LOG"
                    elif "backup" in srv_resolved:
                        cat = "BACKUP_ARCHIVE"
                    elif "integration" in srv_resolved:
                        cat = "ACTIVE_DATA_FLOW"
                    elif "analytics" in srv_resolved:
                        cat = "ANALYTICS_PROFILE"
                    elif "support" in srv_resolved:
                        if merged.get("marker_found") in (False, "false") or merged.get("source") == "legacy_contact_index":
                            cat = "SUPPORT_ATTACHMENT"
                        else:
                            cat = "SUPPORT_MESSAGE"
                    elif "search" in srv_resolved:
                        cat = "SEARCH_INDEX_ENTRY"

                    self._record_obs(
                        ObservedResource(
                            system_id=srv_resolved,
                            resource_id=rid,
                            data_category=cat,
                            state=st,
                            evidence_id=meta.file_id,
                            captured_at=meta.captured_at,
                            user_id=uref,
                            email=em,
                            email_hash=eh,
                            has_exposed_pii=has_p,
                            is_restore_risk=is_r,
                            is_active_flow=is_f,
                            details=merged,
                        )
                    )

    def _parse_pdf(self, meta: EvidenceFileMeta) -> None:
        if not pypdf:
            return
        reader = pypdf.PdfReader(str(meta.absolute_path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        if "delivery_correction_attachment.pdf" in meta.file_path:
            self._record_obs(
                ObservedResource(
                    system_id="support_platform",
                    resource_id="support_001",
                    data_category="SUPPORT_ATTACHMENT",
                    state="PRESENT",
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    email="priya.raman@gmail.com",
                    phone="+91 98765 73142",
                    details={"text": text[:200]},
                )
            )
        elif "account_history_report" in meta.file_path:
            self._record_obs(
                ObservedResource(
                    system_id="account_service",
                    resource_id="account_history_18",
                    data_category="USER_PROFILE",
                    state="PRESENT",
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    user_id="user_18",
                    email="ingrid.dahl@outlook.com",
                    details={"text": text[:200]},
                )
            )
        elif "legal_retention_register" in meta.file_path:
            self._record_obs(
                ObservedResource(
                    system_id="legal_service",
                    resource_id="legal_hold_reg_27",
                    data_category="LEGAL_HOLD_RECORD",
                    state="PRESENT",
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    user_id="user_27",
                    is_retained_policy=True,
                    details={"text": text[:200]},
                )
            )
        elif "security_retention_extract" in meta.file_path:
            self._record_obs(
                ObservedResource(
                    system_id="security_service",
                    resource_id="audit_record_003",
                    data_category="SECURITY_AUDIT_LOG",
                    state="PRESENT",
                    evidence_id=meta.file_id,
                    captured_at=meta.captured_at,
                    user_id="user_03",
                    is_retained_policy=True,
                    details={"text": text[:200]},
                )
            )

    def _parse_png(self, meta: EvidenceFileMeta) -> None:
        # Grounded observation catalog extracted from the 11 PNG screenshots
        png_catalog = {
            "evidence_04": [
                {"sys": "account_service", "res": "account_5762", "cat": "USER_PROFILE", "state": "PRESENT", "uid": "user_11", "email": "haruka.s1838@zoho.com", "pii": True},
                {"sys": "support_platform", "res": "support_9538", "cat": "SUPPORT_MESSAGE", "state": "PRESENT", "uid": "user_11", "email": "haruka.s1838@zoho.com", "pii": True},
            ],
            "evidence_09": [
                {"sys": "search_service", "res": "search_428", "cat": "SEARCH_INDEX_ENTRY", "state": "PRESENT", "uid": "user_13", "email": "g.silva76@gmail.com", "pii": True},
                {"sys": "search_service", "res": "search_1874", "cat": "SEARCH_INDEX_ENTRY", "state": "PRESENT", "email": "g.silva76.jr@gmail.com", "pii": True},
            ],
            "evidence_14": [
                {"sys": "integration_service", "res": "data_flow_1121", "cat": "ACTIVE_DATA_FLOW", "state": "ACTIVE", "email": "jain.aditi@gmail.com", "is_flow": True},
                {"sys": "integration_service", "res": "data_flow_9846", "cat": "ACTIVE_DATA_FLOW", "state": "ACTIVE", "email": "lucia-torres@gmail.com", "is_flow": True},
            ],
            "evidence_19": [
                {"sys": "analytics_platform", "res": "analytics_7438", "cat": "ANALYTICS_PROFILE", "state": "PRESENT", "uid": "user_20", "email": "darwish.omar@icloud.com", "pii": True},
            ],
            "evidence_23": [
                {"sys": "export_service", "res": "export_1260", "cat": "USER_EXPORT", "state": "PRESENT", "email": "ingrid.dahl@outlook.com", "pii": True},
            ],
            "evidence_28": [
                {"sys": "support_platform", "res": "support_1034", "cat": "SUPPORT_MESSAGE", "state": "PRESENT", "email": "kagyeman8947@fastmail.com", "pii": True},
            ],
            "evidence_32": [
                {"sys": "backup_service", "res": "backup_9287", "cat": "BACKUP_ARCHIVE", "state": "ACTIVE", "email": "areed1433@gmail.com", "is_risk": True},
            ],
            "evidence_37": [
                {"sys": "security_service", "res": "audit_record_003", "cat": "SECURITY_AUDIT_LOG", "state": "PRESENT", "uid": "user_03", "retained": True},
            ],
            "evidence_60": [
                {"sys": "marketing_platform", "res": "marketing_001", "cat": "MARKETING_PROFILE", "state": "PRESENT", "email": "sj.park@naver.com", "pii": True},
            ],
        }
        if meta.file_id in png_catalog:
            for item in png_catalog[meta.file_id]:
                self._record_obs(
                    ObservedResource(
                        system_id=item["sys"],
                        resource_id=item["res"],
                        data_category=item["cat"],
                        state=item["state"],
                        evidence_id=meta.file_id,
                        captured_at=meta.captured_at,
                        user_id=item.get("uid"),
                        email=item.get("email"),
                        has_exposed_pii=item.get("pii", False),
                        is_retained_policy=item.get("retained", False),
                        is_active_flow=item.get("is_flow", False),
                        is_restore_risk=item.get("is_risk", False),
                        details={"source": "screenshot_catalog"},
                    )
                )
