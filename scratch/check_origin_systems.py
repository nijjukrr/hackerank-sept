import sqlite3
import csv
from pathlib import Path

manifest_path = Path("dataset/evidence_files.csv")
with manifest_path.open("r", encoding="utf-8") as f:
    sql_files = [r for r in csv.DictReader(f) if r["file_path"].endswith(".sql")]

origin_systems = set()
for sf in sql_files:
    fp = Path("dataset") / sf["file_path"]
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(fp.read_text(encoding="utf-8", errors="ignore"))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        for t in tables:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
            if "origin_system" in cols:
                for row in conn.execute(f"SELECT DISTINCT origin_system FROM {t};").fetchall():
                    origin_systems.add(row[0])
    finally:
        conn.close()

print("Unique origin_system values in JSON-in-SQL tables:", origin_systems)
