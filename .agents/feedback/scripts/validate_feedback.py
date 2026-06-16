#!/usr/bin/env python3
"""Validate Hermes skill feedback JSONL records."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER = ROOT / ".agents" / "feedback" / "skill-feedback.jsonl"
REQUIRED = {
    "timestamp",
    "skill",
    "skill_commit",
    "source",
    "feedback_type",
    "strength",
    "agent_output",
    "human_feedback",
    "review_status",
}
SOURCES = {"github_pr_review", "github_issue", "eval_failure", "incident", "user_correction", "manual_review", "other"}
TYPES = {"false_positive", "false_negative", "wrong_severity", "unactionable", "wrong_fix", "overbuilt", "missed_simplification", "test_failure", "policy_violation", "positive_signal", "other"}
STRENGTHS = {"weak", "repeated_pattern", "explicit_maintainer_statement", "eval_failure", "incident_action_item", "security_critical"}
STATUSES = {"candidate", "hold_for_review", "approved_for_local_patch", "discarded"}
SKILL_RE = re.compile(r"^[a-z0-9-]+$")


def validate_record(record: dict, line_no: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED - set(record))
    if missing:
        errors.append(f"line {line_no}: missing {missing}")
    if "skill" in record and not SKILL_RE.match(str(record["skill"])):
        errors.append(f"line {line_no}: invalid skill {record['skill']!r}")
    if record.get("source") not in SOURCES:
        errors.append(f"line {line_no}: invalid source {record.get('source')!r}")
    if record.get("feedback_type") not in TYPES:
        errors.append(f"line {line_no}: invalid feedback_type {record.get('feedback_type')!r}")
    if record.get("strength") not in STRENGTHS:
        errors.append(f"line {line_no}: invalid strength {record.get('strength')!r}")
    if record.get("review_status") not in STATUSES:
        errors.append(f"line {line_no}: invalid review_status {record.get('review_status')!r}")
    for key in ("agent_output", "human_feedback"):
        if key in record and not str(record[key]).strip():
            errors.append(f"line {line_no}: {key} must be non-empty")
    if record.get("review_status") == "approved_for_local_patch" and record.get("strength") == "weak":
        errors.append(f"line {line_no}: weak feedback cannot be approved_for_local_patch")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", nargs="?", default=str(DEFAULT_LEDGER))
    args = parser.parse_args()
    path = Path(args.ledger)
    if not path.exists():
        print(f"missing ledger: {path}", file=sys.stderr)
        return 1
    errors: list[str] = []
    count = 0
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {i}: invalid JSON: {exc}")
            continue
        errors.extend(validate_record(record, i))
    if errors:
        print("feedback validation failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print(f"feedback validation ok: {count} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
