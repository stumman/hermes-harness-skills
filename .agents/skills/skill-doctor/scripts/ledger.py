#!/usr/bin/env python3
"""Append-only provenance ledger for the skill-doctor champion/challenger loop.

Each champion/challenger version is one JSONL line. The ledger is the external
ledger of record: it survives across runs, drives the kill-switch (revert to the
last keep-decision version), and renders a human CHANGELOG. Stdlib only.
"""
import argparse
import hashlib
import json
import sys


# One ledger line per version. Order is fixed so diffs stay readable; missing
# optional fields are emitted as None rather than dropped.
FIELDS = [
    "timestamp",        # caller-supplied ISO8601 — never datetime.now(), so runs replay identically
    "version_id",       # opaque id for this champion/challenger variant
    "content_hash",     # sha256 of the skill content; identity for keep-or-revert dedupe
    "parent",           # version_id this was derived from (None for the seed champion)
    "proposing_agent",  # which agent emitted the edit
    "operator",         # operator-library operator that produced the change
    "rationale",        # one-line why
    "model_id",         # model that proposed it (provenance)
    "eval_run_id",      # links to the paired-CI-gate eval run
    "scores",           # dict: parsed eval metrics
    "decision",         # "keep" | "revert" | "pending"
]

# Decisions the kill-switch treats as the safe rollback target.
KEEP_DECISION = "keep"


def compute_content_hash(content):
    """sha256 hex of UTF-8 content. Stable identity for a skill body."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def read_ledger(path):
    """Yield parsed entries in file (chronological) order. Missing file = empty."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
    except FileNotFoundError:
        return


def cmd_append(args):
    # content_hash: accept explicit --content-hash, else derive from --content.
    if args.content_hash:
        content_hash = args.content_hash
    elif args.content is not None:
        content_hash = compute_content_hash(args.content)
    else:
        print(json.dumps({"error": "need --content-hash or --content"}))
        return 1

    # scores arrives as a JSON string so arbitrary metric shapes pass through argparse.
    try:
        scores = json.loads(args.scores) if args.scores else {}
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": "scores is not valid JSON: %s" % exc}))
        return 1

    entry = {
        "timestamp": args.timestamp,
        "version_id": args.version_id,
        "content_hash": content_hash,
        "parent": args.parent,
        "proposing_agent": args.proposing_agent,
        "operator": args.operator,
        "rationale": args.rationale,
        "model_id": args.model_id,
        "eval_run_id": args.eval_run_id,
        "scores": scores,
        "decision": args.decision,
    }
    # Reorder to FIELDS for stable on-disk layout; tolerate extra keys = none here.
    ordered = {k: entry.get(k) for k in FIELDS}

    with open(args.ledger, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(ordered, sort_keys=False) + "\n")

    print(json.dumps(ordered))
    return 0


def cmd_list(args):
    entries = list(read_ledger(args.ledger))
    print(json.dumps(entries, indent=2))
    return 0


def cmd_last_good(args):
    # Kill-switch target: most recent entry whose decision == "keep".
    last = None
    for entry in read_ledger(args.ledger):
        if entry.get("decision") == KEEP_DECISION:
            last = entry
    if last is None:
        print(json.dumps({"error": "no keep-decision entry found"}))
        return 1
    print(json.dumps(last))
    return 0


def cmd_changelog(args):
    entries = list(read_ledger(args.ledger))
    lines = ["# CHANGELOG", ""]
    # Newest first reads like a human changelog.
    for entry in reversed(entries):
        decision = entry.get("decision") or "pending"
        ts = entry.get("timestamp") or "?"
        vid = entry.get("version_id") or "?"
        lines.append("## %s — %s [%s]" % (ts, vid, decision))
        operator = entry.get("operator")
        if operator:
            lines.append("- operator: %s" % operator)
        rationale = entry.get("rationale")
        if rationale:
            lines.append("- rationale: %s" % rationale)
        parent = entry.get("parent")
        if parent:
            lines.append("- parent: %s" % parent)
        agent = entry.get("proposing_agent")
        model = entry.get("model_id")
        if agent or model:
            lines.append("- proposed by: %s (%s)" % (agent or "?", model or "?"))
        scores = entry.get("scores")
        if scores:
            lines.append("- scores: %s" % json.dumps(scores))
        eval_run = entry.get("eval_run_id")
        if eval_run:
            lines.append("- eval run: %s" % eval_run)
        hashv = entry.get("content_hash")
        if hashv:
            lines.append("- content: `%s`" % hashv[:12])
        lines.append("")

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(json.dumps({"out": args.out, "entries": len(entries)}))
    else:
        sys.stdout.write(text)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="skill-doctor provenance ledger.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_append = sub.add_parser("append", help="append one version entry (JSONL)")
    p_append.add_argument("--ledger", required=True, help="path to ledger .jsonl")
    p_append.add_argument("--timestamp", required=True,
                          help="ISO8601 timestamp (caller-supplied for reproducibility)")
    p_append.add_argument("--version-id", required=True)
    p_append.add_argument("--content-hash", help="precomputed sha256; else derive from --content")
    p_append.add_argument("--content", help="skill body to hash if --content-hash omitted")
    p_append.add_argument("--parent", default=None)
    p_append.add_argument("--proposing-agent", default=None)
    p_append.add_argument("--operator", default=None)
    p_append.add_argument("--rationale", default=None)
    p_append.add_argument("--model-id", default=None)
    p_append.add_argument("--eval-run-id", default=None)
    p_append.add_argument("--scores", default="{}", help="JSON string of eval metrics")
    p_append.add_argument("--decision", default="pending",
                          choices=["keep", "revert", "pending"])
    p_append.set_defaults(func=cmd_append)

    p_list = sub.add_parser("list", help="print all ledger entries")
    p_list.add_argument("--ledger", required=True)
    p_list.set_defaults(func=cmd_list)

    p_last = sub.add_parser("last-good", help="print most recent keep-decision entry (kill-switch)")
    p_last.add_argument("--ledger", required=True)
    p_last.set_defaults(func=cmd_last_good)

    p_cl = sub.add_parser("changelog", help="render human CHANGELOG.md from ledger")
    p_cl.add_argument("--ledger", required=True)
    p_cl.add_argument("--out", default=None, help="output path; stdout if omitted")
    p_cl.set_defaults(func=cmd_changelog)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
