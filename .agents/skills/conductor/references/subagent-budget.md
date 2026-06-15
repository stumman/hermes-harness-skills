# Subagent Context, Budget & Token Discipline

Follow before spawning any parallel subagents (review lenses or other fan-out work).

## Pre-compute shared context once

Compute shared context ONCE as the parent and pass it to each subagent. Subagents must NOT re-discover this.

| Pre-Computation | What to Compute | Pass to Lenses |
|---|---|---|
| File inventory | List all source files with line counts | All lenses |
| Route table | All HTTP routes, methods, auth middleware, rate limits | Lenses 1,2,3 |
| Tech stack | Framework, language, DB, key dependencies | All lenses |
| Dependency graph | Which modules import which; list circular deps | Lenses 3,4 |
| Test inventory | All test files, test count per file, coverage if available | Lenses 1,5 |
| File-to-lens assignment | Partition files across lenses by domain (auth→L2, queries→L4) | All lenses |

Context format passed in the `context` field of `delegate_task`:

```
## Pre-Computed Context (do NOT re-discover)
- Tech stack: <framework> <language> <key deps>
- Files assigned: <file list with line counts>
- Route table: <summary>
- Dependency graph: <key imports, any cycles>
- Test inventory: <test files, counts>
```

## Token budget tracking

Estimate per-subagent token cost before spawning:

| Component | Estimated Cost |
|---|---|
| System prompt (fixed) | ~8K tokens |
| Skill descriptions (auto) | ~5K tokens |
| Pre-computed context (variable) | ~2-5K tokens |
| Per-file content (variable) | ~1K tokens per file |
| Typical base (no files) | ~15K tokens |
| + 10 files | ~25K tokens |
| + 25 files | ~40K tokens |

## Pre-flight budget gate

Run before spawning ANY subagent:

1. Estimate token cost using the table above.
2. Check thresholds:
   - GREEN (< 30K) → proceed.
   - YELLOW (30-60K) → proceed but log; consider splitting files.
   - RED (> 60K) → STOP. Offer alternatives: split files across more subagents, reduce scope, run sequentially, or ask the user.
3. Speed: target < 120s per subagent; if a subagent exceeds 300s, redesign the task (smaller scope, fewer files, simpler toolset). Prefer `["terminal", "file"]` toolsets over adding `web`.
4. Track cumulative spend. Maintain a rolling budget ledger per session; record actual tokens after each subagent. If cumulative exceeds the session budget, stop spawning and consolidate manually.

## "Think in code" sandbox pattern

For data-heavy subagent tasks (auditing large files, analyzing test outputs, parsing logs), instruct subagents to write analysis SCRIPTS instead of reading data into context:

```
Instead of: read 50 files → analyze in context → report
Do this:    write analyze.py → run it → read only the 3-line summary
```

- "If you need to analyze more than 5 files, write a Python/Node script that processes them and prints a summary."
- "Prefer grep/sed/awk for pattern matching. Don't cat entire files into context."
- "Use `search_files` for finding patterns, not reading files into context."

## Pass-by-reference inter-subagent communication

When subagents share results, use file references instead of inline content. Subagent writes output to `~/.hermes/subagent-outputs/<task-id>.md`; parent and siblings read the path, not the content.

```
Subagent A output: "Audit complete. Results at ~/.hermes/subagent-outputs/audit-lens1.md"
Parent passes to Lens B: "Lens 1 results at ~/.hermes/subagent-outputs/audit-lens1.md — read if needed"
```

A subagent loads the reference file only if its task requires cross-lens coordination; otherwise the parent synthesizes.

## Tool output compression

When a terminal command produces large output (>5000 chars), compress BEFORE injecting into context:

1. Run with output to file: `cmd > /tmp/output.txt`
2. Summarize: `wc -l /tmp/output.txt; head -5 /tmp/output.txt; tail -5 /tmp/output.txt`
3. Reference: "Full output at /tmp/output.txt (N lines). Summary: ..."
4. The subagent reads the summary; if it needs full output, it cats specific sections with `head`/`tail`/`grep`.

## PITFALL: subagents with web toolsets time out

Subagents spawned via `delegate_task` with web toolsets reliably time out at 600 seconds.

**Rule:** Always use terminal+file toolsets for subagents. For web research, do it yourself as the parent using `browser_navigate` + `browser_snapshot`, then pass results as pre-computed context. Curl via terminal in subagents works for API calls. Never spawn a subagent with web toolsets and expect completion.
