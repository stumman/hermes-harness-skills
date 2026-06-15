# Watch Mode & Inbox Mechanism

Polling strategy, dedup algorithm, inbox command parser, and the flow. Follow when wiring watch mode or debugging command execution.

## Flow (watch mode — recommended)

1. VS Code opens workspace → `.vscode/tasks.json` fires `build.py --watch` as a BACKGROUND task.
2. `build.py` runs the initial build cycle: captures sessions, processes inbox, enforces limits, runs curator (weekly), builds instructions.
3. Watcher loop polls every 2s: inbox changed → process commands; memory files changed → rebuild; new VS Code sessions → capture; skills changed → rebuild.
4. Copilot reads `.github/copilot-instructions.md` (symlink) every session.
5. During conversation, Copilot writes structured commands to `inbox.md`.
6. Within 2 seconds, the watcher processes inbox → updates memory → rebuilds instructions.
7. On VS Code close, the watcher terminates with the task.

## Inbox commands

The `instructions.md` teaches Copilot to write structured commands to `~/.copilot-harness/inbox.md` (NOT edit memory files directly):

| Command | Action | Example |
|---------|--------|---------|
| `[REMEMBER: fact]` | Append to memory.md | `[REMEMBER: Project uses pytest with xdist]` |
| `[FORGET: old]` | Remove stale entry from memory and user | `[FORGET: Project uses unittest]` |
| `[UPDATE: old → new]` | In-place replace across all entries | `[UPDATE: DB is MySQL → DB is PostgreSQL 16]` |
| `[PROFILE: fact]` | Append to user.md | `[PROFILE: Prefers dark terminal themes]` |
| `[SAVE_SKILL: name — desc]` | Create skill file | `[SAVE_SKILL: python-debugging — pdb workflow]` followed by markdown body |

For `[SAVE_SKILL:]`, follow the command line with markdown content (steps, pitfalls). The parser captures all lines until the next `[` command.

## Why inbox instead of direct file edits

The inbox guarantees correct execution. Copilot writes simple tagged text; the deterministic parser in `harness/inbox.py` handles `§` delimiters, character limits, and dedup. No risk of Copilot mangling the memory format, and the watcher processes inbox within 2 seconds.

## Garbage prevention

| Mechanism | Implementation |
|-----------|---------------|
| Hard char limits | 2200 memory, 1375 user. `build.py` truncates oldest entries via FIFO eviction. |
| Deduplication | Jaccard word overlap ≥0.75 — entries with 75%+ common words are merged, keeping newest. More robust than Levenshtein for multi-word declarative facts. |
| Replace semantics | `[UPDATE: old → new]` in-place across all entries. Prevents append-bloat from corrections. |
| Remove semantics | `[FORGET: text]` removes any entry containing the text (case-insensitive) from BOTH memory and user. |
| Declarative facts rule | "User prefers concise responses" ✓ — "Always respond concisely" ✗ |
| Priority guidance | User corrections > preferences > conventions > environment facts. |
| Curator | Runs weekly inside `build.py`: 30d inactive → stale, 90d → archived to `skills/.archive/`. |
| Atomic writes | `harness/store.py`: tempfile + fsync + os.replace. Prevents partial writes. |
| File locking | `harness/store.py`: `fcntl.flock LOCK_EX | LOCK_NB`. Prevents concurrent builds from multiple VS Code windows. |
| Drain warnings | At 90% capacity, instructions include a consolidation prompt with specific recommendations. |
| Never-save list | Task progress, TODOs, session outcomes, completed-work logs, trivial facts. |
| Inbox clearing | Inbox is cleared atomically after successful processing. Garbage lines that match no command pattern are cleared too. |

## Embedded workflows

The instructions embed three workflows as prompt patterns, triggered by the user saying the slash-command name:

- `/principle-first` — Before proposing solutions, identify core principles, constraints, and what must be true. Prevents solution-jumping.
- `/council` — Multi-perspective review: Security, Performance, Maintainability, UX, Correctness. Each analyzed independently before synthesizing.
- `/simplify` — Post-solution review: what can be removed, reused, or is over-engineered.

## Curator (skill lifecycle)

Runs weekly inside `build.py`, or manually: `python3 curator.py`.

- Discovery: scans `skills/` for new SKILL.md files.
- Stale detection: 30 days inactivity → marked stale.
- Archiving: 90 days inactivity → moved to `skills/.archive/` (never deleted).
- Pinned skills: exempt from all transitions.
- Telemetry: `skills/.usage.json` sidecar tracks use_count, state, pinned status.
- Commands: `python3 curator.py pin <name>`, `unpin <name>`, `restore <name>`, `pause`, `resume`.
