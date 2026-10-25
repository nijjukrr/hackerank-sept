import sys
from pathlib import Path
sys.path.insert(0, "code")

import csv
from evidence_loader import EvidenceLoader

loader = EvidenceLoader(Path("dataset"))

def get_best_acc_ev(audit_cutoff):
    acc_evs = [
        m for m in loader.files_by_id.values()
        if m.captured_at <= audit_cutoff and (
            "customer_accounts_failover_replica" in m.file_path or
            "customer_data_inventory" in m.file_path or
            "customer_profiles" in m.file_path
        )
    ]
    if acc_evs:
        return max(acc_evs, key=lambda m: m.captured_at)
    # Fallback to any database or snapshot before cutoff
    any_evs = [m for m in loader.files_by_id.values() if m.captured_at <= audit_cutoff]
    return max(any_evs, key=lambda m: m.captured_at) if any_evs else None

# Test on case_01 (sample) cutoff: 2026-09-03
ev_01 = get_best_acc_ev("2026-09-03T10:00:00Z")
print("case_01 best ev:", ev_01.file_id, ev_01.file_path, ev_01.captured_at)

# Test on case_61 cutoff: 2026-02-14T10:00:00Z
ev_61 = get_best_acc_ev("2026-02-14T10:00:00Z")
print("case_61 best ev:", ev_61.file_id, ev_61.file_path, ev_61.captured_at)
