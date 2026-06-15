---
description: Diagnose an Agent Skill against the shippability rubric and report its score.
agent: agent
argument-hint: <skill name or path to SKILL.md>
---

Use the `skill-doctor` skill — Phase A (DIAGNOSE) only.

Run `python3 .agents/skills/skill-doctor/scripts/lint_skill.py` on the skill named in ${input} (resolve to `.agents/skills/<name>/SKILL.md`). Report the structural score, the three token tiers (description / body / bundle), reference depth, and the top issues with concrete fixes. Do NOT change any files.
