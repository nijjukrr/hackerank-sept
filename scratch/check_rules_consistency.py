import csv
from pathlib import Path

rules_file = Path("dataset/deletion_rules.csv")
rules = []
with open(rules_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rules.append(r)

print("=== AUTHORITATIVE RULES IN dataset/deletion_rules.csv ===")
for r in rules:
    print(f"  {r['rule_id']}: {r['data_category']} | Condition: {r['condition']} | Required Action: {r['required_action']}")

# Now search in target files for rule_*, Rule *, tombstone, legal, analytics, backup, data flow
target_files = [
    "AGENTS.md",
    "problem_statement.md",
    "README.md",
    "CONSTANTS.md",
    "evaluation/evaluation_report.md",
    "evaluation/usage_report.md",
    "FINAL_RELEASE_REPORT.md",
    "FINAL_UPLOAD_VERIFICATION.md"
]

print("\n=== SEARCHING FOR RULE MENTIONS IN TARGET FILES ===")
keywords = ["rule_", "rule 0", "rule 1", "rule 2", "rule 3", "rule 4", "rule 5", "rule 6", "rule 7", "rule 8", "rule 9", "rule 10", "rule 11", "rule 12", "rule 13", "rule 14", "rule 15", "tombstone", "legal_hold", "backup", "data_flow", "analytics"]

for fname in target_files:
    p = Path(fname)
    if not p.exists():
        print(f"File {fname} not found!")
        continue
    content = p.read_text(encoding="utf-8")
    lines = content.splitlines()
    matches = []
    for idx, line in enumerate(lines, 1):
        line_lower = line.lower()
        for kw in ["rule_", "rule 0", "rule 1", "tombstone", "legal_hold", "backup_archive", "analytics_profile"]:
            if kw in line_lower:
                matches.append((idx, line.strip()))
                break
    print(f"\n--- {fname} ({len(matches)} matches) ---")
    for lno, text in matches[:15]:
        print(f"  L{lno}: {text}")
