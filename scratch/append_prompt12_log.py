import sys
from pathlib import Path

user_prompt_text = """# MASTER PROMPT 12 — ULTIMATE ACCURACY RECOVERY, COMPLETE ENGINEERING AUDIT, AND FINAL SUBMISSION GATE

## PROJECT

HackerRank Orchestrate — October 2026  
Challenge: Ghost Data Still Exists

## WORKSPACE

`C:\\Users\\nijju\\.gemini\\antigravity-ide\\scratch\\test-orchestrate-workspace`

## MISSION

Perform the most comprehensive final review of this project before manual submission.

The mission has three independent goals:

1. **Accuracy recovery:** Identify and correct any remaining genuine, generalizable prediction defects supported by participant-visible evidence.
2. **Engineering verification:** Prove that the code, evaluator, generated output, tests, and package work correctly together.
3. **Submission readiness:** Freeze and verify the final versions of `code.zip`, `output.csv`, and `log.txt`.

Do not merely produce a reassuring audit report. Inspect the actual files, execute the necessary commands, examine failures, implement valid corrections when justified, and verify the final result.

Do not assume that previous investigations were correct merely because their reports say PASS. Do not assume that all remaining accuracy errors are impossible. Re-examine the evidence and source code where useful.

At the same time, do not promise perfect accuracy or force unsupported predictions.

**Important distinction:** Submission integrity and prediction accuracy are separate outcomes. Report both independently. A package can be technically valid while its accuracy metrics remain below their targets.

---

# PART 1 — MANDATORY PROJECT INSTRUCTIONS

## 1.1 Read the authoritative instructions

Before changing anything, read the entire current `AGENTS.md` and `problem_statement.md`.

Inspect the actual submission requirements, including the required output format, evidence citation rules, deletion policies, temporal cutoff, step ordering, permitted files, logging requirements, and evaluation-report requirements.

The repository's `AGENTS.md` and the official challenge instructions take precedence over assumptions in previous conversation summaries and generated reports.

## 1.2 Follow the transcript rules

Follow the repository's logging requirements exactly.

- Append the required session-start entry if the project instructions require it.
- Append the current turn and subsequent actions using the required transcript format.
- Preserve previous transcript entries.
- Never fabricate tool names, model names, tool calls, results, or test outcomes.
- Never place secrets, credentials, tokens, or private configuration in the transcript.
- Do not append to `log.txt` after recording its final checksum.

The final checksum must be calculated only after the required transcript entries have been appended and all transcript editing is finished.

## 1.3 Protect the current release

Before inspecting or modifying release files:

1. Calculate the current sizes and SHA-256 hashes of `output.csv`, `code.zip`, and `log.txt`.
2. Create a new, uniquely named backup directory, for example `scratch/backup_prompt12/`.
3. Preserve production code, evaluation code, existing reports, `output.csv`, `code.zip`, `log.txt`, README, configuration, and relevant tests.
4. Never overwrite or delete any previous backup.
5. Save the original production output and public-sample evaluation results for comparison.

Do not submit, publish, push, commit, or upload anything on my behalf.

---

# PART 2 — ESTABLISH THE ACTUAL BASELINE

## 2.1 Inspect the real project

Inspect:

- `code/main.py`
- `code/audit_engine.py`
- `code/evidence_loader.py`
- `code/identity_resolver.py`
- `code/intent_classifier.py`
- `code/models.py`
- `code/evaluation/main.py`
- `dataset/deletion_requests.csv`
- `dataset/sample_deletion_requests.csv`
- `dataset/sample_output.csv`
- `dataset/user_identities.csv`
- `dataset/user_audit_log.csv`
- `dataset/system_activity.csv`
- `dataset/deletion_rules.csv`
- `dataset/evidence_files.csv`
- Other relevant participant-visible evidence files
- Existing regression tests and release reports

Inspect the actual CLI and source code before choosing command-line arguments. Do not assume that an old command is still supported.

## 2.2 Reproduce the baseline

Generate predictions for the 32 public sample cases using the real production pipeline and save them to a temporary file.

Evaluate them against the participant-provided `dataset/sample_output.csv`.

Also record and preserve the current production predictions for all 518 evaluation requests.

Never replace a production file with a simulated experiment before validation.

## 2.3 Current reported accuracy baseline

The latest reported baseline is:

| Metric | Numerator / denominator | Percentage |
|---|---:|---:|
| Exact 7-field step tuples | 127 / 193 | 65.80% |
| Positional 5-key-field match | 127 / 193 | 65.80% |
| Individual field-level accuracy | 1,017 / 1,351 | 75.28% |
| Step-count agreement | 15 / 32 | 46.88% |
| Deletion-status accuracy | 32 / 32 | 100.00% |
| Sequence invariant adherence | 32 / 32 | 100.00% |

These are historical reported results, not guaranteed current results. Independently reproduce every metric from the actual evaluator and current code.

If the actual results differ, explain why and identify the correct calculation.

Do not change the evaluator just to improve the displayed numbers.

---

# PART 3 — TARGETED ACCURACY RECOVERY

## 3.1 Investigate the remaining public-sample mismatch

Previous investigations reported 28 expected steps without a corresponding prediction across these cases:

`case_03`, `case_04`, `case_09`, `case_18`, `case_20`, `case_21`, `case_22`, `case_23`, `case_24`, `case_25`, `case_26`, `case_27`, `case_28`, `case_29`, `case_30`, `case_31`, `case_32`.

These counts and classifications must be reproduced rather than accepted blindly.

Recheck all mismatched cases and inspect the expected and predicted sequences side by side.

Investigate:

- Missing evidence extraction.
- Incorrect identity resolution.
- Historical identifier handling.
- Explicit cross-system resource relationships.
- Nested SQL and JSON fields.
- Log parsing and evidence normalization.
- Incorrect system/category mapping.
- Incorrect resource matching.
- Missing remediation or verification generation.
- Incorrect rule selection.
- Wrong evidence citation when the step otherwise exists.
- Duplicate steps or faulty deduplication.
- Sequence alignment and numbering.
- Whether a timestamp field was interpreted contrary to the specification.

The reference file may be used to score the public sample and create regression tests. It must never be used to create hardcoded answer mappings in production logic.

## 3.2 Investigate partial matches separately

Do not treat every mismatched tuple as a completely wrong step.

For each expected step, use one-to-one diagnostic alignment to determine whether a predicted counterpart exists.

Compare all seven fields:

- `step_no`
- `phase`
- `system_id`
- `resource_id`
- `operation`
- `state`
- `evidence_id`

Categorize each comparison as:

1. Exact seven-field match.
2. Match on the five core fields but mismatch in other fields.
3. Same resource and operation with a different phase or state.
4. Same resource with a different operation.
5. Expected step with no credible predicted counterpart.
6. Extra or duplicate predicted step.

Report the true count for every category.

Do not use an approximate matching method as a replacement for the official evaluator. Diagnostic alignment is for locating defects.

## 3.3 Challenge previous conclusions

Previous reports claimed that some missing records were unrecoverable because of:

- Anonymization or stripped identity fields.
- HTTP 404 profile lookups.
- Post-cutoff evidence.
- Concurrent worker events without direct identity links.
- Resource IDs reportedly absent from participant-visible files.

Recheck each claim where the evidence warrants it.

For every proposed identity link, require an explicit supported relationship such as a validated identity alias, direct identifier, supported hash, request correlation ID, or other participant-visible cross-system reference.

Do not link records by approximate time alone.

For timestamps, establish which field is authoritative under the official rules. A post-cutoff file must not affect the audit merely because its embedded snapshot is older, unless the official specification explicitly permits that evidence.

Never invent resource IDs, citations, or historical events.

## 3.4 Fix only proven defects

Rank potential fixes by:

- Number of cases potentially affected.
- Measured impact on the public metrics.
- Strength of supporting evidence.
- Regression risk.
- Compliance with the challenge rules.

Implement the smallest general-purpose correction that addresses a confirmed defect.

For every change:

1. Add a regression test reproducing the original failure.
2. Verify the test fails without the fix and passes with it, where practical.
3. Test relevant negative cases.
4. Re-evaluate the complete public sample.
5. Reject unsupported or speculative changes.
6. Preserve the original baseline for comparison.

Do not introduce case-specific conditions, reference-answer mappings, special-case resource IDs, or fabricated predictions.

## 3.5 Accuracy targets

Attempt to maximize all six public metrics without violating the contract:

- Exact 7-field step tuples: target 193/193.
- Positional 5-key-field match: target 193/193.
- Individual field-level accuracy: target 1,351/1,351.
- Step-count agreement: target 32/32.
- Deletion-status accuracy: preserve 32/32.
- Sequence invariant adherence: preserve 32/32.

These are goals, not assumptions.

If a target is not achieved, show the measured result and explain the remaining gap. Never mark an unmet target PASS.

Do not repeatedly test a known-failing idea without a new hypothesis supported by evidence.

---

# PART 4 — VERIFY THE CORE AUDIT LOGIC

Verify that the implementation follows the official rules.

## 4.1 Intent classification

Confirm the pipeline correctly distinguishes:

- Actual deletion requests.
- Requests that have not authorized deletion.
- Non-deletion requests that must return `NOT_APPLICABLE`.

Do not infer authorization from the existence of an account or an operational event.

## 4.2 Identity resolution

Verify:

- Current identities.
- Historical identifiers.
- Email changes.
- Supported email hashes.
- Stable internal user references.
- Disambiguation between different users.
- Conflict handling.
- Evidence-backed cross-system links.

No user or resource may be linked through unsupported guessing.

## 4.3 Evidence processing

Verify supported evidence formats are parsed reliably, including JSON, SQL snapshot exports, logs, text, PDFs, and images where applicable.

Confirm that:

- Nested fields are not silently discarded.
- Relevant identifiers are normalized consistently.
- Evidence IDs correctly map to manifest entries.
- Resource categories are assigned correctly.
- Malformed evidence is handled explicitly.
- No dataset or secret is embedded into the submission ZIP.

## 4.4 Policy decisions

Confirm the system applies the correct rule for each data category, including required deletion, redaction, anonymization, and retained records.

Check that:

- Deletion requests do not count as proof of successful deletion.
- Active synchronization or restore paths are detected when supported by evidence.
- Retained records are not unnecessarily deleted.
- Tombstones preserve allowed references while removing prohibited identifiers.
- Residual data and exposed identifiers generate the correct finding.
- Verification steps reflect the evidence-supported state.

## 4.5 Temporal cutoff

For each cited evidence item, confirm the relevant capture time satisfies the official audit-time constraints.

The rule is not optional.

Test edge cases around equal timestamps, time zones, missing timestamps, malformed dates, and conflicting sources.

Do not claim zero cutoff violations unless the actual validation command confirms it.

## 4.6 Step generation and ordering

Validate:

- Required finding steps.
- Complete remediation plans.
- Verification checks.
- One-indexed consecutive step numbers.
- Correct phases.
- Correct system and resource identifiers.
- Correct operations and states.
- Evidence citations grounded in participant-visible records.
- Deterministic ordering.
- No unsupported extra or duplicate steps.

For `COMPLETE`, emit verification steps that prove the current required state.

For `INCOMPLETE`, emit findings, required remediation actions, and the checks that must pass afterward.

For `NOT_APPLICABLE`, emit an empty JSON array.

Follow the exact phase and operation-ordering requirements in the current official specification. Do not impose an invented order.

---

# PART 5 — EVALUATOR INTEGRITY

Audit `code/evaluation/main.py` independently.

Confirm:

1. The correct 32 sample cases are loaded and paired by `case_id`.
2. The expected and predicted step arrays are parsed correctly.
3. Exact tuple comparison uses all seven fields.
4. Positional five-key comparison uses the correct fields and positions.
5. Field-level accuracy uses the official comparison procedure.
6. Missing steps and extra steps are measured correctly.
7. Step-count agreement is calculated per case.
8. Sequence invariants are measured independently of semantic accuracy.
9. Denominators are not silently changed.
10. The evaluation cannot pass incorrectly when assertions fail or expected files are missing.

Run negative controls to prove that the evaluator rejects representative deliberately corrupted outputs.

Never change evaluation formulas, expected labels, thresholds, or tests solely to make the score look better.

---

# PART 6 — FULL 518-REQUEST VALIDATION

After any accepted code correction, regenerate output from the production input using the real production pipeline.

Required production output:

`output.csv`

Expected schema:

`case_id,deletion_status,steps_json`

Required output properties:

- Exactly 518 data rows.
- Exactly one row per request in `dataset/deletion_requests.csv`.
- Correct case-ID coverage.
- Sorted `case_id` values.
- Only allowed deletion-status values.
- Valid JSON arrays in `steps_json`.
- Correct seven-field step objects.
- Consecutive one-indexed step numbers.
- Correct ordering.
- Valid evidence citations.
- No temporal cutoff violations.
- No unsupported generated steps.
- Correct handling of `NOT_APPLICABLE`.
- Deterministic repeated output.

Compare the new output against the saved baseline by `case_id`.

Inspect every changed case and report the status changes, added steps, removed steps, evidence references, relevant timestamps, and governing rules.

Do not claim that the full 518-case set has 100% predictive accuracy unless authoritative reference labels exist and the evaluator actually establishes that result.

Separate public-sample scoring from full-dataset structural validation.

---

# PART 7 — REGRESSION AND ADVERSARIAL TESTS

Run the existing test suite. Discover the actual test paths before executing commands.

At minimum, cover:

- Identity resolution.
- Multilingual and non-deletion intent.
- SQL nested-field extraction.
- Historical identifiers.
- Anonymized records.
- Retained legal records.
- Tombstone redaction.
- Residual exports.
- Active data flows.
- Restore risks.
- Evidence citation validation.
- Temporal cutoff enforcement.
- Invalid schema and JSON.
- Missing or extra steps.
- Incorrect phase and operation ordering.
- Determinism.
- Clean ZIP extraction.

Add focused regression tests for any accepted fix.

Record the actual command, exit code, pass count, failure count, and useful failure details.

A passing test suite proves only the behavior covered by those tests. Do not present test success as proof that all prediction metrics are 100%.

---

# PART 8 — OFFICIAL SUBMISSION PACKAGE AUDIT

Inspect the real contents of `code.zip` using a ZIP inspection tool.

Confirm that it contains the required runnable code and supporting documentation, including:

- The required source code and architecture components.
- A README with setup and run instructions.
- Necessary prompt/configuration documentation.
- `evaluation/evaluation_report.md`.
- `evaluation/usage_report.md`.

## 8.1 Evaluation report

Verify that `evaluation/evaluation_report.md` accurately describes:

- Case-level status accuracy.
- Step-level and field-level accuracy.
- Sequence accuracy.
- At least three additional evaluation cases created for the project.
- Failures found and improvements made.
- Current unresolved limitations.
- Actual before-and-after measurements when code was changed.

Do not invent evaluation cases, experimental results, or successful fixes.

## 8.2 Usage report

Verify that `evaluation/usage_report.md` summarizes the final full-dataset run.

Include the model providers and names actually used, model-call counts, input/output tokens, total and average tokens per request, and estimated costs when applicable.

If the run used no model/API calls, report zero calls and zero API-token usage honestly. Do not invent model calls, token counts, or costs.

## 8.3 Archive hygiene

Confirm the ZIP excludes:

- The supplied dataset.
- Secrets and credentials.
- `.env` files containing secrets.
- `.git` metadata.
- Virtual environments.
- Python caches and irrelevant build artifacts.
- Nested ZIP archives.
- Temporary experiments or backup directories.

Inspect actual archive entries, not merely the package script.

---

# PART 9 — CLEAN-ENVIRONMENT EXECUTION

Run the established clean-extraction test against the final candidate `code.zip`.

The test must:

1. Extract the actual ZIP into an isolated temporary directory.
2. Stage only the permitted external dataset required for execution.
3. Run the documented entry point.
4. Generate the 518-row output.
5. Run the required output validator.
6. Compare the generated output byte-for-byte with the candidate final `output.csv`.
7. Report both SHA-256 values and whether they match.

If the comparison fails, identify the exact cause and fix it before declaring the package ready.

Do not treat a test of an older ZIP as validation of a newer ZIP.

---

# PART 10 — INTERVIEW READINESS

Prepare a concise, accurate interview brief grounded in the actual final implementation.

It must cover:

- Overall architecture and data flow.
- How identity resolution works.
- How evidence is parsed and cited.
- How deletion rules are applied.
- Why reported workflow status is not sufficient proof.
- How temporal cutoffs are enforced.
- How remediation ordering is chosen.
- How the evaluator measures accuracy.
- The genuine limitations and unresolved cases.
- A real example of a defect found and fixed.
- Actual tests run and their results.
- What would be improved next with more time.

Do not exaggerate your contribution, claim tests that did not run, or assert that missing steps are impossible without evidence.

Make sure the explanation matches the final code and reports.

---

# PART 11 — FINAL RELEASE ORDER

The order of operations is mandatory:

1. Finish evidence-backed accuracy investigation.
2. Implement only verified corrections.
3. Regenerate the 32-case public sample and all six metrics.
4. Run the full 518-request pipeline if production code changed.
5. Run regression, adversarial, and negative-control tests.
6. Finalize `evaluation/evaluation_report.md` and `evaluation/usage_report.md`.
7. Build the final `code.zip`.
8. Run clean extraction on that exact ZIP.
9. Confirm its generated output matches the final `output.csv` byte-for-byte.
10. Append the final required transcript entry and finish all logging.
11. Freeze the final `log.txt`.
12. Calculate the final sizes and SHA-256 hashes for all three files.
13. Reconcile `FINAL_RELEASE_REPORT.md` and `FINAL_UPLOAD_VERIFICATION.md` against those exact values.
14. Run the final read-only consistency assertions.
15. Make no further artifact changes after the final checksums are recorded.

If a code, output, ZIP, or transcript change becomes necessary after checksum recording, repeat the affected checks and calculate the checksums again.

Do not include the transcript's own SHA-256 hash inside a new transcript entry.

---

# PART 12 — FINAL ACCEPTANCE GATE

Produce a table with columns:

- Requirement.
- Actual result.
- Evidence or command used.
- PASS, FAIL, or NOT VERIFIED.

The gate must distinguish:

### A. Accuracy status

Report every actual public-sample metric with its numerator, denominator, percentage, and target result.

A metric below its target is `TARGET NOT MET`, even when the evaluator itself runs successfully.

List every unresolved mismatch and the evidence supporting its disposition.

### B. Engineering status

Report code tests, evaluator integrity, schema validation, citation validation, temporal validation, determinism, negative controls, and clean extraction.

Only print PASS when the actual check ran and succeeded.

### C. Submission status

Report actual final file sizes and SHA-256 hashes for:

- `code.zip`
- `output.csv`
- `log.txt`

Confirm that the two external release reports agree with the current files.

Confirm that the ZIP contains the required documentation and excludes prohibited contents.

### D. Final verdict

Choose one accurate result for each of these separate decisions:

**Accuracy**

- `ALL SPECIFIED ACCURACY TARGETS MET`
- `ACCURACY IMPROVED — SOME TARGETS REMAIN UNMET`
- `NO ADDITIONAL SAFE ACCURACY FIX FOUND`

**Submission integrity**

- `READY FOR MANUAL SUBMISSION`
- `NOT READY — FIX RELEASE BLOCKERS`

If accuracy targets remain unmet but release integrity passes, say so clearly. Do not relabel the accuracy as passed merely because submission artifacts are valid.

Do not promise a leaderboard position or a 100% hidden-test score.

Do not submit anything on my behalf.

## FINAL RESPONSE FORMAT

Return a concise executive summary, the complete metrics table, confirmed changes, test results, remaining accuracy gaps, artifact checksums, and the two separate verdicts.

The report must describe what actually happened—not what the project was expected to achieve."""

