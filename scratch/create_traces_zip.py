import os
import zipfile
from pathlib import Path

traces_zip_path = Path("submission/agent_traces.zip")
traces_zip_path.parent.mkdir(parents=True, exist_ok=True)

logs_dir = Path(r"C:\Users\nijju\.gemini\antigravity-ide\brain\785ef12a-d337-4b14-a128-e5e4bf536308\.system_generated\logs")

with zipfile.ZipFile(traces_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    # 1. Official chat transcript log.txt
    if Path("log.txt").exists():
        z.write("log.txt", "log.txt")
        print("Added log.txt")

    # 2. System generated trajectory transcripts
    t1 = logs_dir / "transcript.jsonl"
    if t1.exists():
        z.write(t1, "transcript.jsonl")
        print("Added transcript.jsonl")

    t2 = logs_dir / "transcript_full.jsonl"
    if t2.exists():
        z.write(t2, "transcript_full.jsonl")
        print("Added transcript_full.jsonl")

print(f"Successfully created {traces_zip_path}: {traces_zip_path.stat().st_size} bytes ({(traces_zip_path.stat().st_size / (1024*1024)):.2f} MB)")
