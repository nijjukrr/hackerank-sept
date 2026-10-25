import json

path = "dataset/evidence/records/service_resource_export_20260915_114455.json"
data = json.load(open(path, encoding='utf-8'))

exports = data.get("service_exports", {})
print("Services in service_exports:", list(exports.keys()))

for svc, records in exports.items():
    print(f"\n--- Service: {svc} (type={type(records)}, count={len(records) if hasattr(records, '__len__') else 1}) ---")
    if isinstance(records, list) and records:
        print("  Sample record 0:", records[0])
    elif isinstance(records, dict):
        print("  Keys:", list(records.keys())[:5])
