import re

line = '2026-06-08T06:52:09Z requestId=tr-1108860 level=INFO function=search_service message="instance=\\"search-3\\" pod=\\"search-0696\\" region=\\"us-east-2\\" resource_id=\\"search_021\\" event=\\"index_query_completed\\" index=\\"customer_directory_v3\\" result=\\"hit\\" shard=\\"9\\" took_ms=\\"24\\" correlation_key=\\"mrios9507.jr@fastmail.com\\""'

# Current regex and logic
kv = {k: v.strip("\"'") for k, v in dict(re.findall(r"([a-zA-Z0-9_]+)=([^\s]+)", line)).items()}
print("Current extracted KV:")
for k, v in kv.items():
    if k in ("function", "service", "resource_id", "correlation_key", "event", "result"):
        print(f"  {k} = {repr(v)}")

# Look at how the quotes leak:
print("\nCurrent resource_id:", repr(kv.get("resource_id")))
print("Current correlation_key:", repr(kv.get("correlation_key")))
