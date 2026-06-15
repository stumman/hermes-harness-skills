---
description: Run the improvement loop across every skill, one at a time (schedule/loop-ready).
agent: agent
argument-hint: [maxIters per skill]
---

Use the `skill-doctor` skill to improve every skill in the collection, one at a time.

For each skill under `.agents/skills/` (EXCLUDING `skill-doctor` itself), run the harness `.agents/harness/improve-skill.workflow.js` with that skill name and the optional maxIters from ${input}. Keep all winning changes on the `skills/auto-improve` branch with a `docs/skill-changelogs/<skill>.jsonl` provenance entry — never touch main. After each skill, append its baseline→best delta to a summary table. Skip any skill whose diagnose is already clean and whose last run yielded no CI-significant gain. Finish with the full table and stop for human merge.

This prompt is safe to run on a schedule (Claude Code `/schedule`) or in a loop (`/loop`): it is idempotent per run, always lands on a branch, and self-skips converged skills.
