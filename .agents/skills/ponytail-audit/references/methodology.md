# Full Methodology (parent-agent audits)

## Contents

- [Methodology choice](#methodology-choice)
- [Detector-Validator pipeline (Combined only)](#detector-validator-pipeline-combined-only)
- [The Audit Ladder (per file) — expanded](#the-audit-ladder-per-file--expanded)
- [How to Audit](#how-to-audit)
- [Cross-File Consistency Check (MANDATORY)](#cross-file-consistency-check-mandatory)
- [Output Format](#output-format)
- [Overall Rating: X/10](#overall-rating-x10)
- [Cross-File Consistency (build this table first)](#cross-file-consistency-build-this-table-first)
- [Critical (must fix before production)](#critical-must-fix-before-production)
- [High](#high)
- [Medium](#medium)
- [Low](#low)
- [Race Conditions (separate section)](#race-conditions-separate-section)
- [Per-File Scores](#per-file-scores)
- [Test Coverage Audit](#test-coverage-audit)
- [Severity-Weighted Remediation Plan](#severity-weighted-remediation-plan)
- [Clean Surfaces (MANDATORY)](#clean-surfaces-mandatory)
- [Golden-Source Self-Evolution Loop](#golden-source-self-evolution-loop)


Use this for parent-agent audits of production codebases. Subagents use only the quick checklist in the body.

## Methodology choice

1. **Ponytail-only:** restraint ladder + 9-rung audit. Fast, lean. Best for quick scans, single-file reviews, early-stage code, <10 files.
2. **Combined (default):** restraint ladder, then 6-lens rigor, then cross-route comparison, then detector-validator pipeline. Full depth. Best for production codebases, multi-file audits, security-critical code.

## Detector-Validator pipeline (Combined only)

Two passes for precision.

### PASS 1 — DETECTOR (preceded by Gate 0)

**GATE 0 — ANTI-CONFABULATION (MANDATORY):** Before any verdict, echo the exact artifact being judged, read freshly this turn. No inference from context. No recollection from memory.
1. Read the file/function/symbol with a terminal tool call THIS TURN.
2. Paste the relevant content into your reasoning.
3. Only then issue a finding.

A finding issued without a same-turn echo of its target is invalid and MUST be discarded. This prevents the top LLM code-review failure: reporting issues from context memory that don't exist in the actual code.

After Gate 0 clears: find EVERYTHING. Be exhaustive. Flag everything suspicious. Apply all 6 lenses + cross-route comparison. No filtering. No "this might be intentional" — flag it anyway.

### PASS 2 — VALIDATOR

Apply 4 hard gates FIRST, then suppression rules.

**HARD GATES (per finding — any failure = discard or downgrade to Informational):**
- **Gate 1 — ANCHOR:** read the full symbol/function, not just the diff. The finding must reference actual code, not an assumption.
- **Gate 2 — EVIDENCE:** each finding MUST include a file:line citation and relevant pasted content from tool output. No citation = no finding.
- **Gate 3 — SEVERITY:** map to the severity table. Over/under-inflation without justification = recalibrate or discard.
- **Gate 4 — FORMAT:** `[FILE:LINE] ISSUE_TITLE` mandatory. Every finding must be independently verifiable from the format alone.

**EVIDENCE BOUNDARY ANNOTATIONS** — every finding carries a provenance tag:
- `[CONFIRMED]` — tool output, test result, or file content directly observed this turn.
- `[DETECTED]` — high-confidence pattern match, tool-assisted.
- `[INFERRED]` — heuristic, prior knowledge, or indirect evidence. Flag explicitly.

**EVIDENCE SAFETY:** Never quote secret values, tokens, private keys, credentials, or PII in audit reports. Refer only to the path, variable name, secret type, or data category.

**SUPPRESSION RULES** (after hard gates pass — only REPORT findings that survive ALL):
1. **Intentional?** Comment explaining why this pattern was chosen (e.g. `// ponytail: global lock intentional`)? If credible → SUPPRESS.
2. **Documented?** Known decision in AGENTS.md, CLAUDE.md, PLAN.md, or an ADR? If yes → SUPPRESS with reference.
3. **Pattern?** Recurring idiom used consistently across 3+ locations and not itself dangerous? → SUPPRESS (note the pattern).
4. **Confidence?** After rules 1-3, >80% confident it's real? Below → mark LOW severity with "low confidence" note. Above → report at true severity.

**UNSUPPRESSIBLE FINDINGS** — these bypass ALL four suppression rules; a comment, ADR, recurring pattern, or low confidence can NEVER excuse them. Report at true severity regardless:
- Hardcoded production credentials (passwords, API keys, tokens, JWT secrets with literal fallback values — Rung 3).
- Missing authentication on endpoints handling user data or financial operations (Rung 7).
- SQL injection via string concatenation, not parameterized/prepared (Rung 8).

They are unsuppressible because the cost of false suppression (data breach, account takeover, database compromise) dwarfs any false-positive cost.

### Three passes within DETECTOR
1. **Restraint ladder:** run the ladder on every module. Does this code need to exist? Stdlib? Native? Installed dep? One line? Finds bloat, dead code, over-abstraction.
2. **6-lens rigor:** apply correctness, design, security, performance, tests, and placement lenses to every surviving module. Finds race conditions, missing auth, broken error handling, security anti-patterns.
3. **Scaled analysis:** cross-route comparison table, data-flow tracing (always-true → find callers → dead branch), systemic pattern detection (all controllers missing the same defense). Finds architecture-level issues no file-by-file audit catches.

## The Audit Ladder (per file) — expanded

Walk every source file through these rungs. Flag anything that fails.

1. **Does this code need to exist at all?** Dead code (unreachable branches, functions never called, enums never used, classes with zero instantiation); dead imports (every `import` traced to a usage site; exported validators never called by any route/service → dead code); hollow shells (functions that always return the same value, making callers' branches unreachable); duplication.
2. **Is every abstraction earning its keep?** Interface with exactly one implementation → flag. Class with no internal state → should be pure functions. Abstract class with one concrete subclass → dead weight.
3. **Hardcoded secrets?** API keys, tokens, passwords, client secrets with literal fallback values; credentials in source that should be env-only; internal auth tokens hardcoded as defaults.
4. **Resource leaks?** `setInterval`/`setTimeout` not cleared on error paths; file handles/readers not released in `finally`; event listeners not removed; Maps/Sets/arrays that grow unbounded with no eviction; global mutable state persisting across requests with no cleanup.
5. **Race conditions?** Async check-then-act with a gap; boolean flags used as locks without atomic ops; shared mutable state accessed outside synchronization.
6. **Error handling consistent and complete?** Empty `catch` blocks; `void` on promises without `.catch()`; silent error continuation (`continue` on null without logging, `return null` masking failures); inconsistent error response construction; missing error types in centralized taxonomy; batch operations where one failed item aborts the batch (no per-item isolation); missing retry/exponential backoff/circuit breaker on external calls; invalid/unrecognized input silently dropped (no alert, no dead-letter queue); missing idempotency key on webhooks/notifications (replay → duplicate side effects); in-memory dedup/state lost on restart.
7. **Input validation at every trust boundary?** Missing request body size limits; missing parameter sanitization (user input in URLs/commands/templates without encoding); validation that accepts everything (`^.*$`, `return true`); auth middleware missing on some routes (compare all); rate limiting missing on some routes (compare all); missing brute-force/account-lockout protection; entity-level validation gaps (fields without `@Min/@Max/@NotNull/@NotBlank` or runtime checks; role as plain String with no enum constraint); CSV/export safety gaps (formula injection, missing UTF-8 BOM, path traversal on export paths); file upload validation by extension/MIME only without magic-byte inspection; host/protocol header gaps (RFC 7239 `Forwarded` unparsed, naive quote stripping).
8. **Security anti-patterns?** Non-constant-time secret comparison; user input in template strings without encoding (reflected XSS); logging sensitive data; missing dependency/build security scanning (OWASP dependency-check, `npm audit`, Snyk/Dependabot; unpinned version ranges `^`/`~`/`*`/`latest`; transitive deps unchecked; missing license/deprecated metadata; only `postinstall` flagged; bin-linking without target check; aggregation hiding individual failures); missing HTTP security headers (XFO/CSP/HSTS/XCTO); missing response body size limits; image-processing anti-patterns (ImageTragick, incomplete EXIF stripping); CORS `Access-Control-Max-Age` > 3600; mutable module-level exported state; cross-tenant operations without per-record authorization; email security gaps (DKIM/DMARC/SPF, spoofable `From`, missing `List-Unsubscribe`).
9. **Tests covering critical paths?** Count tests — zero is a finding. Error paths tested? Auth failures, rate limiting, invalid input? Concurrent paths? Resource-cleanup paths?

## How to Audit

1. **Read EVERY source file.** No skipping, no assuming. ENUMERATE ALL ARTIFACTS, not just source code: `.sql` migrations, `.xml` Spring configs, `.yml`/`.properties`, `pom.xml`/`package.json` carry high bug density. Use broad enumeration: `find . -type f \( -name '*.java' -o -name '*.sql' -o -name '*.xml' -o -name '*.properties' -o -name '*.yml' -o -name '*.json' -o -name '*.yaml' \) -not -path '*/test/*' -not -path '*/node_modules/*' -not -path '*/target/*'`. For 25+ files, use parallel subagents — run the Pre-Flight Checklist in [parallel-audit-pattern.md](./parallel-audit-pattern.md) first (read manifest → enumerate → assign every file to exactly one group → flag new and high-value files → balance group sizes → verify total matches).
2. **Build a route table FIRST.** Every endpoint: auth? rate limiting? validation? Comparison table is where most cross-file findings come from. Route A has auth, Route B doesn't → HIGH.
3. **Compare files against each other.** Inconsistency between routes handling the same class of operation (e.g. financial) is a finding.
4. **Trace the data flow.** Always-`true` function → find callers → flag dead branch. Imported-never-called → dead import. Defined-never-referenced enum → dead code.
5. **Read the tests.** Almost none → standalone finding. List what's untested: auth failures, rate limiting, validation, error paths, concurrency.
6. **Check repositories/DAOs.** Native queries with unvalidated params? LIKE concatenation? `findAll()` without pagination? Unbounded derived-query string matching?
7. **Inspect entities for validation gaps.** `double` for money? Missing `@Version`? Constrained fields as plain strings? Numeric fields missing bounds?
8. **Inspect application entry point.** Spring Boot: `@EnableCaching`/`@EnableScheduling`/`@EnableAsync` present when the feature is used?
9. **Rate each file 1-10** and explain why.
10. **Rate the whole codebase 1-10** and list every finding with severity.

## Cross-File Consistency Check (MANDATORY)

Build this for every audit; it catches the hardest issues.

| Feature | Route A | Route B | Finding |
|---|---|---|---|
| Auth middleware | yes/no | yes/no | mismatch: HIGH |
| Rate limiting | yes/no | yes/no | mismatch: HIGH |
| Input validation | yes/no | yes/no | mismatch: MEDIUM |
| Centralized errors | yes/no | yes/no | mismatch: MEDIUM |
| Body size limit | yes/no | yes/no | missing on all: HIGH |
| Test coverage | yes/no | yes/no | coverage < 10%: MEDIUM |

When routes handle the same CLASS of operation (both financial, both user-data, both admin), any mismatch in auth or rate limiting is automatically HIGH — not a judgment call.

## Output Format

```
# Audit: <repo-name>

## Overall Rating: X/10
<one-sentence summary>

## Cross-File Consistency (build this table first)
| Route | Method | Auth | Rate Limit | Validation | Centralized Errors | Body Size Limit |
|---|---|---|---|---|---|---|
### Mismatches
- MISMATCH: <route> has <feature> but <route> doesn't — <severity>

## Critical (must fix before production)
- [file:line] Finding — why it matters — fix effort
## High
- [file:line] Finding — why it matters — fix effort
## Medium
- [file:line] Finding — why it matters — fix effort
## Low
- [file:line] Finding — why it matters — fix effort

## Race Conditions (separate section)
- [file:line] TOCTOU / async gap — description

## Per-File Scores
| File | Lines | Score | Key Issue |
|---|---|---|---|

## Test Coverage Audit
| Test File | Tests | What's Tested | What's Missing |
|---|---|---|---|
### Critical Testing Gaps (zero coverage)
- <subsystem> — no tests for <paths>

## Severity-Weighted Remediation Plan
| Priority | Finding | Fix | Effort |
|---|---|---|---|

## Clean Surfaces (MANDATORY)
- <surface> — no issues found
```

Every section is MANDATORY. Do not skip the cross-file table, the test-coverage breakdown, the remediation plan, or the clean-surfaces declaration.

## Golden-Source Self-Evolution Loop

This skill is improved via a golden-source testing loop: audit golden repos with planted issues → compare to manifests → categorize missed findings → patch the ladder → prove improvement.

**Golden-source design.** A detection rate measured on a security-skewed golden source is misleading. Most real production outages are triggered by changes (binary push, config push) — categories nearly absent from security-focused golden sources. Expand golden sources to include production-incident patterns: deployment regressions, config cascades, retry storms, observability gaps, capacity cliffs. Always report detection rate BY CATEGORY (incidents vs security vs correctness), not just as an aggregate.

**Automation:** [compare-to-manifest.py](../scripts/compare-to-manifest.py) compares an audit report against a manifest to compute detection rate; [split-manifest.py](../scripts/split-manifest.py) splits a large manifest for distribution across parallel groups.

**Manifest integrity gate (MANDATORY before every compare):**
1. Check for corruption: `grep -c '^\s*\d+\|' ISSUE-MANIFEST.md` — if >0, recursively strip ALL layers: `python3 -c "import re; t=open('ISSUE-MANIFEST.md').read(); [t:=re.sub(r'^\s*\d+\|','',t,flags=re.M) for _ in range(5)]; open('ISSUE-MANIFEST.md','w').write(t)"`. `read_file` prepends line-number prefixes that survive `write_file` and compound across sessions; a single-layer strip silently misses deeper layers and the compare script then reports a tiny parsed count with bogus detection.
2. Count parseable entries — manifests use ONE of two formats: numbered (`grep -c '^\d+\. '`) or table (`grep -c '^| '`, excluding header/separator rows). If neither returns >10 entries, read the first 20 lines to identify the format and build the matching grep.
3. Compare against the manifest header's claimed count. Mismatch >5% means the manifest wasn't updated after golden-source expansion — fix the manifest first.
4. Only run the compare script AFTER gates 1-3 pass.

**Compare-script pitfalls.**
- **Argument order:** `compare-to-manifest.py <audit.md> <manifest.md>` — audit FIRST, manifest SECOND. Swapping silently parses the audit as a manifest (~30-35 section-header entries) and reports near-100% detection on that tiny subset. Symptom: "Manifest entries: 33" when you expect thousands.
- **Phrasing sensitivity:** the tool uses n-gram matching against the audit text. Condensed phrasing (e.g. "No DKIM/SPF" instead of "No DKIM signing configured — emails can be spoofed") causes false-negative misses. Prefer verbatim manifest phrasing; don't abbreviate multi-word vulnerability names. If the script reports misses, first expand the finding text and re-run before assuming the detector missed it.

**Parallel subagents miss recently-expanded files.** New files with new bug categories get read but not every rung gets applied; misses cluster in the most recent expansion. Flag new files explicitly in subagent context and instruct extra time. Reduce files-per-subagent when >=3 files are new. After consolidation, grep the audit for each new file — if any has <5 findings, re-audit it directly. Prefer direct parent audit for <=3 newly-expanded files. See [parallel-audit-pattern.md](./parallel-audit-pattern.md) for the full mitigation.
