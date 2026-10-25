# DESIGN.md — Ghost Data Still Exists Deletion-Audit Agent

## 1. Problem in One Paragraph
Northstar Shop lost $2.4 million when a customer who was supposedly deleted reappeared as a ghost in its systems because secondary databases, replicas, search indexes, analytics profiles, support attachments, exports, logs, backups, and active synchronization pipelines preserved or resurrected the customer's personal data. For each deletion request in `dataset/deletion_requests.csv`, the audit agent must: (1) determine whether the request authorizes deletion (`COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`); (2) resolve the subject's current and historical identifiers across `user_identities.csv` and `user_audit_log.csv`; (3) establish the ground-truth state of all subject records and data pipelines strictly at or before the case's `audit_at` cutoff from the available evidence files under `dataset/evidence/` rather than trusting unverified workflow claims; (4) apply the 15 data categories and retention conditions in `dataset/deletion_rules.csv`; and (5) produce the canonical `output.csv` containing sorted `case_id`, `deletion_status`, and a strictly ordered, schema-compliant `steps_json` containing findings, remediation actions, and verification checks.

---

## 2. Output Contract
The solution produces `output.csv` at the repository root with exactly 518 data rows (+1 header row) sorted by `case_id` in ascending order (`case_33` through `case_550`).

| Column | Allowed Values (Exact) | Source (Model Field or Code Rule) | Rule ID |
|---|---|---|---|
| `case_id` | `case_33` to `case_550` | Input row verbatim (never reformatted) | CONTRACT-01 |
| `deletion_status` | `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE` | Code decision rule based on request authorization and evidence reconciliation | DECISION-STATUS |
| `steps_json` | Valid JSON array string of step objects | Code step generation engine strictly ordered by phase, operation, system_id, resource_id | STEPS-SERIALIZE |

### Constraints & Formatting:
- **Encoding**: UTF-8 with standard LF (`\n`) newlines.
- **CSV quoting**: RFC 4180 standard escaping; `steps_json` cells properly quoted.
- **Step object schema**:
  ```json
  {
    "step_no": 1,
    "phase": "FINDING" | "REMEDIATION" | "VERIFICATION",
    "system_id": "<string>",
    "resource_id": "<string>",
    "operation": "<allowed_operation>",
    "state": "<allowed_state>",
    "evidence_id": "<file_id | activity_id | audit_id | empty string>"
  }
  ```
- **Consecutive numbering**: `step_no` starts at `1` and increments consecutively with no gaps.
- **Evidence citing**: Findings cite valid participant-visible evidence IDs. Verification steps in `COMPLETE` cases cite evidence proving compliant state. Proposed remediation and future verification steps in `INCOMPLETE` cases use an empty string `""`. Non-deletion requests use an empty array `[]`.

---

## 3. Architecture

### Entry Point:
- `code/main.py` is the top-level CLI entry point.
- Also callable with optional arguments: `--input dataset/deletion_requests.csv --output output.csv`.

### Pipeline Stages (in strict sequential order):
1. **Input Loading & Schema Validation**: Ingest `deletion_requests.csv`, `deletion_rules.csv`, `user_identities.csv`, `user_audit_log.csv`, `system_activity.csv`, and `evidence_files.csv`. Validate required columns, types, and uniqueness.
2. **Identity Resolution**: For each request email, resolve the primary `user_id`, current name, current phone, current email hash, and historical email/phone/hash changes from `user_audit_log.csv`.
3. **Intent Authorization Classifier**: Classify `request_text` into deletion authorization vs. non-deletion action (e.g., access, export, rectification, marketing opt-out, contact info update). Non-deletion requests immediately route to `NOT_APPLICABLE` with `steps_json=[]`.
4. **Temporal Cutoff & Activity Tracing**: Filter all evidence and system activity events strictly to timestamps $\le \text{audit\_at}$. Group deletion-worker operational streams and candidate resources.
5. **Multi-Source Evidence Inspection & Fact Extraction**:
   - Structured JSON snapshot bundles (`customer_data_snapshot_bundle_*.json`, `service_resource_export_*.json`).
   - SQL snapshot dumps (SQLite tables: failover replicas, read replicas, search primaries, customer inventory).
   - Log files (trace readbacks, observability exports, syslog archives, support logs).
   - Document artifacts (PDF reports and registers parsed via `pypdf`).
   - Image consoles (deterministic ground-truth facts extracted from admin, search, connector, telemetry, and storage consoles).
6. **Policy Engine (`deletion_rules.csv`)**: Reconcile observed resource states against rules 01 through 15:
   - Identify remaining records (`REPORT_REMAINING_RECORD`).
   - Identify exposed PII on retained records, messages, and tombstones (`REPORT_EXPOSED_PII`).
   - Identify enabled data pipelines (`REPORT_ACTIVE_DATA_FLOW`).
   - Identify unblocked restore paths (`REPORT_RESTORE_RISK`).
   - Respect lawful retention exemptions (security audit logs within retention period, active legal holds).
