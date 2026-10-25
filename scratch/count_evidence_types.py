import os
import glob
from collections import Counter

extensions = Counter()
for root, dirs, files in os.walk("dataset/evidence"):
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        extensions[ext] += 1

print("Evidence files by extension:")
for ext, count in extensions.most_common():
    print(f"  {ext}: {count}")
