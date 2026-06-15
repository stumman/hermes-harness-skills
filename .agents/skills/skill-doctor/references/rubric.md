# Shippability Rubric, Lint Spec, and Split/Merge Heuristics

## Contents
- [Structural checklist](#structural-checklist) — pass/fail lint gates a skill must clear
- [Token tiers](#token-tiers) — three budgets measured separately
- [Split-vs-improve-vs-merge](#split-vs-improve-vs-merge) — routing decision
- [Sources](#sources)

## Structural checklist
Each item is a lint gate. FAIL blocks ship; WARN is advisory. Drives the keep-or-revert decision and the lint pass before any challenger is scored.

Metadata (always-loaded — see tiers):
- name MUST match `^[a-z0-9-]{1,64}$`. FAIL otherwise. (kebab-case, filesystem- and router-safe.)
- name MUST NOT contain `anthropic` or `claude`. FAIL. (reserved-vendor collision; Anthropic skill-naming guidance.)
- description present. FAIL if empty.
- description length <= 1024 chars. FAIL above. (YAML frontmatter hard cap.)
- description has a WHAT clause (what the skill does) AND a "Use when" WHEN clause (trigger conditions). FAIL if either missing. (CSO: router matches on both halves.)
- description 120–300 chars target. WARN outside. (too short = under-triggers; too long = dilutes match signal.)

Body (loaded on trigger):
- SKILL.md body <= 500 lines. FAIL above. WARN at ~400. (progressive-disclosure budget; push detail to refs before this.)
- reference depth <= 1 — refs may not link to further nested refs. FAIL on depth 2+. (one hop keeps load cost bounded.)
- any bundled `.md` > 100 lines MUST open with a `## Contents` TOC. FAIL otherwise. (navigability standard for long files.)

Content quality:
- no option-soup: reject "X or Y or Z" enumerations presented as equal choices. WARN. (pick one default; list alternatives only with selection criteria.)
- consistent terminology — no synonym drift for a single concept (champion/challenger, keep-or-revert, paired CI gate, operator library, rejected-edit buffer, external ledger, SLOW_UPDATE protected region used verbatim). WARN per drifted term. (router and reader both rely on one name per thing.)
- no time-sensitive date strings (e.g. "as of 2026", "latest", hardcoded years/versions in prose). WARN. (skills are evergreen; dated text rots.)
- scripts solve-not-punt — no `TODO`, `pass`-only bodies, `raise NotImplementedError`, or stub returns on the success path. FAIL. (a referenced script must do the task.)
- no undocumented magic numbers — every non-obvious numeric constant in a script has a one-line comment naming the assumption. WARN per bare constant.
- dependencies listed — scripts declare their runtime (stdlib-only stated, or deps enumerated). WARN if a non-stdlib import is undeclared.
- forward-slash paths only in docs/scripts. WARN on backslash paths. (cross-platform; portable refs.)
- eval count >= 3 — skill ships with at least three eval prompts/cases. FAIL below 3. (need a sample to run the paired CI gate; n<3 cannot bound variance.)

## Token tiers
Measure and report each tier independently — they have different load semantics and budgets:
1. metadata/description — name + description frontmatter. Loaded ALWAYS, for EVERY skill in the collection, into every session. Tightest budget; every char here is a tax on all other skills. This is why the 120–300 char target matters.
2. body — SKILL.md body below frontmatter. Loaded only when the skill triggers. Budget tracks the <=500-line / ~400 WARN gate.
3. total bundle — body + all references + scripts. Loaded on demand (refs read only when the body points to them). Largest allowance; the point of pushing detail to one-level refs is to keep tier 1 and 2 small while tier 3 absorbs depth.

Regressions in tier 1 are weighted hardest in keep-or-revert: a challenger that grows the always-loaded metadata must clear a higher bar than one that only grows on-demand bundle.

## Split-vs-improve-vs-merge
Default: improve-in-place. Edit the existing skill; do not spawn a new one. Most challengers are in-place rewrites scored by the paired CI gate.

Move-to-refs (still one skill): when the body nears the tier-2 budget (~400 lines WARN), relocate detail into a one-level reference rather than splitting. Keep the trigger surface and procedure in the body; push tables, long examples, and edge-case catalogs to refs. This is the preferred response to "the skill is getting big."

Split to a SEPARATE skill: ONLY when trigger conditions are genuinely distinct — two non-overlapping sets of WHEN clauses that a router can cleanly tell apart, each large enough to warrant its own progressive-disclosure budget. Distinct triggers, not distinct sections, justify a split. If you cannot write two non-overlapping "Use when" descriptions, do not split.

MERGE: apply the router-disambiguation litmus across the WHOLE collection. For each pair of skills, ask: could a human, reading only the two descriptions, reliably say which one a borderline prompt should fire? If NO — if the boundary is a coin-flip — merge them. Overlapping triggers cause router thrash and silent mis-fires; one well-scoped skill beats two ambiguous ones. Run this litmus collection-wide whenever a new skill is added.

Decision order: improve-in-place → move-to-refs (budget pressure) → split (distinct triggers) → merge (ambiguous triggers). Splitting and merging are the rare cases; treat in-place improvement as the norm.

## Sources
- Anthropic Agent Skills authoring best-practices — progressive disclosure, frontmatter caps, CSO description structure (WHAT + WHEN), kebab-case naming, evergreen content.
- Context-engineering — three-tier token accounting (always-loaded metadata vs. on-trigger body vs. on-demand bundle), one-level reference depth, router-disambiguation across a skill collection.
