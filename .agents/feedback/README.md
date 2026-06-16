# Skill Feedback Ledger

This directory is the evidence layer for Oz-style self-improving Skills in Hermes.

The rule is simple:

```text
Inner loop runs Skills on real work.
Humans/tests/maintainers provide feedback.
Outer update Skills may propose local companion Skill diffs from that feedback.
```

Feedback records live in `skill-feedback.jsonl` and must conform to
`skill-feedback.schema.json`.

## Promotion rule

A feedback record may influence a local Skill only when it is either:

- a repeated pattern,
- an explicit maintainer statement,
- an eval failure,
- an incident action item, or
- security-critical.

Weak one-off feedback stays as `candidate` or `hold_for_review` and must not be
promoted into permanent Skill text.

## Core vs local Skills

Core Skills are stable contracts. Local companion Skills are the allowed learning
surface.

```text
core:  .agents/skills/critical-review/SKILL.md
local: .agents/skills/critical-review-local/SKILL.md
outer: .agents/skills/update-critical-review/SKILL.md
```

Outer update Skills should patch only their matching `*-local` companion unless a
human explicitly approves a broader change.
