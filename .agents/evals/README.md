# Golden Source Eval Program

This directory turns skills into research-grade artifacts: every skill gets real public change data, frozen eval cases, deterministic graders where possible, and paired champion/challenger reports.

## Principles copied from serious eval programs

- **Real sources first:** prefer merged public PRs, issue-linked fixes, CVE fixes, and executable bug benchmarks over synthetic prompts.
- **Datasets and graders are separate:** a case records source/provenance; a grader records how to score it.
- **Executable checks beat opinions:** use tests, patch application, static checks, link checks, diff invariants, and security scanners when available.
- **Pairwise keep-or-revert:** compare champion vs challenger on identical cases; keep only measured wins with zero critical regressions.
- **Held-out discipline:** TRAIN may inform edits; VALIDATION decides keep/revert; TEST confirms generalization.
- **Trace capture:** store prompt, skill version, source PR/issue, diff, model/tool versions, output, grader evidence, and final decision.
- **Human/LLM judge calibration:** use LLM judges only with rubrics, evidence, A/B blinding, and periodic human spot checks.

## Directory layout

```text
.agents/evals/
  README.md
  methodology.md
  sources.json
  skills-map.json
  cases/
    <skill>.jsonl
  scripts/
    harvest_github_prs.py
```

## Case lifecycle

1. Harvest candidate PR/issue/dataset records.
2. Normalize into the case schema.
3. Human/researcher review: remove noisy, non-reproducible, license-risky, or trivial cases.
4. Freeze split: TRAIN / VALIDATION / TEST.
5. Run champion skill and challenger skill on same cases.
6. Keep only if gates pass.
7. Add every newly observed failure as a regression case.
