#!/usr/bin/env python3
"""Deterministic (no-LLM) attester for DataOps DataCompare run reports.

Usage: datacompare_verify.py <report.json>
Exit code: 0 = PASS, 1 = FAIL, 2 = INDETERMINATE (unrecognized report shape)
"""
import json
import sys

PASS_WORDS = {"pass", "passed", "completed"}
FAIL_WORDS = {"fail", "failed"}
COUNT_ROW_LABELS = {
    "only in a count",
    "duplicates in a count",
    "only in b count",
    "duplicates in b count",
}


def verdict_from_top_level_status(report):
    status = report.get("status")
    if not isinstance(status, str):
        return None
    normalized = status.strip().lower()
    if normalized in PASS_WORDS:
        return True, [f"top-level status: {status}"]
    if normalized in FAIL_WORDS:
        return False, [f"top-level status: {status}"]
    return None


def verdict_from_summary_table(report):
    summary = report.get("Summary")
    if not isinstance(summary, list):
        return None
    reasons = []
    saw_count_row = False
    all_pass = True
    for row in summary:
        if not isinstance(row, list) or len(row) < 2:
            continue
        label = str(row[0]).strip().lower()
        if label in COUNT_ROW_LABELS:
            saw_count_row = True
            cell_status = str(row[-1]).strip().lower()
            reasons.append(f"{row[0]}: {row[-1]}")
            if cell_status not in PASS_WORDS:
                all_pass = False
    if not saw_count_row:
        return None
    return all_pass, reasons


def attest(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    result = verdict_from_top_level_status(report)
    if result is None:
        result = verdict_from_summary_table(report)
    if result is None:
        return 2, ["could not determine a verdict: no recognized 'status' or 'Summary' field"]

    passed, reasons = result
    return (0 if passed else 1), reasons


def main():
    if len(sys.argv) != 2:
        print("usage: datacompare_verify.py <report.json>", file=sys.stderr)
        return 2

    code, reasons = attest(sys.argv[1])
    verdict = {0: "PASS", 1: "FAIL", 2: "INDETERMINATE"}[code]
    print(verdict)
    for reason in reasons:
        print(f"  - {reason}")
    return code


if __name__ == "__main__":
    sys.exit(main())
