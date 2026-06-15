---
description: Ultra-mode code audit — report findings by severity with evidence and fixes.
agent: agent
argument-hint: <file/dir to audit, or blank for whole repo>
---

Use the `ponytail-audit` skill to run an ultra-mode code audit.

Target: ${input} — if blank, audit the current selection/file (${selection} in ${file}), or the whole repo if no editor context.

Report findings grouped by severity (Critical / High / Medium / Low). For each finding include the evidence (file + line) and a concrete fix.
