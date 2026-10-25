import sys
from pathlib import Path

log_path = Path("log.txt")

prompt_text = """# MASTER PROMPT 11 \u2014 FINAL PROJECT COMPLETION, RELEASE FREEZE & SUBMISSION READINESS
## HackerRank Orchestrate October 2026 \u2014 Ghost Data Still Exists
## FINAL EXECUTION PROMPT

### MISSION

Finish the October challenge project and prepare the final submission artifacts for manual upload.

The project has already undergone:
- Core implementation and evidence-parser development.
- Identity-resolution and deletion-policy validation.
- Public sample accuracy investigation.
- Multi-format log-parser correction.
- Full 518-case output generation.
- Code packaging and clean-extraction testing.
- AI interview preparation.

The latest Antigravity reports claim:
- Public deletion-status accuracy: 32/32.
- Exact full-case agreement: 15/32.
- Exact seven-field step tuples matched: 126/193.
- Individual field accuracy: 1,016/1,351.
- Full evaluation dataset: 518 rows.
- Zero reported evidence-cutoff violations.
- Deterministic output and a verified `code.zip`.

Treat these as previous results to reproduce, not unquestionable facts.

**Your mission now is to finish the project safely, validate the latest artifacts, correct any genuine release blocker, freeze the final version, and tell me precisely what to upload.**

Do not start another broad accuracy investigation. Do not restart completed development work without a demonstrated reason.

---

## PHASE 1 \u2014 PROTECT THE CURRENT WORKING VERSION

Before running any command that changes files:

1. Confirm that the current directory is the October challenge workspace.
2. Confirm that the current Git branch and workspace are the expected ones.
3. Do not access or modify the September challenge project.
4. Create a timestamped backup under `scratch/final_release_backup/`.
5. Preserve the latest:
   - `code/`
   - `output.csv`
   - `code.zip`
   - `log.txt`
   - `FINAL_RELEASE_REPORT.md`, if present
   - `FINAL_UPLOAD_VERIFICATION.md`, if present
   - Current evaluation and accuracy reports.
6. Do not overwrite the earlier backups made for Prompts 07, 08, and 09.
7. Do not delete or rewrite existing `log.txt` entries.
8. Do not commit, push, alter Git remotes, submit to HackerRank, or perform external actions.

Record the baseline file sizes and SHA-256 checksums before any modification.

If the current code already passes every required check, preserve it rather than rewriting it.

---

## PHASE 2 \u2014 VERIFY THE OFFICIAL SUBMISSION CONTRACT

Read the current workspace copies of:
- `AGENTS.md`
- `problem_statement.md`
- `README.md`

Extract the exact final requirements for:
- `output.csv`
- `code.zip`
- `log.txt`
- Required evaluation and usage reports.
- Additional required configuration or prompt files.
- AI interview.
- Archive structure and forbidden files.
- Required output schema, ordering, evidence rules, and validation procedure.

Resolve any apparent differences between the official instructions and older agent-generated prompts by following the authoritative repository contract.

Do not assume that a requirement from an earlier assistant prompt is an official requirement unless the repository instructions support it.

Create an explicit checklist mapping every mandatory requirement to its corresponding file, command, or test.

If a material requirement cannot be resolved from the available official instructions, mark it `BLOCKED` rather than inventing an answer.

---

## PHASE 3 \u2014 FINAL SOURCE AND OUTPUT VALIDATION

### A. Reproduce the public sample metrics

Execute the actual production pipeline from the latest source.

Compare the generated predictions with `dataset/sample_output.csv`.

Recalculate:
- Deletion-status accuracy.
- Exact full-case agreement.
- Exact ordered seven-field step-sequence agreement.
- Step-count agreement.
- Exact seven-field tuple agreement.
- Individual field-level accuracy.

For each metric, provide the actual numerator, denominator, formula, and value.

The latest reported targets to reproduce are:

| Metric | Previously reported result |
|---|---:|
| Public status accuracy | 32/32 |
| Exact full-case agreement | 15/32 |
| Exact seven-field tuples | 126/193 |
| Individual field accuracy | 1,016/1,351 |

Do not change prediction logic merely to increase a metric.

Do not claim that the remaining discrepancies are proven benchmark defects unless the evidence supports that conclusion. Do not use public expected answers inside the production prediction path.

### B. Validate the full evaluation output

Run the production pipeline using the official evaluation input and regenerate the root `output.csv`.

Verify:
1. Exactly 518 data rows plus the required header.
2. Every required input case appears exactly once.
3. Required header: `case_id,deletion_status,steps_json`.
4. Correct ordering according to the official contract.
5. Every `steps_json` cell parses into a valid JSON array.
6. Every step contains precisely the required fields.
7. Every step number is consecutive and one-indexed.
8. Phases and operations follow the prescribed official order.
9. Status values are limited to the allowed values.
10. Non-deletion cases use the required `NOT_APPLICABLE` representation.
11. Every historical finding cites valid participant-facing evidence.
12. No finding uses evidence captured after its case's `audit_at`.
13. No unsupported resource, identity, or evidence association is introduced.
14. Remediation and verification steps comply with the official evidence-ID rules.
15. The result is deterministic across independent runs.

If an existing validation script does not check a required contract invariant, identify that gap and run a separate direct check.

Do not claim semantic correctness merely because the schema validator passes.

### C. Handle failures safely

If a test fails:
- Reproduce the failure.
- Identify whether it is a genuine defect or an incorrect test assumption.
- Apply only the smallest justified repair.
- Add or update a regression test.
- Rerun the affected tests.
- Rerun the full 32-case public sample and all 518 evaluation requests.
- Recheck every changed status and prediction.
- Recheck identity isolation, evidence citations, policy actions, and audit-time cutoffs.

If the failure cannot be resolved safely, stop and report it.

Do not replace a working implementation with an untested rewrite.

---

## PHASE 4 \u2014 FINAL REQUIRED TEST SUITE

Run the actual existing tests, where present, including:

- `scratch/test_identity_resolution.py`
- `scratch/test_synthetic_intent.py`
- `scratch/test_adversarial_semantics.py`
- `scratch/test_validator_negative_controls.py`
- `scratch/test_clean_extraction.py`
- `scratch/test_determinism.py`
- `code/evaluation/main.py`

Also run any official test command required by `AGENTS.md` or `README.md`.

For every command, record:
- Command executed.
- Exit code.
- PASS or FAIL.
- Relevant output.
- Any unresolved issue.

Do not report a test as passed merely because the script exists.

Confirm that the following stay intact:
- Public status accuracy.
- Identity isolation.
- Multilingual intent handling.
- Evidence provenance and cutoff compliance.
- Policy-based remediation.
- Ordered step serialization.
- Full row coverage.
- Deterministic output.

If any required test fails, do not declare the release ready.

---

## PHASE 5 \u2014 REBUILD AND TEST THE FINAL `code.zip`

Rebuild `code.zip` using the official packaging method, such as `package_solution.py`, only after the source and output checks pass.

Inspect the complete archive member list.

Confirm the archive contains the exact files and paths required by the official instructions, including:
- The runnable `code/` source.
- `README.md`.
- Required constants or configuration documentation.
- Required evaluation and usage reports at their authoritative paths.
- Any other mandatory runtime or prompt files.

Check both root-level and in-code evaluation-report paths against the actual contract. Include both copies only if this is compatible with the official packaging requirements and the packaging method.

Confirm there are no:
- Datasets prohibited from the archive.
- Secrets, API keys, tokens, or credentials.
- `.git` directories.
- Virtual environments.
- Python bytecode caches.
- Unnecessary nested archives.
- Temporary debug artifacts or unrelated scratch scripts.

### Clean-extraction requirement

1. Create a new isolated temporary directory.
2. Extract the newly built `code.zip`.
3. Supply only the external inputs that the official execution contract explicitly expects.
4. Follow the documented execution command.
5. Confirm the package actually runs.
6. Compare its generated output against the finalized root `output.csv`.
7. Confirm byte-for-byte equality.
8. Confirm that the package does not depend on undeclared workspace-only files.
9. Re-run the required package validator.

Do not place the public expected output or hidden answers into the package.

Do not claim standalone execution if the test secretly depends on files that are missing from the archive and not specified as external inputs.

If a packaging change is required, repeat the clean-extraction test after rebuilding the archive.

---

## PHASE 6 \u2014 VERIFY THE EVALUATION AND USAGE REPORTS

Ensure the latest reports match the final source, output, and actual test results.

### Evaluation report

Verify that it contains:
- Correctly defined public sample metrics.
- Full-dataset validation results.
- Required additional test cases and rationales.
- Failures found and fixes made.
- Known limitations.
- A clear distinction between structural validation and semantic correctness.
- An accurate explanation of the remaining public mismatches.

Correct stale values where necessary. Do not inflate accuracy numbers or describe unverified assumptions as proven facts.

### Usage report

Verify:
- The actual production prediction pipeline's model calls.
- Model provider and name, if applicable.
- Actual token and cost figures supported by available usage records.
- Runtime and test execution summary.
- Proper distinction between production inference and AI coding-assistant activity.

If the production inference pipeline makes zero model calls, report zero inference calls, zero inference tokens, and zero production inference cost. Do not invent token usage for the coding agent.

Ensure all required reports are located at the exact official archive paths.

---

## PHASE 7 \u2014 FINAL CHAT TRANSCRIPT VALIDATION

Verify the actual root `log.txt`.

Check:
- Existing entries remain intact and append-only.
- Required turn sections and runtime metadata are populated.
- Prompts are recorded in the prescribed format.
- Any known supplemental transcript correction remains in place.
- No entry falsely claims that an unperformed test passed.
- No secrets, API keys, or unrelated private data are included.
- The transcript satisfies the official requirements.

Ensure the current release-preparation turn is recorded according to `AGENTS.md`.

Do not rewrite earlier entries for cosmetic reasons.

If the current transcript is incomplete or invalid, report the exact problem and apply only a compliant append-only correction where the original content can be recovered.

After the final required transcript entry is appended, run the final transcript check. Do not modify the log afterward without repeating the relevant validation.

---

## PHASE 8 \u2014 FREEZE THE FINAL RELEASE

After all required tests pass:

1. Finalize the root `output.csv`.
2. Finalize `code.zip`.
3. Finalize the required reports.
4. Finalize `log.txt`.
5. Record the final SHA-256 checksums and sizes for `output.csv` and `code.zip`.
6. Verify that the output inside the clean-extraction test matches the final root `output.csv`.
7. Ensure no additional source edits occur after packaging.
8. Confirm the upload instructions use the latest file versions, not files from the earlier backups.

Create or update `FINAL_RELEASE_REPORT.md` with:
- The authoritative requirements checklist.
- Exact commands executed.
- Public sample metrics and their formulas.
- Full 518-case validation results.
- Test results with exit codes.
- Archive contents and forbidden-file results.
- Clean-extraction results.
- Output and ZIP checksums.
- Transcript validation status.
- Remaining known limitations.
- Exact files required for manual submission.

Do not include a checksum for `log.txt` until after its final required entry and validation have occurred. If any file changes after the recorded checksum, recalculate it.

---

## PHASE 9 \u2014 FINAL VERDICT

Choose exactly ONE verdict.

### `READY FOR MANUAL SUBMISSION`

Use this only if every mandatory deliverable is present and all required release checks pass.

List the exact upload files and their final paths.

### `NOT READY \u2014 RELEASE CHECK FAILED`

Use this if any mandatory test fails, any required artifact is missing, or a confirmed release-blocking defect remains.

Explain the problem and the smallest safe next action.

### `BLOCKED \u2014 OFFICIAL REQUIREMENT UNCLEAR`

Use this only when a material requirement cannot be determined from the official instructions and cannot be resolved safely.

Do not hide a failed check behind an overall passing verdict.

### Final response requirements

Give me:
1. The final verdict.
2. The exact files to upload.
3. The measured metrics.
4. The required test results.
5. The known limitations.
6. The final file sizes and applicable checksums.
7. Any remaining manual action I must perform.

Do not guarantee a top-10 position or a perfect score.
Do not claim hidden tests passed unless they were actually run.
Do not submit anything to HackerRank.
Do not push commits or change Git remotes.

**The task is to produce a verified, frozen release that I can submit manually\u2014not to create another speculative development cycle.**"""

