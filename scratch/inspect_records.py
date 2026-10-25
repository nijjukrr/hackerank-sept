import json

def inspect_json(filepath, target_keys):
    print(f"\n--- Inspecting {filepath} ---")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Let's see top-level keys
    print("Top-level keys:", list(data.keys()))

    # Walk through data to find target_keys
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                cur_path = f"{path}.{k}" if path else k
                for tk in target_keys:
                    if tk in str(k) or (isinstance(v, (str, int)) and tk in str(v)):
                        print(f"Found {tk} at {cur_path}: {v}")
                    elif isinstance(v, dict) and any(tk in str(x) for x in v.values()):
                        print(f"Found {tk} in dict at {cur_path}: {v}")
                walk(v, cur_path)
        elif isinstance(obj, list):
            for i, it in enumerate(obj):
                cur_path = f"{path}[{i}]"
                for tk in target_keys:
                    if tk in str(it):
                        print(f"Found {tk} in list item at {cur_path}: {it}")
                        break
                walk(it, cur_path)

    walk(data)

inspect_json("dataset/evidence/records/customer_data_snapshot_bundle_20260915.json", ["audit_record_7068", "tombstone_9178"])
inspect_json("dataset/evidence/records/service_resource_export_20260915_114455.json", ["account_5482", "audit_record_9265", "account_6440"])
inspect_json("dataset/evidence/records/customer_data_snapshot_bundle_20260917.json", ["audit_record_9265", "audit_record_3954", "audit_record_1707"])
