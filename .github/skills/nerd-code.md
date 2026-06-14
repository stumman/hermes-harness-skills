---
name: nerd-code
version: 1.5.0
description: >
  Write production-grade code from a one-line prompt. Runs the full pipeline:
  restraint ladder → spec-forge → behavioral-spec → architect → contract-first → implement →
  test-engineer → critical-review → refactor. v1.5.0: Stage 0 is now COMPLEXITY CLASSIFIER
  with TRIVIAL/MEDIUM/COMPLEX routing + UNBYPASSABLE hard exit rules (SWE-bench proven:
  raw model 242s 1-line fix vs full pipeline 600s timeout). v1.4.0: Stage 0 HARD EXIT.
  v1.3.0: SUBAGENT MODE.
---
---
# Nerd Code — Production-Grade Code from a Single Prompt

You write code like a senior staff engineer who has seen every architecture, every pattern, every failure mode. You build exactly what's needed and nothing more. The code reads like it was always there.

## SUBAGENT MODE — TOKEN-OPTIMIZED (use when running as a subagent)

When you are a subagent spawned by a parent conductor or implementation lens, use THIS condensed pipeline (~500 tokens). Do NOT load references — the parent has already pre-computed spec, contracts, and architecture.

**Quick Pipeline (7 stages, condensed):**
0. **COMPLEXITY CLASSIFIER (MANDATORY):** Output `COMPLEXITY: [TRIVIAL|MEDIUM|COMPLEX]` before anything else. TRIVIAL (≤5 lines, clear root cause) → HARD EXIT. Skip to Stage 4+5 only. SWE-bench proven: full pipeline on 1-line fix = 600s timeout vs raw model 242s. MEDIUM (5-30 lines) → Stages 1,3,4,5,6. COMPLEX → Full 1-7. Rule: if TRIVIAL and ran more than Stage 4+5 = VIOLATION.
1. **SPEC:** Goal, in/out of scope, testable ACs, input/output shapes, edge cases, open questions. For multi-dimensional features (e.g., "N contexts"), verify each dimension has an AC or explicit scope decision.
2. **BEHAVIORAL:** (COMPLEX only) Per AC: failure modes, invariants. Stateful: transition table.
3. **ARCHITECT:** Monolith-first. Deps inward. DAG. ADR for non-obvious choices.
4. **CONTRACTS:** Types before bodies. Illegal states unrepresentable. Validate at edge.
5. **IMPLEMENT:** Smallest diff. Right idiom. No magic. Delete dead code. `// ponytail:` comments. Match target runtime.
6. **TEST:** ACs as test cases. Edges. Test integrity scan. Operator coverage.
7. **REVIEW + REFACTOR:** (MEDIUM+ only) Blocker/Major/Minor. Delete dead exports. Simplify. Inline one-callers. Perfect names.

**Quality:** simplicity, correctness, placement, testability, readability, durability. Framework-free domain logic.

**Pitfalls (condensed):** streaming errors survive cancel path. Concurrency slot release on ALL exit paths. State transition resource cleanup. Async resource cleanup: allocate before await → try/finally release. Dual-use type/value import. Drain guard unconditional. Matching-buffer premature eviction. For-loop mutation skips iterations. Global cross-entity operation serialization. Prototype pollution via key traversal (add hasOwnProperty guard). DSL tag ambiguity: use readPath() for first token, check delim keywords in parseBody, include @/$ in identifier regex, detect numeric literal paths. DP table memory: add product-of-lengths safety cap before allocating O(m×n) table; fall back to chunked/heuristic when exceeded. Options propagation: trace every constructor option to its leaf consumer — options that don't reach a downstream constructor are dead config. Multi-stream operator output: when an operator receives input from multiple streams (join, union, merge), wire its output through the regular operator chain via next.push(), not a side-channel sink that's never connected. Drain finalization: on stop/drain, operators that accumulate state (windows, joins, aggregations) must emit final results — trigger terminal watermarks or flush calls before clearing buffers. Mutable internal state exposure: public accessors that return direct references to mutable internal arrays/collections enable silent invariant corruption — return shallow copies ([...arr], new Map(m), ReadonlyArray type). Numeric constructor division: when a constructor divides by a user-provided numeric parameter (e.g., `this.ratio = bitSize / expectedEntries`), clamp with `Math.max(param, 1)` — zero produces Infinity → infinite loops/hangs in dependent loops (hash count, bucket count, capacity). Compaction merge tombstone propagation: when merging entries from multiple sources with delete markers (tombstones), propagate tombstones through all but the terminal/bottommost level — dropping them unconditionally causes key resurrection when lower levels hold surviving data for the same key. Binary format zero-length guard: zero-length fields in binary formats (entryLen=0, count=0) can bypass bounds checks (`offset + 0` never exceeds total length). Distinguish two cases: (A) field controls loop offset advance directly (`offset += fieldLen`) — zero = infinite loop, break. (B) field controls only allocation size while offset advances by a fixed constant (`offset += HEADER_SIZE + fieldLen`) — zero is valid, skip allocation/read but continue. Only break in case A. Add guard: for case A use `if (fieldLen === 0 || offset + fieldLen > len) break`; for case B use `if (offset + HEADER_SIZE + fieldLen > len) break` (no zero-break needed). External data parsing without try/catch: constructors and recovery paths that parse untrusted external data (WAL files, binary formats, serialized state) without try/catch crash the process on corrupt input — wrap parsing in try/catch with graceful degradation (skip corrupt entry, truncate tail, return partial state).

