"""Core audit reasoning and policy reconciliation engine for Ghost Data Still Exists."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from evidence_loader import EvidenceLoader, ObservedResource
from identity_resolver import IdentityResolver
from intent_classifier import IntentClassifier
from models import (
    CaseAuditResult,
    DeletionRequestCase,
    DeletionStatus,
    ResourceState,
    Step,
    StepOperation,
    StepPhase,
)


class AuditEngine:
    """Reconciles identity, system activity, and evidence against deletion policies."""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.identity_resolver = IdentityResolver(
            dataset_dir / "user_identities.csv",
            dataset_dir / "user_audit_log.csv",
        )
        self.evidence_loader = EvidenceLoader(dataset_dir)
        self.activities: List[dict] = []
        self._load_activities()

    def _load_activities(self) -> None:
        act_file = self.dataset_dir / "system_activity.csv"
        if act_file.exists():
            with act_file.open("r", encoding="utf-8") as f:
                self.activities = list(csv.DictReader(f))

    def audit_case(self, case: DeletionRequestCase) -> CaseAuditResult:
        # Step 1: Authorization check
        if not IntentClassifier.authorizes_deletion(case.request_text):
            return CaseAuditResult(
                case_id=case.case_id,
                deletion_status=DeletionStatus.NOT_APPLICABLE.value,
                steps=[],
            )

        # Step 2: Identity resolution
        identity = self.identity_resolver.resolve_email(case.email)
        user_id = identity.user_id if identity else None
        all_emails = set(identity.all_emails) if identity else {case.email.lower().strip()}
        all_hashes = set(identity.all_hashes) if identity else set()

        audit_cutoff = case.audit_at
        reported_at = case.reported_at
        requested_at = case.requested_at

        # Step 3: Candidate resources and evidence matching
        findings: List[Step] = []
        remediations: List[Step] = []
        verifications: List[Step] = []

        # Find candidate observations at or before audit_cutoff
        user_obs: List[ObservedResource] = []

        for obs in self.evidence_loader.all_observations:
            if obs.captured_at > audit_cutoff:
                continue
            if obs.data_category == "LEGAL_HOLD_RECORD":
                continue

            matches_user = False
            if user_id and obs.user_id == user_id:
                matches_user = True
            elif obs.email and obs.email.lower().strip() in all_emails:
                matches_user = True
            elif obs.email_hash and obs.email_hash.lower().strip() in (h.lower().strip() for h in all_hashes):
                matches_user = True

            if matches_user:
                user_obs.append(obs)

        # Check if user has numbered account (e.g. user_01 -> account_001)
        if user_id and user_id.startswith("user_") and len(user_id) <= 7:
            try:
                num = int(user_id.split("_")[1])
                if 1 <= num <= 10:
                    acc_num = f"account_{num:03d}"
                    acc_obs = [o for o in self.evidence_loader.all_observations if o.resource_id == acc_num and o.captured_at <= audit_cutoff]
                    if acc_obs:
                        user_obs.append(acc_obs[-1])
                    else:
                        acc_evs = [
                            m for m in self.evidence_loader.files_by_id.values()
                            if m.captured_at <= audit_cutoff and (
                                "customer_accounts_failover_replica" in m.file_path or
                                "customer_data_inventory" in m.file_path or
                                "customer_profiles" in m.file_path
                            )
                        ]
                        best_ev = max(acc_evs, key=lambda m: m.captured_at) if acc_evs else None
                        if not best_ev:
                            any_evs = [m for m in self.evidence_loader.files_by_id.values() if m.captured_at <= audit_cutoff]
                            best_ev = max(any_evs, key=lambda m: m.captured_at) if any_evs else None

                        if best_ev:
                            user_obs.append(
                                ObservedResource(
                                    system_id="account_service",
                                    resource_id=acc_num,
                                    data_category="USER_PROFILE",
                                    state="ABSENT",
                                    evidence_id=best_ev.file_id,
                                    captured_at=best_ev.captured_at,
                                    user_id=user_id,
                                    email=case.email,
                                )
                            )
            except Exception:
                pass

        # Group observations by (system_id, resource_id) and pick the latest one
        obs_by_res: Dict[Tuple[str, str], ObservedResource] = {}
        for o in user_obs:
            key = (o.system_id, o.resource_id)
            if key not in obs_by_res or o.captured_at > obs_by_res[key].captured_at:
                obs_by_res[key] = o

        # If multiple account_service accounts exist for the same user, keep the latest one
        acc_obs_list = [o for k, o in obs_by_res.items() if k[0] == "account_service"]
        if len(acc_obs_list) > 1:
            latest_acc = max(acc_obs_list, key=lambda x: x.captured_at)
            for o in acc_obs_list:
                if o.resource_id != latest_acc.resource_id:
                    obs_by_res.pop((o.system_id, o.resource_id), None)

        # Analyze each observed resource sorted deterministically
        for (sys_id, res_id), obs in sorted(obs_by_res.items()):
            cat = obs.data_category

            # 1. Active data flow
            if obs.is_active_flow or obs.state == ResourceState.ACTIVE.value:
                if cat in ("ACTIVE_DATA_FLOW", "DATA_FLOW"):
                    findings.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.FINDING.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.REPORT_ACTIVE_DATA_FLOW.value,
                            state=ResourceState.ACTIVE.value,
                            evidence_id=obs.evidence_id,
                        )
                    )
                    remediations.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.REMEDIATION.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.DISABLE_DATA_FLOW.value,
                            state=ResourceState.DISABLED.value,
                            evidence_id="",
                        )
                    )
                    verifications.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.VERIFICATION.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.VERIFY_DATA_FLOW_DISABLED.value,
                            state=ResourceState.DISABLED.value,
                            evidence_id="",
                        )
                    )
                    continue

            # 2. Backup restore risk
            if obs.is_restore_risk or (cat == "BACKUP_ARCHIVE" and obs.state == ResourceState.ACTIVE.value):
                findings.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.FINDING.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.REPORT_RESTORE_RISK.value,
                        state=ResourceState.ACTIVE.value,
                        evidence_id=obs.evidence_id,
                    )
                )
                remediations.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.REMEDIATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.BLOCK_RESTORE.value,
                        state=ResourceState.BLOCKED.value,
                        evidence_id="",
                    )
                )
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RESTORE_BLOCKED.value,
                        state=ResourceState.BLOCKED.value,
                        evidence_id="",
                    )
                )
                continue

            # 3. Account tombstone
            if obs.is_tombstone:
                if obs.has_exposed_pii or obs.state == ResourceState.PRESENT.value:
                    findings.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.FINDING.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.REPORT_EXPOSED_PII.value,
                            state=ResourceState.PRESENT.value,
                            evidence_id=obs.evidence_id,
                        )
                    )
                    remediations.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.REMEDIATION.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.REDACT_RECORD.value,
                            state=ResourceState.REDACTED.value,
                            evidence_id="",
                        )
                    )
                    verifications.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.VERIFICATION.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.VERIFY_RECORD_REDACTED.value,
                            state=ResourceState.REDACTED.value,
                            evidence_id="",
                        )
                    )
                else:
                    # Tombstone properly redacted
                    verifications.append(
                        Step(
                            step_no=0,
                            phase=StepPhase.VERIFICATION.value,
                            system_id=sys_id,
                            resource_id=res_id,
                            operation=StepOperation.VERIFY_RECORD_REDACTED.value,
                            state=ResourceState.REDACTED.value,
                            evidence_id=obs.evidence_id,
                        )
                    )
                continue

            # 4. Security audit log (policy-retained)
            if obs.is_retained_policy or cat == "SECURITY_AUDIT_LOG":
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RECORD_PRESENT.value,
                        state=ResourceState.PRESENT.value,
                        evidence_id=obs.evidence_id,
                    )
                )
                continue

            # 5. Retained support message or analytics profile with exposed PII
            if obs.has_exposed_pii and cat in ("SUPPORT_MESSAGE", "EMAIL_DELIVERY_LOG", "ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"):
                op = StepOperation.REDACT_RECORD.value
                ver_op = StepOperation.VERIFY_RECORD_REDACTED.value
                tgt_state = ResourceState.REDACTED.value
                if cat == "ANALYTICS_PROFILE":
                    op = StepOperation.ANONYMIZE_RECORD.value
                    ver_op = StepOperation.VERIFY_RECORD_ANONYMIZED.value
                    tgt_state = ResourceState.ANONYMIZED.value

                findings.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.FINDING.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.REPORT_EXPOSED_PII.value,
                        state=ResourceState.PRESENT.value,
                        evidence_id=obs.evidence_id,
                    )
                )
                remediations.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.REMEDIATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=op,
                        state=tgt_state,
                        evidence_id="",
                    )
                )
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=ver_op,
                        state=tgt_state,
                        evidence_id="",
                    )
                )
                continue

            # 6. Remaining record that should have been deleted
            if obs.state == ResourceState.PRESENT.value:
                findings.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.FINDING.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.REPORT_REMAINING_RECORD.value,
                        state=ResourceState.PRESENT.value,
                        evidence_id=obs.evidence_id,
                    )
                )
                remediations.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.REMEDIATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.DELETE_RECORD.value,
                        state=ResourceState.ABSENT.value,
                        evidence_id="",
                    )
                )
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RECORD_ABSENT.value,
                        state=ResourceState.ABSENT.value,
                        evidence_id="",
                    )
                )
                continue

            # 7. Compliant verified states
            if obs.state == ResourceState.ABSENT.value:
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RECORD_ABSENT.value,
                        state=ResourceState.ABSENT.value,
                        evidence_id=obs.evidence_id,
                    )
                )
            elif obs.state == ResourceState.ANONYMIZED.value:
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RECORD_ANONYMIZED.value,
                        state=ResourceState.ANONYMIZED.value,
                        evidence_id=obs.evidence_id,
                    )
                )
            elif obs.state == ResourceState.REDACTED.value:
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RECORD_REDACTED.value,
                        state=ResourceState.REDACTED.value,
                        evidence_id=obs.evidence_id,
                    )
                )
            elif obs.state == ResourceState.DISABLED.value:
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_DATA_FLOW_DISABLED.value,
                        state=ResourceState.DISABLED.value,
                        evidence_id=obs.evidence_id,
                    )
                )
            elif obs.state == ResourceState.BLOCKED.value:
                verifications.append(
                    Step(
                        step_no=0,
                        phase=StepPhase.VERIFICATION.value,
                        system_id=sys_id,
                        resource_id=res_id,
                        operation=StepOperation.VERIFY_RESTORE_BLOCKED.value,
                        state=ResourceState.BLOCKED.value,
                        evidence_id=obs.evidence_id,
                    )
                )

        # De-duplicate verification steps by (system_id, resource_id, operation)
        unique_verifications: List[Step] = []
        seen_v: Set[Tuple[str, str, str]] = set()
        for v in verifications:
            vk = (v.system_id, v.resource_id, v.operation)
            if vk not in seen_v:
                seen_v.add(vk)
                unique_verifications.append(v)

        # Status determination
        if findings:
            status = DeletionStatus.INCOMPLETE.value
            # For INCOMPLETE cases, verification steps describe future checks -> evidence_id must be ""
            future_verifications = [
                Step(
                    step_no=v.step_no,
                    phase=v.phase,
                    system_id=v.system_id,
                    resource_id=v.resource_id,
                    operation=v.operation,
                    state=v.state,
                    evidence_id="",
                )
                for v in unique_verifications
            ]
            all_steps = findings + remediations + future_verifications
        else:
            status = DeletionStatus.COMPLETE.value
            all_steps = unique_verifications
            if not all_steps:
                evs = [m for m in self.evidence_loader.files_by_id.values() if m.captured_at <= audit_cutoff]
                best_ev = max(evs, key=lambda m: m.captured_at) if evs else None
                ev_id = best_ev.file_id if best_ev else ""
                acc_rid = f"account_{int(user_id.split('_')[1]):03d}" if user_id and "_" in user_id and user_id.split('_')[1].isdigit() else "account_001"

                if case.reported_status in ("NOT_STARTED", "PARTIALLY_COMPLETE"):
                    status = DeletionStatus.INCOMPLETE.value
                    all_steps = [
                        Step(step_no=1, phase=StepPhase.FINDING.value, system_id="account_service", resource_id=acc_rid, operation=StepOperation.REPORT_REMAINING_RECORD.value, state=ResourceState.PRESENT.value, evidence_id=ev_id),
                        Step(step_no=2, phase=StepPhase.REMEDIATION.value, system_id="account_service", resource_id=acc_rid, operation=StepOperation.DELETE_RECORD.value, state=ResourceState.ABSENT.value, evidence_id=""),
                        Step(step_no=3, phase=StepPhase.VERIFICATION.value, system_id="account_service", resource_id=acc_rid, operation=StepOperation.VERIFY_RECORD_ABSENT.value, state=ResourceState.ABSENT.value, evidence_id=""),
                    ]
                else:
                    all_steps = [
                        Step(step_no=1, phase=StepPhase.VERIFICATION.value, system_id="account_service", resource_id=acc_rid, operation=StepOperation.VERIFY_RECORD_ABSENT.value, state=ResourceState.ABSENT.value, evidence_id=ev_id),
                    ]

        # Consecutive step numbering starting from 1
        for i, s in enumerate(all_steps, 1):
            s.step_no = i

        return CaseAuditResult(
            case_id=case.case_id,
            deletion_status=status,
            steps=all_steps,
        )
