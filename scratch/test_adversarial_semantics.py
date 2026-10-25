"""Adversarial testing suite for temporal, evidence, and identity semantics."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path("code").resolve()))

from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource
from identity_resolver import IdentityResolver
from intent_classifier import IntentClassifier
from models import (
    DeletionRequestCase,
    DeletionStatus,
    ResourceState,
    StepOperation,
    StepPhase,
)

class AdversarialSemanticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_dir = Path("dataset")
        cls.engine = AuditEngine(cls.dataset_dir)
        cls.resolver = cls.engine.identity_resolver
        cls.loader = cls.engine.evidence_loader

    def test_01_deletion_event_after_audit_at_ignored(self):
        """Scenario 1: A successful deletion event captured after audit_at must not be used."""
        case = DeletionRequestCase(
            case_id="adv_01",
            email="elena.v@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Please delete my account permanently.",
        )
        # Create an observation before audit_at (PRESENT) and one after audit_at (ABSENT)
        obs_before = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_01",
            data_category="USER_PROFILE",
            state="PRESENT",
            evidence_id="evidence_54",
            captured_at="2026-09-04T12:00:00Z",
            email="elena.v@example.com",
        )
        obs_after = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_01",
            data_category="USER_PROFILE",
            state="ABSENT",
            evidence_id="evidence_55",
            captured_at="2026-09-06T12:00:00Z", # After audit_at
            email="elena.v@example.com",
        )
        self.loader.all_observations.extend([obs_before, obs_after])
        res = self.engine.audit_case(case)
        # At audit_at, the account was still PRESENT, so status must be INCOMPLETE
        self.assertEqual(res.deletion_status, DeletionStatus.INCOMPLETE.value)
        self.assertTrue(any(s.resource_id == "acc_adv_01" and s.operation == "REPORT_REMAINING_RECORD" for s in res.steps))

    def test_02_newer_observation_contradicts_older_deletion_success(self):
        """Scenario 2: A newer observation showing PRESENT overrides older deletion claims."""
        case = DeletionRequestCase(
            case_id="adv_02",
            email="marcus.t@example.com",
            requested_at="2026-08-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-08-02T10:00:00Z",
            audit_at="2026-08-10T12:00:00Z",
            request_text="Delete my profile.",
        )
        obs_old_absent = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_02",
            data_category="USER_PROFILE",
            state="ABSENT",
            evidence_id="evidence_01",
            captured_at="2026-08-03T12:00:00Z",
            email="marcus.t@example.com",
        )
        obs_new_present = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_02",
            data_category="USER_PROFILE",
            state="PRESENT",
            evidence_id="evidence_02",
            captured_at="2026-08-05T12:00:00Z", # Newer recreation
            email="marcus.t@example.com",
        )
        self.loader.all_observations.extend([obs_old_absent, obs_new_present])
        res = self.engine.audit_case(case)
        self.assertEqual(res.deletion_status, DeletionStatus.INCOMPLETE.value)

    def test_03_stale_snapshot_superseded_by_newer_valid_absence(self):
        """Scenario 3: An older snapshot showing PRESENT is superseded by a newer valid absence proof before cutoff."""
        case = DeletionRequestCase(
            case_id="adv_03",
            email="sophia.l@example.com",
            requested_at="2026-07-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-07-05T10:00:00Z",
            audit_at="2026-07-15T12:00:00Z",
            request_text="Please delete all data.",
        )
        obs_stale = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_03",
            data_category="USER_PROFILE",
            state="PRESENT",
            evidence_id="evidence_10",
            captured_at="2026-07-02T12:00:00Z",
            email="sophia.l@example.com",
        )
        obs_verified = ObservedResource(
            system_id="account_service",
            resource_id="acc_adv_03",
            data_category="USER_PROFILE",
            state="ABSENT",
            evidence_id="evidence_11",
            captured_at="2026-07-10T12:00:00Z",
            email="sophia.l@example.com",
        )
        self.loader.all_observations.extend([obs_stale, obs_verified])
        res = self.engine.audit_case(case)
        self.assertEqual(res.deletion_status, DeletionStatus.COMPLETE.value)
        self.assertTrue(any(s.resource_id == "acc_adv_03" and s.state == "ABSENT" for s in res.steps))

    def test_04_backup_retained_under_policy(self):
        """Scenario 4: A backup with restore_allowed=False is compliant under retention policy."""
        case = DeletionRequestCase(
            case_id="adv_04",
            email="david.k@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Close account and purge data.",
        )
        obs_backup = ObservedResource(
            system_id="backup_service",
            resource_id="backup_adv_04",
            data_category="BACKUP_ARCHIVE",
            state="BLOCKED",
            evidence_id="evidence_54",
            captured_at="2026-09-03T12:00:00Z",
            email="david.k@example.com",
            is_restore_risk=False,
        )
        self.loader.all_observations.append(obs_backup)
        res = self.engine.audit_case(case)
        # Should verify restore blocked, NOT report a risk
        self.assertTrue(any(s.operation == "VERIFY_RESTORE_BLOCKED" for s in res.steps))
        self.assertFalse(any(s.operation == "REPORT_RESTORE_RISK" for s in res.steps))

    def test_05_restore_risk_detection(self):
        """Scenario 5: A backup with restore_allowed=True triggers REPORT_RESTORE_RISK and BLOCK_RESTORE."""
        case = DeletionRequestCase(
            case_id="adv_05",
            email="hanna.b@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Delete my personal records.",
        )
        obs_backup = ObservedResource(
            system_id="backup_service",
            resource_id="backup_adv_05",
            data_category="BACKUP_ARCHIVE",
            state="ACTIVE",
            evidence_id="evidence_54",
            captured_at="2026-09-03T12:00:00Z",
            email="hanna.b@example.com",
            is_restore_risk=True,
        )
        self.loader.all_observations.append(obs_backup)
        res = self.engine.audit_case(case)
        self.assertEqual(res.deletion_status, DeletionStatus.INCOMPLETE.value)
        self.assertTrue(any(s.operation == "REPORT_RESTORE_RISK" and s.state == "ACTIVE" for s in res.steps))
        self.assertTrue(any(s.operation == "BLOCK_RESTORE" and s.state == "BLOCKED" for s in res.steps))

    def test_06_active_data_flow_detection(self):
        """Scenario 6: Active connector/stream triggers REPORT_ACTIVE_DATA_FLOW and DISABLE_DATA_FLOW."""
        case = DeletionRequestCase(
            case_id="adv_06",
            email="liam.c@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Delete account and stop sending data.",
        )
        obs_flow = ObservedResource(
            system_id="integration_service",
            resource_id="flow_adv_06",
            data_category="ACTIVE_DATA_FLOW",
            state="ACTIVE",
            evidence_id="evidence_54",
            captured_at="2026-09-03T12:00:00Z",
            email="liam.c@example.com",
            is_active_flow=True,
        )
        self.loader.all_observations.append(obs_flow)
        res = self.engine.audit_case(case)
        self.assertEqual(res.deletion_status, DeletionStatus.INCOMPLETE.value)
        self.assertTrue(any(s.operation == "REPORT_ACTIVE_DATA_FLOW" and s.state == "ACTIVE" for s in res.steps))
        self.assertTrue(any(s.operation == "DISABLE_DATA_FLOW" and s.state == "DISABLED" for s in res.steps))

    def test_07_unrelated_subject_isolation(self):
        """Scenario 7: Evidence belonging to an unrelated subject must never be included."""
        case = DeletionRequestCase(
            case_id="adv_07",
            email="user_a@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Delete my account.",
        )
        obs_other = ObservedResource(
            system_id="account_service",
            resource_id="acc_unrelated_99",
            data_category="USER_PROFILE",
            state="PRESENT",
            evidence_id="evidence_54",
            captured_at="2026-09-03T12:00:00Z",
            email="user_b@example.com", # Completely different user
            user_id="user_b_id",
        )
        self.loader.all_observations.append(obs_other)
        res = self.engine.audit_case(case)
        self.assertFalse(any(s.resource_id == "acc_unrelated_99" for s in res.steps))

    def test_08_evidence_capture_after_cutoff_not_usable(self):
        """Scenario 8: Evidence file captured after cutoff is excluded even if observation is claimed earlier."""
        case = DeletionRequestCase(
            case_id="adv_08",
            email="noah.p@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Delete my data.",
        )
        obs_late = ObservedResource(
            system_id="search_service",
            resource_id="search_late_08",
            data_category="SEARCH_INDEX_ENTRY",
            state="PRESENT",
            evidence_id="evidence_late",
            captured_at="2026-09-10T12:00:00Z", # File captured 5 days after cutoff
            email="noah.p@example.com",
        )
        self.loader.all_observations.append(obs_late)
        res = self.engine.audit_case(case)
        self.assertFalse(any(s.resource_id == "search_late_08" for s in res.steps))

    def test_09_tombstone_pii_leakage(self):
        """Scenario 9: An account tombstone with exposed email or phone triggers REPORT_EXPOSED_PII and REDACT_RECORD."""
        case = DeletionRequestCase(
            case_id="adv_09",
            email="tombstone.user@example.com",
            requested_at="2026-09-01T10:00:00Z",
            reported_status="COMPLETE",
            reported_at="2026-09-02T10:00:00Z",
            audit_at="2026-09-05T12:00:00Z",
            request_text="Delete account permanently.",
        )
        obs_tombstone = ObservedResource(
            system_id="identity_service",
            resource_id="tombstone_adv_09",
            data_category="ACCOUNT_TOMBSTONE",
            state="PRESENT",
            evidence_id="evidence_54",
            captured_at="2026-09-03T12:00:00Z",
            email="tombstone.user@example.com",
            is_tombstone=True,
            has_exposed_pii=True,
        )
        self.loader.all_observations.append(obs_tombstone)
        res = self.engine.audit_case(case)
        self.assertEqual(res.deletion_status, DeletionStatus.INCOMPLETE.value)
        self.assertTrue(any(s.operation == "REPORT_EXPOSED_PII" for s in res.steps))
        self.assertTrue(any(s.operation == "REDACT_RECORD" for s in res.steps))

    def test_10_historical_identifier_resolution(self):
        """Scenario 10: Request submitted using historical email resolves correctly via user_audit_log."""
        # user_12 historical email was minjun.kim@gmail.com
        ident = self.resolver.resolve_email("minjun.kim@gmail.com")
        self.assertIsNotNone(ident)
        self.assertEqual(ident.user_id, "user_12")
        self.assertTrue(len(ident.all_hashes) > 0)

if __name__ == "__main__":
    unittest.main()