## FULL PIPELINE (use for parent-agent implementation, NOT subagents)

## The Pipeline (runs in order, gates between stages)

### Stage 0: COMPLEXITY CLASSIFIER (MANDATORY — HARD EXIT GATE)

**This is the most important stage in the entire pipeline. You MUST complete it before ANY other action. It is not optional. It is not skippable. It determines whether the pipeline runs at all.**

**Step 1: OUTPUT THE CLASSIFICATION (mandatory format)**

Before any plan, any code, any spec — output EXACTLY this:

```
COMPLEXITY: [TRIVIAL | MEDIUM | COMPLEX]
RATIONALE: <one sentence>
ESTIMATED LINES: <number>
```

**Step 2: ROUTE BASED ON CLASSIFICATION**

| Classification | Criteria | Pipeline |
|---|---|---|
| **TRIVIAL** | ≤5 lines, clear root cause from issue, fix is a 1-liner or typo | **HARD EXIT.** Skip to Stage 4+5 only. Write fix. Write test. Done. |
| **MEDIUM** | 5-30 lines, needs function/class design, single file | Stages 1, 3, 4, 5, 6 (skip Behavioral Spec and Refactor) |
| **COMPLEX** | >30 lines, multi-file, architectural changes, new module | Full Stages 1-7 |

**Step 3: THE UNBYPASSABLE RULES**

1. If you classified **TRIVIAL** and ran ANY stage other than 4+5 → **YOU VIOLATED THIS SKILL.** Undo everything. Do the minimum.
2. If you classified **TRIVIAL** and wrote more than 5 lines → **YOU VIOLATED THIS SKILL.** Undo. The fix is 1-5 lines.
3. If the issue description literally tells you the root cause → it's **TRIVIAL.** Just fix it.
4. The SWE-bench astropy__astropy-12907 test PROVED this: raw model (no skills) = 242s, correct fix. nerd-code with full pipeline = 600s timeout. On a 1-character fix. The pipeline MUST NOT run on trivial tasks.

**Step 4: CLASSIFICATION EXAMPLES**

```
TRIVIAL: "separability_matrix returns wrong values for nested models — the cright[...] = 1 should be cright[...] = right"
→ 1 line. Hard exit. Skip to Stage 4+5.

MEDIUM: "Add rate limiting middleware for Express with configurable window"
→ ~20 lines. Stages 1,3,4,5,6.

COMPLEX: "Build a distributed saga orchestrator with compensation transactions"
→ 200+ lines. Full Stages 1-7.
```

**If you're unsure, classify UP (MEDIUM instead of TRIVIAL, COMPLEX instead of MEDIUM). But if the issue describes a clear root cause with a specific line/function → TRIVIAL.**

Original restraint rules still apply — stop at the first rung that holds:
1. **Does this need to exist at all?** (YAGNI)
2. **Does stdlib already do it?** Use it.
3. **Does a native platform feature cover it?** Use it.
4. **Does an already-installed dependency solve it?** Use it.
5. **Can it be one line?** One line.
6. **Only then:** the minimum code that works.

### Stage 1: SPEC FORGE → from vague to crisp
Turn the user's prompt into a tight spec:
- **Goal:** one sentence on the user-facing outcome
- **In scope / Out of scope:** explicit non-goals are the highest-leverage part
- **Acceptance criteria:** concrete, testable, checkable
- **Inputs & outputs:** data shapes, formats, ranges, units
- **Edge cases:** empty, huge, concurrent, malformed, unauthorized, offline
- **Constraints:** perf budgets, compliance, backward-compat
- **Open questions:** anything you'd otherwise guess — ask these instead

Gate: spec must have testable acceptance criteria before advancing.

**Gate — spec dimension coverage:** Requirements often list multi-dimensional features (e.g., "context-aware escaping: HTML, attribute, JS, CSS, URL"). For each feature dimension listed in the requirement, verify there is at least one corresponding acceptance criterion or an explicit decision that the dimension is out of scope. A feature with 5 listed dimensions but only 1 AC means 4 dimensions are silently dropped. This gate catches spec interpretation gaps before they reach implementation. It also catches "enumeration without implementation" — where a requirement names N variants/strategies/modes but the code only implements one.

### Stage 1.5: BEHAVIORAL SPEC — failure modes and invariants
For every acceptance criterion, identify:
- **Failure modes:** what can go wrong (concurrent modification, timeout, invalid input, crash mid-execution, external service unavailable)
- **Edge cases:** empty, boundary values, maximum sizing, ordering ambiguity
- **Invariants:** what must always be true (pre-conditions, post-conditions, loop invariants)
- **State transitions:** for stateful components, enumerate valid transitions and invalid ones explicitly

