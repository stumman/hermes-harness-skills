---
name: copilot-memory-harness
description: "Replicate Hermes Agent's persistent memory + skill self-improvement in VS Code Copilot Chat. Clean package architecture (8 modules, 1770 lines, 47 tests, ADR). Structured inbox guarantees command execution. Watch mode rebuilds within 2s. No daemons, no CLI, no Hermes, no external deps — pure VS Code Task."
version: 2.0.0
author: Hermes Agent
metadata:
  tags: [copilot, vscode, memory, skills, self-improvement, harness]
  related_skills: [hermes-agent]
---

# Copilot Memory Harness

Replicate Hermes Agent's persistent cross-session memory and skill self-improvement system inside VS Code Copilot Chat — with zero daemons, zero background processes, and no Hermes CLI dependency. Copilot edits memory files directly during conversations. A VS Code Task (`tasks.json`) triggers `build.py` on workspace open to enforce limits, deduplicate, capture sessions, and merge everything into `.github/copilot-instructions.md` — the injection point Copilot reads every session.

**The insight**: Copilot writes structured commands to `~/.copilot-harness/inbox.md`. A background VS Code task (build.py --watch) processes them within 2 seconds — parsing, deduplicating, enforcing limits. The watch daemon also auto-captures sessions from VS Code JSONL every 30s. You get the same self-improvement loop Hermes has — guaranteed execution, no "maybe Copilot will follow through."

**v2.0.0 major upgrade**: Continuous watch mode (--watch) replaces single-shot workspace-open trigger. Structured inbox mechanism guarantees memory command execution. Auto session capture every 30s instead of only on VS Code exit.

## When to Use

- User wants Copilot to remember preferences, conventions, and corrections across sessions
- User wants Copilot to accumulate reusable skills over time
- User has no Hermes CLI access in their VS Code environment
- User wants agent-like persistent memory but is constrained to Copilot
- **CRITICAL**: User explicitly rejects Hermes CLI extraction, external daemons, launchd services, cron jobs, or any background process outside VS Code. The harness runs ONLY as a VS Code Task. Do NOT propose daemons, watcher processes, or `hermes chat -q` calls.

## Architecture

```
~/.copilot-harness/
├── harness/                    # Clean package (8 modules, ~1100 lines)
│   ├── config.py               Constants, paths, limits — single source of truth
│   ├── store.py                File I/O: atomic writes, entry parsing, fcntl locks
│   ├── memory.py               Memory logic: Jaccard dedup (≥0.75), FIFO limit
│   ├── inbox.py                Command parser: [REMEMBER/FORGET/UPDATE/PROFILE/SKILL]
│   ├── sessions.py             VS Code JSONL session capture
│   ├── skills.py               Skill discovery and metadata
│   ├── curator.py              Skill lifecycle: stale 30d → archive 90d
│   ├── builder.py              Instructions assembly (pure function, no I/O)
│   └── watcher.py              Polling-based file change detection (no deps)
├── build.py                    Thin CLI entry (197 lines, orchestrates build cycle)
├── tests/                      Test suite (47 tests, stdlib unittest)
│   ├── test_memory.py          Dedup, limits, stats
│   ├── test_inbox.py           Parsing, apply, pipeline
│   ├── test_builder.py         Assembly, drain warnings, skills listing
│   └── test_integration.py     E2E pipeline, sessions, atomic write
├── docs/
│   └── ADR-001-memory-system.md  Architecture Decision Record
├── memory.md                   Copilot writes durable facts (§-delimited)
├── user.md                     Copilot writes user profile facts
├── inbox.md                    Structured command queue (Copilot writes, harness processes)
├── skills/                     Copilot creates SKILL.md files
├── sessions/                   Auto-captured from VS Code JSONL (every 30s in watch mode)
├── instructions.md             REBUILT within 2s of any file change
└── .state.json                 Tracks processed sessions, last curator run
```

**Flow (watch mode — recommended):**
1. VS Code opens workspace → `.vscode/tasks.json` fires `build.py --watch` as BACKGROUND task
2. build.py runs initial build cycle: captures sessions, processes inbox, enforces limits, runs curator (weekly), builds instructions
3. Watcher loop polls every 2s: inbox changes? → process commands. Memory files changed? → rebuild. New VS Code sessions? → capture. Skills changed? → rebuild.
4. Copilot reads `.github/copilot-instructions.md` (symlink) every session
5. During conversation, Copilot writes structured commands to `inbox.md`
6. Within 2 seconds, watcher processes inbox → updates memory → rebuilds instructions
7. On VS Code close, watcher terminates with the task

