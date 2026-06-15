---
description: OWASP-style security audit — flag vulnerabilities by severity with remediations.
agent: agent
argument-hint: <file/dir, or blank>
---

Use the `security-sentinel` skill to run an OWASP-style security audit.

Target: ${input} — if blank, audit the current selection/file (${selection} in ${file}), or the whole repo if no editor context.

Flag vulnerabilities grouped by severity (Critical / High / Medium / Low). For each, include the evidence (file + line) and a concrete remediation.