Gate: every acceptance criterion has at least one failure mode and one invariant documented. Stateful components have explicit transition tables (valid + invalid).

**Pitfall — crash recovery resume paths:** For durable stateful systems that support crash recovery, enumerate a resume path for EVERY non-terminal state — not just the primary active/running state. Include "crash mid-state-X" as a failure mode for each state. Example: a saga with states `pending → running → compensating → compensated` needs resume paths for `running` (pick up forward execution) AND `compensating` (jump directly to compensation). Missing the `compensating` resume path means a crash mid-compensation leaves the saga stuck in an invalid transition.

### Stage 2: ARCHITECT → structural decisions
Choose the lightest architecture that holds:
- **Monolith-first unless proven otherwise.** Microservices are a response to organizational scale, not a starting point.
- **Dependency direction inward.** Domain → Application → Infrastructure → Presentation. Domain depends on nothing.
- **Boundaries along change axes.** Things that change together belong together.
- **Small public surface.** Expose intentful interfaces; hide internals.
- **Design for testability.** Side effects at the edges.
- **Directory nesting proportional to file count.** Under ~8 source files, a flat directory is cleaner than subdirectories with 1-2 files each. Nest only when a module outgrows its parent. A lone file in a subdirectory is a smell.

For any non-obvious choice, produce a 3-line ADR: Context, Decision, Consequences.

Gate: dependency graph must be a DAG. No circular dependencies.

### Stage 3: CONTRACT FIRST → types before bodies
- **Model the data, then the operations.** Illegal states unrepresentable. Value objects over primitives.
- **Write the signatures.** Inputs, outputs, errors as part of the type. A function's signature tells the truth about failure.
- **Pin the boundaries.** API shapes, event schemas, DB schema, versioning, idempotency, pagination.
- **Null/empty/absent explicitly.** Most bugs live in the difference.
- **Validate at the edge.** Parse external input once at the boundary; interior works with validated types.
- **Verify polymorphic initial states.** When a factory produces initial state shared by multiple strategy/interpreter implementations, check that each implementation's semantics are satisfied by the same initial values. Token bucket starts with `tokens=burst`; sliding window starts with `tokens=0`. If they disagree, the factory must be strategy-aware or each strategy must handle its own defaults.

Gate: every public function/endpoint has typed inputs, outputs, and errors.

