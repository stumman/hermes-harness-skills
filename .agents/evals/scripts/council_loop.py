#!/usr/bin/env python3
"""Data-backed research council loop for Hermes skill evals.

Conservative by design:
- validates existing artifacts
- harvests public PR metadata only
- scores candidates with transparent heuristics
- writes machine-readable reports and decision logs
- does not vendor third-party code or auto-approve golden cases
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
EVALS = ROOT / ".agents" / "evals"
CASES = EVALS / "cases"
HARVESTED = EVALS / "harvested" / "github-pr-candidates.jsonl"
REPORTS = EVALS / "reports"
DECISIONS = EVALS / "decisions" / "decision_log.jsonl"
LATEST_JSON = REPORTS / "latest" / "council_report.json"
LATEST_MD = REPORTS / "latest" / "council_report.md"

REQUIRED_CASE_FIELDS = {
    "id", "skill", "split", "stratum", "source_type", "source_url", "repo", "title",
    "task_prompt", "gold_signal", "assertions", "critical", "grader", "license_notes", "review_status"
}

LOW_VALUE_TITLE = re.compile(r"\b(lockfile|bump|dependency update|typo|formatting|prettier|eslint|translations?)\b", re.I)
HIGH_VALUE_TITLE = re.compile(r"\b(fix|bug|regression|security|cve|test|crash|error|vulnerab|race|leak|compat|breaking)\b", re.I)
KNOWN_GOOD_LICENSE_HINTS = re.compile(r"\b(MIT|Apache|BSD|MPL|CC0|CC-BY|public GitHub metadata)\b", re.I)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], timeout: int = 120) -> dict[str, Any]:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {"cmd": cmd, "exit_code": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows, errors = [], []
    if not path.exists():
        return rows, [f"missing {path}"]
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            errors.append(f"{path}:{i}: {e}")
    return rows, errors


def validate_artifacts() -> dict[str, Any]:
    errors, warnings = [], []
    for p in [EVALS / "sources.json", EVALS / "skills-map.json"]:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{p}: {e}")

    case_counts = {}
    seen_ids = set()
    for p in sorted(CASES.glob("*.jsonl")):
        rows, errs = read_jsonl(p)
        errors.extend(errs)
        case_counts[p.stem] = len(rows)
        for idx, row in enumerate(rows, 1):
            missing = sorted(REQUIRED_CASE_FIELDS - set(row))
            if missing:
                errors.append(f"{p}:{idx}: missing fields {missing}")
            cid = row.get("id")
            if cid in seen_ids:
                errors.append(f"duplicate case id {cid}")
            seen_ids.add(cid)
            if row.get("review_status") == "approved" and row.get("grader") in {"pairwise-llm", "researcher-review-required"}:
                warnings.append(f"{cid}: approved with weak/non-concrete grader")
    return {"errors": errors, "warnings": warnings, "case_counts": case_counts, "total_cases": sum(case_counts.values())}


def score_candidate(c: dict[str, Any], existing_urls: set[str], existing_ids: set[str]) -> dict[str, Any]:
    title = c.get("title") or ""
    source_url = c.get("source_url") or ""
    license_notes = c.get("license_notes") or ""
    gold = c.get("gold_signal") or {}
    assertions = c.get("assertions") or []

    scores = {
        "license": 8 if KNOWN_GOOD_LICENSE_HINTS.search(license_notes) else 4,
        "provenance": 10 if source_url.startswith("https://github.com/") else 6,
        "quality": 0,
        "relevance": 8,
        "uniqueness": 0,
        "safety": 10,
        "maintainer_trust": 4 if any(org in source_url for org in ["microsoft", "kubernetes", "envoyproxy", "nodejs", "rust-lang"]) else 2,
    }
    if HIGH_VALUE_TITLE.search(title):
        scores["quality"] += 7
    if gold.get("patch_url"):
        scores["quality"] += 4
    if assertions:
        scores["quality"] += 3
    if LOW_VALUE_TITLE.search(title):
        scores["quality"] -= 6
        scores["relevance"] -= 3
    duplicate = source_url in existing_urls or c.get("id") in existing_ids
    scores["uniqueness"] = 0 if duplicate else 8
    scores = {k: max(0, v) for k, v in scores.items()}
    # Normalize approximate 100-point scale from max 20+20+20+15+10+10+5=100; our raw weights already approximate lower max.
    overall = scores["license"] + scores["provenance"] + scores["quality"] + scores["relevance"] + scores["uniqueness"] + scores["safety"] + scores["maintainer_trust"]
    reasons = []
    if duplicate:
        decision = "discard"
        reasons.append("duplicate existing URL or id")
    elif overall >= 45 and scores["quality"] >= 7:
        decision = "hold_for_review"
        reasons.append("candidate has provenance and relevant quality signals but needs human grader/license review")
    else:
        decision = "discard"
        reasons.append("below quality threshold for 30m council loop")
    if LOW_VALUE_TITLE.search(title):
        reasons.append("low-value title heuristic matched")
    return {"scores": scores, "overall_score": overall, "decision": decision, "reasons": reasons}


def load_existing_case_keys() -> tuple[set[str], set[str]]:
    urls, ids = set(), set()
    for p in CASES.glob("*.jsonl"):
        rows, _ = read_jsonl(p)
        for r in rows:
            if r.get("source_url"):
                urls.add(r["source_url"])
            if r.get("id"):
                ids.add(r["id"])
    return urls, ids


def audit_skills() -> dict[str, Any]:
    auditor = ROOT / ".agents" / "skills" / "skill-anatomy-optimizer" / "scripts" / "audit_skill.py"
    results = {}
    if not auditor.exists():
        return {"available": False, "results": results}
    for skill in sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md")):
        r = run([sys.executable, str(auditor), str(skill)], timeout=30)
        try:
            data = json.loads(r["stdout"])
        except Exception:
            data = {"gate_pass": False, "parse_error": r}
        results[skill.parent.name] = {
            "score_0_100": data.get("score_0_100"),
            "gate_pass": data.get("gate_pass"),
            "failed": [c.get("id") for c in data.get("checks", []) if not c.get("passed") and c.get("severity") == "fail"],
            "warnings": [c.get("id") for c in data.get("checks", []) if not c.get("passed") and c.get("severity") == "warn"],
        }
    return {"available": True, "results": results}


def write_report(report: dict[str, Any]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "latest").mkdir(parents=True, exist_ok=True)
    (REPORTS / "history").mkdir(parents=True, exist_ok=True)
    run_id = report["run_id"]
    hist = REPORTS / "history" / run_id
    hist.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    LATEST_JSON.write_text(text + "\n", encoding="utf-8")
    (hist / "council_report.json").write_text(text + "\n", encoding="utf-8")

    decisions = Counter(x["decision"] for x in report["candidate_scores"])
    md = [
        f"# Council Run {run_id}",
        "",
        f"Timestamp: `{report['timestamp']}`",
        "",
        "## Entscheidungen",
        "",
        *(f"- {k}: {v}" for k, v in sorted(decisions.items())),
        "",
        "## Validierung",
        "",
        f"- JSON/JSONL errors: {len(report['validation']['errors'])}",
        f"- Warnings: {len(report['validation']['warnings'])}",
        f"- Total approved/candidate seed cases: {report['validation']['total_cases']}",
        "",
        "## Skill-Audit",
        "",
    ]
    for skill, res in report["skill_audit"].get("results", {}).items():
        md.append(f"- {skill}: score={res.get('score_0_100')} gate={res.get('gate_pass')} fails={res.get('failed')} warns={res.get('warnings')}")
    md += ["", "## Top Kandidaten", ""]
    for c in sorted(report["candidate_scores"], key=lambda x: x["overall_score"], reverse=True)[:10]:
        md.append(f"- {c['decision']} score={c['overall_score']} skill={c.get('skill')} title={c.get('title')} url={c.get('source_url')}")
    if report["validation"]["errors"]:
        md += ["", "## Fehler", ""] + [f"- {e}" for e in report["validation"]["errors"][:20]]
    LATEST_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    (hist / "council_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    harvest = run([sys.executable, str(EVALS / "scripts" / "harvest_github_prs.py"), "--per-skill", "10"], timeout=180)
    validation = validate_artifacts()
    rows, harvest_errors = read_jsonl(HARVESTED)
    validation["warnings"].extend(harvest_errors)
    existing_urls, existing_ids = load_existing_case_keys()
    scored = []
    for row in rows:
        s = score_candidate(row, existing_urls, existing_ids)
        row2 = {k: row.get(k) for k in ["id", "skill", "title", "source_url", "repo", "review_status"]}
        row2.update(s)
        scored.append(row2)
    audit = audit_skills()
    decision = "keep_provisionally"
    reasons = []
    if validation["errors"]:
        decision = "discard"
        reasons.append("validation errors present; no setup changes should be promoted")
    elif any(x["decision"] == "hold_for_review" for x in scored):
        decision = "needs_human_review"
        reasons.append("new candidates found but require human review before golden approval")
    else:
        decision = "revert"
        reasons.append("no high-quality novel candidates found this run")

    report = {
        "run_id": run_id,
        "timestamp": now_iso(),
        "harvest": harvest,
        "validation": validation,
        "candidate_scores": scored,
        "skill_audit": audit,
        "council_decision": decision,
        "decision_reasons": reasons,
        "data_summary": {
            "harvested_candidates": len(rows),
            "candidate_decisions": dict(Counter(x["decision"] for x in scored)),
            "skills_with_cases": len(validation["case_counts"]),
            "total_cases": validation["total_cases"],
            "skill_audit_failures": {k: v for k, v in audit.get("results", {}).items() if v.get("failed")},
        },
    }
    write_report(report)
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": report["timestamp"],
        "run_id": run_id,
        "decision": decision,
        "reasons": reasons,
        "data_summary": report["data_summary"],
        "report": str(LATEST_MD.relative_to(ROOT)),
    }
    with DECISIONS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(LATEST_MD.read_text(encoding="utf-8"))
    return 0 if decision != "discard" else 1


if __name__ == "__main__":
    raise SystemExit(main())
