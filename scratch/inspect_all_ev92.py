import json

data = json.load(open("dataset/evidence/records/service_resource_export_20260915_114455.json", encoding='utf-8'))
exports = data.get("service_exports", {})

print("--- SECURITY AUDIT RECORDS in evidence_92 ---")
for r in exports.get("security_service", {}).get("audit_records", []):
    print(r)

print("\n--- ACCOUNT PROFILE LOOKUPS in evidence_92 ---")
for r in exports.get("account_service", {}).get("profile_lookups", []):
    print(r)

print("\n--- ANALYTICS PROFILES in evidence_92 ---")
for r in exports.get("analytics_platform", {}).get("profiles", []):
    print(r)
