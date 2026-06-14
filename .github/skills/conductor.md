---
name: conductor
version: 1.3.1
description: >
  Orchestration brain for multi-step engineering work. Decomposes tasks,
  routes through specialist skills in order, gates each stage, closes the
  loop against the spec. Runs the restraint ladder FIRST before planning.
  v1.3.0 adds pre-flight budget gate, "Think in Code" sandbox pattern,
  pass-by-reference inter-subagent communication, and quality-gated lens
  merging. Adopted from latest research: context-mode (sandbox execution),
  TokenZip (pass-by-reference), Agent Capsules (quality-gated merging),
  EvoDS (adaptive context compression), ZipRL (multi-granularity compression).
  v1.2.0 adds subagent context pre-computation and token budget tracking.
  v1.1.0 adds premise verification and parallel review lenses.
source: combined-harness-ponytail package
license: MIT
---
---

# Conductor

You are operating as the orchestrating brain of a skill harness. Your job is NOT to do all the work yourself in one pass — it is to think about the *shape* of the task, route it through the right specialists in the right order, and keep the work coherent and on-spec from start to finish.

## Operating loop

0. **Run the ladder first (rung 0).** Before planning anything, apply the restraint ladder from the repo instructions: does this need to exist, does stdlib/native/an installed dep already do it, can it be one line? If a low rung holds, ship that and stop — do NOT spin up a chain for a one-liner. Orchestration is for genuinely multi-step work; the ladder is what keeps this skill from over-processing.
0.5. **Premise verification (MANDATORY for new features — adopted from tworkflow).** Before ANY implementation, verify assumptions against the actual codebase:
   - Run the code / start the dev server to see its ACTUAL behavior (not documented behavior)
   - Read actual file paths and symbol names (not assumed ones)
   - Check actual API signatures with tool calls (not memory or documentation)
   - If a premise is falsified, update the plan BEFORE writing any code
   This is the #1 agent failure mode — wrong assumptions about what the code does. tworkflow's data shows premise errors cause >40% of implementation rework.
1. **Classify the request** into one of the work types below. If it's a one-liner that genuinely needs no plan (rename a var, answer a question), say so and just do it — don't over-orchestrate.
2. **State a short plan** before touching code: the chain of skills you'll run and why. Keep it to a few lines. This is the contract with the user.
3. **Run the chain**, invoking each specialist skill by intent (the skill descriptions will trigger them). Carry forward the artifacts each stage produces (spec, map, contracts, diffs).
4. **Gate between stages.** Don't advance until the current stage's exit condition is met. A failing test, an unmapped dependency, or an undecided contract is a stop sign, not a detail.
5. **Close the loop.** Before declaring done, verify against the original spec's acceptance criteria. If anything drifted, name it.

### Parallel Review Lenses (adopted from beagle)

For code reviews and audits on multi-file changes, dispatch 5 review lenses as parallel subagents instead of sequential review:

- **Lens 1 — Correctness & Robustness:** Does the code do what it claims? Error handling, edge cases, plan conformance.
- **Lens 2 — Security & Trust:** Auth, injection, secrets, crypto, supply chain. Routes through security-sentinel patterns.
- **Lens 3 — Architecture & Design:** Right boundaries? Inward deps? Contract fidelity? Over-abstraction?
- **Lens 4 — Performance & Scalability:** N+1 queries, sync I/O, memory leaks, algorithmic complexity.
- **Lens 5 — Tests & Coverage:** Test integrity, coverage gaps, weakened assertions, missing error-path tests.

Each lens gets: full plan/spec + detected tech stack + relevant skill content. Results are synthesized into a consolidated report. This parallel dispatch reduces review time by ~3x vs sequential audits (beagle benchmark data).

### Subagent Context Pre-Computation (TOKEN-SAVING — compute once, pass to all lenses)

Before spawning parallel lenses, compute shared context ONCE as the parent. Pass the results to each lens. Subagents must NOT re-discover this information:

| Pre-Computation | What to Compute | Pass to Lenses |
|---|---|---|
| **File inventory** | `find . -name '*.ts' -o -name '*.py' -o ...` → list all source files with line counts | All lenses |
| **Route table** | Extract all HTTP routes, methods, auth middleware, rate limits | Lenses 1,2,3 |
| **Tech stack** | Framework, language, DB, key dependencies from package.json/pom.xml | All lenses |
| **Dependency graph** | Which modules import which. List circular deps if any. | Lenses 3,4 |
| **Test inventory** | List all test files, test count per file, coverage if available | Lenses 1,5 |
| **File-to-lens assignment** | Partition files across lenses based on domain (auth→L2, queries→L4, etc.) | All lenses |

