"""Data models and contract schemas for Ghost Data Still Exists audit agent."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DeletionStatus(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StepPhase(str, Enum):
    FINDING = "FINDING"
    REMEDIATION = "REMEDIATION"
    VERIFICATION = "VERIFICATION"


class StepOperation(str, Enum):
    # Findings
    REPORT_REMAINING_RECORD = "REPORT_REMAINING_RECORD"
    REPORT_EXPOSED_PII = "REPORT_EXPOSED_PII"
    REPORT_ACTIVE_DATA_FLOW = "REPORT_ACTIVE_DATA_FLOW"
    REPORT_RESTORE_RISK = "REPORT_RESTORE_RISK"
    # Remediation
    DISABLE_DATA_FLOW = "DISABLE_DATA_FLOW"
    BLOCK_RESTORE = "BLOCK_RESTORE"
    DELETE_RECORD = "DELETE_RECORD"
    REDACT_RECORD = "REDACT_RECORD"
    ANONYMIZE_RECORD = "ANONYMIZE_RECORD"
    # Verification
    VERIFY_RECORD_ABSENT = "VERIFY_RECORD_ABSENT"
    VERIFY_RECORD_PRESENT = "VERIFY_RECORD_PRESENT"
    VERIFY_RECORD_REDACTED = "VERIFY_RECORD_REDACTED"
    VERIFY_RECORD_ANONYMIZED = "VERIFY_RECORD_ANONYMIZED"
    VERIFY_DATA_FLOW_DISABLED = "VERIFY_DATA_FLOW_DISABLED"
    VERIFY_RESTORE_BLOCKED = "VERIFY_RESTORE_BLOCKED"


class ResourceState(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    REDACTED = "REDACTED"
    ANONYMIZED = "ANONYMIZED"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"


PHASE_RANK = {
    StepPhase.FINDING.value: 1,
    StepPhase.REMEDIATION.value: 2,
    StepPhase.VERIFICATION.value: 3,
}

OPERATION_RANK = {
    StepPhase.FINDING.value: {
        StepOperation.REPORT_REMAINING_RECORD.value: 1,
        StepOperation.REPORT_EXPOSED_PII.value: 2,
        StepOperation.REPORT_ACTIVE_DATA_FLOW.value: 3,
        StepOperation.REPORT_RESTORE_RISK.value: 4,
    },
    StepPhase.REMEDIATION.value: {
        StepOperation.DISABLE_DATA_FLOW.value: 1,
        StepOperation.BLOCK_RESTORE.value: 2,
        StepOperation.DELETE_RECORD.value: 3,
        StepOperation.REDACT_RECORD.value: 4,
        StepOperation.ANONYMIZE_RECORD.value: 5,
    },
    StepPhase.VERIFICATION.value: {
        StepOperation.VERIFY_RECORD_ABSENT.value: 1,
        StepOperation.VERIFY_RECORD_PRESENT.value: 2,
        StepOperation.VERIFY_RECORD_REDACTED.value: 3,
        StepOperation.VERIFY_RECORD_ANONYMIZED.value: 4,
        StepOperation.VERIFY_DATA_FLOW_DISABLED.value: 5,
        StepOperation.VERIFY_RESTORE_BLOCKED.value: 6,
    },
}


@dataclass(frozen=True)
class SubjectIdentity:
    user_id: str
    name: str
    current_email: str
    all_emails: tuple[str, ...]
    all_phones: tuple[str, ...]
    all_hashes: tuple[str, ...]


@dataclass
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_no": self.step_no,
            "phase": self.phase,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "state": self.state,
            "evidence_id": self.evidence_id,
        }

    def sort_key(self) -> tuple[int, int, str, str]:
        p_rank = PHASE_RANK.get(self.phase, 99)
        op_map = OPERATION_RANK.get(self.phase, {})
        op_rank = op_map.get(self.operation, 99)
        return (p_rank, op_rank, self.system_id, self.resource_id)


@dataclass
class DeletionRequestCase:
    case_id: str
    email: str
    requested_at: str
    reported_status: str
    reported_at: str
    audit_at: str
    request_text: str


@dataclass
class CaseAuditResult:
    case_id: str
    deletion_status: str
    steps: list[Step] = field(default_factory=list)

    def to_csv_row(self) -> tuple[str, str, str]:
        if self.deletion_status == DeletionStatus.NOT_APPLICABLE.value:
            steps_str = "[]"
        else:
            # Steps must be consecutive starting at 1
            sorted_steps = sorted(self.steps, key=lambda s: s.sort_key())
            renumbered = []
            for idx, s in enumerate(sorted_steps, 1):
                renumbered.append(
                    Step(
                        step_no=idx,
                        phase=s.phase,
                        system_id=s.system_id,
                        resource_id=s.resource_id,
                        operation=s.operation,
                        state=s.state,
                        evidence_id=s.evidence_id,
                    ).to_dict()
                )
            steps_str = json.dumps(renumbered, separators=(",", ":"))
        return (self.case_id, self.deletion_status, steps_str)
