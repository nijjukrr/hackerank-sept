import json
import os
from pathlib import Path

for root, dirs, files in os.walk("dataset"):
    for fname in files:
        if fname.endswith(".json"):
            p = Path(root) / fname
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if isinstance(d, dict) and "service_exports" in d:
                    ss = d["service_exports"].get("search_service")
                    if ss:
                        iqs = ss.get("index_queries", [])
                        print(f"{p.name}: {len(iqs)} index_queries")
                        for q in iqs[:3]:
                            print(f"  keys: {list(q.keys())}")
                            print(f"  query={q.get('query')}, res_id={q.get('resource_id')}")
                            if "hits" in q:
                                print(f"  hits total={q['hits'].get('total')}, docs={len(q['hits'].get('documents', []))}")
                                for doc in q['hits'].get('documents', [])[:1]:
                                    print(f"    doc keys: {list(doc.keys())}, email={doc.get('email')}, cust_ref={doc.get('customer_reference')}")
            except Exception as e:
                pass