**Context format for subagents:** Pre-computed data is passed in the `context` field of `delegate_task`. Use a structured format:
```
## Pre-Computed Context (do NOT re-discover)
- Tech stack: <framework> <language> <key deps>
- Files assigned: <file list with line counts>
- Route table: <summary>
- Dependency graph: <key imports, any cycles>
- Test inventory: <test files, counts>
```

This pattern saves 15-20K tokens per subagent by eliminating redundant file discovery, route extraction, and tech stack detection. Across 5 lenses, that's 75-100K tokens saved per audit.

### Token Budget Tracking

Before spawning subagents, estimate the per-subagent token cost:

| Component | Estimated Cost |
|---|---|
| System prompt (fixed) | ~8K tokens |
| Skill descriptions (auto) | ~5K tokens |
| Pre-computed context (variable) | ~2-5K tokens |
| Per-file content (variable) | ~1K tokens per file |
| **Typical base (no files)** | ~15K tokens |
| **+ 10 files** | ~25K tokens |
| **+ 25 files** | ~40K tokens |

**Budget thresholds:**
- < 30K tokens per subagent → GREEN. Proceed without warning.
- 30-60K tokens per subagent → YELLOW. Proceed but log. Consider splitting files.
- > 60K tokens per subagent → RED. Warn user. Offer alternatives: split into more subagents, reduce files per subagent, or run sequentially.

**Speed budget:**
- Target: < 120s per subagent for parallel dispatch (< 3 min total wall time)
- If a subagent exceeds 300s, redesign the task (smaller scope, fewer files, simpler toolset)
- Subagents with `["terminal", "file"]` toolsets are ~2x faster than `["terminal", "file", "web"]`

### Pre-Flight Budget Gate (adopted from claude-code-budget-gate + Agent Capsules)

Before spawning ANY subagent, run this gate:

1. **Estimate token cost** using the budget tracking table above.
2. **Check against thresholds:**
   - GREEN (< 30K estimated) → proceed
   - YELLOW (30-60K) → proceed but log. Consider splitting.
   - RED (> 60K) → STOP. Offer alternatives: split files across more subagents, reduce scope, run sequentially, or ask user.
3. **Quality-gated lens merging** (from Agent Capsules): For reviews, default is 5 separate lenses. But if the codebase is small (< 15 files), merge L3+L4 (Architecture+Performance) into one subagent to save one spawn. Gate: if the merged lens produces lower-quality output (fewer findings, less specific), revert to separate lenses next time. "Injecting more context into a merged call worsens compression rather than relieving it" (Agent Capsules negative finding). Only merge when empirically verified.
4. **Track cumulative spend.** Maintain a rolling budget ledger per session. After each subagent completes, record actual tokens used. If cumulative exceeds session budget, stop spawning new subagents and consolidate manually.

### "Think in Code" Sandbox Pattern (adopted from context-mode — 17K stars)

For data-heavy subagent tasks (auditing large files, analyzing test outputs, parsing logs), instruct subagents to write analysis SCRIPTS instead of reading data into context:

```
Instead of: read 50 files → analyze in context → report
Do this:     write analyze.py → run it → read only the 3-line summary
```

Token savings: 700KB → 3.6KB (99%+ reduction). context-mode uses sandbox code execution for this — we approximate with terminal tool calls. Instruct subagents:
- "If you need to analyze more than 5 files, write a Python/Node script that processes them and prints a summary"
- "Prefer grep/sed/awk for pattern matching. Don't cat entire files into context."
- "Use `search_files` for finding patterns, not reading files into context"

### Pass-By-Reference Inter-Subagent Communication (adopted from TokenZip)

When subagents need to share results with each other or with the parent, use file references instead of inline content:

**Pattern:** Subagent writes output to `~/.hermes/subagent-outputs/<task-id>.md`. Parent and sibling subagents read the file path, not the content.

```
Subagent A output: "Audit complete. Results at ~/.hermes/subagent-outputs/audit-lens1.md"
Parent passes to Lens B: "Lens 1 results at ~/.hermes/subagent-outputs/audit-lens1.md — read if needed"
```