### Stage 4: IMPLEMENT → minimum correct code
- **Smallest diff that fully solves the spec.** Nothing else.
- **Right spot, established pattern.** Follow the codebase idiom.
- **Name for the reader.** Intention-revealing; one function, one abstraction level.
- **Handle errors at the right layer.** Don't swallow. Don't log-and-rethrow. Fail with context.
  - **Pitfall — streaming handler errors silently lost:** When implementing streaming patterns (server-stream, bidi-stream), handler errors caught via `.catch(() => writer.cancel())` discard the error. The caller gets `null` from `read()` with no indication of WHY the stream ended. Fix: store the error on the writer (e.g., `writer._error = err`) and expose it via `stream.error()` or reject on the next `read()`. Error context must survive the cancel path so the caller can differentiate "stream completed normally" from "stream failed with INTERNAL error."
  - **Pitfall — concurrency slot leak on async state transitions:** When a job/request transitions from an active state (RUNNING) to a scheduled deferred state (RETRYING via setTimeout, delayed re-enqueue, backoff timer), the concurrency slot (worker count, semaphore permit, active count) must be released BEFORE the timer is set — not after the timer fires. The slot was acquired at dequeue/dispatch; failing to release it on ALL exit paths (success, permanent failure, AND scheduled retry) keeps the worker count inflated and prevents other jobs from running. Symptoms: graceful shutdown hangs waiting for `activeCount → 0`, throughput drops because slots are "occupied" by jobs that aren't executing, and scheduled timers survive shutdown. Fix: call the slot-release function in every branch of the failure handler (including the retry branch), AND track all scheduled timers in a collection that gets cancelled on shutdown to prevent dangling callbacks.
  - **Pitfall — state transition resource cleanup (generalization of slot leak):** Every transition OUT of a state must release ALL resources (timers, intervals, subscriptions, locks, slots) acquired while IN that state. This is not just about concurrency slots — it applies to heartbeat intervals, watchdog timers, event listeners, transport subscriptions, and any other resource scoped to a particular state. Classic failure: a LEADER→FOLLOWER transition clears the election timer but forgets to clear the heartbeat interval — the ex-leader keeps broadcasting heartbeats at a stale term, causing followers to oscillate between two `leaderId` values (flapping). Another: a CANDIDATE→FOLLOWER transition that clears the election timer but leaves a pending OK-response timeout running. Check EVERY transition for orphaned resources — the failure mode is "phantom" behavior from a previous state destabilizing the current state. Fix: for each state, enumerate every resource acquired on entry; verify that every exit transition (including error transitions and term-stepdown transitions) releases every resource. Track interval handles alongside timeout handles — `clearInterval` is the counterpart to `clearTimeout` and must not be forgotten.
  - **Pitfall — async method resource cleanup on exception paths:** When an async method allocates a resource (timer, interval, file handle, listener, lock) BEFORE an `await` that might throw, the resource must be cleaned up in a try/finally — not just on the normal return path. Classic failure: `start()` calls `this.startWatermarkTimer()` (setInterval), then `await this.run()`. If `run()` throws (source iterator failure, validation error), the timer leaks — `clearWatermarkTimer()` is only called in `doDrain()` which never executes. The callback keeps firing even though the pipeline is dead. Fix: allocate resource, then immediately wrap the await in try/finally: `try { await this.run(); } finally { this.clearWatermarkTimer(); }`. This applies to any async method where resource allocation precedes an await: `const handle = setInterval(...); try { await work(); } finally { clearInterval(handle); }`. The pattern generalizes beyond timers: file handles opened before await, locks acquired before await, subscriptions created before await — all need try/finally cleanup.
  - **Pitfall — dual-use type/value import split:** When a module exports both a runtime const and a same-named type (`export const ErrorCode = { ... } as const; export type ErrorCode = ...`), you need both the value (for `ErrorCode.PROTOCOL_ERROR`) and the type annotation (for `code: ErrorCode`). A single value import `import { ErrorCode } from './types.ts'` provides BOTH — the value at runtime, and the type is stripped from annotations. Do NOT split into `import type { ErrorCode } from ...` + a separate value import — the type-only import adds nothing and the split creates confusion. This caused the #1 recurring strip-types bug: using `ErrorCode` as a value after importing it with `import type`.
  - **Pitfall — drain/shutdown guard that depends on just-reset state:** When implementing graceful drain or shutdown, the guard that prevents new work from being picked up must be an unconditional state check (`if (this.draining) return`), not a compound condition that depends on internal fields the completion path just reset. Example: `if (this.draining && this.currentMessage) return` — reads as "if draining but still have a current message, finish it" — but `this.currentMessage` is ALWAYS null at that call site because `finishDelivery()` sets it to null immediately before re-entering the delivery loop. The guard silently degrades and new messages are picked up during drain. This pattern recurs whenever a completion/reset path feeds back into the main loop with a guard that checks the just-reset field. Fix: make the drain guard unconditional — one boolean flag, no compound conditions. If "finish current work" semantics are needed, handle them separately by checking the active/delivering flag before the drain check, not in the same condition.
  - **Pitfall — matching-buffer premature eviction (join, merge, dedup):** In stateful matching buffers (stream-stream join, event merge by key, deduplication windows), entries should ONLY be evicted on time-based watermark expiration — never during individual `add()` calls based on timestamp distance to a single new event. Example: a join buffer with left=[L1(ts=200)] and right=[R1(ts=100)], windowMs=50. When `add(L1)` processes, R1's ts=100 is 100ms from L1's ts=200 — exceeding windowMs — so R1 gets evicted. But a future out-of-order event L2(ts=130) could match R1 (|130−100|=30 ≤ 50). The premature eviction loses the match. Fix: in `add()`, only match and append. Eviction goes exclusively in `onWatermark()` via cutoff-based filtering (`ts >= wm - windowMs`). The `add()` path must never reduce the matching pool.
  - **Pitfall — for-loop variable mutation skips iterations:** Mutating a `for` loop's increment variable inside the loop body causes iteration skip. Example: `for (let wStart = earliestStart; wStart <= event.timestamp; wStart += slide) { if (wStart < 0) wStart = 0; ... }` — setting `wStart = 0` overwrites the loop variable, and the next `wStart += slide` jumps from 0 to `slide` instead of from the original negative value. Windows/iterations between the original value and 0 are silently skipped. Fix: use `continue` instead of mutation (`if (wStart < 0) continue`), or guard the loop body with the condition without mutating the variable.
  - **Pitfall — prototype pollution via key traversal:** When resolving dot-paths or dynamic keys against user-provided data objects (e.g., `resolvePath(obj, ["user", "name"])`), traversing without `hasOwnProperty` check walks the prototype chain. Single-segment paths like `["__proto__"]` or `["constructor"]` leak internal objects. Multi-segment paths like `["constructor", "constructor"]` permit arbitrary code execution via `Function`. Fix: add a deny-list (`['__proto__', 'constructor', 'prototype']`) and/or `Object.prototype.hasOwnProperty.call(current, key)` guard at each traversal step. This applies to any function that walks object keys dynamically: template engines, query builders, config resolvers, JSON-path evaluators.
  - **Pitfall — DSL tag ambiguity (expression vs. helper, delimiter vs. expression, special chars in identifiers):** When building recursive-descent parsers for tag-based DSLs (template engines, query languages, config DSLs), four ambiguity patterns recur: (1) single-identifier expressions vs. multi-token helper calls — use `readPath()` for the first token, then check for continuation tokens; (2) block delimiters like `{{else}}` inside `parseBody` — check for delimiter keywords before falling through to generic expression parsing; (3) special characters in identifiers (e.g., `@index`) — include them in the `readWord()` regex; (4) numeric/string literal arguments to helpers — detect literal-form paths in the evaluator. Full patterns and fixes at `references/dsl-parser-pitfalls.md`.
  - **Pitfall — DP algorithm table memory:** Dynamic programming algorithms (LCS, edit distance, sequence alignment, knapsack variants) allocate an O(m×n) table. Without a product-of-lengths safety cap, even moderate inputs (10K×10K = 100M cells) cause OOM. Classic failure: a diff engine using character-level LCS on two 20K-character inputs allocates a 400M-entry table and crashes. Fix: add a product-of-lengths safety cap (e.g., `a.length * b.length > 250_000`) and fall back to a chunked, heuristic, or approximate approach when exceeded. The cap should be sized to keep the table under ~1–2 MB. This applies to ANY algorithm that builds a full m×n matrix — validate the product before allocation, not just individual lengths.
  - **Pitfall — constructor options not propagated to downstream constructors:** When a class accepts configuration options (e.g., `cbThreshold`, `cbCooldownMs`, `chunkSize`, `timeout`) but never passes them to the constructors of its internal dependencies, those dependencies silently use hardcoded defaults instead of the user's configured values. The system appears configurable but isn't. Classic failure: `LoadBalancer` accepts `cbThreshold`/`cbCooldownMs` options but creates `new CircuitBreaker(DEFAULTS.cbThreshold, DEFAULTS.cbCooldownMs)` — user's configuration is silently ignored. Another: a diff engine accepts `chunkSize` but creates `new BinaryDiffer()` without passing it through. Fix: after writing every constructor that delegates to other constructors, trace every option field to verify it reaches the leaf constructor. If an option has no leaf consumer, either wire it through or remove it from the interface. This is a subclass of dead-config — options that exist in the type system but have no runtime effect.
  - **Pitfall — multi-stream operator output disconnected from chain:** When an operator receives input from multiple streams (join, union, merge, cross-stream aggregator), its output must be wired through the regular operator chain — not a side-channel sink that's never connected. Classic failure: a `JoinOp` is added to the pipeline chain via `appendOp()` (correctly receiving left-stream events), and a separate `SinkOp` routes right-stream events into it. But the join's matched output pairs are sent to a `setSink()` method that's never called by the pipeline — all join results are silently dropped. The join appears to work (no errors, buffers populated) but produces zero output. Fix: implement `push()` on the multi-stream operator to route through `this.next.push(...)`, not a separate sink. The operator is a regular chain node — its output goes to `this.next`, same as MapOp, FilterOp, etc. Any operator that receives cross-stream input must still emit through the chain, not a side channel.
  - **Pitfall — drain/completion doesn't finalize accumulated state:** When stopping or draining a pipeline, operators that accumulate state (windows, joins, aggregations, buffers) must emit their final results. Classic failure: `doDrain()` flushes event buffers and calls `flush()` on operators, but `flush()` only propagates to the next operator — it doesn't trigger window emission or join match emission. The stateful operators hold accumulated data that's never released to the sink. Symptoms: all tests pass because the core logic is correct, but in production the pipeline stops with results still trapped in un-flushed windows. Fix: in the drain/stop path, emit a terminal watermark (e.g., `maxSeenTimestamp + maxWindowSize + 1`) on every accumulating operator before flushing buffers. This triggers window computation, join eviction, and any other stateful finalization. After the terminal watermark, flush remaining event buffers. The pattern: any operator whose `push()` stores rather than forwards must have a finalization step that's explicitly called during shutdown.
  - **Pitfall — mutable internal state exposed through public accessors:** When a public method returns a direct reference to a mutable internal data structure (array, Map, Set, object), callers can silently corrupt internal state. Classic failure: `getNeighbors(id)` returns `this.adj.get(id)` — the caller pushes a new edge onto the returned array, and the graph's internal adjacency list is mutated with no error, no audit trail, and no detection. This applies to any class that manages internal collections: caches returning their internal Map, stores returning their internal array, queues returning their internal buffer. The corruption can be invisible — all tests pass because no test mutates the returned reference, but real callers do. Fix: return a defensive copy — `return [...(this.adj.get(id) ?? [])]` for arrays, `new Map(this.#cache)` for maps, `new Set(this.#items)` for sets, `{...this.#config}` for objects. Alternatively, type the return as `ReadonlyArray<T>` to make mutation a compile error (works in TypeScript; no runtime cost). The choice (`ReadonlyArray` vs copy) depends on whether callers need a snapshot or can tolerate seeing subsequent mutations — if they need a snapshot, copy; if they only need to read, `ReadonlyArray` is cheaper.
  - **Pitfall — numeric constructor parameters feeding division without guard:** When a public constructor performs division or modulo on user-provided numeric parameters, unguarded zero or negative values produce `Infinity`, `NaN`, or nonsensical internal state. Classic failure: `BloomFilter(expectedEntries=0)` computes `this.#hashCount = Math.round((bitSize / 0) * Math.LN2) = Infinity` — the `for (let i = 0; i < this.#hashCount; i++)` loop in `add()`/`has()` becomes infinite and hangs the process. Fix: clamp with `Math.max(param, 1)` or `Math.max(param, 0)` before arithmetic that feeds into loop bounds, array sizes, or buffer dimensions. This applies to any data structure whose constructor derives internal dimensions from user-provided counts: bloom filters (bit size, hash count), hash tables (bucket count), ring buffers (capacity), rate limiters (window size), skip lists (max level). The fix is always the same pattern: `const safe = Math.max(raw, MINIMUM)` before the division. Combine with Stage 3's "validate at the edge" — constructors are a trust boundary for public APIs.
  - **Pitfall — compaction/merge tombstone propagation:** When merging entries from multiple sorted sources with delete markers (tombstones), tombstones must propagate through compaction into the merged output for ALL levels except the bottommost/terminal level. Classic failure: a k-way merge function drops tombstones unconditionally (`if (!entry.tombstone) result.push(entry)`) — the deleted key is absent from the compacted level, so reads fall through to lower levels where the key's old data still survives, causing key resurrection. This applies to any merge-based system with delete markers: LSM tree compaction, log compaction in event stores, merge-on-read in MVCC stores, sorted-string-table merges. Fix: retain tombstones through all but the bottommost level — check if the current compaction target is the terminal level before dropping: `const isBottommost = sources.every(s => s.level === maxLevel); if (!entry.tombstone || !isBottommost) result.push(entry)`. Tombstones in the terminal level are safe to drop because no lower level exists to resurrect from.
  - **Pitfall — binary format zero-length field guard:** When parsing binary formats with length-prefixed fields (WAL entries, network protocols, file headers), a zero-length field can bypass bounds checks that use addition. Two distinct cases: **(A) Field controls loop offset directly** (`offset += fieldLen` alone, no fixed header) — zero = stuck at same position → infinite loop. Classic failure: a WAL recovery loop reads `entryLen = buf.readUInt32LE(offset)`, advances `offset += 4`, then guards with `if (offset + entryLen > data.length) break`. If `entryLen === 0`, the guard passes (offset + 0 never exceeds data.length) and `offset = entryStart + 0` doesn't advance → infinite loop. Fix: `if (entryLen === 0 || offset + entryLen > data.length) break`. **(B) Field controls only allocation size; offset has a fixed advance** (`offset += HEADER_SIZE + fieldLen` where HEADER_SIZE is constant) — zero is valid, offset still advances by HEADER_SIZE. Fix: skip allocation/read when zero, but do NOT break: `if (fieldLen === 0) { payload = Buffer.alloc(0); } else { ... read ... }`. The guard should prevent zero-size allocation (allocUnsafe(0) is safe but wasteful), not abort the entire scan. This applies to any binary format with length-prefixed fields: WAL entries, SSTable blocks, network frame headers, serialized message formats. Every length-prefixed field that feeds into a loop or bounds check needs a zero guard — but the guard action depends on whether the field participates in the offset advance formula.
  - **Pitfall — external data parsing without try/catch in constructors/recovery:** When constructors or recovery/startup paths parse untrusted external data (WAL files, binary SSTables, serialized state, config files), parsing without try/catch can crash the constructor. Classic failure: `recover()` reads a WAL file with `fs.readFileSync`, then parses entries with `readUInt8`/`readUInt16LE`/`toString` — a truncated or corrupt entry where internal fields (keyLen, valueLen) point outside the buffer throws an uncaught `RangeError`, crashing the `LsmTree` constructor and rendering the database permanently inaccessible until the WAL is manually removed. Fix: wrap each entry's parsing in try/catch; on error, break the loop and truncate the corrupt tail. Mark the catch with `// ponytail: corrupt entry — skip and truncate`. This applies to any system that reads external data at startup: WAL recovery, journal replay, SSTable scanning on boot, config deserialization, state hydration. The pattern: parse external data inside try/catch, not in bare constructor body.
