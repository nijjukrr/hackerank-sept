import sys
from pathlib import Path
import re
import csv
import json
from collections import defaultdict

sys.path.insert(0, str(Path("code").resolve()))
from evidence_loader import EvidenceLoader, EvidenceFileMeta

loader = EvidenceLoader(Path("dataset"))

# Get all 24 log files from evidence_files.csv
manifest = {}
with open("dataset/evidence_files.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        manifest[r["file_id"]] = r

log_metas = [m for m in loader.files_by_id.values() if m.file_path.endswith(".log")]
print(f"Total log evidence files found in manifest: {len(log_metas)}")

per_file_report = []

for meta in sorted(log_metas, key=lambda m: m.file_id):
    file_path = meta.absolute_path
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    total_lines = len(lines)
    
    # Analyze line formats
    format_counts = defaultdict(int)
    extracted_obs = []
    traces = {}
    
    # Temporarily capture observations for this single file
    orig_record_obs = loader._record_obs
    file_obs = []
    loader._record_obs = lambda obs: file_obs.append(obs)
    
    try:
        loader._parse_log(meta)
    finally:
        loader._record_obs = orig_record_obs
    
    # Classify formats of non-empty lines
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("{") or ('"severity"' in line_s and "{" in line_s):
            format_counts["JSON"] += 1
        elif "|" in line_s:
            format_counts["PIPE"] += 1
        elif re.match(r"^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]", line_s):
            format_counts["BRACKET"] += 1
        elif re.match(r"^(\S+)\s+<[^>]+>", line_s):
            format_counts["SYSLOG"] += 1
        elif "message=\"" in line_s:
            format_counts["KV_EMBEDDED"] += 1
        else:
            format_counts["KV_STANDARD"] += 1
            
    dominant_format = max(format_counts.items(), key=lambda x: x[1])[0] if format_counts else "EMPTY"
    
    # Check trace safety: in this file, does any trace_id link to multiple distinct non-null user_ids or emails?
    trace_users = defaultdict(set)
    trace_emails = defaultdict(set)
    for obs in file_obs:
        tid = obs.details.get("trace_id") or obs.details.get("requestId")
        if tid:
            if obs.user_id: trace_users[tid].add(obs.user_id)
            if obs.email: trace_emails[tid].add(obs.email)
            
    cross_user_leak = any(len(u) > 1 for u in trace_users.values())
    cross_email_leak = any(len(e) > 1 for e in trace_emails.values())
    
    # Check polluted fields
    bad_rids = [o for o in file_obs if any(c in o.resource_id for c in ['"', "'", "\\"])]
    bad_emails = [o for o in file_obs if o.email and any(c in o.email for c in ['"', "'", "\\"])]
    
    per_file_report.append({
        "file_id": meta.file_id,
        "filename": Path(meta.file_path).name,
        "captured_at": meta.captured_at,
        "total_lines": total_lines,
        "dominant_format": dominant_format,
        "format_breakdown": dict(format_counts),
        "total_observations": len(file_obs),
        "unique_systems": sorted(list(set(o.system_id for o in file_obs))),
        "unique_categories": sorted(list(set(o.data_category for o in file_obs))),
        "bad_rids": len(bad_rids),
        "bad_emails": len(bad_emails),
        "cross_user_leak": cross_user_leak,
        "cross_email_leak": cross_email_leak,
    })

print(f"{'File ID':<12} {'Lines':<6} {'Obs':<5} {'Dominant Format':<14} {'Clean':<6} {'Trace Safe':<10} {'Filename'}")
print("-" * 80)
for r in per_file_report:
    clean_str = "YES" if r["bad_rids"] == 0 and r["bad_emails"] == 0 else "NO"
    trace_safe = "YES" if not r["cross_user_leak"] and not r["cross_email_leak"] else "NO"
    print(f"{r['file_id']:<12} {r['total_lines']:<6} {r['total_observations']:<5} {r['dominant_format']:<14} {clean_str:<6} {trace_safe:<10} {r['filename']}")

# Summary of check
total_obs = sum(r['total_observations'] for r in per_file_report)
total_polluted = sum(r['bad_rids'] + r['bad_emails'] for r in per_file_report)
any_leaks = any(r['cross_user_leak'] or r['cross_email_leak'] for r in per_file_report)

print("\n=== 24 LOG FILES AUDIT SUMMARY ===")
print(f"Total observations across all 24 log files: {total_obs}")
print(f"Total polluted observations: {total_polluted}")
print(f"Cross-user / cross-email trace leaks: {'FOUND' if any_leaks else 'NONE (100% ISOLATED)'}")
