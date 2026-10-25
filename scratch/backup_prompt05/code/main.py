"""Main entry point for HackerRank Orchestrate: Ghost Data Still Exists."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

# Add current code directory to path
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from audit_engine import AuditEngine
from models import DeletionRequestCase


def run_pipeline(
    input_path: Path,
    output_path: Path,
    dataset_dir: Path,
    quiet: bool = False,
) -> int:
    """Runs the deletion audit engine end to end and writes canonical output.csv."""
    start_time = time.time()
    if not quiet:
        print(f"[Ghost Data Still Exists] Initializing audit engine from {dataset_dir}...")

    engine = AuditEngine(dataset_dir)

    if not quiet:
        print(f"[Ghost Data Still Exists] Loading requests from {input_path}...")

    cases: list[DeletionRequestCase] = []
    with input_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cases.append(
                DeletionRequestCase(
                    case_id=row["case_id"].strip(),
                    email=row["email"].strip(),
                    requested_at=row["requested_at"].strip(),
                    reported_status=row["reported_status"].strip(),
                    reported_at=row["reported_at"].strip(),
                    audit_at=row["audit_at"].strip(),
                    request_text=row["request_text"].strip(),
                )
            )

    # Sort cases by case_id to preserve canonical input order
    cases.sort(key=lambda c: c.case_id)

    if not quiet:
        print(f"[Ghost Data Still Exists] Auditing {len(cases)} requests...")

    results = []
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

    for idx, case in enumerate(cases, 1):
        try:
            res = engine.audit_case(case)
            status_counts[res.deletion_status] = status_counts.get(res.deletion_status, 0) + 1
            results.append(res)
        except Exception as e:
            # Failure guardrail: single row error never halts batch
            if not quiet:
                print(f"[WARN] Error auditing case {case.case_id}: {e}", file=sys.stderr)
            # Default to safe INCOMPLETE evaluation
            from models import CaseAuditResult
            fallback_res = CaseAuditResult(case_id=case.case_id, deletion_status="INCOMPLETE", steps=[])
            status_counts["INCOMPLETE"] += 1
            results.append(fallback_res)

        if not quiet and (idx % 100 == 0 or idx == len(cases)):
            print(f"  Processed {idx}/{len(cases)} cases...")

    # Write output.csv
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["case_id", "deletion_status", "steps_json"])
        for res in sorted(results, key=lambda r: r.case_id):
            writer.writerow(res.to_csv_row())

    elapsed = time.time() - start_time
    if not quiet:
        print(f"[Ghost Data Still Exists] Output successfully written to {output_path}")
        print(f"Summary: {len(results)} cases in {elapsed:.2f}s | "
              f"COMPLETE: {status_counts.get('COMPLETE', 0)}, "
              f"INCOMPLETE: {status_counts.get('INCOMPLETE', 0)}, "
              f"NOT_APPLICABLE: {status_counts.get('NOT_APPLICABLE', 0)}")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ghost Data Still Exists - Deletion Audit Pipeline")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("dataset/deletion_requests.csv"),
        help="Path to input deletion requests CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output.csv"),
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("dataset"),
        help="Path to dataset root folder",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run pipeline on sample dataset and evaluate against sample_output.csv",
    )

    args = parser.parse_args()

    if args.sample:
        sample_input = args.dataset_dir / "sample_deletion_requests.csv"
        sample_output = Path("sample_test_output.csv")
        code = run_pipeline(sample_input, sample_output, args.dataset_dir)
        # Compare with sample_output.csv
        expected_path = args.dataset_dir / "sample_output.csv"
        if expected_path.exists():
            from evaluation.main import evaluate_predictions
            evaluate_predictions(sample_output, expected_path)
        sys.exit(code)

    code = run_pipeline(args.input, args.output, args.dataset_dir)
    sys.exit(code)


if __name__ == "__main__":
    main()
