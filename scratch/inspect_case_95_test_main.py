import csv, json
for r in csv.DictReader(open("scratch/test_current_main.csv", encoding="utf-8")):
    if r["case_id"] == "case_95":
        steps = json.loads(r["steps_json"])
        print("case_95 in test_current_main.csv:")
        for s in steps:
            print(f"  {s['step_no']}: [{s['phase']}] {s['system_id']}:{s['resource_id']} {s['operation']}")