**Why this architecture:**
- **No daemons outside VS Code.** The watcher lives as a VS Code background task, dies with VS Code. No launchd, no cron.
- **Structured inbox guarantees execution.** Copilot writes `[REMEMBER: ...]` to inbox.md. build.py parses it deterministically. No "maybe Copilot will follow through."
- **Clean separation.** Each module has ONE responsibility. builder.py is a pure function. inbox.py is a state machine. No god objects.
- **Zero external deps.** Python 3 stdlib only. No pytest, no watchdog, no requests.
- **Enterprise quality.** 47 tests, ADR documented, type hints throughout, dataclass models.

## Memory Format (1:1 Hermes)

| Property | Value |
|----------|-------|
| File | `memory.md` (agent facts), `user.md` (user profile) |
| Delimiter | `§` on its own line between entries |
| Char limits | 2200 (memory), 1375 (user) |
| Write style | Declarative facts, not instructions |
| Atomic writes | Hermes uses tempfile+fsync+os.replace; Copilot edits directly |

**Declarative facts, not instructions:**
```
✓ "User prefers concise responses, no fluff"
✗ "Always respond concisely without fluff"
```

**What to save:**
- User corrections, preferences, conventions
- Environment facts, tool quirks, project conventions
- Any fact that prevents the user from repeating themselves

**What NOT to save:**
- Task progress, TODOs, temporary state
- Session outcomes, completed-work logs
- Trivial facts easily re-discovered

## Skill Format

Same as Hermes SKILL.md: YAML frontmatter (`name`, `description`) + markdown body with numbered steps and a pitfalls section.

## Setup

### 1. Deploy harness files

The harness lives at `~/.copilot-harness/`. The package is `harness/` with `build.py` as the entry point.

```bash
mkdir -p ~/.copilot-harness/{harness,skills,sessions,tests,docs}
# Deploy the harness/ package + build.py + curator (from this skill's linked files)
# OR: the package is already deployed from a prior session — verify with:
ls ~/.copilot-harness/harness/*.py
```

### 2. Seed memory files

```bash
# Option A: Copy existing Hermes memory to bootstrap (recommended)
cp ~/.hermes/memories/MEMORY.md ~/.copilot-harness/memory.md
cp ~/.hermes/memories/USER.md ~/.copilot-harness/user.md

# Option B: Create empty
touch ~/.copilot-harness/memory.md ~/.copilot-harness/user.md
```

### 3. Build initial instructions

```bash
python3 ~/.copilot-harness/build.py
```

### 4. Wire up each repo

In each repo where Copilot should have persistent memory:

```bash
cd ~/projects/<repo>
mkdir -p .github .vscode

# Symlink: Copilot reads this every session
ln -sf ~/.copilot-harness/instructions.md .github/copilot-instructions.md
```

Create `.vscode/tasks.json` (from `templates/tasks.json`):
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Copilot Harness (watch)",
      "type": "shell",
      "command": "python3 ~/.copilot-harness/build.py --watch",
      "isBackground": true,
      "problemMatcher": {
        "owner": "copilot-harness",
        "background": {
          "activeOnStart": true,
          "beginsPattern": "Watcher ready",
          "endsPattern": "Build complete"
        }
      },
      "presentation": { "reveal": "silent", "panel": "dedicated" },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Copilot Harness (rebuild once)",
      "type": "shell",
      "command": "python3 ~/.copilot-harness/build.py",
      "presentation": { "reveal": "always", "panel": "shared" }
    }
  ]
}
```

### 5. Verify

```bash
# Run test suite
cd ~/.copilot-harness && python3 -m unittest discover -s tests
# Expected: Ran 47 tests in 0.009s — OK

