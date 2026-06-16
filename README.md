# Hermes Harness Skills

Research-backed GitHub Copilot / agent skill pack for building, reviewing, auditing, and improving production code.

This repo is intentionally split into two layers:

```text
.agents/skills/                 # canonical skills Copilot/agents load by description
.github/prompts/                # slash-command wrappers: /build, /review, /audit, ...
.github/agents/                 # optional specialist review personas
.github/copilot-instructions.md # always-on repository guidance
.agents/evals/                  # research/eval council, golden-source cases, candidate harvesters
.agents/feedback/               # feedback ledger for self-improving local companion skills
```

The canonical skills live in `.agents/skills/<skill>/SKILL.md`. Long references and helper scripts sit beside each skill so the main skill stays small and Copilot only loads deeper material when needed.

---

## Install into a project

From the repo you want to use the harness in:

```bash
git clone https://github.com/stumman/hermes-harness-skills.git /tmp/hermes-harness-skills
cp -R /tmp/hermes-harness-skills/.agents ./.agents
mkdir -p .github
cp -R /tmp/hermes-harness-skills/.github/prompts ./.github/prompts
cp -R /tmp/hermes-harness-skills/.github/agents ./.github/agents
cp /tmp/hermes-harness-skills/.github/copilot-instructions.md ./.github/copilot-instructions.md
```

Then open the target project in VS Code with GitHub Copilot Chat. Copilot should auto-discover:

- skills from `.agents/skills/`
- slash prompts from `.github/prompts/`
- custom agents from `.github/agents/`
- always-on instructions from `.github/copilot-instructions.md`

If your Copilot build does not auto-load skills yet, paste the relevant `SKILL.md` content into chat or invoke the matching prompt file manually.

---

## Skill layout

```text
.agents/skills/<name>/
  SKILL.md              # short trigger description + operational protocol
  references/*.md       # detailed methods, loaded only when needed
  scripts/*             # deterministic helper scripts / graders
  templates/*           # optional templates
```

Current skills:

| Skill | Use when | Best entry point |
|---|---|---|
| `nerd-code` | Build or implement production code from a rough request | `/build` |
| `conductor` | Multi-step feature, migration, refactor, or work needing parallel review lenses | `/orchestrate` |
| `critical-review` | Pre-ship review of a diff/PR, severity classification, fix suggestions | `/review` |
| `ponytail-audit` | Bug/code audit with detector-validator discipline | `/audit` |
| `security-sentinel` | Deep security/threat-model/OWASP/CWE review | `/secaudit` |
| `ponytail` | Minimal correct solution, dependency/abstraction deletion, YAGNI check | `/lazy` |
| `copilot-memory-harness` | Set up persistent project memory and Copilot working-memory conventions | direct request |
| `skill-doctor` | Improve a skill using eval-backed, keep/revert discipline | `improve-skill.prompt.md` |
| `skill-anatomy-optimizer` | Static anatomy audit of skills against the repo standard | `diagnose-skill.prompt.md` |

Self-improvement companions:

| Skill | Purpose |
|---|---|
| `critical-review-local`, `security-sentinel-local`, `nerd-code-local`, `ponytail-audit-local` | Project-specific learning surfaces. These may accumulate reviewed feedback patterns; core skills remain stable. |
| `update-critical-review`, `update-security-sentinel`, `update-nerd-code`, `update-ponytail-audit` | Outer-loop skills that read `.agents/feedback/skill-feedback.jsonl` and propose minimal diffs to the matching `*-local` companion only. |

---

## Best prompts for real work

### 1. Build a spec before code

Use this when you want a clean feature spec, acceptance criteria, and test plan before implementation:

```text
/orchestrate Build a spec for <feature>.
Context:
- Goal: <user/business outcome>
- Current files: <paths>
- Constraints: <performance/security/backcompat/deadline>
- Non-goals: <what must not be built>

Do not implement yet. First produce:
1. crisp goal
2. in/out of scope
3. acceptance criteria
4. edge cases/failure modes
5. architecture options with recommendation
6. test plan
7. open questions
```

For a smaller feature, use:

```text
/build Spec only first: <feature>. Do not edit files until the spec and tests are agreed.
```

### 2. Implement after the spec is accepted

```text
/build Implement the accepted spec for <feature>.
Use the existing code style. Make the smallest complete diff.
Must include tests for the acceptance criteria and failure modes.
After implementation, summarize changed files and how to run tests.
```

### 3. Review a PR/diff before shipping

```text
/review Review the current diff as a skeptical staff engineer.
Focus on correctness, regression risk, maintainability, and test gaps.
Group findings as Blocker / Major / Minor / Nit.
Every finding must include file:line evidence and a concrete fix.
Ignore style-only opinions unless they hide a real risk.
```

For GitHub PRs, give Copilot the PR URL or checked-out branch:

```text
/review Review PR <url>. Compare against main. Only report evidence-backed findings.
```

### 4. Security review

```text
/secaudit Threat-model the current diff.
Focus on authN/authZ, injection, secrets, SSRF, deserialization, path traversal, supply chain, data exposure, and unsafe defaults.
For every issue: exploit path, impacted asset, severity, and minimal fix.
```

### 5. Deep bug audit of a path

