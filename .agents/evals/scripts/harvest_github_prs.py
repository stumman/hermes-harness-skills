#!/usr/bin/env python3
"""Harvest public GitHub PR metadata as candidate golden sources.

This intentionally stores metadata and patch URLs, not vendored code. Review license and
quality before marking cases approved.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_QUERIES = {
    "nerd-code": "repo:microsoft/vscode is:pr is:merged label:bug",
    "security-sentinel": "repo:kubernetes/kubernetes is:pr is:merged security OR repo:envoyproxy/envoy is:pr is:merged security",
    "ponytail-audit": "repo:envoyproxy/envoy is:pr is:merged bug",
    "critical-review": "repo:nodejs/node is:pr is:merged semver-major OR label:semver-major",
    "conductor": "repo:rust-lang/rust is:pr is:merged rollup OR refactor",
    "ponytail": "repo:nodejs/node is:pr is:merged small fix",
}


def request_json(url: str, token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "hermes-skill-eval-harvester"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".agents/evals/harvested/github-pr-candidates.jsonl")
    ap.add_argument("--per-skill", type=int, default=10)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for skill, query in DEFAULT_QUERIES.items():
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "sort": "updated", "order": "desc", "per_page": args.per_skill}
        )
        try:
            data = request_json(url, token)
        except Exception as e:
            print(f"WARN {skill}: {e}", file=sys.stderr)
            continue
        for item in data.get("items", []):
            pr_url = item.get("html_url", "")
            rows.append({
                "id": f"{skill}-github-pr-{item.get('number')}",
                "skill": skill,
                "split": "TRAIN",
                "stratum": "candidate",
                "source_type": "github_pr",
                "source_url": pr_url,
                "repo": "/".join(pr_url.split("/")[3:5]) if "github.com" in pr_url else None,
                "title": item.get("title"),
                "task_prompt": "Researcher must convert this real merged PR into an approved golden case with explicit assertions and grader.",
                "gold_signal": {"patch_url": pr_url + ".patch" if pr_url else None, "expected_findings": []},
                "assertions": ["must cite diff evidence", "must define executable or rubric grader before approval"],
                "critical": False,
                "grader": "researcher-review-required",
                "license_notes": "public metadata only; verify repo license before redistributing patch/code",
                "review_status": "candidate"
            })
        time.sleep(1)

    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} candidates to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
