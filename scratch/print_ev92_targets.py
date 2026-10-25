import json

data = json.load(open('dataset/evidence/records/service_resource_export_20260915_114455.json', encoding='utf-8'))
exports = data["service_exports"]

targets = {
    "account_service": "account_5684",
    "security_service": "audit_record_5416",
    "support_platform": "support_4715",
    "analytics_platform": "analytics_4566",
    "integration_service": "data_flow_6244",
    "backup_service": "backup_3120",
}

for srv, rid in targets.items():
    print(f"\n=== {srv} : {rid} ===")
    subdict = exports[srv]
    for k, items in subdict.items():
        for it in items:
            if it.get("resource_id") == rid:
                print(it)
