import re

with open("code/evidence_loader.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for idx, line in enumerate(lines):
    if "ObservedResource(" in line:
        # inspect the next 20 lines
        block = "".join(lines[idx:idx+25])
        end_idx = block.find(")")
        call = block[:end_idx+1]
        has_hash = "email_hash=" in call
        has_details = "details=" in call
        system_match = re.search(r'system_id=["\']?([^,"\']+)', call)
        sys_id = system_match.group(1) if system_match else "unknown"
        print(f"Line {idx+1}: {sys_id} | passes email_hash? {has_hash}")
