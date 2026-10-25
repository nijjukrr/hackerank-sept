import csv
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path("code").resolve()))
from intent_classifier import IntentClassifier

with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    eval_requests = list(csv.DictReader(f))

with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_requests = list(csv.DictReader(f))

print(f"Total eval requests: {len(eval_requests)}")
print(f"Total sample requests: {len(sample_requests)}")

# Check classifications in eval_requests
na_eval = [r for r in eval_requests if not IntentClassifier.authorizes_deletion(r["request_text"])]
print(f"\nEval requests classified as NOT_APPLICABLE ({len(na_eval)}):")
for r in na_eval:
    print(f"  {r['case_id']}: {r['request_text']}")

# Check classifications in sample_requests
na_sample = [r for r in sample_requests if not IntentClassifier.authorizes_deletion(r["request_text"])]
print(f"\nSample requests classified as NOT_APPLICABLE ({len(na_sample)}):")
for r in na_sample:
    print(f"  {r['case_id']}: {r['request_text']}")

# Check if any requests in eval_requests contain keywords like "access", "export", "copy", "receipt", "unsubscribe", "opt-out", "portability", "correct"
suspicious_keywords = ["access", "export", "copy", "receipt", "invoice", "unsubscribe", "opt-out", "portability", "download", "keep", "active", "retain"]

print("\nScanning all eval requests for potential non-deletion intents:")
potential_na = []
for r in eval_requests:
    text = r["request_text"].lower()
    has_suspicious = any(kw in text for kw in suspicious_keywords)
    is_auth = IntentClassifier.authorizes_deletion(r["request_text"])
    if has_suspicious:
        potential_na.append((r["case_id"], is_auth, r["request_text"]))

print(f"Found {len(potential_na)} requests with suspicious keywords.")
# Let's inspect those that are classified as True (authorized deletion) but have 'keep' or 'retain' or 'copy'
for cid, is_auth, txt in potential_na:
    if is_auth and any(k in txt.lower() for k in ["keep", "retain", "copy", "invoice", "receipt", "active"]):
        print(f"\n[Case {cid}] (auth={is_auth}):\n  {txt}")
