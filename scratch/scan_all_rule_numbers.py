import re
from pathlib import Path

files_to_check = [
    "AGENTS.md",
    "problem_statement.md",
    "README.md",
    "CONSTANTS.md",
    "evaluation/evaluation_report.md",
    "evaluation/usage_report.md",
    "FINAL_RELEASE_REPORT.md",
    "FINAL_UPLOAD_VERIFICATION.md",
    "AUDIT_REPORT.md",
    "ACCURACY_IMPROVEMENT_REPORT.md",
    "SAMPLE_ACCURACY_CLOSURE_REPORT.md",
    "code/evaluation/evaluation_report.md",
    "code/evaluation/usage_report.md"
]

print("=== CHECKING SPECIFIC RULE LABELS ACROSS ALL DOCS ===")
for fname in files_to_check:
    p = Path(fname)
    if not p.exists():
        continue
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()
    for idx, line in enumerate(lines, 1):
        # check for Rule \d or rule_\d
        matches = re.findall(r"(?:rule[_\s](\d+))", line, re.IGNORECASE)
        if matches:
            for m in matches:
                # check context
                print(f"{fname}:{idx} -> Rule {m} in line: {line.strip()[:100]}")
