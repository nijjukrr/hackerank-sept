import json

data = json.load(open("dataset/evidence/records/service_resource_export_20260915_114455.json", encoding='utf-8'))
exports = data.get("service_exports", {})

for svc, recs in exports.items():
    if isinstance(recs, dict):
        for subk, items in recs.items():
            if isinstance(items, list):
                for it in items:
                    s_it = str(it)
                    if any(x in s_it for x in ['5416', '4715', '6244', '3120', '5684', '4566']):
                        print(f"case_26 item in {svc}.{subk}:", it)
