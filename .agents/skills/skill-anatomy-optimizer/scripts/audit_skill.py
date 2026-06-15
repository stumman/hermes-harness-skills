#!/usr/bin/env python3
"""Deterministic anatomy auditor for Agent Skill bundles.

Stdlib-only. Emits JSON with gates, token-tier metrics, and actionable findings.
Use as the static gate before/after any skill edit.
"""
import json
import os
import re
import sys
from pathlib import Path

ALLOWED_KEYS = {"name", "description", "argument-hint", "user-invocable", "disable-model-invocation", "context"}
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
BANNED = re.compile(r"\b(v\d+\.\d+(?:\.\d+)?|version\s*\d|benchmark|state-of-the-art|sota|blazing|cutting-edge|world-class|revolutionary|seamless|powerful|best-in-class|production-grade|enterprise-grade|TODO|FIXME|WIP)\b", re.I)
LINK_RE = re.compile(r"\]\((\./(?:references|scripts|templates)/[^)\s#]+)")
ANY_LOCAL_RE = re.compile(r"\]\((\./[^)\s#]+)")


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 4:].lstrip("\n")
    fm = {}
    key = None
    folding = False
    for line in raw.splitlines():
        if folding and (line.startswith(" ") or not line.strip()):
            fm[key] = (fm[key] + " " + line.strip()).strip()
            continue
        folding = False
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in {">", ">-", "|", "|-"}:
            fm[key] = ""
            folding = True
        else:
            fm[key] = val.strip('"\'')
    return fm, body


def add(checks, cid, passed, detail, severity="fail"):
    checks.append({"id": cid, "passed": bool(passed), "severity": severity, "detail": detail})


def audit(path):
    p = Path(path).resolve()
    text = p.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    skill_dir = p.parent
    name = fm.get("name", "")
    desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()
    body_words = len(body.split())
    checks = []

    add(checks, "frontmatter_present", bool(fm), "frontmatter block exists")
    add(checks, "name_matches_folder", name == skill_dir.name, f"name={name!r}, folder={skill_dir.name!r}")
    add(checks, "name_regex", bool(NAME_RE.fullmatch(name)), "name must be kebab-case <=64 chars")
    extra = sorted(set(fm) - ALLOWED_KEYS)
    add(checks, "frontmatter_keys", not extra, f"extra keys: {extra}" if extra else "ok")
    add(checks, "description_present", bool(desc), "description exists")
    add(checks, "description_cap", len(desc) <= 1024, f"description chars={len(desc)} <=1024")
    add(checks, "description_target", 120 <= len(desc) <= 300, f"description chars={len(desc)} target 120-300", "warn")
    has_use = bool(re.search(r"\buse\b", desc, re.I))
    what = re.split(r"\buse\b", desc, maxsplit=1, flags=re.I)[0].strip(" .,:;-—")
    add(checks, "description_what_when", has_use and len(what) >= 3, "requires WHAT + Use when trigger")
    add(checks, "body_word_budget", body_words <= 500, f"body words={body_words} target <=500", "warn")
    add(checks, "body_token_smell", len(body.encode()) // 4 <= 3000, f"body est_tokens={len(body.encode()) // 4} target <=3000", "warn")

    dangling = []
    for m in ANY_LOCAL_RE.finditer(text):
        rel = m.group(1)
        if not (skill_dir / rel).exists():
            dangling.append(rel)
    add(checks, "no_dangling_links", not dangling, f"dangling links: {dangling}" if dangling else "ok")

    linked = {Path(m.group(1)).name for m in LINK_RE.finditer(text)}
    bundled = [x for x in skill_dir.rglob("*") if x.is_file() and x.name not in {"SKILL.md", ".DS_Store"}]
    orphans = [str(x.relative_to(skill_dir)) for x in bundled if x.name not in linked]
    add(checks, "no_orphan_files", not orphans, f"unlinked files: {orphans}" if orphans else "ok")

    long_without_toc = []
    for x in bundled:
        if x.suffix == ".md":
            sub = x.read_text(encoding="utf-8", errors="replace")
            if sub.count("\n") + 1 > 100 and "## Contents" not in sub:
                long_without_toc.append(str(x.relative_to(skill_dir)))
    add(checks, "long_refs_have_toc", not long_without_toc, f"long md without ## Contents: {long_without_toc}" if long_without_toc else "ok")

    drift = sorted(set(m.group(0) for m in BANNED.finditer(text)))
    add(checks, "no_drift_tokens", not drift, f"drift tokens: {drift}" if drift else "ok")

    hard = [c for c in checks if c["severity"] == "fail"]
    gate_pass = all(c["passed"] for c in hard)
    score = round(100 * sum(c["passed"] for c in checks) / len(checks), 1)
    return {
        "path": str(p),
        "name": name,
        "metrics": {
            "description_chars": len(desc),
            "body_words": body_words,
            "body_lines": body.count("\n") + 1 if body else 0,
            "body_est_tokens": len(body.encode()) // 4,
            "bundle_files": len(bundled),
        },
        "checks": checks,
        "score_0_100": score,
        "gate_pass": gate_pass,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: audit_skill.py path/to/SKILL.md", file=sys.stderr)
        sys.exit(2)
    result = audit(sys.argv[1])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["gate_pass"] else 1)
