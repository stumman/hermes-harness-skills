#!/usr/bin/env python3
"""Append a feedback record to .agents/feedback/skill-feedback.jsonl."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / ".agents" / "feedback" / "skill-feedback.jsonl"


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--skill", required=True)
    p.add_argument("--source", default="manual_review")
    p.add_argument("--type", dest="feedback_type", required=True)
    p.add_argument("--strength", default="weak")
    p.add_argument("--agent-output", required=True)
    p.add_argument("--human-feedback", required=True)
    p.add_argument("--desired-update", default="")
    p.add_argument("--repo", default="")
    p.add_argument("--pr", type=int)
    p.add_argument("--issue", type=int)
    p.add_argument("--run-id", default="")
    p.add_argument("--case-id", default="")
    p.add_argument("--evidence-url", action="append", default=[])
    p.add_argument("--review-status", default="candidate")
    p.add_argument("--review-notes", default="")
    args = p.parse_args()

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill": args.skill,
        "skill_commit": git_commit(),
        "source": args.source,
        "repo": args.repo,
        "pr": args.pr,
        "issue": args.issue,
        "run_id": args.run_id,
        "case_id": args.case_id,
        "agent_output": args.agent_output,
        "human_feedback": args.human_feedback,
        "feedback_type": args.feedback_type,
        "strength": args.strength,
        "desired_update": args.desired_update,
        "evidence_urls": args.evidence_url,
        "review_status": args.review_status,
        "review_notes": args.review_notes,
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    print(f"appended feedback for {args.skill} to {LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