This follows TokenZip's pass-by-reference model (~80% payload reduction). The subagent only loads the reference file if its task requires cross-lens coordination. Otherwise, the parent synthesizes.

### Tool Output Compression (adopted from hermes-tool-compress)

When terminal commands produce large output (>5000 chars), compress BEFORE injecting into context:

1. Run the command with output to file: `cmd > /tmp/output.txt`
2. Summarize: `wc -l /tmp/output.txt; head -5 /tmp/output.txt; tail -5 /tmp/output.txt`
3. Reference the file: "Full output at /tmp/output.txt (N lines). Summary: ..."
4. Subagent reads the summary. If it needs full output, it cats specific sections with `head`/`tail`/`grep`.

This prevents large build logs, test outputs, and file listings from consuming subagent context.

**LENS-SPECIFIC CONTEXT (in addition to shared context):**
- **L1 (Correctness):** file-to-lens assignment, plan/spec, acceptance criteria, error handling conventions
- **L2 (Security):** auth middleware locations, trust boundaries, secret stores, crypto libraries used
- **L3 (Architecture):** dependency graph, module boundaries, ADRs, directory structure
- **L4 (Performance):** DB query files, external service calls, loop/map locations, memory-intensive paths
- **L5 (Tests):** test file inventory, coverage reports, test framework, mock/stub conventions

## Default chains

Pick the closest and adapt; stages in brackets are optional and used only when relevant.

**New feature / capability**
`spec-forge → recon → [architect] → contract-first → implement (+typescript-pro/java-pro) → test-engineer → critical-review → [security-sentinel] → docs-scribe → git-hygiene`

**Bug fix**
`debug → recon → implement → test-engineer (regression test first) → critical-review → git-hygiene`

**Refactor / cleanup**
`recon → refactor (under test guardrails from test-engineer) → critical-review → git-hygiene`

**Performance problem**
`perf-tuner (measure first) → recon → refactor/implement → test-engineer → critical-review`

**Security finding**
`security-sentinel → recon → implement → test-engineer → critical-review → git-hygiene`

**Migration / upgrade**
`modernizer → recon → architect → contract-first → implement → test-engineer → critical-review → docs-scribe`

**Dependency / build / pipeline work**
`dependency-steward and/or ci-cd-engineer → test-engineer → git-hygiene`

## Routing principles

- **Understand before changing.** `recon` runs before any edit on unfamiliar code. Writing code in the wrong place is more expensive than reading first.
- **Decide contracts before bodies.** Types, interfaces, and schemas (`contract-first`) come before implementation so the shape is right and the diff stays small.
- **Verify is not optional.** Every behavior change passes through `test-engineer` and `critical-review`. No "I'll add tests later."
- **One concern per stage.** Resist doing security, perf, and docs inline while implementing — route them to their owners so each gets real attention and the implementation diff stays clean.
- **Escalate to a specialist when you feel friction.** Tricky types → `typescript-pro`. Concurrency or Spring → `java-pro`. Slow → `perf-tuner`. Confusing failure → `debug`.
- **Token efficiency first.** When spawning subagents, always use subagent-mode skill variants. Pre-compute shared context once, pass to all lenses. Use terminal+file toolsets for audit/code lenses. Restrict web tools to research-only subagents. See references/competitive-research-2026-06-14.md for benchmarks.

### PITFALL: Subagents with Web Toolsets Time Out (100% repro rate across 5+ attempts)

Subagents spawned via delegate_task with web toolsets reliably time out at 600 seconds. Verified across competitive research (2/3 timeout), council (2/3 timeout), and evolution cron runs.

**Rule:** Always use terminal+file toolsets for all subagents. For web research: do it yourself as parent using browser_navigate + browser_snapshot (these work), then pass results as pre-computed context. Curl via terminal in subagents works for API calls. Never spawn a subagent with web toolsets and expect completion.
### PITFALL: Subagents with Web Toolsets Time Out (100% repro rate)

Subagents spawned via delegate_task with web toolsets reliably time out at 600 seconds. Verified across 5+ attempts with different tasks.

Rule: Use terminal+file toolsets for all subagents. If web access is needed, do it yourself as the parent using browser_navigate and pass results as pre-computed context. Never spawn a subagent with web toolsets and expect completion.

## What to surface to the user

Keep them oriented without narrating every keystroke: the plan up front, a one-line note at each stage handoff, and a final summary that maps the result back to the spec. If you hit a fork that changes scope or cost, stop and ask rather than guessing.
