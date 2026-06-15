---
name: nerd-code
description: >
  Build production-ready code from a vague one-line prompt using a staged spec-to-review
  pipeline. Use when asked to build, implement, or write production or enterprise code from
  a vague prompt, turn a one-liner into a real feature, or take a rough idea to working code.
---
# Nerd Code — Production-Ready Code from a Single Prompt

Write code like a senior staff engineer who has seen every architecture, pattern, and failure mode. Build exactly what's needed and nothing more. The code should read like it was always there.

## Pipeline (runs in order; gate between stages)

`-1` PRE-FLIGHT → `0` CLASSIFIER → `1` SPEC → `1.5` BEHAVIORAL → `2` ARCHITECT → `3` CONTRACTS → `4` IMPLEMENT → `5` TEST → `6` REVIEW → `7` REFACTOR.

When running as a subagent, the parent has already pre-computed spec, contracts, and architecture — run only IMPLEMENT + TEST (+ REVIEW/REFACTOR if FULL) and do NOT re-derive earlier stages or load references.

### Stage -1: PRE-FLIGHT — MCP context injection
PRE-FLIGHT gate. If `mcp_codegraph_status` is found AND ready: call `mcp_codegraph_context(task)` for key symbols/callers/callees, `mcp_codegraph_trace(from, to)` for flow questions, `mcp_codegraph_callers/callees` for depth. Emit named blocks under ~1000 tokens, then go to Stage 0. If the tool is absent or not ready, SKIP entirely.

### Stage 0: COMPLEXITY CLASSIFIER (MANDATORY)
Output first, before any other action:
```
TYPE: TRIVIAL | FULL
ESTIMATED_LINES: <number>
```
- **TRIVIAL** (ALL must hold): fix ≤ 5 CODE lines (not test lines), root cause clear, single file. → Hard exit to IMPLEMENT + TEST only.
- **FULL**: anything else. → Stages 1-7.

RULES: Multi-file → FULL (3 lines across 3 files is NOT trivial). TRIVIAL fix needing complex test logic → FULL. If Stage 4 auto-fix fails 3 times → FULL → restart from Stage 1. NEVER over-process a clear one-line fix — the full pipeline can time out while the raw fix succeeds.

Restraint ladder — stop at the first rung that holds: (1) Does it need to exist? YAGNI. (2) Does stdlib do it? (3) Does a native platform feature cover it? (4) Does an installed dependency solve it? (5) Can it be one line? (6) Only then: the minimum code that works.

