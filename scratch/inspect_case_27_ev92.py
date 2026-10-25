import json

data = json.load(open("dataset/evidence/records/service_resource_export_20260915_114455.json", encoding='utf-8'))
exports = data.get("service_exports", {})

for svc, recs in exports.items():
    if isinstance(recs, dict):
        for subk, items in recs.items():
            if isinstance(items, list):
                for it in items:
                    s_it = str(it)
                    if any(x in s_it for x in ['3830', '4707', '2295', '5970', '3866', '4574']):
                        print(f"case_27 item in {svc}.{subk}:", it)