7. **Remediation & Verification Planning**:
   - For incomplete deletions: generate ordered remediation operations (`DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `DELETE_RECORD`, `REDACT_RECORD`, `ANONYMIZE_RECORD`) followed by post-remediation verification checks.
   - For complete deletions: emit verification checks citing the exact evidence proving absence, redaction, anonymization, disabled flow, and blocked restore.
8. **Deterministic Sorting & Serialization**: Sort steps using canonical tuple `(phase_priority, operation_priority, system_id, resource_id)`. Renumber steps consecutively from 1. Serialize `steps_json` to JSON and write final `output.csv`.
9. **Automated Verification & Evaluation**: Run independent validators against `output.csv` checking row count, sorting, column types, JSON integrity, and timing consistency.

---

## 4. The Seam
The boundary between input parsing and deterministic rule execution is represented by explicit dataclasses:

```python
@dataclass(frozen=True)
class SubjectIdentity:
    user_id: str
    name: str
    current_email: str
    all_emails: tuple[str, ...]
    all_phones: tuple[str, ...]
    all_hashes: tuple[str, ...]

@dataclass(frozen=True)
class ResourceObservation:
    system_id: str
    resource_id: str
    observed_state: str        # 'ABSENT', 'PRESENT', 'REDACTED', 'ANONYMIZED', 'ACTIVE', 'BLOCKED', 'DISABLED'
    data_category: str        # Matches deletion_rules.csv categories
    evidence_id: str          # file_id proving observation
    captured_at: str          # ISO-8601 timestamp <= audit_at
    is_tombstone: bool = False
    has_exposed_pii: bool = False
    is_retained_policy: bool = False
    is_active_flow: bool = False
    is_restore_risk: bool = False

@dataclass(frozen=True)
class AuditDecision:
    case_id: str
    status: str               # 'COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'
    steps: tuple[Step, ...]
```

Code enforces all invariants: decisions are based on booleans and enums, never free text.

---

## 5. Decision Rules (Ordered)

| Order | Rule ID | Condition | Outcome | Why this order |
|---|---|---|---|---|
| 1 | R_NON_DELETION | Request text does not authorize deletion (access, export, update, opt-out) | `NOT_APPLICABLE`, `steps_json=[]` | Highest priority: unauthorized operations must not trigger deletion actions or audits |
| 2 | R_RISK_ACTIVE_FLOW | Enabled connector / synchronization process can copy or resurrect personal data | Emit `REPORT_ACTIVE_DATA_FLOW`, remediate with `DISABLE_DATA_FLOW`, verify `VERIFY_DATA_FLOW_DISABLED` | Data flows must be severed before modifying downstream or upstream stores |
| 3 | R_RISK_RESTORE | Backup archive permits restore of deleted user data | Emit `REPORT_RESTORE_RISK`, remediate with `BLOCK_RESTORE`, verify `VERIFY_RESTORE_BLOCKED` | Restore paths must be blocked to prevent immediate resurrection |
| 4 | R_REMAINING_RECORD | Record that policy requires deleted remains present in primary, replica, index, or export | Emit `REPORT_REMAINING_RECORD`, remediate with `DELETE_RECORD`, verify `VERIFY_RECORD_ABSENT` | Prohibited data stores must be identified and removed |
| 5 | R_EXPOSED_PII | Retained support message, analytics profile, or tombstone exposes direct identifiers | Emit `REPORT_EXPOSED_PII`, remediate with `REDACT_RECORD` or `ANONYMIZE_RECORD` | Policy-permitted records must be sanitized |
| 6 | R_RETAINED_PERMITTED | Security audit log or legal hold record is required to be retained by policy | Verify `VERIFY_RECORD_PRESENT` | Compliance records must remain available and proven |
| 7 | R_TOMBSTONE_COMPLIANT | Tombstone preserves internal `user_id` while direct PII is removed | Verify `VERIFY_RECORD_REDACTED` | Account tombstone contract preserves stable references |
| 8 | R_RECORD_ABSENT | Primary profile and secondary copies confirmed absent at `audit_at` | Verify `VERIFY_RECORD_ABSENT` | Evidence proves deletion completion |
| 9 | R_STATUS_RESOLUTION | If any finding exists -> `INCOMPLETE`; else if all required verifications hold -> `COMPLETE` | Final `deletion_status` | Status is a deterministic derivative of findings and verifications |

---

## 6. Escalation and Refusal
- **Reply with NOT_APPLICABLE when**: `request_text` explicitly requests data access, porting/export, contact updates, invoice copies, or marketing unsubscribe without authorizing account or data deletion.
- **Reply with INCOMPLETE when**: Any violation of `deletion_rules.csv`, remaining profile, unredacted tombstone, un-anonymized profile, active data flow, or unblocked backup is discovered at or before `audit_at`.
- **Reply with COMPLETE when**: All prohibited copies are verified absent/sanitized, required retained logs are verified present, no active flows or restore risks exist, and valid participant evidence proves the compliant state.
- **Default when evidence is missing/contradictory**: Incomplete with honest finding citing the earliest contradictory record. "Complete" requires affirmative evidence proof; absence of evidence is never assumed to be proof of deletion.
- **Why "escalate everything" and "reply to everything" are both wrong**: Blanket classification fails the 30% Output CSV accuracy and 30% AI interview depth; the dataset contains a precise balance of verified complete deletions, complex incomplete multi-system violations, and explicit non-deletion requests.

---

## 7. Input Validation and Overrides
1. **Empty File / Missing Header**: Validate required CSV columns (`case_id`, `email`, `requested_at`, `reported_status`, `reported_at`, `audit_at`, `request_text`). Raise descriptive error.
2. **Missing Identifiers**: If email is unresolvable in `user_identities.csv`, check `user_audit_log.csv` historical records.
3. **Temporal Bounds**: If evidence `captured_at > audit_at`, discard from consideration for that case to prevent temporal leakage.
4. **Adversarial / Injection Defense**: Treat `request_text` strictly as untrusted user input; search for intent keywords using regex/semantic rules rather than executing embedded instructions.
5. **Decoy Data Filtering**: Distinguish unrelated users with similar emails (e.g. `g.silva76.jr@gmail.com` vs `g.silva76@gmail.com`).

---

## 8. Failure Handling

| Failure Type | What Happens to the Row | Logged Where | Run Continues? |
|---|---|---|---|
| Malformed input text | Sanitized and parsed using fallback regex | `log.txt` warning | Yes |
| Missing user in current identities | Fall back to historical identity audit log | `log.txt` info | Yes |
| Unhandled exception on single row | Emits conservative safe row, records error | `log.txt` error | Yes (never halts batch) |
| File I/O transient error | Bounded retry (max 3), then fallback | `log.txt` error | Yes |

---

## 9. Retrieval Architecture
- **In-Memory Pre-Indexed Datastores**:
  - `IdentityIndex`: Maps current and historical emails, phones, and email hashes to stable `user_id`.
  - `ActivityIndex`: Indexes `system_activity.csv` by `resource_id` and timestamp window.
  - `EvidenceIndex`: Maps `file_id` to metadata, timestamps, and structured object trees.
  - `ResourceStateIndex`: Aggregates point-in-time states of resources per user from SQL, JSON, logs, documents, and console captures.
- **Recall Target**: 100% recall on the 32 sample cases before running full evaluation.

---

## 10. Test Plan
- **Unit Tests**:
  - Identity resolution (current vs. historical).
  - Authorization classification (deletion vs. non-deletion).
  - Temporal cutoff filtering.
  - Sorting and step numbering order.
  - JSON serialization compliance.
- **Sample Regression Tests**: Run all 32 public sample cases against `sample_output.csv`. Measure case status accuracy, step accuracy, operation accuracy, and evidence ID citations.
- **Adversarial & Edge Case Tests**:
  - Unrelated decoy users with similar emails.
  - Account tombstones (redacted vs. exposed PII).
  - Historical email change before deletion.
  - Data flow active while database deleted.
  - Backup restore unblocked while database deleted.
  - Non-deletion requests (update phone, export data, invoices, email change).
- **Determinism Check**: Run pipeline twice from clean state; assert byte-for-byte identical output.

---

## 11. Decisions Log

| # | Decision | Alternative Rejected | Why |
|---|---|---|---|
| 1 | Hybrid deterministic architecture with parsed evidence indexing | Pure LLM prompt generating full CSV | Pure LLM introduces hallucinations, formatting bugs, non-determinism, and token cost exceeding budget |
| 2 | Direct programmatic extraction of all 11 console image artifacts | External OCR binary (tesseract) | Tesseract is not installed on the system; direct extraction guarantees 100% deterministic, error-free capture |
| 3 | Use `pypdf` for native PDF text extraction | Converting PDFs to images or skipping documents | `pypdf` is installed, lightweight, fully offline, and reliably extracts exact text from support attachments and registers |
| 4 | Strict 4-tuple sorting key for `steps_json` | Ad-hoc or unsorted step lists | The grader strictly compares array order; sorting by phase, operation, system_id, resource_id guarantees exact canonical order |
| 5 | Explicit resolution of historical emails via `user_audit_log.csv` | Matching only on current `user_identities.csv` email | 107 historical email changes exist; matching only current email causes false misses on valid deletion requests |
| 6 | Separate non-deletion requests as `NOT_APPLICABLE` with `steps_json=[]` | Auditing them as deletion cases | Section 6.3 explicitly defines `NOT_APPLICABLE` with `[]` for cases where deletion was not authorized |

---

## 12. Known Limits
1. If an organizer creates a novel image format outside the 11 known console UI structures without an accessible text layer, image OCR requires an external multimodal API or local vision model.
2. Highly ambiguous multi-intent natural language requests (e.g. "delete my old order history but keep my account") are classified according to whether account deletion is authorized.
3. If activity logs contain overlapping timestamp collisions for different users without resource identifiers, matching relies on temporal proximity to reported workflow intervals.

---

## 13. Review Gate
- [x] Every output column has a named source
- [x] Every allowed label is produced by a rule
- [x] Escalation rule explained in one sentence
- [x] Risk rules come first in the order
- [x] Failure table has no empty cell
- [x] Decisions log has at least 5 entries
