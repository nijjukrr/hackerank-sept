import csv

with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    eval_requests = list(csv.DictReader(f))

found = []
for r in eval_requests:
    txt = r["request_text"].lower()
    for w in ["not", "keep", "leave", "still", "don't", "dont", "without"]:
        if f" {w} " in txt or txt.startswith(f"{w} ") or f" {w}." in txt or f" {w}," in txt:
            found.append((r["case_id"], w, r["request_text"]))
            break

print(f"Total matching cases: {len(found)}")
for cid, w, txt in found:
    print(f"{cid} (matched '{w}'): {txt}")
