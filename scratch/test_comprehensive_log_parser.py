import sys
from pathlib import Path
import re
import json

sys.path.insert(0, str(Path("code").resolve()))
from evidence_loader import EvidenceLoader, ObservedResource, EvidenceFileMeta

def parse_log_line(line: str):
    """Parses a log line in any known format into (service, trace_id, event, kv_dict)."""
    line = line.strip()
    if not line:
        return None, None, None, {}

    # 1. JSON
    if line.startswith("{") or ('"severity"' in line and "{" in line):
        try:
            jstart = line.find("{")
            jd = json.loads(line[jstart:])
            srv = jd.get("service") or jd.get("logger") or jd.get("function")
            tid = jd.get("trace_id") or jd.get("requestId")
            ev = jd.get("event")
            return srv, tid, ev, jd
        except Exception:
            pass

    # 2. Pipe format: timestamp | level | service | trace_id | event | kv...
    if "|" in line:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6:
            # parts[0]: ts, parts[1]: level, parts[2]: srv, parts[3]: tid, parts[4]: ev, parts[5]: rest
            srv = parts[2]
            tid = parts[3]
            ev = parts[4]
            rest = " | ".join(parts[5:])
            raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
            kv = {}
            for k, v in raw_pairs:
                cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
                kv[k] = cleaned_v
            return srv, tid, ev, kv

    # 3. Bracket format: ts [level] [service] [trace_id] event: kv...
    m_bracket = re.match(r"^(\S+)\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+\[([^\]]+)\]\s+([^:]+):\s*(.*)$", line)
    if m_bracket:
        srv = m_bracket.group(3)
        tid = m_bracket.group(4)
        ev = m_bracket.group(5)
        rest = m_bracket.group(6)
        raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
        kv = {}
        for k, v in raw_pairs:
            cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
            kv[k] = cleaned_v
        return srv, tid, ev, kv

    # 4. Syslog RFC 5424 format: ts <pri> node service trace_id - - kv...
    m_syslog = re.match(r"^(\S+)\s+<[^>]+>\S*\s+\S+\s+(\S+)\s+(\S+)\s+-\s+-\s+(.*)$", line)
    if m_syslog:
        srv = m_syslog.group(2)
        tid = m_syslog.group(3)
        rest = m_syslog.group(4)
        raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', rest)
        kv = {}
        for k, v in raw_pairs:
            cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
            kv[k] = cleaned_v
        ev = kv.get("event")
        return srv, tid, ev, kv

    # 5. Generic Key-Value format (including Cloud Runtime logs)
    raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', line)
    kv = {}
    for k, v in raw_pairs:
        cleaned_v = v.strip("'\"\\").replace('\\"', '').replace('"', '').strip()
        kv[k] = cleaned_v
    srv = kv.get("service") or kv.get("source_system") or kv.get("function") or kv.get("logger")
    tid = kv.get("trace_id") or kv.get("requestId")
    ev = kv.get("event")
    return srv, tid, ev, kv

# Test on lines from operations_stream (pipe), application_trace (bracket), syslog, cloud_runtime
test_lines = [
    '2026-02-03T05:57:48Z | WARN | support_platform | tr-1382666 | message_pii_scan | instance="support-7" pod="support-e036" region="us-east-2" resource_id="support_8538" matched_value="csantos2609@gmail.com" detector="direct_identifier"',
    '2026-07-28T05:51:18Z [DEBUG] [account_service] [tr-6074163] profile_lookup_started: instance="account-5" pod="account-886d" region="ap-northeast-1" resource_id="account_2210"',
    '2026-03-25T08:51:15Z <15>1 node-1 support_platform tr-7458912 - - level=DEBUG instance="support-4" pod="support-6150" region="ap-southeast-1" resource_id="support_101"',
    '2026-06-08T06:52:09Z requestId=tr-1108860 level=INFO function=search_service message="instance=\\"search-3\\" pod=\\"search-0696\\" region=\\"us-east-2\\" resource_id=\\"search_021\\" event=\\"index_query_completed\\" index=\\"customer_directory_v3\\" result=\\"hit\\" shard=\\"9\\" took_ms=\\"24\\" correlation_key=\\"mrios9507.jr@fastmail.com\\""'
]

for idx, tl in enumerate(test_lines, 1):
    srv, tid, ev, kv = parse_log_line(tl)
    print(f"Test line {idx}:")
    print(f"  srv: {srv}")
    print(f"  tid: {tid}")
    print(f"  ev:  {ev}")
    print(f"  rid: {kv.get('resource_id')}")
    print(f"  val: {kv.get('matched_value') or kv.get('correlation_key')}")
