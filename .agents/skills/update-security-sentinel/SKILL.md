---
name: update-security-sentinel
description: Improve `.agents/skills/security-sentinel-local/SKILL.md` from reviewed feedback while keeping the core `security-sentinel` skill read-only. Use as the outer self-improvement loop for Security Sentinel.
---

# Update Security Sentinel

Use this skill to turn real feedback into a minimal, reviewable diff for
`.agents/skills/security-sentinel-local/SKILL.md`.

The core skill `.agents/skills/security-sentinel/SKILL.md` is the stable cross-repo contract
and is read-only from this loop.

## Write surface

This self-improvement loop may only write to:

- `.agents/skills/security-sentinel-local/SKILL.md`

It must not write to:

- `.agents/skills/security-sentinel/SKILL.md`
- any other core skill
- source code
- eval cases
- `.github/` configuration
- secrets or environment files

If a broader change seems necessary, stop and ask for human review.

## Inputs

- Feedback ledger: `.agents/feedback/skill-feedback.jsonl`
- Optional time window or filtered records supplied by the caller
- Optional target repository context

## Workflow

1. Validate the feedback ledger:

```bash
python3 .agents/feedback/scripts/validate_feedback.py
```

2. Read feedback records where `skill == "security-sentinel"`.
3. Ignore records with `review_status == "discarded"`.
4. Promote only records with one of these strengths:
   - `repeated_pattern`
   - `explicit_maintainer_statement`
   - `eval_failure`
   - `incident_action_item`
   - `security_critical`
5. Cluster repeated feedback into a small number of generalizable patterns.
6. Propose the smallest edit to `.agents/skills/security-sentinel-local/SKILL.md` that prevents the observed failure without duplicating existing guidance.
7. Run the Skill validator:

```bash
python3 .agents/skills/skill-anatomy-optimizer/scripts/audit_skill.py .agents/skills/security-sentinel-local/SKILL.md
```

8. Summarize:
   - evidence records used,
   - guidance added or changed,
   - why it generalizes,
   - risks/regression concerns,
   - validation output.

## Evidence rules

- Do not learn from one weak anecdote.
- Do not encode user/reporter claims as fact unless maintainer-verified.
- Prefer deleting/consolidating stale local guidance over appending forever.
- If feedback points to broken tooling or tests, recommend a code/eval fix instead of a Skill patch.
- Keep the local companion short; every instruction must pay rent.

## Output contract

Return either:

```text
NO_CHANGE: insufficient reviewed evidence
```

or a normal git diff plus an evidence summary.
