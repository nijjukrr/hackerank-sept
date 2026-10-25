import sqlite3
import csv
import json
from pathlib import Path

manifest_path = Path("dataset/evidence_files.csv")
with manifest_path.open("r", encoding="utf-8") as f:
    sql_files = [r for r in csv.DictReader(f) if r["file_path"].endswith(".sql")]

samples_by_sys = {}
for sf in sql_files:
    fp = Path("dataset") / sf["file_path"]
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(fp.read_text(encoding="utf-8", errors="ignore"))
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        for t in tables:
            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t});").fetchall()]
            if "origin_system" in cols and "record_json" in cols:
                for row in conn.execute(f"SELECT origin_system, collection_name, record_json FROM {t};").fetchall():
                    sys_name = row[0]
                    if sys_name not in samples_by_sys:
                        samples_by_sys[sys_name] = (row[1], json.loads(row[2]))
    finally:
        conn.close()

for sys_name, (col, doc) in sorted(samples_by_sys.items()):
    print(f"\n=== System: {sys_name} (collection: {col}) ===")
    print("  keys:", list(doc.keys()) if isinstance(doc, dict) else "not dict")
    print("  sample:", json.dumps(doc)[:150])
