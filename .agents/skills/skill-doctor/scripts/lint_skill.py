#!/usr/bin/env python3
"""STEP 0 structural rubric gate for skill-doctor.

Score a target SKILL.md against the shippability rubric WITHOUT spending any
model tokens. Any challenger that fails this gate is rejected before eval
(see Phase A / Phase C step 0 in SKILL.md). Emits JSON; exits 1 on gate fail.

Stdlib only. No frontmatter library — a hand parser keeps it dependency-free.
"""

import argparse
import json
import os
import re
import sys

# --- Rubric constants (each names the assumption it encodes) -----------------
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")          # Agent Skill name charset+len
DESC_MAX = 1024                                      # description hard cap (chars)
DESC_WARN_LO, DESC_WARN_HI = 120, 300                # description "sweet spot" band
BODY_HARD = 500                                      # body lines: hard ceiling
BODY_WARN = 400                                      # body lines: warn threshold
TOKENS_PER_BYTE = 0.25                               # est tokens = bytes/4 heuristic
CONTENTS_LINE_THRESHOLD = 100                        # bundled .md over this needs ToC
ALLOWED_KEYS = {                                     # frontmatter key whitelist
    "name", "description", "argument-hint",
    "user-invocable", "disable-model-invocation", "context",
}
BANNED_NAME_TOKENS = ("anthropic", "claude")         # vendor names forbidden in skill name
# Marketing/version/benchmark drift tokens — skills are specs, not landing pages.
DRIFT_RE = re.compile(
    r"\b(v\d+\.\d+(?:\.\d+)?|version\s*\d|benchmark|state-of-the-art|sota|"
    r"blazing|cutting-edge|world-class|revolutionary|seamless|powerful|"
    r"best-in-class|production-grade|enterprise-grade|lightning-fast)\b",
    re.IGNORECASE,
)
# WHEN clause: description must say when to use it (CSO trigger guidance).
WHEN_RE = re.compile(r"\buse\b", re.IGNORECASE)
# Local reference links inside the skill bundle.
LOCAL_LINK_RE = re.compile(r"\]\(\s*(\.?/?(?:references|scripts|templates)/[^)\s#]+)")
ANY_LOCAL_LINK_RE = re.compile(r"\]\(\s*(\.[^)\s#]+)")  # any ./… relative target