summary_text = """Conducted the final project completion, release freeze, and submission readiness verification for the October 2026 Ghost Data Still Exists challenge. Verified and reproduced public sample metrics (32/32 status, 15/32 exact full-case, 126/193 step tuples, 1,016/1,351 field cells) and full 518-case output validity with zero schema or temporal cutoff violations. Executed the complete test suite including clean environment extraction, verified deterministic byte-for-bit output reproduction, and packaged the final compliant code.zip archive. Confirmed all evaluation and usage reports, froze deliverables, and prepared the final manual submission report with exact SHA-256 digests and upload instructions."""

actions_text = """* Created pre-modification backup under scratch/final_release_backup/
* Executed Phase 3 source validation reproducing 100% of public sample and full 518-case metrics
* Executed comprehensive test suite (identity resolution, synthetic intent, adversarial semantics, validator negative controls, determinism, clean extraction)
* Rebuilt and validated code.zip with zero forbidden files
* Performed clean-extraction isolated execution verifying byte-for-byte output identity
* Validated evaluation and usage reports against production pipeline metrics
* Appended release freeze turn entry to log.txt and updated FINAL_RELEASE_REPORT.md"""

entry = f"""## [2026-10-25T11:35:00+05:30] Master Prompt 11 \u2014 Final Release Freeze & Submission Readiness

User Prompt (verbatim, secrets redacted):
{prompt_text}

Agent Response Summary:
{summary_text}

Actions:
{actions_text}

Context:
tool=Antigravity
model=Gemini 3.8 Flash (High)
branch=main
repo_root=c:\\Users\\nijju\\.gemini\\antigravity-ide\\scratch\\test-orchestrate-workspace
worktree=main
parent_agent=none

"""

with log_path.open("a", encoding="utf-8") as f:
    f.write(entry)

print("Master Prompt 11 turn successfully appended to log.txt.")
