# Edit-Operator Library

## Contents
- [Operators](#operators) — the eight allowed edits, one applied per iteration
- [Read-frequency signals](#read-frequency-signals) — turn observed file reads into edit candidates
- [Altitude matching](#altitude-matching) — match degrees of freedom to step fragility
- [Iteration constraints](#iteration-constraints) — budget, protected region, reject buffer

## Operators
Each challenger applies exactly ONE operator. Pick the operator whose failure signal the champion's
losing transcripts actually exhibit — do not guess.

| Operator | When to apply | Failure signal it fixes |
|---|---|---|
| **add-missing-instruction** | A correct run requires a step the skill never states. | Trajectory does the right thing only by luck / omits it entirely. |
| **strengthen-to-MUST/imperative** | A stated rule is hedged ("prefer", "try to", "you may"). | Agent reads the rule, then rationalizes around it (ignored rule). |
| **promote-rule-to-top** | A load-bearing rule sits below ~line 100 or after long prose. | Rule obeyed when transcript is short, dropped on long runs (recency loss). |
| **inline-frequently-read-file** | A reference file is opened on nearly every run. | Repeated read of same file == latency + risk it's skipped under budget. |
| **delete-never-read-file** | A bundled file is never opened across the eval set. | Dead weight: inflates skill, dilutes attention, never load-bearing. |
| **split-body-into-reference** | SKILL.md body is long AND a section is read only conditionally. | Body bloat pushes high-frequency rules down; cold detail crowds hot path. |
| **crossover-merge** | Two prior challengers each near-missed on *different* sections. | Each variant fixed one half; neither dominates — splice both best sections. |
| **Lamarckian reverse-engineer** | A run PASSED without explicit guidance for the winning move. | Implicit competence: extract what the passing trajectory did, write it as a rule. |

Notes:
- crossover-merge draws only from the external ledger's recorded near-miss variants (their diffs and
  per-section scores), never from live invention — it recombines proven sections.
- Lamarckian: read the passing transcript, name the decisive action, encode it imperatively. Reverse
  direction from the usual (rule->behavior); here behavior->rule.

## Read-frequency signals
Collect per-file open counts from the eval trajectories, then map to a candidate operator:

| Observed signal | Operator candidate |
|---|---|
| File never read across all runs | `delete-never-read-file` |
| File read on most/all runs | `inline-frequently-read-file` |
| Rule present in context but contradicted by action | `strengthen-to-MUST/imperative` (ignored rule) |

A signal yields a *candidate*, not a mandate — altitude and budget still gate it.

## Altitude matching
Match degrees of freedom to fragility. Wrong altitude is itself a failure mode, independent of wording.

- **Fragile exact step** (exact flag, literal string, ordered sequence): keep it specific. NEVER vaguify
  — "run `pytest -q`" must not become "run the tests."
- **Open-ended task** (judgment, design, synthesis): keep degrees of freedom open. NEVER over-specify —
  do not hard-code one acceptable answer where many are valid; over-constraint causes brittle false fails.
- Before applying any operator, ask: does this edit move altitude toward the step's true fragility, or
  away from it? Reject edits that flatten that match.

## Iteration constraints
- **One edit per iteration.** The paired CI gate must attribute the delta to a single operator, else
  keep-or-revert is uninterpretable.
- **Edit budget (textual learning rate).** Cap characters changed per iteration. Large rewrites are
  high-variance and unattributable; prefer the smallest edit that could plausibly flip the gate.
- **SLOW_UPDATE protected region.** NEVER edit inside it. Operators that would touch it abort and the
  candidate is discarded before testing.
- **Rejected-edit buffer.** Any edit that failed its paired CI gate (challenger did not beat champion)
  is logged with its operator + diff. NEVER re-propose a buffered edit; consult the buffer before
  emitting a candidate so iterations explore new ground.
