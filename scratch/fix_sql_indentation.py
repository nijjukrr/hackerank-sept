from pathlib import Path

target = Path("code/evidence_loader.py")
lines = target.read_text(encoding="utf-8").splitlines()

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if line.strip() == "for r in rows:" and any("for t in tables:" in x for x in lines[i-3:i]):
        start_idx = i
    if start_idx is not None and line.strip() == "finally:" and any("conn.close()" in x for x in lines[i+1:i+3]):
        end_idx = i
        break

print(f"Indent range: start={start_idx+1}, end={end_idx}")
assert start_idx is not None and end_idx is not None

for j in range(start_idx, end_idx):
    if lines[j].strip():
        lines[j] = "    " + lines[j]

target.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("Successfully fixed indentation in code/evidence_loader.py")
