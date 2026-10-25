import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path("code").resolve()))
from evaluation.main import validate_csv

class ValidatorNegativeControlsTest(unittest.TestCase):

    def run_val(self, rows, header=None, expected_count=None):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, suffix=".csv") as tf:
            writer = csv.writer(tf)
            if header is not None:
                writer.writerow(header)
            else:
                writer.writerow(["case_id", "deletion_status", "steps_json"])
            for r in rows:
                writer.writerow(r)
            tf_path = Path(tf.name)
        try:
            errors = validate_csv(tf_path, expected_count=expected_count)
            return errors
        finally:
            if tf_path.exists():
                tf_path.unlink()

    def test_01_missing_header(self):
        errors = self.run_val([], header=["case", "status", "json"])
        self.assertTrue(any("Invalid header" in e for e in errors))

    def test_02_row_count_mismatch(self):
        errors = self.run_val([["case_01", "NOT_APPLICABLE", "[]"]], expected_count=518)
        self.assertTrue(any("Row count mismatch" in e for e in errors))

    def test_03_invalid_status(self):
        errors = self.run_val([["case_01", "MAYBE_DELETED", "[]"]])
        self.assertTrue(any("Invalid deletion_status" in e for e in errors))

    def test_04_malformed_json(self):
        errors = self.run_val([["case_01", "COMPLETE", "{bad json]"]])
        self.assertTrue(any("Malformed JSON" in e for e in errors))

    def test_05_missing_step_fields(self):
        # Missing 'operation' and 'state'
        step = {"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "evidence_id": "ev_1"}
        errors = self.run_val([["case_01", "COMPLETE", json.dumps([step])]])
        self.assertTrue(any("Missing required fields" in e for e in errors))

    def test_06_forbidden_extra_step_fields(self):
        # Extra 'internal_score'
        step = {"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev_1", "internal_score": 99}
        errors = self.run_val([["case_01", "COMPLETE", json.dumps([step])]])
        self.assertTrue(any("Forbidden extra fields" in e for e in errors))

    def test_07_invalid_phase_operation_combination(self):
        # ANONYMIZE_RECORD is REMEDIATION, not FINDING
        step = {"step_no": 1, "phase": "FINDING", "system_id": "account_service", "resource_id": "acc_1", "operation": "ANONYMIZE_RECORD", "state": "PRESENT", "evidence_id": "ev_1"}
        errors = self.run_val([["case_01", "INCOMPLETE", json.dumps([step])]])
        self.assertTrue(any("not allowed in phase" in e for e in errors))

    def test_08_incorrect_step_numbering(self):
        # step_no starts at 2 instead of 1
        step = {"step_no": 2, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev_1"}
        errors = self.run_val([["case_01", "COMPLETE", json.dumps([step])]])
        self.assertTrue(any("step_no" in e and "consecutive index" in e for e in errors))

    def test_09_complete_with_empty_evidence_id(self):
        step = {"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}
        errors = self.run_val([["case_01", "COMPLETE", json.dumps([step])]])
        self.assertTrue(any("COMPLETE verification step must cite valid evidence_id" in e for e in errors))

    def test_10_incomplete_remediation_with_nonempty_evidence_id(self):
        step1 = {"step_no": 1, "phase": "FINDING", "system_id": "account_service", "resource_id": "acc_1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev_1"}
        step2 = {"step_no": 2, "phase": "REMEDIATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": "ev_1"} # Error!
        step3 = {"step_no": 3, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}
        errors = self.run_val([["case_01", "INCOMPLETE", json.dumps([step1, step2, step3])]])
        self.assertTrue(any("INCOMPLETE REMEDIATION step must have empty evidence_id" in e for e in errors))

    def test_11_out_of_order_phases(self):
        # REMEDIATION before FINDING
        step1 = {"step_no": 1, "phase": "REMEDIATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""}
        step2 = {"step_no": 2, "phase": "FINDING", "system_id": "account_service", "resource_id": "acc_1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev_1"}
        errors = self.run_val([["case_01", "INCOMPLETE", json.dumps([step1, step2])]])
        self.assertTrue(any("violates phase ordering" in e for e in errors))

    def test_12_incomplete_missing_remediation_step(self):
        step1 = {"step_no": 1, "phase": "FINDING", "system_id": "account_service", "resource_id": "acc_1", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "ev_1"}
        step2 = {"step_no": 2, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}
        errors = self.run_val([["case_01", "INCOMPLETE", json.dumps([step1, step2])]])
        self.assertTrue(any("INCOMPLETE case must have at least one REMEDIATION step" in e for e in errors))

    def test_13_unsorted_case_ids(self):
        rows = [
            ["case_02", "NOT_APPLICABLE", "[]"],
            ["case_01", "NOT_APPLICABLE", "[]"],
        ]
        errors = self.run_val(rows)
        self.assertTrue(any("not sorted strictly by case_id" in e for e in errors))

    def test_14_duplicate_case_ids(self):
        rows = [
            ["case_01", "NOT_APPLICABLE", "[]"],
            ["case_01", "NOT_APPLICABLE", "[]"],
        ]
        errors = self.run_val(rows)
        self.assertTrue(any("Duplicate case_ids detected" in e for e in errors))

    def test_15_not_applicable_with_nonempty_steps(self):
        step = {"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "acc_1", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "ev_1"}
        errors = self.run_val([["case_01", "NOT_APPLICABLE", json.dumps([step])]])
        self.assertTrue(any("NOT_APPLICABLE must have empty steps_json []" in e for e in errors))

if __name__ == "__main__":
    unittest.main()
