# Clean Architecture & Layout

Module decomposition, test strategy, and the directory layout for the harness package. Follow when deploying or modifying the `harness/` package.

## Directory layout

```
~/.copilot-harness/
├── harness/                    # package (one responsibility per module)
│   ├── config.py               Constants, paths, limits — single source of truth
│   ├── store.py                File I/O: atomic writes, entry parsing, fcntl locks
│   ├── memory.py               Memory logic: Jaccard dedup (≥0.75), FIFO limit
│   ├── inbox.py                Command parser: [REMEMBER/FORGET/UPDATE/PROFILE/SKILL]
│   ├── sessions.py             VS Code JSONL session capture
│   ├── skills.py               Skill discovery and metadata
│   ├── curator.py              Skill lifecycle: stale 30d → archive 90d
│   ├── builder.py              Instructions assembly (pure function, no I/O)
│   └── watcher.py              Polling-based file change detection (no deps)
├── build.py                    Thin CLI entry (orchestrates build cycle)
├── tests/                      Test suite (stdlib unittest)
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
├── sessions/                   Auto-captured from VS Code JSONL
├── instructions.md             Rebuilt within 2s of any file change
└── .state.json                 Tracks processed sessions, last curator run
```

## Module responsibilities (package source)

The package is not deployable scripts — it lives at `~/.copilot-harness/harness/`.

- `harness/config.py` — Constants and paths. Change limits here.
- `harness/store.py` — File I/O abstraction: `atomic_write`, `read_entries`, `write_entries`, `with_lock`.
- `harness/memory.py` — Memory logic: `deduplicate()`, `enforce_limit()`, `clean_entries()`, `get_stats()`.
- `harness/inbox.py` — Command parser: `parse_inbox()`, `apply_commands()`, `process_inbox()`.
- `harness/sessions.py` — VS Code JSONL capture: `find_new_sessions()`, `save_session()`.
- `harness/skills.py` — Skill discovery: `load_skills()`, `SkillMetadata` dataclass.
- `harness/curator.py` — Skill lifecycle: `Curator` class with stale/archive transitions.
- `harness/builder.py` — Instructions assembly: `build_instructions()` pure function.
- `harness/watcher.py` — Polling loop: `Watcher` class with `on_change` callback.
- `build.py` — Thin CLI entry point: build cycle orchestrator, `--watch` dispatch.

## Quality standards (enforce when user demands "no AIslop")

- Clean module separation — never a single monolithic file.
- Type hints throughout; dataclass models.
- Pure functions where possible (`builder.py` is pure; `inbox.py` is a state machine).
- stdlib-only dependencies. No pytest, no watchdog, no requests.
- Test suite + ADR documentation.

## Why this architecture

- **No daemons outside VS Code.** The watcher lives as a VS Code background task and dies with VS Code. No launchd, no cron.
- **Structured inbox guarantees execution.** Copilot writes `[REMEMBER: ...]`; `build.py` parses it deterministically.
- **Clean separation.** Each module has one responsibility. No god objects.
- **Zero external deps.** Python 3 stdlib only.
