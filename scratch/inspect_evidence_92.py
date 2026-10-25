import json

path = "dataset/evidence/records/service_resource_export_20260915_114455.json"
data = json.load(open(path, encoding='utf-8'))

print("Top level keys / structure:", type(data))
if isinstance(data, dict):
    print("Dict keys:", list(data.keys())[:20])
    for k in list(data.keys())[:5]:
        val = data[k]
        print(f"Sample key {k}: type={type(val)}, len={len(val) if hasattr(val, '__len__') else val}")
elif isinstance(data, list):
    print("List len:", len(data))
    print("Sample item 0:", data[0])
