---
name: copilot-memory-harness
description: Give VS Code Copilot Chat persistent cross-session memory and self-improving skills using only a VS Code background task, no daemons or CLI. Use when the user wants Copilot to remember preferences and corrections across sessions, accumulate reusable skills, or asks for agent-like memory.
---

# Copilot Memory Harness

Replicate persistent cross-session memory and skill self-improvement inside VS Code Copilot Chat with no daemons, no background processes outside VS Code, and no Hermes CLI dependency. Copilot writes structured commands to an inbox; a VS Code background task running `build.py --watch` processes them within ~2s — deduplicating, enforcing char limits, capturing sessions, and rebuilding `.github/copilot-instructions.md`, the file Copilot reads every session.

## When to use

- User wants Copilot to remember preferences, conventions, and corrections across sessions.
- User wants Copilot to accumulate reusable skills over time.
- User has no Hermes CLI access, or wants agent-like memory constrained to Copilot.
- **MUST honor the no-daemon constraint.** If the user says "no daemons" / "VS Code only" / "without CLI", NEVER propose launchd, cron, file watchers outside VS Code, or `hermes chat -q` calls. The harness runs ONLY as a VS Code background task.

## Hard rules

- NEVER write the harness as a single monolithic file. Split into the `harness/` package, one responsibility per module — see [clean architecture](./references/clean-architecture.md), follow before deploying or editing the package.
- ALWAYS have Copilot write inbox commands, NEVER edit `memory.md`/`user.md` directly — the deterministic parser owns the `§` format, char limits, and dedup.
- ALWAYS store declarative facts ("User prefers concise responses"), NEVER instructions ("Always respond concisely").
- Python 3 stdlib only. NEVER add pytest, watchdog, or requests.

## Setup

1. **Deploy harness files** to `~/.copilot-harness/` (package `harness/` + `build.py`). If a prior session deployed them, verify: `ls ~/.copilot-harness/harness/*.py`. Layout and module responsibilities: [clean architecture](./references/clean-architecture.md).
2. **Seed memory files** — bootstrap from Hermes (`cp ~/.hermes/memories/MEMORY.md ~/.copilot-harness/memory.md` and `USER.md` → `user.md`), or `touch` empty `memory.md` and `user.md`. Format details: [Hermes memory internals](./references/hermes-memory-internals.md), read before editing entries.
3. **Build initial instructions**: `python3 ~/.copilot-harness/build.py`.
4. **Wire up each repo** — `.github/copilot-instructions.md` is per-workspace, so each repo needs its own symlink and task:
   ```bash
   cd ~/projects/<repo> && mkdir -p .github .vscode
   ln -sf ~/.copilot-harness/instructions.md .github/copilot-instructions.md
   ```
   Copy [tasks.json](./templates/tasks.json) into `.vscode/` (runs `build.py --watch` on folder open) and [copilot-instructions.md](./templates/copilot-instructions.md) as the symlink target.
5. **Verify**: `cd ~/.copilot-harness && python3 -m unittest discover -s tests`, then reopen the workspace (or Cmd+Shift+P → "Tasks: Run Task" → "Copilot Harness (watch)").

## How it works

Copilot writes tagged commands (`[REMEMBER]`, `[FORGET]`, `[UPDATE]`, `[PROFILE]`, `[SAVE_SKILL]`) to `inbox.md`; the watcher processes them within ~2s, then rebuilds instructions. See [watch mode & inbox](./references/watch-mode-inbox.md) for the full command table, flow, dedup (Jaccard ≥0.75), garbage-prevention mechanisms, embedded workflows, and the curator — consult when implementing or debugging command execution.

## Pitfalls

VS Code platform constraints (session-capture flush timing, propagation lag, per-workspace wiring, the inbox parsing bug, runtime deps) are in [Copilot chat internals](./references/copilot-chat-internals.md) — read when debugging capture or propagation.
