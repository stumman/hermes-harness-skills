---
description: Autonomously improve one Agent Skill with the champion/challenger keep-or-revert loop.
agent: agent
argument-hint: <skill name> [maxIters] [targetPassRate]
---

Use the `skill-doctor` skill to run the full improvement loop on the skill named in ${input}.

Drive the bundled swarm harness at `.agents/harness/improve-skill.workflow.js` for that skill (in Claude Code: the Workflow tool with `args: { skill: "<name>", maxIters, targetPassRate }`). Enforce the governance rules: one bounded edit per iteration, statistical paired keep-or-revert gate, never edit the eval set. Apply winning changes ONLY on the `skills/auto-improve` branch with an external changelog entry under `docs/skill-changelogs/` — never on main. Report the baseline→best pass-rate delta and what was kept vs reverted, and stop for human merge.
