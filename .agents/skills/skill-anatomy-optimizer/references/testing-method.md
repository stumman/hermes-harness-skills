# Testing Method for Skill Improvements

Use this method before claiming a skill improved.

## What other systems do

- Promptfoo-style evals separate prompts, test cases, providers, and assertions; gates compare baseline vs candidate in CI.
- OpenAI Evals / Inspect AI-style harnesses store datasets, graders, traces, model settings, and pass/fail artifacts for replay.
- DeepEval/RAGAS-style checks combine deterministic assertions with semantic judges, not a single vague quality score.
- DSPy / ProTeGi / OPRO-style optimization treats failures as gradients: propose candidate edits, score on held-out cases, keep only measured wins.
- Claude subagents / OpenHands microagents / AGENTS.md conventions make routing, tool access, scope, and validation explicit so an agent can select and execute the right instruction.

## Evaluation layers

1. **Static anatomy gate** — deterministic, cheap, always run.
   - frontmatter schema, name/folder match, description shape, token tiers, link health, orphan files, banned drift.
2. **Routing gate** — user prompts that should and should not trigger the skill.
   - include hard negatives sharing keywords with true positives.
3. **Behavior gate** — task cases where the skill changes the agent output.
   - score outcomes, not exact tool-call order.
4. **Safety gate** — adversarial cases and critical constraints.
   - any critical failure blocks keep even if average score improves.
5. **Cost gate** — token/body growth, tool-call growth, latency if measured.
   - accept growth only with a meaningful behavior gain.

## Minimal golden set

Start with at least six cases:

- 2 happy in-scope cases;
- 1 edge case;
- 1 near-miss;
- 1 should-not-trigger case;
- 1 adversarial case.

For serious promotion, grow to 50–200 cases. Split once and freeze:

- TRAIN: edit proposal may inspect failures;
- VALIDATION: keep/revert decision;
- TEST: final confirmation after keep.

## Case schema

```json
{
  "id": "skill-routing-001",
  "stratum": "happy|edge|near-miss|should-not|adversarial",
  "prompt": "User request verbatim",
  "reference": "Expected correct behavior",
  "assertions": [
    "must ...",
    "must NOT ..."
  ],
  "critical": false
}
```

## Pairwise judging rules

Use pairwise baseline-vs-candidate when output quality is subjective.

- Hide which output is baseline.
- Judge correctness first, then instruction-following, then concision/cost.
- Swap A/B order or use at least two independent judges for high-risk changes.
- Require evidence quotes or diff references; unsupported verdicts fail.
- Prefer deterministic graders for format, links, file changes, and test results.

## Keep-or-revert policy

Keep if:

- static gate passes;
- validation score improves or ties while reducing cost;
- zero critical regressions;
- no previously passing case becomes failing;
- token growth is <=10%, unless behavior gain is material and documented.

Revert if:

- any critical safety case fails;
- links/frontmatter/loadability regress;
- candidate bloats without measured gain;
- candidate solves TRAIN but regresses VALIDATION/TEST;
- edit combines multiple hypotheses so the cause of improvement is unknowable.
