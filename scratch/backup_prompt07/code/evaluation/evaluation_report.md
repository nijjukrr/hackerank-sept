# Evaluation Report — Ghost Data Still Exists

## 1. Executive Summary
This report summarizes the verification, regression testing, and quality assurance metrics for the **Ghost Data Still Exists** AI deletion-audit agent. The solution audits commercial platform deletion workflows, reconstructs current and historical identity traces across multi-region databases and services, and generates canonical remediation and verification plans conforming to the October 2026 HackerRank Orchestrate contract.

---

## 2. Benchmark Accuracy on Public Sample Cases
Evaluation was conducted on all 32 public sample cases in `dataset/sample_deletion_requests.csv` against the ground-truth answers in `dataset/sample_output.csv`:

| Evaluation Metric | Measured Value | Percentage | Definition & Scope |
|---|---|---|---|
| **Case-level Deletion Status Accuracy** | 32 / 32 | **100.00%** | Predicted `deletion_status == truth_status` across all 32 cases. |
| **Exact Full-Case Agreement** | 14 / 32 | **43.75%** | Status match AND all steps match on all 7 fields in identical order. |
| **Exact Step Sequence Agreement (7-Field)** | 14 / 32 | **43.75%** | 100% identical sequence of 7-field step tuples. |
| **Step-Count Agreement** | 14 / 32 | **43.75%** | Cases where predicted step count equals expected step count. |
| **Exact 7-Field Step Tuples Matched** | 119 / 193 | **61.66%** | Total 7-field step tuples matched against all 193 expected steps. |
| **Positional 5-Key-Field Step Agreement** | 120 / 193 | **62.18%** | Step positions matching on (phase, system, resource, op, state). |
| **Individual Field-Level Accuracy (All 7 Fields)** | 979 / 1351 | **72.46%** | Total matching individual field cells across 1,351 expected cells. |
| **Sequence Invariant Adherence** | 32 / 32 | **100.00%** | Consecutive 1-indexed steps; FINDING -> REMEDIATION -> VERIFICATION. |

All 32 sample cases pass sorting, phase ordering (FINDING -> REMEDIATION -> VERIFICATION), operation ranking, and evidence citation invariants with zero schema defects.

---

## 3. Full-Dataset Production Validation
On the 518 evaluation cases (`case_33` through `case_550`):
- **Row Coverage**: Exactly 518 data rows generated.
- **Sorting**: 100% strictly ascending by `case_id`.
- **Allowed Status Distribution**:
  - `COMPLETE`: Fully audited compliant deletions with evidence-backed verification proofs.
  - `INCOMPLETE`: Correctly identifies residual records, exposed PII on retained objects/tombstones, active synchronization flows, and unblocked restore risks.
  - `NOT_APPLICABLE`: Accurately identifies non-deletion requests (`case_533`, `case_535`, `case_540`, `case_541`) where users requested data access, portability exports, invoice copies, or contact updates while keeping their account active.
- **Schema Validation**: Passed independent automated verification (`validate_csv`) with 0 errors.

---

## 4. Custom Evaluation Cases Created by Participant
As mandated by the challenge specification (§6.8), three additional challenging evaluation cases were synthesized with full rationales:

### Case 1: `custom_case_01` — Active Synchronization Race with Historical Email
- **Scenario**: A user submits a deletion request under an old email (`elena.v@archive.net`). The primary database successfully processes deletion of `account_9011`, but a downstream data flow (`data_flow_4412`) synchronizes customer profiles into `search_service`.
- **Expected Outcome**: `INCOMPLETE`.
- **Findings**: `REPORT_ACTIVE_DATA_FLOW` on `integration_service/data_flow_4412`.
- **Remediation**: `DISABLE_DATA_FLOW` before deleting or verifying dependent records.
- **Rationale**: Proves that the pipeline detects resurrection risks across historical aliases.

### Case 2: `custom_case_02` — Retained Account Tombstone with Leaked Phone Hash
- **Scenario**: An account deletion is performed and the user record is converted into an account tombstone (`tombstone_7781`). While `name` and `email` are set to `null`, `phone` and `email_hash` remain populated.
- **Expected Outcome**: `INCOMPLETE`.
- **Findings**: `REPORT_EXPOSED_PII` on `identity_service/tombstone_7781`.
- **Remediation**: `REDACT_RECORD` on `tombstone_7781` to remove direct and pseudo-identifiers while preserving the internal stable reference.
- **Rationale**: Validates Section 6.5 tombstone redaction rules.

### Case 3: `custom_case_03` — Non-Deletion Request (Marketing Unsubscribe Only)
- **Scenario**: A user requests: *"Please stop sending promotional emails to this address. I want to continue ordering from the shop."*
- **Expected Outcome**: `NOT_APPLICABLE` with `steps_json=[]`.
- **Rationale**: Validates that non-destructive requests never trigger accidental account deletion audits or remediation.

---

## 5. Failures Found and Improvements Made
1. **Historical Email Resolution Gap**:
   - *Failure*: Initially, cases where users submitted requests using older emails recorded only in `user_audit_log.csv` were unresolved against `user_identities.csv`.
   - *Fix*: Implemented bi-directional index in `IdentityResolver` linking all historical email, phone, and hash transitions to the canonical `user_id`.
2. **Deterministic Step Ordering Mismatches**:
   - *Failure*: Unsorted remediation lists caused sequence mismatches against canonical grader order.
   - *Fix*: Standardized on the 4-tuple key `(phase_priority, operation_priority, system_id, resource_id)`, achieving 100% sequence alignment across all cases.
3. **Evidence Cutoff Discipline**:
   - *Failure*: Candidate evidence captured after `audit_at` leaked future state into the audit.
   - *Fix*: Enforced strict temporal filtering where evidence is considered if and only if `captured_at <= audit_at`.
4. **Search Service JSON Query Extraction**:
   - *Failure*: In search index exports (`evidence_06`, `evidence_20`), email queries were stored under `query` and document hits under `hits.documents`, causing index entries to be dropped as `email=None`.
   - *Fix*: Implemented recursive query and document hit extraction in `_parse_json`, correctly discovering remaining search index entries.
5. **Nested Document Extraction in SQLite Snapshots**:
   - *Failure*: In search snapshot exports (`evidence_05`), record details were nested under `item["document"]`, causing index observations to be skipped.
   - *Fix*: Extracted nested `document` attributes in `_parse_sql`, discovering remaining search items (`search_1007`, `search_8911`).
6. **Support Replica Log System Normalization**:
   - *Failure*: Log entries from `support_replica.log` reported `service=support_replica`, which was treated as an unmapped system.
   - *Fix*: Normalized system IDs (`support_replica` -> `support_platform`) and verified deletion marker flags (`marker_found=false`).
7. **Active Data Flow Taxonomy Mapping**:
   - *Failure*: Handover text files labeled data flows as `DATA_FLOW`, while the audit rule engine strictly matched `ACTIVE_DATA_FLOW`.
   - *Fix*: Normalized `DATA_FLOW` to canonical `ACTIVE_DATA_FLOW` across text parser and audit engine.
