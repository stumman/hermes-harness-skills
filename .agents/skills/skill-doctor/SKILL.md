---
name: skill-doctor
description: >
  Diagnose any Agent Skill against the shippability rubric, then autonomously improve it via a
  champion/challenger keep-or-revert loop with statistical eval gating and immutable versioning.
  Use when asked to diagnose, harden, or auto-improve a skill — not one-shot fixes (skill-evolve)
  or new-skill creation (skill-creator).
---
# Skill Doctor — diagnose and autonomously improve any Agent Skill

Make a SKILL.md measurably better without bloating it or breaking what already works. You diagnose against a deterministic rubric, then run a champion/challenger loop: propose ONE bounded edit, eval it against the current best, and keep it only when paired statistics prove a real gain with zero regressions — otherwise revert.

## Where this fits

Compose, don't duplicate: `skill-evolve` = quick one-shot fix; `skill-creator` = human-reviewed creation/eval of a new skill; `auto-optimize` = the single-agent keep-or-revert spine. **skill-doctor wraps that spine with a static rubric gate, statistical keep-gate, a diverse judge panel, side-effect/anti-bloat metrics, and immutable versioning** — the governed, autonomous layer. Defer subjective net-new authoring to skill-creator.

## Two-layer rule (do not break this)

Humans edit *this* skill's instructions, operator library, and config. The loop edits ONLY the target skill's files. Tuning the loop = editing meta-instructions, never hand-editing a candidate mid-run. This separation is what makes the harness skill-agnostic.

## Phase A — DIAGNOSE (deterministic, no model spend)

Run `scripts/lint_skill.py <target SKILL.md>` to score the target against the shippability rubric and emit a report (frontmatter compliance, body line/token count, reference depth, terminology drift, the three token tiers). Full checklist + regexes: [rubric.md](./references/rubric.md) — read before interpreting a diagnose report. This is also STEP 0 of the loop: any challenger that fails the lint is rejected **before** any eval token is spent. Supporting scripts: [lint_skill.py](./scripts/lint_skill.py), [score_paired.py](./scripts/score_paired.py), and [ledger.py](./scripts/ledger.py).

## Phase B — EVAL SETUP (define "better" before changing anything)

A change is "better" only if a structural gate AND a behavioral eval both say so.
- Build or confirm the golden set in the standard schema, stratified (happy / edge / near-miss / should-NOT-trigger / adversarial), split TRAIN / VALIDATION / TEST. Schema + split rules + grading format: [eval-schema.md](./references/eval-schema.md) — read before writing eval cases.
- Establish the baseline: run the current skill (champion) and a no-skill or previous-version control.
- Gate to proceed: ≥3 scenarios, each with a reference solution and outcome-based assertions (never assert tool-call order).
- Prefer code/regex grading. Use a model judge only for nuanced output, and then a diverse 3-judge panel — never a single judge. Judge rules, panel composition, and bias controls: [stats.md](./references/stats.md).

## Phase C — THE LOOP (champion/challenger, one edit per iteration)

1. **Read state:** champion SKILL.md + the append-only ledger + the rejected-edit buffer. Never re-propose a buffered reject.
2. **Analyze (TRAIN only):** from failing transcripts, write ONE root-cause sentence citing specific cases. Reject vague critiques. Read-frequency signals: never-read file → delete candidate; repeatedly-read file → inline candidate; ignored rule → strengthen candidate.
3. **Propose ONE bounded edit** from the fixed operator library, matched to the section's required freedom (don't vaguify a fragile exact step; don't over-specify an open task). Respect the per-iteration edit budget; never touch a `<!-- SLOW_UPDATE_START -->…<!-- SLOW_UPDATE_END -->` region. Write the hypothesis ("should raise assertion X from A→B because…"). Operators + when each applies: [operators.md](./references/operators.md).
4. **Apply as a new immutable version:** one git commit = one challenger. Never edit in place.
5. **Eval (paired, parallel):** run champion and challenger on the IDENTICAL locked eval set, k≥3 trials each, on ≥2 model tiers. The loop may NOT edit the eval. Capture pass@k, pass^k, tokens±sd, latency±sd.
6. **Keep-or-revert gate** — three outcomes; run `scripts/score_paired.py` to compute the paired-difference decision. Stats + formulas: [stats.md](./references/stats.md).
   - **CRASH** (eval failed / malformed skill): one cheap fix-and-rerun; if still broken, revert and log "crash".
   - **KEEP** iff ALL hold: (a) paired improvement is CI-significant on held-out VALIDATION; (b) zero regression on any previously-passing case; (c) pass^k did not drop; (d) side-effect metrics did not worsen (body tokens, scope creep, removed safety constraints); (e) non-dominated on the per-case Pareto frontier. Tie → keep only if the edit reduces body tokens, else revert.
   - **REVERT** otherwise: `git reset` to champion; log the edit + reason to the rejected-edit buffer.
7. **Version + ledger:** on KEEP, the challenger becomes champion; append one provenance entry to the external ledger. Run `scripts/ledger.py` to write it. Provenance lives OUTSIDE SKILL.md (version is not a spec field).
8. **Converge / escalate:** stop when held-out TEST clears target with all complaints addressed, OR no CI-significant delta remains, OR max iterations, OR plateau (K consecutive reverts) → force a radical crossover of near-misses, else escalate to a human with the diagnosis (skill-approach vs assertions vs test-set).

## Phase D — GOVERN

Immutable content-hashed versions on a dedicated branch; external append-only ledger + CHANGELOG sibling to the skill; merge-blocking CI gate (fail if the pass-rate CI lower bound < threshold); a kill-switch to repoint to last-known-good. Before marking any version shippable, run the security pass over bundled scripts and dependencies (the loop edits code). Schemas + gate: [governance.md](./references/governance.md).

## Phase E — SCALE (optional swarm)

For a hard skill where a measured single-agent baseline is weak, run the bundled improvement swarm at repo path `.agents/harness/improve-skill.workflow.js` (complexity router → propose pool → executor → judge panel → statistician). It applies this exact loop with parallel proposers and verifiers. Keep it bounded: a complexity router caps spend, the lint gate kills losers before eval, minibatch-then-confirm avoids full-eval cost on obvious losers.

## Anti-patterns (never)

- Edit the eval set, weaken an assertion, or delete a discriminating test to make a change "pass".
- Make more than one change per iteration, or skip the revert when the score ties or drops.
- Trust a single judge, or let the model that wrote the edit also judge it.
- Add a section speculatively — add only on an observed failure, and prefer a reference-file pointer over inlining.
- Mutate SKILL.md in place or write version/provenance into the skill itself.

## When to split vs improve in place

Improve in place by default. Move detail to one-level-deep reference files as the body approaches its budget. Split into a separate skill ONLY when the trigger conditions are genuinely distinct; MERGE two skills when a human can't tell which one a borderline prompt should fire (the router can't either). Heuristics: [rubric.md](./references/rubric.md).
