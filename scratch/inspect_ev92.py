import json

data = json.load(open('dataset/evidence/records/service_resource_export_20260915_114455.json', encoding='utf-8'))
print("Keys in evidence_92:", list(data.keys()))
if "service_exports" in data:
    for k, v in data["service_exports"].items():
        print(f"Service {k}: {len(v)} subitems, type={type(v)}")
        if isinstance(v, dict):
            for subk, subv in v.items():
                print(f"   subk {subk}: count={len(subv) if isinstance(subv, list) else type(subv)}")
                # check if account_5684 is here
                s = json.dumps(subv)
                if 'account_5684' in s:
                    print(f"      FOUND account_5684 in {subk}!")
                if 'audit_record_5416' in s:
                    print(f"      FOUND audit_record_5416 in {subk}!")
                if 'support_4715' in s:
                    print(f"      FOUND support_4715 in {subk}!")
                if 'analytics_4566' in s:
                    print(f"      FOUND analytics_4566 in {subk}!")
                if 'data_flow_6244' in s:
                    print(f"      FOUND data_flow_6244 in {subk}!")
                if 'backup_3120' in s:
                    print(f"      FOUND backup_3120 in {subk}!")
