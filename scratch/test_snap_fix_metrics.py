import sys
from pathlib import Path
sys.path.insert(0, "code")
import csv
import json

from evidence_loader import EvidenceLoader
from audit_engine import AuditEngine
from models import DeletionRequestCase

# Let's inspect what happens if snap.get("captured_at") is used in EvidenceLoader._parse_json
# We can monkeypatch or test a subclass of EvidenceLoader
class FixedEvidenceLoader(EvidenceLoader):
    def _parse_json(self, meta):
        with meta.absolute_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # First run original for non-snapshot parts
        # Then specifically fix snapshots
        super()._parse_json(meta)

# Actually let's just inspect which observations in EvidenceLoader have meta.captured_at != snap.captured_at
loader = EvidenceLoader(Path("dataset"))
diff_snaps = 0
for obs in loader.all_observations:
    pass

print("Loader loaded successfully.")