```text
/audit src/payments
Find real bugs only. Use detector-validator discipline:
- confirmed evidence first
- no speculative findings without a reachable path
- include file:line and repro/test idea
- separate confirmed bugs from risk notes
```

### 6. Minimalism / delete dead weight

```text
/lazy Review this design/diff for over-engineering.
Apply the restraint ladder:
1. Does this need to exist?
2. Can stdlib/native platform do it?
3. Can an existing dependency do it?
4. Can this be one line / one function?
Return what to delete, simplify, or keep.
```

---

## Recommended workflow

### For building a feature

```text
/orchestrate <feature> spec only
# review/edit spec
/build implement accepted spec
/review current diff
/secaudit current diff
/audit <changed paths>
```

### For reviewing an existing PR

```text
/review PR <url or branch>
/secaudit PR <url or branch>
/audit <critical paths>
/lazy Is any abstraction/dependency/change unnecessary?
```

### For small one-line fixes

Use `/build <fix>` directly. `nerd-code` has a mandatory complexity classifier and should take the trivial path when the root cause is clear, single-file, and ≤5 code lines.

---

## How to test the skills locally

Run these from the root of this repo.

### 1. Static anatomy audit for every skill

```bash
for f in .agents/skills/*/SKILL.md; do
  echo "== $f =="
  python3 .agents/skills/skill-anatomy-optimizer/scripts/audit_skill.py "$f"
done
```

Expected: every skill returns `gate: true` or equivalent passing status.

### 2. Eval/council loop smoke test

```bash
python3 .agents/evals/scripts/council_loop.py
```

Outputs:

```text
.agents/evals/reports/latest/council_report.json
.agents/evals/reports/latest/council_report.md
.agents/evals/decisions/decision_log.jsonl
```

Interpretation:

- `validation_errors = 0` is required.
- `skill_audit_failures = 0` is required before claiming the repo is healthy.
- `hold_for_review` means candidate source may be useful but is not approved.
- `discard` means the candidate/approach did not meet quality gates.

### 3. Harvest public PR candidates

```bash
python3 .agents/evals/scripts/harvest_github_prs.py --per-skill 3
```

This stores metadata only. It does **not** vendor third-party code.

### 4. JSON/JSONL validation

```bash
python3 - <<'PY'
from pathlib import Path
import json
for p in Path('.agents/evals').rglob('*.json'):
    json.loads(p.read_text())
for p in Path('.agents/evals').rglob('*.jsonl'):
    for i,line in enumerate(p.read_text().splitlines(),1):
        if line.strip(): json.loads(line)
print('json/jsonl ok')
PY
```

---

## Self-improving Skill loop

This repo now follows an Oz-style inner/outer loop model:

```text
inner loop: use a core Skill on real work
feedback: human/test/maintainer correction is recorded
outer loop: update-* Skill proposes a diff to the matching *-local companion
promotion: validator/evals/human review decide keep vs revert
```

Core Skills are stable contracts. Local companion Skills are the bounded learning surface:

```text
.agents/skills/critical-review/SKILL.md        # core contract
.agents/skills/critical-review-local/SKILL.md  # repo-specific feedback patterns
.agents/skills/update-critical-review/SKILL.md # outer improvement loop
```

Record feedback manually:

```bash
python3 .agents/feedback/scripts/record_feedback.py \
  --skill critical-review \
  --type false_positive \
  --source github_pr_review \
  --repo org/repo \
  --pr 123 \
  --agent-output "Major: retry race in payment worker" \
  --human-feedback "False positive: per-key lock middleware serializes this path" \
  --strength explicit_maintainer_statement \
  --desired-update "Check upstream locking before reporting retry races."
```

Validate feedback records:

```bash
python3 .agents/feedback/scripts/validate_feedback.py
```

Promotion rules:

1. Do not learn from one weak anecdote.
2. Promote only repeated patterns, explicit maintainer statements, eval failures, incident action items, or security-critical feedback.
3. Update Skills may patch only their matching `*-local/SKILL.md` file.
4. Core Skill edits require separate human review and stronger eval evidence.
5. Outer loops propose reviewable diffs; they do not silently mutate production behavior.
6. Prefer code/tool/eval fixes over prompt growth when the failure is deterministic.

---

## How to use evals correctly

The eval data is for **keep/revert decisions**, not vibes.

Rules:

1. Candidate cases start as `review_status: candidate`.
2. Do not call a case golden until provenance, license risk, and grader are reviewed.
3. Do not call a skill better unless it beats the baseline on the same cases.
4. Prefer executable/end-state checks over LLM-judge opinions.
5. Keep TRAIN / VALIDATION / TEST separate.
6. Any failed approach is logged and discarded instead of patched around silently.

The 30-minute council loop follows this principle: summarize what was harvested, held, discarded, or failed; do not overclaim.

---

## Maintenance commands

```bash
# inspect repo cleanliness
git status --short --branch

# run council smoke test
python3 .agents/evals/scripts/council_loop.py

# audit all skills
for f in .agents/skills/*/SKILL.md; do python3 .agents/skills/skill-anatomy-optimizer/scripts/audit_skill.py "$f"; done
```

When editing a skill:

1. Change `SKILL.md` minimally.
2. Run the anatomy audit.
3. Run relevant eval cases or council smoke test.
4. Keep only measured improvements; revert or discard failures.

---

## License

MIT — use freely. Attribution appreciated.
