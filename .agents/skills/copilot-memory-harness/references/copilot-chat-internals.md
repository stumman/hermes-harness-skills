# VS Code Copilot Chat Internals

Storage research and platform constraints. Follow when debugging session capture, propagation timing, or per-workspace wiring.

## Pitfalls

1. **Copilot has no tool loop.** Unlike Hermes, Copilot only acts during text generation. The inbox bridges this: Copilot writes tagged text, the deterministic parser executes it — but Copilot must still be instructed to write to inbox. Agent Mode in VS Code 1.99+ narrows this gap.

2. **Session capture is delayed until VS Code flushes JSONL.** VS Code holds Copilot Chat data in memory and only flushes to `workspaceStorage/chatSessions/*.jsonl` on exit. In watch mode the watcher scans every 30s and captures sessions once they appear on disk — but they only appear after VS Code saves them. Real-time capture needs a VS Code extension with the `chatHooks` proposed API.

3. **Mid-session updates propagate within 2 seconds.** Watch mode polls file mtimes every 2s with 3s debounce. After Copilot writes to inbox, the watcher rebuilds instructions within ~2 seconds. BUT Copilot only re-reads instructions on session start, so updates take effect next session (or next message, depending on Copilot's caching).

4. **Dedup threshold is contextual.** Jaccard word overlap at 0.75 catches identical facts with one-word differences; truly distinct facts pass through. Verify the threshold with real memory entries.

5. **`.github/copilot-instructions.md` is per-workspace.** There is no global instructions file in VS Code. Each repo needs its own symlink and `.vscode/tasks.json`. Copy the tasks.json from any wired-up repo.

6. **Instructions file size budget.** If memory + skills grow large, instructions may approach Copilot's context budget. The 2200/1375 char limits keep this controlled.

7. **Python 3 is the only runtime dependency.** macOS ships with Python 3. No pip installs, no pytest (stdlib unittest), no watchdog (os.stat polling), no requests (no HTTP).

8. **Inbox parsing.** In `harness/inbox.py` `parse_inbox()`, always append any non-None `current_command` before overwriting, and always append the last command regardless of type — otherwise non-skill commands (REMEMBER/FORGET/UPDATE/PROFILE) are silently dropped.
