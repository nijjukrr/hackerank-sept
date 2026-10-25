import csv

with open("dataset/evidence_files.csv", "r", encoding="utf-8") as f:
    files = [r for r in csv.DictReader(f) if r["captured_at"] <= "2026-02-14T10:00:00Z"]

print(f"Total files before 2026-02-14: {len(files)}")
for f in files:
    print(f"  {f['file_id']}: {f['file_path']} ({f['origin']}) captured {f['captured_at']}")
