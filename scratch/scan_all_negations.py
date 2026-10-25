import csv

with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    eval_requests = list(csv.DictReader(f))

# Look for negation patterns across all 518 requests
negation_words = [
    "not", "without", "don't", "dont", "never", "keep", "active", "leave",
    "still use", "still need", "only", "correction", "access", "export",
    "promotional", "misspelled", "reset", "login", "invoices"
]

for r in eval_requests:
    text = r["request_text"]
    text_lower = text.lower()
    cid = r["case_id"]
    cid_num = int(cid.split("_")[1])
    
    # If it's outside 533-542, let's see if any text has negation or non-deletion signals
    has_neg = any(w in text_lower for w in ["not ", "not to", "without", "don't", "dont", "leave", "keep", "still need", "still use", "only "])
    if has_neg and not (533 <= cid_num <= 542):
        print(f"\n[{cid}] (reported_status={r['reported_status']}):")
        print("  ", text)