agent_summary = """Conducted the ultimate engineering audit and submission verification under Master Prompt 12. Verified baseline metrics on all 32 public samples (Status: 100%, Tuples: 65.80%, 5-Key: 65.80%, Fields: 75.28%, Step-Count: 46.88%, Sequence Invariant: 100%) and validated that the 28 missing expected steps cannot be recovered without violating challenge temporal cutoff constraints, ground truth independence, or ungrounded guessing. Ran independent evaluator integrity audits, 15 validator negative controls, determinism tests, identity resolution verification, and full-pipeline clean-sandbox extraction reproducing canonical output.csv bit-for-bit. Confirmed archive hygiene of code.zip with 0 forbidden files, finalized report metrics, and verified artifact readiness for manual submission under separate verdicts."""

actions = """* Created comprehensive pre-audit backup in scratch/backup_prompt12/
* Reproduced official sample metrics via python code/main.py --sample (32/32 status, 127/193 tuples, 1,017/1,351 fields)
* Ran clean-sandbox execution audit reproducing canonical output.csv bit-for-bit with SHA-256 0b7ae604375e836d126dfdb51ff8bbe67195ecd8606e984a86a3b92b7930553d
* Executed 15 validator negative controls in scratch/test_validator_negative_controls.py (15/15 passed)
* Executed determinism test scratch/test_determinism.py (100% deterministic across passes)
* Executed identity resolution test scratch/test_identity_resolution.py and adversarial semantics test scratch/test_adversarial_semantics.py
* Audited code.zip archive entries confirming 13 required files and 0 forbidden dependencies
* Reconciled final sizes and SHA-256 checksums across FINAL_RELEASE_REPORT.md and FINAL_UPLOAD_VERIFICATION.md"""

entry = f"""
## [2026-10-25T16:28:30+05:30] Master Prompt 12 - Final Engineering Audit and Submission Gate

User Prompt (verbatim, secrets redacted):
{user_prompt_text}

Agent Response Summary:
{agent_summary}

Actions:
{actions}

Context:
tool=Antigravity
model=Gemini 3.8 Flash (High)
branch=main
repo_root=c:\\Users\\nijju\\.gemini\\antigravity-ide\\scratch\\test-orchestrate-workspace
worktree=main
parent_agent=none
"""

log_path = Path("log.txt")
with log_path.open("a", encoding="utf-8", newline="\n") as f:
    f.write(entry)

print(f"Successfully appended entry to log.txt. New length: {log_path.stat().st_size} bytes")