# Reopen workspace — VS Code runs build.py --watch
# Or manually: Cmd+Shift+P → "Tasks: Run Task" → "Copilot Harness (watch)"
```

## How Copilot Uses It

The instructions.md teaches Copilot to write structured commands to `~/.copilot-harness/inbox.md` (NOT edit memory files directly):

| Command | Action | Example |
|---------|--------|---------|
| `[REMEMBER: fact]` | Append to memory.md | `[REMEMBER: Project uses pytest with xdist]` |
| `[FORGET: old]` | Remove stale entry from both memory and user | `[FORGET: Project uses unittest]` |
| `[UPDATE: old → new]` | In-place replace across all entries | `[UPDATE: DB is MySQL → DB is PostgreSQL 16]` |
| `[PROFILE: fact]` | Append to user.md | `[PROFILE: Prefers dark terminal themes]` |
| `[SAVE_SKILL: name — desc]` | Create skill file | `[SAVE_SKILL: python-debugging — pdb workflow]` followed by markdown body |

**Why inbox instead of direct file edits:**
The inbox guarantees correct execution. Copilot writes simple tagged text. The deterministic parser in `harness/inbox.py` handles `§` delimiters, character limits, and dedup. No risk of Copilot mangling the memory format. No "maybe Copilot will follow through" — the watcher processes inbox within 2 seconds.

For `[SAVE_SKILL:]`, follow the command line with markdown content (steps, pitfalls). The parser captures all lines until the next `[` command.

## Garbage Prevention (1:1 Hermes)

| Mechanism | Implementation |
|-----------|---------------|
| Hard char limits | 2200 memory, 1375 user. build.py truncates oldest entries via FIFO eviction |
| Deduplication | **Jaccard word overlap ≥0.75** — entries with 75%+ common words are merged, keeping newest. More robust than Levenshtein for multi-word declarative facts. |
| Replace semantics | `[UPDATE: old → new]` in-place across all entries. Prevents append-bloat from corrections. |
| Remove semantics | `[FORGET: text]` removes any entry containing the text (case-insensitive) from BOTH memory and user. |
| Declarative facts rule | "User prefers concise responses" ✓ — "Always respond concisely" ✗ |
| Priority guidance | User corrections > preferences > conventions > environment facts |
| Curator | Runs weekly inside build.py: 30d inactive → stale, 90d → archived to `skills/.archive/` |
| Atomic writes | `harness/store.py`: tempfile + fsync + os.replace. Prevents partial writes and corruption. |
| File locking | `harness/store.py`: fcntl.flock LOCK_EX | LOCK_NB. Prevents concurrent builds from multiple VS Code windows. |
| Drain warnings | At 90% capacity, instructions include ⚠️ consolidation prompt with specific recommendations. |
| Never-save list | Task progress, TODOs, session outcomes, completed-work logs, trivial facts easily re-discovered. |
| Inbox clearing | Inbox is cleared atomically after successful processing. Garbage lines that don't match any command pattern are cleared too.

## Workflows (Hermes /principle-first, /council, /simplify)

The instructions embed three Hermes workflows as prompt patterns:

**`/principle-first`** — Before proposing solutions, identify core principles, constraints, and what must be true. Prevents solution-jumping.

**`/council`** — Multi-perspective review (like Hermes subagents): Security, Performance, Maintainability, UX, Correctness. Each perspective analyzed independently before synthesizing.

**`/simplify`** — Post-solution review: "What can be removed? What should be reused? What's over-engineered?"

These are triggered by the user saying the slash command name.

## Curator (Skill Lifecycle)

Runs weekly inside build.py (triggered on workspace open), or manually: `python3 curator.py`.

- **Discovery**: scans `skills/` for new SKILL.md files
- **Stale detection**: 30 days inactivity → marked stale
- **Archiving**: 90 days inactivity → moved to `skills/.archive/` (never deleted)
- **Pinned skills**: exempt from all transitions
- **Telemetry**: `skills/.usage.json` sidecar tracks use_count, state, pinned status

Commands: `python3 curator.py pin <name>`, `unpin <name>`, `restore <name>`, `pause`, `resume`

## Pitfalls

1. **USER REJECTS DAEMONS.** If the user says "no daemons" or "VS Code only" or "without CLI" — STOP. Do not propose launchd, cron, file watchers outside VS Code, or `hermes chat -q` calls. The harness runs as a VS Code background task only. The user corrected this 3+ times. Embed this permanently.

2. **USER DEMANDS ENTERPRISE QUALITY.** "No AIslop" means: clean module separation (not monoliths), type hints, dataclasses, pure functions, stdlib-only deps, test suite, ADR documentation. Do NOT write a 686-line single file. Split into `harness/` package with `config.py`, `store.py`, `memory.py`, etc. — one responsibility per module.

3. **Inbox parsing bug: non-skill commands not appended.** In `harness/inbox.py` `parse_inbox()`, the original code only appended previous commands to the result list when they were skill commands. Non-skill commands (REMEMBER, FORGET, UPDATE, PROFILE) were silently dropped. Always append any non-None `current_command` before overwriting, and always append the last command regardless of type.

4. **Copilot has no tool loop.** Unlike Hermes which can autonomously decide mid-task to save, Copilot only acts during text generation. The inbox mechanism bridges this: Copilot writes tagged text, the deterministic parser executes it. But Copilot still needs to be told (or instructed) to write to inbox. Agent Mode in VS Code 1.99+ reduces this gap.

5. **Session capture is delayed until VS Code flushes JSONL.** VS Code holds Copilot Chat data in memory and only flushes to `workspaceStorage/chatSessions/*.jsonl` on exit. In watch mode, the watcher scans every 30s and captures sessions as soon as they appear on disk — but they only appear after VS Code saves them. Real-time capture requires a VS Code extension with `chatHooks` proposed API.

6. **Mid-session updates propagate within 2 seconds.** Watch mode polls file mtimes every 2s with 3s debounce. If Copilot writes to inbox, the watcher processes it and rebuilds instructions within ~2 seconds. BUT Copilot only re-reads instructions on session start — the updated instructions take effect next Copilot Chat session (or next message in the same VS Code session depending on Copilot's caching).

7. **Dedup threshold is contextual.** Jaccard word overlap at 0.75 catches identical facts with one-word differences. Truly distinct facts with different subjects pass through. Test with real-world memory entries to verify threshold.

8. **`.github/copilot-instructions.md` is per-workspace.** No global instructions file in VS Code. Each repo needs its own symlink and `.vscode/tasks.json`. Copy the tasks.json from any wired-up repo.

9. **Instructions file size budget.** If memory + skills grow large, instructions may approach Copilot's context budget. The 2200/1375 char limits keep this under control.

10. **Python 3 is the only runtime dependency.** macOS ships with Python 3. No pip installs needed. No pytest (use stdlib unittest). No watchdog (use os.stat polling). No requests (no HTTP calls).

## Supporting Files

- `references/copilot-chat-internals.md` — VS Code Copilot Chat storage research: JSONL format, workspace paths, flush timing, state.vscdb keys
- `references/hermes-memory-internals.md` — Hermes memory system internals: §-delimiter, char limits, SQLite schema, curator rules, MemoryManager lifecycle
- `references/watch-mode-inbox.md` — Watch mode + inbox mechanism: polling strategy, dedup algorithm (Jaccard), inbox command parser state machine, debounce logic
- `references/clean-architecture-v2.md` — v2.0 architecture decisions: module decomposition, test strategy, ADR format, enterprise quality standards
- `templates/tasks.json` — VS Code task definition: runs build.py --watch as background task on folder open
- `templates/copilot-instructions.md` — Symlink target: the instructions.md that build.py rebuilds. Symlink this into `.github/`

**Package source** (not deployable scripts — the package lives at `~/.copilot-harness/harness/`):
- `harness/config.py` — Constants and paths. Change limits here.
- `harness/store.py` — File I/O abstraction: atomic_write, read_entries, write_entries, with_lock
- `harness/memory.py` — Memory logic: deduplicate(), enforce_limit(), clean_entries(), get_stats()
- `harness/inbox.py` — Command parser: parse_inbox(), apply_commands(), process_inbox()
- `harness/sessions.py` — VS Code JSONL capture: find_new_sessions(), save_session()
- `harness/skills.py` — Skill discovery: load_skills(), SkillMetadata dataclass
- `harness/curator.py` — Skill lifecycle: Curator class with stale/archive transitions
- `harness/builder.py` — Instructions assembly: build_instructions() pure function
- `harness/watcher.py` — Polling loop: Watcher class with on_change callback
- `build.py` — Thin CLI entry point: build cycle orchestrator, --watch dispatch
