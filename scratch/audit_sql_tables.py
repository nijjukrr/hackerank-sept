import sqlite3
import csv
from pathlib import Path

manifest_path = Path("dataset/evidence_files.csv")
with manifest_path.open("r", encoding="utf-8") as f:
    sql_files = [r for r in csv.DictReader(f) if r["file_path"].endswith(".sql")]

print(f"Total SQL files: {len(sql_files)}")

all_table_schemas = {}
for sf in sql_files:
    fp = Path("dataset") / sf["file_path"]
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(fp.read_text(encoding="utf-8", errors="ignore"))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        for t in tables:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
            row_count = conn.execute(f"SELECT count(*) FROM {t};").fetchone()[0]
            if t not in all_table_schemas:
                all_table_schemas[t] = (cols, row_count, sf["file_id"])
    finally:
        conn.close()

for t, (cols, count, sample_fid) in sorted(all_table_schemas.items()):
    print(f"Table '{t}' ({count} rows, sample: {sample_fid}): cols={cols}")
