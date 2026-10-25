"""Comprehensive regression and negative controls test suite for identity enrichment and nested SQL details extraction."""

import sys
from pathlib import Path

# Add code directory to path
CODE_DIR = Path(__file__).resolve().parent.parent / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from audit_engine import AuditEngine
from evidence_loader import EvidenceLoader, ObservedResource, EvidenceFileMeta
from models import DeletionRequestCase, StepPhase, StepOperation, ResourceState


def test_sql_owner_email_extraction():
    """Verify that SQL replica parsing extracts owner_email and USER_EXPORT category from record_json."""
    loader = EvidenceLoader(Path("dataset"))
    
    # Check that export_3120 was properly parsed and associated with oeze0067@fastmail.com
    exports = [o for o in loader.all_observations if o.resource_id == "export_3120"]
    assert len(exports) >= 1, "export_3120 should be parsed from evidence_47"
    
    exp = exports[0]
    assert exp.system_id == "export_service", f"Expected export_service, got {exp.system_id}"
    assert exp.data_category == "USER_EXPORT", f"Expected USER_EXPORT, got {exp.data_category}"
    assert exp.email == "oeze0067@fastmail.com", f"Expected oeze0067@fastmail.com, got {exp.email}"
    assert exp.state == "PRESENT", f"Expected state PRESENT, got {exp.state}"
    assert exp.evidence_id == "evidence_47", f"Expected evidence_47, got {exp.evidence_id}"


def test_case_504_end_to_end():
    """Verify case_504 end-to-end: export_3120 flags INCOMPLETE with DELETE_RECORD remediation."""
    engine = AuditEngine(Path("dataset"))
    case = DeletionRequestCase(
        case_id="case_504",
        email="oeze0067@fastmail.com",
        requested_at="2026-01-27T07:00:00Z",
        reported_status="PARTIALLY_COMPLETE",
        reported_at="2026-01-29T07:00:00Z",
        audit_at="2026-02-08T07:00:00Z",
        request_text="I would like to submit a request to delete this account and its personal data.",
    )
    result = engine.audit_case(case)
    
    assert result.deletion_status == "INCOMPLETE", f"case_504 must be INCOMPLETE, got {result.deletion_status}"
    
    # Check findings
    findings = [s for s in result.steps if s.phase == "FINDING"]
    assert any(s.system_id == "export_service" and s.resource_id == "export_3120" and s.operation == "REPORT_REMAINING_RECORD" for s in findings), \
        "Findings must report export_3120 as remaining record"
    
    # Check remediation
    remediations = [s for s in result.steps if s.phase == "REMEDIATION"]
    assert any(s.system_id == "export_service" and s.resource_id == "export_3120" and s.operation == "DELETE_RECORD" for s in remediations), \
        "Remediation must propose DELETE_RECORD for export_3120"


def test_negative_mismatched_owner():
    """Negative test: An export with a different owner must NOT be associated with the user."""
    engine = AuditEngine(Path("dataset"))
    case = DeletionRequestCase(
        case_id="test_neg_01",
        email="unrelated_user@example.com",
        requested_at="2026-01-27T07:00:00Z",
        reported_status="COMPLETE",
        reported_at="2026-01-29T07:00:00Z",
        audit_at="2026-02-08T07:00:00Z",
        request_text="Please delete my data.",
    )
    result = engine.audit_case(case)
    
    # Must NOT contain export_3120
    assert not any(s.resource_id == "export_3120" for s in result.steps), \
        "export_3120 must not be matched to an unrelated email"


def test_negative_post_cutoff_evidence():
    """Negative test: Evidence captured strictly after audit_at must never be included."""
    engine = AuditEngine(Path("dataset"))
    # Audit cutoff BEFORE evidence_47 was captured (captured 2026-02-08T07:00:00Z)
    case = DeletionRequestCase(
        case_id="test_neg_cutoff",
        email="oeze0067@fastmail.com",
        requested_at="2026-01-27T07:00:00Z",
        reported_status="PARTIALLY_COMPLETE",
        reported_at="2026-01-29T07:00:00Z",
        audit_at="2026-02-01T07:00:00Z",  # Cutoff is before evidence_47 (Feb 8)
        request_text="Please delete my account.",
    )
    result = engine.audit_case(case)
    
    # export_3120 was captured on 2026-02-08, so at 2026-02-01 it must NOT appear
    assert not any(s.resource_id == "export_3120" for s in result.steps), \
        "export_3120 captured after audit_at must not be included"


def test_negative_invalid_hash_and_identity():
    """Negative test: Malformed or non-hex hashes in details must NOT be enriched as email_hash."""
    loader = EvidenceLoader(Path("dataset"))
    malformed_obs = ObservedResource(
        system_id="test_service",
        resource_id="test_001",
        data_category="USER_PROFILE",
        state="PRESENT",
        evidence_id="evidence_01",
        captured_at="2026-09-01T00:00:00Z",
        details={"email_hash": "not_a_valid_64_char_hex_hash", "user_id": "not_user_prefix"},
    )
    loader._record_obs(malformed_obs)
    
    assert malformed_obs.email_hash is None, "Malformed hash must not be accepted"
    assert malformed_obs.user_id is None, "Invalid user_id must not be accepted"


if __name__ == "__main__":
    test_sql_owner_email_extraction()
    print("PASS: test_sql_owner_email_extraction")
    test_case_504_end_to_end()
    print("PASS: test_case_504_end_to_end")
    test_negative_mismatched_owner()
    print("PASS: test_negative_mismatched_owner")
    test_negative_post_cutoff_evidence()
    print("PASS: test_negative_post_cutoff_evidence")
    test_negative_invalid_hash_and_identity()
    print("PASS: test_negative_invalid_hash_and_identity")
    print("\nALL 5 REGRESSION & NEGATIVE CONTROL TESTS PASSED!")