- **No magic.** Named constants/config. No hidden globals. Pure functions where possible.
- **Delete commented-out code.** Leave it runnable and wired in.
- **Comment discipline — default to zero comments.** Only add comments when the WHY is non-obvious. Never explain WHAT the code does — well-named identifiers already do that. Never reference the current task, fix, or specific callers — those belong in the PR description and rot. A comment is a failure to express intent in code; add one only when the code cannot be made clearer.
- **Mark intentional simplifications with `// ponytail:` comments.** In-memory stores instead of DB, branded types without runtime cost, non-critical error suppression — each gets a one-line `// ponytail: <why this is intentional>`. These comments feed downstream audit tools so they correctly suppress false positives instead of flagging deliberate tradeoffs as issues.
- **Don't add error handling, fallbacks, or validation for scenarios that can't happen.** Trust internal code and framework guarantees. Only validate at system boundaries. Guard against impossible states and you'll drown in dead branches.
- **Don't add features, refactor, or introduce abstractions beyond what the task requires.** A bug fix doesn't need surrounding cleanup. Three similar lines is better than a premature abstraction. No half-finished implementations — ship what's needed, nothing more.
- **Per-key concurrency serialization — see `references/patterns/per-key-serialization.md`.** Use Promise-chain serialization (`Map<key, Promise<void>>`) when multiple async operations target the same resource and must not interleave. Proven zero-dependency pattern across 4+ iterations.
  - **Pitfall — global cross-entity operations without serialization:** Per-key locking (`Map<id, Promise<void>>`) serializes operations targeting the SAME entity, but global operations that iterate ALL entities (like `rotateAll`, `migrateAll`, `reindexAll`, `rotateMasterKey`) have no protection against concurrent global calls. Two concurrent `rotateMasterKey()` calls both add new key versions to a shared map, both iterate the entity store, and the interleaving can corrupt state — one rotation removes a key version the other still needs for decryption. Fix: add a dedicated global-operation lock using the same Promise-chain pattern with a constant key (e.g., `"_global"`). Check every operation that reads or writes shared cross-entity state — if it's not serialized by a per-entity lock, it needs a global lock. This is the generalization of per-key locking to the cross-entity level.
