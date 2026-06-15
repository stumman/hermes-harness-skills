# Research-Grade Skill Eval Methodology

## Sources to imitate

- **SWE-bench / SWE-bench Verified:** real GitHub issue-to-patch tasks with executable tests and human validation.
- **OpenAI Evals / Inspect AI:** dataset + grader separation, trace artifacts, reproducible config.
- **Promptfoo:** prompt variants, assertions, CI gates, adversarial tests.
- **DSPy / ProTeGi / OPRO:** prompt/skill changes as candidate programs optimized against metrics.
- **Anthropic-style preference evals:** pairwise, blinded, safety/helpfulness/honesty dimensions.
- **HELM / LM Eval Harness:** scenario-level reporting, multiple metrics, transparent limitations.
- **RAGAS / LangSmith-style tracing:** separate retrieval/context failure from generation failure.
- **METR-style agent tasks:** sandboxed environment, end-state verification, time/cost budgets.

## Case schema

Each JSONL line should follow:

```json
{
  "id": "nerd-code-swebench-0001",
  "skill": "nerd-code",
  "split": "TRAIN|VALIDATION|TEST",
  "stratum": "happy|edge|near-miss|should-not|adversarial|regression",
  "source_type": "github_pr|github_issue|swe-bench|cvefixes|defects4j|bugs-in-py|codereviewer",
  "source_url": "https://github.com/org/repo/pull/123",
  "repo": "org/repo",
  "title": "PR or issue title",
  "task_prompt": "What the agent should be asked to do",
  "gold_signal": {
    "patch_url": "...",
    "tests": ["..."],
    "review_comments": ["..."],
    "expected_findings": ["..."]
  },
  "assertions": [
    "must ...",
    "must NOT ..."
  ],
  "critical": false,
  "grader": "static|unit-test|patch-apply|security-rubric|pairwise-llm|human",
  "license_notes": "public GitHub metadata; check repo license before redistributing patches",
  "review_status": "candidate|approved|rejected"
}
```

## Skill-to-source mapping

- `nerd-code`: SWE-bench Verified/Lite, DevEval, CodeEditorBench, real VS Code/TypeScript/Rust feature PRs.
- `ponytail-audit`: Envoy, Kubernetes, Node.js, PostgreSQL bug-fix PRs; CodeReviewer review-comment data.
- `security-sentinel`: CVEfixes, Vul4J, Big-Vul/MegaVul, Kubernetes/Envoy security-sensitive PRs, OWASP Benchmark.
- `critical-review`: PRs with severity labels, breaking-change labels, release-blocker discussions, Node.js semver-major PRs.
- `conductor`: large multi-PR migrations, Rust rollups, Kubernetes feature gates, VS Code refactors.
- `ponytail`: accepted simplification/removal PRs, dependency-removal PRs, stdlib replacement PRs, small fixes that reject overengineering.
- `copilot-memory-harness`: agent memory/instruction PRs, Copilot prompt-file PRs, AGENTS.md/CLAUDE.md repo instruction changes, trace-to-regression cases.
- `skill-doctor` and `skill-anatomy-optimizer`: prompt/skill/instruction-file changes, OpenHands microagents, Claude/Copilot prompt files, Promptfoo/DSPy eval configs.

## Gates

Keep a skill change only when:

1. Static anatomy/loadability gates pass.
2. Critical safety failures remain zero.
3. No previously-passing approved case regresses.
4. VALIDATION improves, or ties while reducing token/body/tool cost.
5. TEST confirms the gain after keep.
6. Every subjective judge verdict includes evidence.

## Research-team roles

Run these lenses independently on high-risk skill changes:

- **Dataset Curator:** source quality, licensing, split discipline, contamination risk.
- **Benchmark Engineer:** executable harness, reproducibility, trace capture.
- **Skill Anatomist:** trigger, scope, progressive disclosure, examples, output contract.
- **Safety/Security Reviewer:** prompt injection, destructive tools, secrets, unsafe advice.
- **Statistician:** paired deltas, confidence, category regressions, false positives.
- **Research Scout:** new public datasets, papers, eval frameworks, industry methods.
