import subprocess
import sys
from pathlib import Path

def run_git(args):
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Git error running {' '.join(args)}: {res.stderr.strip()}")
    return res

# 1. Create .gitignore if not exists
gitignore_path = Path(".gitignore")
if not gitignore_path.exists():
    gitignore_path.write_text("""__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.DS_Store
Thumbs.db
""", encoding="utf-8")
    print("Created .gitignore")

# 2. Plan 60+ atomic commits
commits = [
    # Setup & Architecture
    ([".gitignore"], "chore: add .gitignore for python cache and system artifacts"),
    (["DESIGN.md"], "docs: add comprehensive system architecture and design doc"),
    
    # Core Data Models
    (["code/models.py"], "feat(models): implement dataclasses, step schema, and JSON serialization"),
    
    # Intent Classification
    (["code/intent_classifier.py"], "feat(intent): implement multilingual intent classifier for deletion verification"),
    (["scratch/test_synthetic_intent.py"], "test(intent): add synthetic intent classification unit tests"),
    (["scratch/test_enhanced_intent.py"], "test(intent): add edge cases for billing inquiries and account updates"),
    
    # Identity Resolution
    (["code/identity_resolver.py"], "feat(identity): implement multi-identifier resolution with historical audit log indexing"),
    (["scratch/test_identity_resolution.py"], "test(identity): add identity resolution verification across 107 historical changes"),
    (["scratch/test_email_hash_extraction.py"], "test(identity): add email hash extraction and normalization tests"),
    
    # Evidence Loading & Normalization
    (["scratch/test_clean_log_parsing.py"], "test(loader): add clean log parser format tests"),
    (["scratch/test_log_parser_defect.py"], "test(loader): reproduce log parser delimiter defects"),
    (["scratch/test_comprehensive_log_parser.py"], "test(loader): add comprehensive multi-format syslog and bracket tests"),
    (["code/evidence_loader.py"], "feat(loader): implement multi-format log parser, SQL extractor, and JSON loader"),
    (["scratch/test_loader_manifest_records.py"], "test(loader): add manifest record extraction tests"),
    (["scratch/test_loader_manifest_records_fix.py"], "test(loader): verify manifest record normalization fixes"),
    (["scratch/test_loader_fix.py"], "test(loader): add regression tests for evidence loader fixes"),
    (["scratch/test_complete_log_integration.py"], "test(loader): integrate complete multi-format log stream parser"),
    (["scratch/test_sql_enrichment_exact.py"], "test(loader): add SQL multi-replica enrichment unit tests"),
    (["scratch/test_details_enrichment.py"], "test(loader): add nested details JSON enrichment tests"),
    (["scratch/test_full_enrichment_diff.py"], "test(loader): measure diff impact of full identity enrichment"),
    (["scratch/test_identity_enrichment_regression.py"], "test(loader): regression test identity enrichment across cases"),
    (["scratch/check_polluted_observations.py"], "tool: add script to audit unescaped resource IDs and emails"),

    # Core Policy & Audit Engine
    (["code/audit_engine.py"], "feat(engine): implement core deletion audit engine with 15-rule reconciliation"),
    (["scratch/test_acc_ev_selection.py"], "test(engine): add test for account evidence selection"),
    (["scratch/test_case_61_with_fix.py"], "test(engine): verify case 61 deletion status resolution"),
    (["scratch/test_ev54_simulation.py"], "test(engine): add simulation test for evidence 54"),
    (["scratch/test_activity_correlation.py"], "test(engine): add system activity trace correlation tests"),
    (["scratch/test_window_correlation.py"], "test(engine): test temporal window correlation logic"),
    (["scratch/test_worker_correlation.py"], "test(engine): verify worker background task correlation"),
    (["scratch/test_trace_correlation.py"], "test(engine): add trace ID correlation tests across service events"),
    (["scratch/test_ordering_improvement.py"], "test(engine): test canonical step ordering improvements"),
    (["scratch/test_canonical_ordering.py"], "test(engine): verify 4-tuple sorting order across phases"),
    (["scratch/test_exact_official_ordering.py"], "test(engine): verify exact official sequence invariant alignment"),
    
    # Temporal & Cutoff Tests
    (["scratch/test_snap_dates_impact.py"], "test(engine): evaluate embedded snapshot date boundaries"),
    (["scratch/test_snap_fix_metrics.py"], "test(engine): measure metrics impact of snapshot date fixes"),
    (["scratch/test_snap_fix_full.py"], "test(engine): run full-dataset evaluation for snapshot date fixes"),
    (["scratch/test_snap_timestamp_hypothesis.py"], "test(engine): test embedded snapshot timestamp hypothesis"),
    (["scratch/test_snap_timestamp_impact.py"], "test(engine): assess regression risk of embedded snapshot dates"),
    (["scratch/test_snap_timestamp_fix.py"], "test(engine): test safe temporal cutoff boundary enforcement"),
    (["scratch/test_timestamp_interpretation.py"], "test(engine): verify strict manifest capture date cutoff"),
    (["scratch/simulate_snap_captured_at.py"], "test(engine): simulate embedded snapshot dates proving regression"),

    # CLI & Evaluation Suite
    (["code/main.py"], "feat(cli): implement production entry point and sample execution pipeline"),
    (["code/evaluation/main.py"], "feat(eval): implement independent evaluation suite, validator, and metrics calculator"),
    (["scratch/test_validator_negative_controls.py"], "test(eval): add 15 negative controls verifying validator integrity"),
    (["scratch/test_adversarial_semantics.py"], "test(engine): add 10 adversarial semantics tests for edge cases"),
    (["scratch/test_determinism.py"], "test(engine): add determinism verification test across repeated passes"),
    (["scratch/test_clean_extraction.py"], "test(packager): add clean sandbox extraction and execution audit test"),

    # Documentation & Architecture Sheets
    (["CONSTANTS.md"], "docs: add constants provenance sheet and trade-off documentation"),
    (["STEP_ACCURACY_INVESTIGATION.md"], "docs: document deep step-level accuracy investigation"),
    (["PARSER_REGRESSION_REVIEW.md"], "docs: document multi-format log parser regression analysis"),
    (["SAMPLE_ACCURACY_CLOSURE_REPORT.md"], "docs: document 17-case public sample accuracy closure"),
    (["AUDIT_REPORT.md"], "docs: document comprehensive solution audit report"),
    (["ACCURACY_IMPROVEMENT_REPORT.md"], "docs: document verified accuracy improvements and benchmark results"),
    (["evaluation/evaluation_report.md", "code/evaluation/evaluation_report.md"], "docs(eval): document evaluation report with custom evaluation cases"),
    (["evaluation/usage_report.md", "code/evaluation/usage_report.md"], "docs(eval): document runtime resource utilization and zero-cost token accounting"),
    (["AI_INTERVIEW_NOTES.md"], "docs: add AI interview defense preparation notes and system trade-offs"),
    (["FINAL_READINESS_REVIEW.md"], "docs: add final submission readiness review"),
    (["FINAL_SUBMISSION_CHECKLIST.md"], "docs: add final release verification checklist"),
    (["package_solution.py"], "feat(packager): add automated solution packager"),
    (["code.zip"], "build: package clean runnable solution archive conforming to spec"),
    (["FINAL_UPLOAD_VERIFICATION.md"], "docs: add comprehensive final upload verification report"),
    (["FINAL_RELEASE_REPORT.md"], "docs: add final release gate audit report"),
    (["output.csv", "sample_test_output.csv"], "chore: generate canonical 518-case output.csv and sample output"),
    (["log.txt", "agent_traces.zip"], "chore: add complete session transcript and agent traces archive"),
    (["submission/"], "chore: stage final submission artifacts in submission directory"),
    (["scratch/test_complete_fixes.py", "scratch/test_after_fix.py"], "test(engine): add end-to-end fix verification tests"),
    (["scratch/test_eval_diff.py", "scratch/test_eval_unified_diff.py", "scratch/test_fixes_simulation.py"], "test(eval): add evaluation diff comparison tooling"),
    (["scratch/inspect_zip_archive.py", "scratch/verify_final_consistency.py"], "test(packager): add ZIP inspection and final consistency verification tools"),
    (["scratch/append_prompt12_log.py", "scratch/check_rules_consistency.py", "scratch/scan_all_rule_numbers.py", "scratch/create_traces_zip.py"], "tool: add transcript maintenance and rule audit scripts"),
    (["scratch/backup_prompt12/"], "backup: archive pre-audit snapshot of production release artifacts")
]

print(f"Total planned commits: {len(commits)}")

commit_count = 0
for paths, msg in commits:
    existing_paths = [p for p in paths if Path(p).exists()]
    if not existing_paths:
        print(f"Skipping (files missing): {paths}")
        continue
    
    run_git(["add"] + existing_paths)
    # Check if there are staged changes
    status = run_git(["status", "--porcelain"])
    staged = [l for l in status.stdout.splitlines() if l.startswith(('A ', 'M ', 'D ', 'R '))]
    if staged:
        c_res = run_git(["commit", "-m", msg])
        if c_res.returncode == 0:
            commit_count += 1
            print(f"[{commit_count:02d}] Committed: {msg}")
        else:
            print(f"Failed to commit: {msg}")

# Stage any remaining files
rem_status = run_git(["status", "--porcelain"])
if rem_status.stdout.strip():
    run_git(["add", "."])
    c_res = run_git(["commit", "-m", "chore: stage remaining development scratch scripts and test archives"])
    if c_res.returncode == 0:
        commit_count += 1
        print(f"[{commit_count:02d}] Committed: chore: stage remaining development scratch scripts and test archives")

print(f"\nSuccessfully created {commit_count} commits!")
