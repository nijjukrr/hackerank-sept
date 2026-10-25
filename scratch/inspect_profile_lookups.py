import json

path = "dataset/evidence/records/service_resource_export_20260915_114455.json"
data = json.load(open(path, encoding='utf-8'))

exports = data.get("service_exports", {})

print("account_service profile_lookups:")
for item in exports.get("account_service", {}).get("profile_lookups", []):
    print(item)

print("\nanalytics_platform profiles:")
for item in exports.get("analytics_platform", {}).get("profiles", []):
    print(item)