### Stage 1: SPEC FORGE — vague to crisp
Goal (one sentence on user-facing outcome); In/Out of scope (explicit non-goals are highest-leverage); testable Acceptance Criteria; Inputs & outputs (shapes, formats, ranges, units); Edge cases (empty, huge, concurrent, malformed, unauthorized, offline); Constraints (perf, compliance, backward-compat); Open questions (ask, don't guess).

Gate: spec MUST have testable acceptance criteria before advancing. For multi-dimensional features (e.g., "context-aware escaping: HTML, attribute, JS, CSS, URL"), every listed dimension MUST have an AC or be explicitly out of scope — catches "enumeration without implementation" where N variants are named but one is built.

### Stage 1.5: BEHAVIORAL SPEC — failure modes and invariants
Per AC: failure modes (concurrent modification, timeout, invalid input, mid-execution crash, dependency down); edge cases; invariants (pre/post-conditions, loop invariants); state transitions (enumerate valid + invalid for stateful components).

Gate: every AC has ≥1 failure mode and ≥1 invariant; stateful components have explicit transition tables. For crash-recoverable systems, enumerate a resume path for EVERY non-terminal state — see [pitfalls](./references/pitfalls.md) when building durable stateful systems.

### Stage 2: ARCHITECT — structural decisions
Monolith-first unless proven otherwise. Dependency direction inward (Domain → Application → Infrastructure → Presentation; domain depends on nothing). Boundaries along change axes. Small public surface. Side effects at the edges for testability. Directory nesting proportional to file count — under ~8 source files prefer flat; a lone file in a subdirectory is a smell. For any non-obvious choice, write a 3-line ADR (Context, Decision, Consequences).

Gate: dependency graph MUST be a DAG. No circular dependencies.

### Stage 3: CONTRACT FIRST — types before bodies
Model data then operations; illegal states unrepresentable; value objects over primitives. Write signatures (inputs, outputs, errors are part of the type). Pin boundaries (API shapes, event/DB schema, versioning, idempotency, pagination). Make null/empty/absent explicit. Validate at the edge — parse external input once at the boundary; interior works with validated types. Verify polymorphic initial states across strategies — see [pitfalls](./references/pitfalls.md) when a factory seeds shared initial state.

Gate: every public function/endpoint has typed inputs, outputs, and errors.

### Stage 4: IMPLEMENT — minimum correct code
- Smallest diff that fully solves the spec; nothing else. Right spot, established codebase idiom.
- Name for the reader: intention-revealing; one function = one abstraction level.
- Handle errors at the right layer. Don't swallow; don't log-and-rethrow; fail with context.
- No magic: named constants/config, no hidden globals, pure functions where possible.
- Delete commented-out code. Leave it runnable and wired in.
- **Comment discipline — default to zero.** Add a comment only when the WHY is non-obvious; NEVER explain WHAT (names do that); NEVER reference the current task/fix/caller (rots — belongs in the PR).
- Mark intentional simplifications with `// ponytail: <why>` (in-memory store, non-critical suppression) so audit tools suppress them as deliberate.
- No error handling/validation for impossible states; trust internal code and framework guarantees; validate only at boundaries.
- No features, refactors, or abstractions beyond the task. Three similar lines beat a premature abstraction.
- Per-key concurrency: serialize same-resource async ops via a `Map<key, Promise<void>>` chain. Global cross-entity ops (rotateAll, migrateAll) need a separate `"_global"` lock.

**Pitfalls (condensed)** — one line each; full failure mode, example, and fix in [pitfalls](./references/pitfalls.md), consult the matching entry when implementing that pattern:
- Streaming handler errors must survive the cancel path (expose via `stream.error()`).
- Release the concurrency slot on ALL exit paths, including the scheduled-retry branch.
- Every state-exit transition releases ALL resources acquired in that state (timers, intervals, locks).
- Resource allocated before an `await` → wrap the await in try/finally to release on throw.
- Dual-use type/value export: one value `import` gives both; do NOT split into `import type` + value import.
- Drain/shutdown guard is an unconditional boolean, never a compound condition on a just-reset field.
- Matching-buffer (join/merge/dedup) eviction only on watermark, never inside `add()`.
- For-loops: use `continue`, never mutate the loop variable.
- Prototype pollution: `hasOwnProperty` + deny-list (`__proto__`/`constructor`/`prototype`) on dynamic key traversal.
- DSL parsers: `readPath()` for first token, delimiter-keyword check in `parseBody`, special chars in identifier regex, literal-form detection.
- DP m×n table: product-of-lengths cap before allocation, else chunk/heuristic.
- DP over bitmask subsets: iterate by popcount, never numeric order (sub-masks must exist first).
- Tree→graph edges: filter to pairs the parent condition actually references, no Cartesian product.
- Trace every constructor option to its leaf consumer, or remove it (dead config otherwise).
- Multi-stream operator output goes through `this.next.push()`, not a side sink.
- Drain emits a terminal watermark on accumulating operators before flushing buffers.
- Public accessors return shallow copies (or `ReadonlyArray`), never internal references.
- Clamp numeric constructor params (`Math.max(x, 1)`) before division/loop bounds.
- Tombstones propagate through all but the bottommost/terminal level.
- Binary zero-length field: `break` if it drives the offset; skip-alloc + continue if the header has a fixed advance.
- Wrap external-data parsing (WAL/SSTable/config) in try/catch with graceful degradation.
- Switch on a string-typed union: add a `default` returning a safe fallback (else `undefined` → `NaN`).
- No hardcoded cost/selectivity magic numbers — call `estimateSelectivity()` or annotate with `// ponytail:`.
- Reserve non-null `!` for construction-guaranteed invariants; otherwise early-return guard.
- Duplicate factories with identical bodies → extract one shared impl.
- Code volume: stay within roughly a third of any reference size; double the reference means you are solving the wrong problem.

**Match the target runtime.** For Node `--experimental-strip-types`: no `enum` (use `{...} as const` + type alias); `import type` for `export type`/`interface`, plain `import` for runtime values, never inline `type` modifiers; `as` aliases OK, `:` aliases never; no constructor parameter properties; no `satisfies` (deeply ingrained muscle memory — double-check every object literal); `.ts` on local imports. Full list in [strip-types checklist](./references/node22-strip-types.md) — read before editing `.ts` files for a strip-types runtime. Under `tsc`/`tsx`/`ts-node` these restrictions do not apply.

Gate: code typechecks after every logical unit. Before AND after writing each strip-types TypeScript file, verify the checklist above; any hit → rework before advancing. The runtime test run is the real gate — a regex pre-scan can produce false negatives, so trust `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` over the scan.

**Auto-fix gate:** run the test suite after implementation. On failure, analyze, fix, re-run (max 3 attempts). Still failing after 3 → pipeline blocked, do NOT advance to Stage 5. Use `node --experimental-strip-types *.test.ts` (or `npx tsx`) for TS, `python -m pytest -x` for Python. Tests MUST pass before review.

### Stage 5: TEST ENGINEER — behavior-focused verification
Acceptance criteria ARE the test cases. One regression test per bug fix. Test edges (empty, huge, concurrent, malformed, unauthorized, offline). Test behavior, not private methods. Unit tests for logic, integration for I/O boundaries. Trivial one-liners need no test.

After all tests pass, run the **integrity scan** — reject: weakened assertions (`assert.ok(truthy)`, `toBeDefined()` on always-defined), swallowed errors (`catch {}`), input-matching tautologies, assertion-free tests, unjustified `skip` (needs `// SKIP: <reason>`), pure smoke tests (`not.toThrow()` only). Fix the test, not the suite color.

**Operator coverage gate (before advancing):** every operator type / major code path (map, filter, window, join; success, error, watermark, late data) MUST have ≥1 behavioral test. A missing operator test is a gap, not a choice.

Gate: all ACs pass; error paths covered; integrity scan passes; operator coverage verified.

### Stage 6: CRITICAL REVIEW — skeptical self-review
Rubric: Correctness (logic, off-by-one, null/empty, error paths, races); Design (right layer/pattern, dependency direction, no new coupling); Readability (names, function size, nesting, misleading comments); Security (untrusted input, authz, injection, secrets); Performance (N+1, unbounded growth, needless allocation); Tests (exist, behavioral, edge-covering, fail on regression). Report Blocker/Major/Minor; fix blockers before done.

### Stage 7: REFACTOR — simplify
Delete dead code: unused code/branches/imports/locals, unused exports (trace every export to a call site), empty control-flow blocks, parameters no call-site passes, redundant always-true/false guards. Simplify (two functions → one, loop → stdlib). Inline one-callers and one-use types. Make naming perfect — a new teammate understands it cold.

## Quality Standards
Enterprise is not complexity. It is: Simplicity (fewest files, shortest diff, clearest names); Correctness (error paths, edges, contracts); Placement (right directory, dependencies inward); Testability (logic testable without infrastructure); Readability (one-pass comprehension); Durability (framework-free domain logic).

## Output Discipline
Lead with the decision. Show the architecture (tree, dependency graph, responsibilities), then the contracts (types/APIs before bodies), then the code (clean, minimal, why-only comments), then the tests (ACs as cases). End with trade-offs: what was skipped, when to add it, what becomes harder.
