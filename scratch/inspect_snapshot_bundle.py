import json

data = json.load(open('dataset/evidence/records/customer_data_snapshot_bundle_20260917.json', encoding='utf-8'))

def search_obj(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if 'account_3866' in str(v) or 'account_5684' in str(v):
                print(f"Path: {path}.{k} -> {v}")
            search_obj(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if 'account_3866' in str(v) or 'account_5684' in str(v):
                print(f"Path: {path}[{i}] -> {v}")
            search_obj(v, f"{path}[{i}]")

search_obj(data)
