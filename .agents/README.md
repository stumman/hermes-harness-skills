# Hermes Skills for GitHub Copilot

A set of GitHub Copilot **Agent Skills** that turn Copilot into a disciplined senior-engineer harness for *any* code change — from a one-line fix to a multi-file feature, plus review, security, and audit passes.

Everything here follows the [Copilot Skill Anatomy Standard](./SKILL-ANATOMY-STANDARD.md). Skills are graded by [`score.py`](./score.py) against [`skill-rubric.json`](./skill-rubric.json); see [BENCHMARK.md](./BENCHMARK.md) for the data.

## Layout

```
.agents/skills/<name>/SKILL.md         ← the skill (auto-loaded by description)
.agents/skills/<name>/references/*.md  ← deep detail, loaded only when linked/needed
.agents/skills/<name>/scripts/*        ← helper scripts, run on demand
.github/prompts/<name>.prompt.md       ← /slash-command entry points
.github/agents/<name>.agent.md         ← read-only review personas (agents dropdown)
.github/copilot-instructions.md        ← always-on repo guidance
```

> Skills are discovered from `.agents/skills/` (also valid: `.github/skills/`, `.claude/skills/`). They work in VS Code Copilot, the Copilot CLI, and the cloud agent. No install — clone the repo and they're active.

## The skills

| Skill | Use it for | Slash command |
|---|---|---|
| **nerd-code** | Build/implement/write production code from a vague prompt | `/build` |
| **conductor** | Orchestrate a multi-step feature, migration, or refactor | `/orchestrate` |
| **critical-review** | Skeptical pre-ship review of a diff/PR | `/review` |
| **ponytail-audit** | Audit code for bugs, secrets, leaks, security anti-patterns | `/audit` |
| **security-sentinel** | Threat-model / OWASP-style security audit | `/secaudit` |
| **ponytail** | Find the leanest correct solution (anti-over-engineering) | `/lazy` |
| **copilot-memory-harness** | Set up persistent cross-session memory in Copilot Chat | — |

## How to use it for any code change

**1. Just describe the task.** Skills auto-trigger on their description — you don't name them.
- *"implement a rate limiter for the upload endpoint"* → **nerd-code** runs the spec→test→review pipeline.
- *"review this diff before I push"* → **critical-review**.
- *"is there anything insecure here?"* → **security-sentinel** / **ponytail-audit**.
- *"do we even need this abstraction?"* → **ponytail**.

**2. Or invoke explicitly** with a slash command in Copilot Chat when you want a specific pass:
```
/build add idempotent retry to the payment webhook
/review
/audit src/api
/secaudit
/orchestrate migrate the auth module to JWT
/lazy parse this CSV
```

**3. A recommended flow for a non-trivial change:**
1. `/orchestrate <goal>` — conductor decomposes it and routes through the specialists, **or** `/build <goal>` to go straight to the nerd-code pipeline.
2. `/review` then `/secaudit` before shipping.
3. `/audit <path>` periodically on existing code to catch rot.

Small fixes need none of this — nerd-code's complexity classifier auto-takes the TRIVIAL path (implement + test only) so a one-liner stays a one-liner.

## Maintaining the skills

- Edit a `SKILL.md`, then re-grade: `python3 .agents/score.py .agents/skills/<name>/SKILL.md` (target ≥ 90).
- Keep every-run guidance in the body; move long examples, tables, and language-specific detail to `references/` linked with a *when-to-follow* clause.
- Frontmatter = only `name` + `description` (+ rarely `argument-hint`/`context`). No `version`/`author`/`tags`. Provenance goes in `docs/skill-changelogs/`, not the skill.