def parse_frontmatter(text):
    """Return (frontmatter_dict, body_str). Minimal YAML: scalar + folded scalars."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    fm, cur_key, folding = {}, None, False
    for line in raw.split("\n"):
        if folding and (line.startswith("  ") or line.startswith("\t") or not line.strip()):
            fm[cur_key] = (fm[cur_key] + " " + line.strip()).strip()
            continue
        folding = False
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        cur_key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):  # YAML block scalar openers
            fm[cur_key], folding = "", True
        else:
            fm[cur_key] = val.strip("'\"")
    return fm, body


def main():
    ap = argparse.ArgumentParser(description="STEP 0 structural rubric gate for a SKILL.md")
    ap.add_argument("path", help="path to the target SKILL.md")
    args = ap.parse_args()

    path = os.path.abspath(args.path)
    checks = []

    def add(cid, passed, detail):
        checks.append({"id": cid, "passed": bool(passed), "detail": detail})

    if not os.path.isfile(path):
        print(json.dumps({"path": path, "checks": [
            {"id": "file_exists", "passed": False, "detail": "not a file"}],
            "score_0_100": 0, "gate_pass": False}))
        return 1

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    fm, body = parse_frontmatter(text)
    folder = os.path.basename(os.path.dirname(path))
    skill_dir = os.path.dirname(path)
    name = fm.get("name", "")
    desc = fm.get("description", "")

    # --- name -----------------------------------------------------------------
    add("name_regex", bool(NAME_RE.match(name)),
        f"name={name!r} must match ^[a-z0-9-]{{1,64}}$")
    add("name_matches_folder", name == folder,
        f"name={name!r} vs folder={folder!r}")
    add("name_no_vendor", not any(t in name.lower() for t in BANNED_NAME_TOKENS),
        f"name must not contain {BANNED_NAME_TOKENS}")

    # --- description ----------------------------------------------------------
    add("desc_present", bool(desc.strip()), "description must be non-empty")
    add("desc_len_cap", len(desc) <= DESC_MAX, f"len={len(desc)} <= {DESC_MAX}")
    add("desc_has_when", bool(WHEN_RE.search(desc)),
        "description needs a 'use ...' WHEN clause")
    # WHAT = first clause before the first 'use'; require non-empty content there.
    what = WHEN_RE.split(desc, maxsplit=1)[0].strip(" .,:;")
    add("desc_has_what", len(what) >= 3, f"WHAT clause empty/short: {what!r}")
    in_band = DESC_WARN_LO <= len(desc) <= DESC_WARN_HI
    add("desc_len_band", in_band,
        f"WARN len={len(desc)} outside {DESC_WARN_LO}-{DESC_WARN_HI} (advisory)")

    # --- body size ------------------------------------------------------------
    body_lines = body.count("\n") + (1 if body and not body.endswith("\n") else 0)
    est_tokens = int(len(text.encode("utf-8")) * TOKENS_PER_BYTE)
    add("body_line_hard", body_lines <= BODY_HARD,
        f"body lines={body_lines} <= {BODY_HARD}")
    add("body_line_warn", body_lines <= BODY_WARN,
        f"WARN body lines={body_lines} > {BODY_WARN} (advisory)")
    add("body_est_tokens", True, f"est_tokens={est_tokens} (bytes/4, informational)")

    # --- frontmatter key whitelist -------------------------------------------
    extra = set(fm) - ALLOWED_KEYS
    add("frontmatter_keys", not extra,
        f"unexpected frontmatter keys: {sorted(extra)}" if extra else "ok")

    # --- reference link depth (<=1 level deep) --------------------------------
    deep = []
    for m in LOCAL_LINK_RE.finditer(text):
        rel = m.group(1).lstrip("./")
        # depth = path segments beyond the top-level subdir (references/scripts/templates)
        if len(rel.split("/")) > 2:
            deep.append(m.group(1))
    add("ref_depth_le_1", not deep,
        f"links deeper than one level: {deep}" if deep else "ok")

    # --- dangling local links -------------------------------------------------
    dangling = []
    for m in ANY_LOCAL_LINK_RE.finditer(text):
        rel = m.group(1)
        if not os.path.exists(os.path.normpath(os.path.join(skill_dir, rel))):
            dangling.append(rel)
    add("no_dangling_links", not dangling,
        f"dangling ./ links: {dangling}" if dangling else "ok")

    # --- bundled files: orphans + ToC requirement -----------------------------
    bundled, orphans, missing_toc = [], [], []
    for root, _dirs, files in os.walk(skill_dir):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.abspath(fp) == path:
                continue
            bundled.append(fp)
    text_lower_basenames = text  # link-by-basename scan
    for fp in bundled:
        base = os.path.basename(fp)
        # every non-SKILL.md file must be referenced by basename somewhere in SKILL.md
        if base not in text_lower_basenames:
            orphans.append(os.path.relpath(fp, skill_dir))
        if fp.endswith(".md"):
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as r:
                    sub = r.read()
                if sub.count("\n") + 1 > CONTENTS_LINE_THRESHOLD and "## Contents" not in sub:
                    missing_toc.append(os.path.relpath(fp, skill_dir))
            except OSError:
                pass
    add("no_orphan_files", not orphans,
        f"unlinked bundled files: {orphans}" if orphans else "ok")
    add("long_md_has_contents", not missing_toc,
        f"md >100 lines lacking '## Contents': {missing_toc}" if missing_toc else "ok")

    # --- drift / marketing tokens ---------------------------------------------
    drift = sorted({m.group(0) for m in DRIFT_RE.finditer(text)})
    add("no_marketing_drift", not drift,
        f"version/benchmark/marketing tokens: {drift}" if drift else "ok")

    # --- score + gate ---------------------------------------------------------
    # Advisory checks never block the gate; everything else is mandatory.
    advisory = {"desc_len_band", "body_line_warn", "body_est_tokens"}
    score = round(100 * sum(c["passed"] for c in checks) / len(checks))
    gate_pass = all(c["passed"] for c in checks if c["id"] not in advisory)

    print(json.dumps({
        "path": path,
        "checks": checks,
        "score_0_100": score,
        "gate_pass": gate_pass,
    }, indent=2))
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
