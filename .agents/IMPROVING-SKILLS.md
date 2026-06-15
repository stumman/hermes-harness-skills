# Continuously Improving the Skills

A reusable, data-backed harness that makes any Agent Skill measurably better without bloating it. Built on the prior art it borrows from — Anthropic `skill-creator` (executor/grader/comparator/analyzer + parallel A/B), the local `auto-optimize` skill (Karpathy keep-or-revert spine), and Microsoft `SkillOpt` (frozen-target + bounded edits + strict gate) — plus a statistical keep-gate, a diverse judge panel, anti-bloat side-effect metrics, and immutable versioning we added on top.

## Pieces

| Piece | Path | What it is |
|---|---|---|
| **skill-doctor** | `.agents/skills/skill-doctor/` | The reusable meta-skill: diagnose a skill + drive the improvement loop. Scores 100/100 on the standard. |
| **improvement swarm** | `.agents/harness/improve-skill.workflow.js` | The "prompt for Claude that spawns the team" — a bounded role×phase agent swarm running the champion/challenger loop. |
| **scorer / lint** | `.agents/skills/skill-doctor/scripts/lint_skill.py`, `.agents/score.py` | Deterministic structural gate (STEP 0). |
| **stats gate** | `.agents/skills/skill-doctor/scripts/score_paired.py` | Paired-difference CI keep-or-revert decision. |
| **ledger** | `.agents/skills/skill-doctor/scripts/ledger.py` | Append-only provenance + CHANGELOG generator. |
| **prompts** | `.github/prompts/{diagnose,improve}-skill.prompt.md`, `improve-all.prompt.md` | On-demand + schedule-ready entry points. |

## How "better" is decided (the keep criterion)

A challenger is promoted only if **both** gates pass:
1. **Structural gate** (cheap, deterministic, runs first): `lint_skill.py` — frontmatter/description/body-budget/links/anti-bloat. A challenger that fails is rejected *before any eval token is spent*.
2. **Behavioral gate** (statistical): champion and challenger run **in parallel** on an identical, locked golden set, k≥3 trials each. KEEP iff a **paired** comparison is CI-significant on held-out validation, with **zero regressions**, no `pass^k` (reliability) drop, no side-effect worsening (body tokens / scope / removed safety constraints), and non-dominated on the per-case Pareto frontier. Ties break toward the *simpler* (fewer-token) skill. Else **revert** (`git reset`) and log the edit to the rejected-edit buffer so it's never re-proposed.

One bounded edit per iteration. The harness never edits the eval set, never weakens an assertion, never makes two changes at once.

## Run it on demand

**In Claude Code** (the swarm):
```
Workflow({ scriptPath: ".agents/harness/improve-skill.workflow.js",
           args: { skill: "ponytail-audit", maxIters: 5, kTrials: 3, targetPassRate: 0.9 } })
```
**In Copilot Chat** (conversational): `/diagnose-skill ponytail-audit` then `/improve-skill ponytail-audit`.

## Run it continuously (schedule / loop)

- **Loop:** `/loop /improve-all` — self-paced; re-runs across all skills, self-skipping converged ones.
- **Cron (Claude Code):** `/schedule` a nightly routine running the `improve-all` prompt. Each run lands winners on the `skills/auto-improve` branch with a changelog entry.

## Governance (why it's safe to run unattended)

- **Auto-apply on a branch, you merge.** Every kept challenger is one immutable, content-hashed commit on `skills/auto-improve`. Nothing touches `main` without your merge.
- **Provenance lives outside the skill.** Version/rationale/scores go to `docs/skill-changelogs/<skill>.jsonl` + a generated `CHANGELOG.md` — never into `SKILL.md` (version is not a spec field).
- **Reversible in one step.** `ledger.py last-good` gives the last known-good version for a kill-switch.
- **Anti-reward-hacking.** Side-effect metrics (token bloat, scope creep, removed safety constraints) are first-class regression signals in the gate.

## Reusable for any skill (the durability rule)

Two layers: **humans edit `skill-doctor`** (its instructions, operator library, config); **the loop edits only the target skill**. Because the golden set, split, ledger, and changelog are conventions *external* to `SKILL.md`, the same harness runs unchanged on any Anthropic or Copilot skill — drop in a skill, point the harness at it, go.

## Honest caveats

- The improvement swarm performs real git commits and runs the bundled scripts via its agents — run it on a clean working tree so the branch isolation holds.
- A trustworthy behavioral signal needs a real golden set (the harness scaffolds a minimal ≥3-case one; expand toward ~50+ stratified cases for statistical power — `stats.md` explains the power analysis and will warn when a suite is too small to detect your target delta).
- "20+ agents" = breadth of roles × the eval matrix, not redundant clones; the complexity router shrinks the swarm for easy skills (evidence shows sampling gains are front-loaded by ~N≈5).
