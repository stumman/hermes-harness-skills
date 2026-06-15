---
name: skill-anatomy-optimizer
description: >
  Audit and improve agent SKILL.md files with evidence-based anatomy checks, eval design, and keep-or-revert gates. Use when asked to review, quality-check, optimize, harden, compare, or test a reusable skill or prompt.
---
# Skill Anatomy Optimizer

Improve a skill only when evidence shows the candidate is better than the current champion. Treat skills as code: lint structure, define the eval, propose the smallest useful edit, test the candidate, then keep or revert.

## Operating rule

Never call a skill “better” from taste alone. Require one deterministic anatomy gain and no critical regression. For behavior-changing edits, require paired baseline-vs-candidate eval cases.

## Procedure

1. **Snapshot champion.** Save the original `SKILL.md` and list bundled files. Do not edit before baseline metrics exist.
2. **Audit anatomy.** Run the deterministic auditor: `[audit script](./scripts/audit_skill.py) — run before and after every candidate edit`. Also run any repo-local linter if present.
3. **Classify edit type.**
   - Structural: frontmatter, links, TOC, terminology, dead metadata, token tier placement.
   - Behavioral: trigger wording, procedure, constraints, tools, examples, output contract.
   - Risky: split/merge, scope change, safety rule removal, tool permission change.
4. **Define “better” before editing.** Use `[evaluation method](./references/testing-method.md) — read before judging behavioral changes` to create or select golden cases.
5. **Propose one bounded edit.** Use failure evidence as the reason. Prefer patch-sized changes; never rewrite the whole skill unless the anatomy is unrecoverable.
6. **Test champion vs challenger.** Compare structural metrics, token tiers, link health, trigger clarity, and golden-case behavior. Use pairwise judging for subjective outputs.
7. **Keep gate.** Keep only if all hold:
   - deterministic gates pass or improve;
   - no dangling/orphan files;
   - no critical safety/behavior regression;
   - token growth is justified by a measured behavioral gain;
   - the diff is explainable as one edit hypothesis.
8. **Report evidence.** Output baseline, candidate, delta, failed gates, risk, and the exact patch or files changed.

## Anatomy rubric

Check these dimensions in order:

- **Loadability:** folder name equals `name`; kebab-case; documented frontmatter keys only.
- **Routing:** description has WHAT + WHEN, concrete user phrases, distinctive first 80 chars, sibling disambiguation when needed.
- **Progressive disclosure:** description = routing only; body = every-run procedure; references/scripts/templates = conditional depth.
- **Procedure:** numbered steps, gates, success criteria, failure handling, output contract.
- **Tool policy:** when to search/read/edit/run/delegate; destructive actions gated; side effects verified.
- **Examples:** only examples that change behavior; positive, negative, and edge examples move to references when long.
- **Eval readiness:** at least happy, edge, should-not, and adversarial cases for behavioral claims.
- **Maintainability:** no marketing, version lore, metric bragging, TODOs, duplicate rules, or unlinked bundle files.

## Output format

```text
DECISION: KEEP | REVERT | NEEDS EVAL
WHY: <one sentence>
BASELINE: <score/gates/tokens>
CANDIDATE: <score/gates/tokens>
DELTA: <what improved, what worsened>
REGRESSION CHECK: <cases or deterministic proof>
PATCH: <files changed or suggested diff>
NEXT: <smallest next test/edit>
```

## Anti-patterns

- Do not optimize against the test set you used to design the edit.
- Do not weaken tests or delete discriminating cases to make a candidate pass.
- Do not let the model that wrote a broad rewrite be the only judge.
- Do not add generic advice without a failure it prevents.
- Do not split a skill unless the `Use when` triggers are separable by a router.
