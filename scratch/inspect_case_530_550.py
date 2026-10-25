import csv

with open("dataset/deletion_requests.csv", encoding="utf-8") as f:
    eval_requests = list(csv.DictReader(f))

for r in eval_requests:
    cid_num = int(r["case_id"].split("_")[1])
    if cid_num >= 530:
        print(f"\n{r['case_id']}:")
        print("  text:", r["request_text"])
        print("  reported_status:", r["reported_status"])