- **Match the target runtime.** If generating TypeScript for Node.js with `--experimental-strip-types`, avoid ALL unsupported syntax:
  - No `enum` — use `{ ... } as const` + type alias instead (`export const Status = { ... } as const; export type Status = (typeof Status)[keyof typeof Status]`).
  - Use `import type { X } from '...'` for types declared with `export type` or `export interface` — these are stripped at export time by Node.js, so ONLY `import type` can import them. Use plain `import { Y } from '...'` for runtime values (functions, classes, const objects). Never use inline `type` modifiers (`import { type X, Y } from ...`).
  - Import aliases (`import { X as Y }`) using `as` ARE supported — use them freely for namespace shortening (e.g., `import { ErrorCode as EC }`). The `:` syntax (`import { X: Y }`) is invalid JS/TS in all contexts and never works.
  - No parameter properties in constructors (`public readonly x` → separate field + assignment).
  - No `satisfies` operator — use explicit type annotation on the variable instead (`const x: Foo = { ... };`, not `const x = { ... } satisfies Foo`). **`satisfies` is deeply ingrained TS muscle memory. Double-check every object literal.**
  - **Pitfall — parameter properties in constructors (ALL classes):** `constructor(public/private/readonly x: T)` is the single most recurring parameter-property violation across all iterations. It happens on EVERY class type — utility classes (Lexer, Parser, Scanner, Tokenizer), error subclasses, service classes, etc. Error subclasses are especially prone because `public readonly` on constructor params is the idiomatic TS pattern for immutable error fields. Every time you write ANY class, mentally rewrite the constructor: declare fields separately, assign in body. Do not trust muscle memory here — it will produce `constructor(public readonly ...)` every time. Run `node --experimental-strip-types` on the file to catch these; regex-based pre-scans with `search_files` can silently miss them (false negatives — see gate caution below).
  - No inline `type` modifiers in value import statements (`import { type Foo, Bar } from ...` → split into `import type { Foo } from ...` + `import { Bar } from ...`).
  - Use explicit `.ts` extensions on all local imports (`from './foo.ts'`, not `from './foo'`).
  - If the runtime is `tsc`-compiled or `tsx`/`ts-node`, these restrictions do not apply. Full checklist at `references/node22-strip-types.md`.

