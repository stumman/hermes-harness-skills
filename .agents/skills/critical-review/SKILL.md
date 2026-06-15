---
name: critical-review
description: >
  Critical code review across correctness, design, security, performance, and
  tests, reporting findings by severity with concrete fixes. Use when asked to
  review code, review a diff or PR, find bugs before shipping, or critique a
  change.
---

# Critical Review

Review is where defects are cheapest to catch. Be the reviewer you'd want: specific, prioritized, and honest. Praise is fine but findings are the point.

## Review against the spec first

Does the change actually satisfy the acceptance criteria and stay inside scope? A correct implementation of the wrong thing still fails review.

## Rubric (walk every dimension)

1. **Correctness** — logic, off-by-ones, null/empty/boundary handling, error paths, race conditions, the cases the happy path ignores.
2. **Design** — does it belong here, match patterns, respect layering and dependency direction? Any new coupling, duplication, or abstraction that earns its keep (or doesn't)?
3. **Readability** — would a teammate understand it cold? Names, function size, nesting, misleading comments.
4. **Security** — untrusted input, authz checks, injection, secrets, unsafe deserialization. Delegate deep analysis to `security-sentinel` if it's hairy.
5. **Performance** — obvious hotspots, N+1s, unbounded growth, needless allocation in hot paths. Delegate deep work to `perf-tuner`.
6. **Tests** — do they exist, test behavior, and cover the edges? Would they fail if the code regressed?

## Reporting

Group findings by severity: **Blocker** (must fix — bug, security, data loss), **Major** (should fix — design/maintainability risk), **Minor/Nit** (optional polish). For each: where it is, why it matters, and a concrete suggested fix. Don't bury a blocker among nits, and don't inflate nits into blockers.

If it's genuinely good, say so briefly and ship it — manufactured findings waste everyone's time.
