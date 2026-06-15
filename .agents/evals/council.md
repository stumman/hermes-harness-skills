# Research Council Protocol

Purpose: run a conservative, data-backed council loop for Hermes skill evals. The council may discover, score, and propose changes, but it must not claim improvement unless the evidence passes gates.

## Council roles

1. **Dataset Curator / Research Scout**
   - Finds public real-world sources: merged PRs, issue-linked fixes, SWE-bench, CVEfixes, CodeReviewer, Defects4J, BugsInPy, BugSwarm, Promptfoo/DSPy/agent-instruction repos.
   - Rejects weak provenance, unclear license, no immutable source, synthetic-only happy paths, duplicates, and irrelevant PRs.

2. **Eval Scientist / Statistician**
   - Defines baseline, primary metric, sample size, confidence cap, effect threshold, and keep/revert/discard decision.
   - Blocks overclaiming from tiny samples or non-comparable tests.

3. **Benchmark Engineer**
   - Maintains validation scripts, JSONL schemas, reproducible reports, decision logs, and no-vendored-code policy.
   - Ensures all failures become visible data, not silent success.

4. **Skill Anatomist / Optimizer**
   - Runs static anatomy checks across skills and proposes minimal patches only when backed by lint/eval evidence.
   - Separates static improvement from behavioral improvement.

5. **Safety / License Reviewer**
   - Checks privacy, secrets, exploit risk, destructive action risk, license ambiguity, and redistribution risk.
   - Blocks automatic approval when uncertain.

## 30-minute loop

Each scheduled run should produce data, not prose-only opinions:

1. Harvest real candidate sources.
2. Validate all JSON/JSONL/eval files.
3. Score harvested candidates.
4. Run static skill anatomy audit.
5. Produce a run report with counts and decisions.
6. Append a machine-readable decision record.
7. Keep only metadata/schema/report improvements that pass validation.
8. Reject/discard approaches that fail validation or lack measurable evidence.

## Decision labels

- `keep`: objective checks improved and no critical regression.
- `keep_provisionally`: promising but sample/confidence insufficient; must retest.
- `needs_human_review`: valuable but license/security/subjective judgment requires human review.
- `revert`: no meaningful gain or mixed result.
- `discard`: invalid, unsafe, low-quality, duplicate, non-reproducible, or materially worse.

## Default gates

Keep/provisional keep requires:

- Valid JSON/JSONL and schema fields.
- No vendored third-party code or patches.
- License/provenance notes present.
- Static anatomy gate passes for changed skills.
- Candidate quality score >= threshold for its decision.
- No critical safety or privacy flags.

Discard immediately if:

- No license or all-rights-reserved where reuse is needed.
- No immutable source URL/version/commit/DOI.
- Duplicate of an existing case with lower quality.
- Pure formatting/lockfile/bot bump unless explicitly relevant.
- Secret/PII/malware/leaked data risk.
- Test was non-comparable or metric undefined.