Gate: code compiles/typechecks after every logical unit. **Before writing any TypeScript file, mentally pre-audit: no `enum` (use const objects), split type-only imports into `import type { X }` statements, runtime imports into `import { Y }`, no `satisfies`, no parameter properties, no inline `type` in value imports, `.ts` on local imports.** Then after writing, **scan every file for runtime-compatibility violations:** `enum` keyword; `import type` mixed with value imports (must be separate statements); parameter properties in constructors (`constructor(public/private x)`) — especially in `extends Error` classes where `public readonly` is idiomatic TS; the `satisfies` operator; inline `type` modifiers in value imports (`import { type X }`); import type/value split violations (using plain `import { X }` for `export type`/`export interface` — must be `import type { X }`); and extensionless local imports (must end in `.ts`). Any hit → rework before advancing. This scan is non-negotiable — the "Match the target runtime" rule above must be verified, not assumed.

**Caution — regex pre-scan may produce false negatives:** The `search_files`-based regex scan can silently miss violations (observed with `constructor\(private|public|...` patterns returning 0 matches despite violations being present). The real enforcement gate is the actual `node --experimental-strip-types` test run in the Auto-fix gate below. Treat the regex pre-scan as a best-effort lint, not a guarantee. If the test run fails with `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`, trust the runtime error over the regex scan.

**Auto-fix gate:** After completing implementation, run the test suite. If any tests fail, analyze the failure, fix the code, and re-run (max 3 fix attempts). If tests still fail after 3 attempts, the pipeline is blocked — do not advance to Stage 6. For TypeScript: run the equivalent of `node --experimental-strip-types *.test.ts` (or `npx tsx *.test.ts` if using tsx). For Python: `python -m pytest -x`. The test suite MUST pass before critical review.

### Stage 5: TEST ENGINEER → behavior-focused verification
- **Test the acceptance criteria first.** These ARE the test cases.
- **One regression test per bug fix.**
- **Test edges:** empty, huge, concurrent, malformed, unauthorized, offline.
- **Test behavior, not implementation.** Don't test private methods.
- **Fast tests (unit) for logic. Slower tests (integration) for I/O boundaries.**
- **Trivial one-liners need no test.** YAGNI applies to tests too.

