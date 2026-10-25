import json
import glob
import os

json_files = glob.glob("dataset/evidence/**/*.json", recursive=True)
print(f"Total json files: {len(json_files)}")

for fpath in json_files:
    fname = os.path.basename(fpath)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                print(f"{fname}: keys={list(data.keys())[:8]}")
            elif isinstance(data, list):
                print(f"{fname}: list of {len(data)} items, first item keys={list(data[0].keys()) if data else 'empty'}")
    except Exception as e:
        print(f"{fname}: ERROR {e}")
