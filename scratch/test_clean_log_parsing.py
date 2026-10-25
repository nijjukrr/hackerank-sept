import re

line1 = '2026-06-08T06:52:09Z requestId=tr-1108860 level=INFO function=search_service message="instance=\\"search-3\\" pod=\\"search-0696\\" region=\\"us-east-2\\" resource_id=\\"search_021\\" event=\\"index_query_completed\\" index=\\"customer_directory_v3\\" result=\\"hit\\" shard=\\"9\\" took_ms=\\"24\\" correlation_key=\\"mrios9507.jr@fastmail.com\\""'
line2 = '2026-06-08T09:51:04Z requestId=tr-0305307 level=WARN function=support_platform message="instance=\\"support-5\\" pod=\\"support-6b03\\" region=\\"eu-central-1\\" resource_id=\\"support_2498\\" event=\\"message_pii_scan\\" matched_value=\\"aarav-singh@proton.me\\" detector=\\"direct_identifier\\""'
line3 = '2026-06-08T09:51:18Z requestId=tr-0315808 level=WARN function=integration_service message="instance=\\"integration-2\\" pod=\\"integration-3314\\" region=\\"ap-south-1\\" resource_id=\\"data_flow_2010\\" event=\\"connector_heartbeat\\" enabled=\\"true\\" scheduler_registered=\\"true\\" last_run=\\"success\\""'

for idx, line in enumerate([line1, line2, line3], 1):
    raw_pairs = re.findall(r'([a-zA-Z0-9_]+)=((?:\\"[^"]*\\"|"[^"]*"|[^\s]+))', line)
    kv = {}
    for k, v in raw_pairs:
        cleaned_v = v.strip("\"'\\").replace('\\"', '').replace('\"', '').strip()
        kv[k] = cleaned_v
    print(f"Line {idx}:")
    print(f"  function: {kv.get('function')}")
    print(f"  resource_id: {repr(kv.get('resource_id'))}")
    print(f"  correlation_key: {repr(kv.get('correlation_key'))}")
    print(f"  matched_value: {repr(kv.get('matched_value'))}")
    print(f"  enabled: {repr(kv.get('enabled'))}")
    print(f"  event: {repr(kv.get('event'))}")