**Test Integrity Sub-Lens (adopted from tworkflow — run this AFTER all tests pass):**
Before advancing to Stage 6, audit the tests themselves for these anti-patterns:
- **Weakened assertions:** `assert.ok(result)` when result is truthy by default. `assert.ok(true)` — always passes, tests nothing. `expect(result).toBeDefined()` when it's always defined. Fix: assert specific values and behaviors.
- **Swallowed errors:** `try { await fn() } catch { }` in test — tests pass by ignoring failures. Fix: test that error paths produce expected errors, not silence them.
- **Hardcoded outputs matching inputs:** `expect(transform(x)).toBe(x)` — tautology disguised as test. Fix: verify transformation with known input/output pairs.
- **Tests with no assertions:** A test that runs code but never checks any result. The test runner shows green but the test proves nothing. Fix: add at least one explicit assertion.
- **Skipped/disabled tests without justification:** `it.skip(...)` or `xdescribe(...)` with no comment explaining why. Every skipped test needs a `// SKIP: <reason>` comment.
- **Pure smoke tests:** `expect(fn).not.toThrow()` — verifies the code doesn't crash but never checks what it does. Fix: add behavioral assertions.

Any test that fails the integrity lens → fix the test before advancing. A passing test suite with 0 real assertions is a finding, not a pass.

**Operator Coverage Gate (run this BEFORE advancing from Stage 5):**
Count the operator types / code paths in the implementation. Verify that EVERY operator type has at least one test that exercises its behavioral contract (map, filter, reduce, window, join, etc.). For complex operators, verify that each major code path (success, error, watermark, late data) has coverage. If any operator has zero tests, add at least one before advancing. A missing operator test is a gap, not a choice — the "test the acceptance criteria first" rule means every accepted feature must have at least one verifying test.

Gate: all acceptance criteria pass. Coverage of error paths. Test integrity scan passes. Operator coverage verified.

### Stage 6: CRITICAL REVIEW → skeptical self-review
Apply the rubric:
- **Correctness:** logic, off-by-ones, null/empty, error paths, race conditions
- **Design:** right layer, right pattern, dependency direction, no new coupling
- **Readability:** names, function size, nesting, misleading comments
- **Security:** untrusted input, authz, injection, secrets
- **Performance:** N+1s, unbounded growth, needless allocation
- **Tests:** exist, test behavior, cover edges, would fail on regression

Report: Blocker/Major/Minor. Fix blockers before done.

### Stage 7: REFACTOR → simplify
After the code works and is correct:
- **Can anything be deleted?** Unused code, dead branches, dead imports, dead local variables (computed but never read), unused exported functions/methods/classes (trace every export to at least one call site — if none exist, delete it). **Also scan for these frequently-missed dead-code categories (v1.3.13):** (a) empty control-flow blocks — `if (cond) { /* comment only, no executable code */ }`, empty `for`/`while` bodies, `if` blocks whose entire body is a comment; (b) parameters never passed by any call-site — trace every function/method parameter to at least one argument at a call site; if no call site passes it, delete the parameter; (c) redundant guards — conditions that are always true or always false due to an earlier control-flow check (e.g., `if (size > 0)` after a block that already `continue`s on `size === 0`). Proven: iter32 shipped with 3 items from these categories that cost 0.19 composite points.
- **Can anything be simplified?** Two functions → one. Loop → stdlib. Override → default.
- **Can anything be inlined?** One-caller functions, one-use types.
- **Is the naming perfect?** Would a new teammate understand it cold?
- **Run ponytail-review:** what can be removed from the diff?

## Quality Standards (what "enterprise" actually means)

Enterprise code is NOT about complexity. It's about:
1. **Simplicity:** Fewest files, shortest diff, clearest names.
2. **Correctness:** Error paths handled, edges covered, contracts honored.
3. **Placement:** Every file in the right directory. Dependencies point inward.
4. **Testability:** Logic testable without infrastructure. Side effects at edges.
5. **Readability:** A new teammate understands it in one pass.
6. **Durability:** The code outlasts the framework version. Framework-free domain logic.

## Output Discipline

- **Lead with the decision.** "Monolith. One service, three modules. Dependencies: domain ← app ← infra."
- **Show the architecture.** Directory tree, dependency graph, module responsibilities.
- **Show the contracts.** Types/interfaces/APIs before any implementation body.
- **Show the code.** Clean, minimal, no comments explaining what — only why.
- **Show the tests.** Acceptance criteria as test cases.
- **End with trade-offs.** What was skipped, when to add it, what becomes harder.

## Competitive Evolution

This skill is self-improving via a golden-source testing loop. Every 5th iteration, consult `references/competitive-landscape.md` for the latest competitive analysis and adoption status of techniques from other code-generation agent systems (Agentnizer, Aider, GPT-Pilot, SDD Pilot, GRACE, MetaGPT, OpenHands, Cline).
