import json

files = [
    "dataset/evidence/records/connector_configurations_20260812.json",
    "dataset/evidence/records/security_audit_ledger_20261001.json",
    "dataset/evidence/records/customer_export_manifest_20260409.json",
]

systems = set()
types = set()
results = set()

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for r in data.get("records", []):
            systems.add(r.get("system"))
            types.add(r.get("record_type"))
            results.add(r.get("result"))

print("systems:", systems)
print("record_types:", types)
print("results:", results)
