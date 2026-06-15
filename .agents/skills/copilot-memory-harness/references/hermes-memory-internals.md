# Hermes Memory Internals

The memory format the harness replicates 1:1. Follow when seeding, formatting, or debugging memory entries.

## Memory format

| Property | Value |
|----------|-------|
| File | `memory.md` (agent facts), `user.md` (user profile) |
| Delimiter | `§` on its own line between entries |
| Char limits | 2200 (memory), 1375 (user) |
| Write style | Declarative facts, not instructions |
| Atomic writes | Hermes uses tempfile + fsync + os.replace; Copilot edits via inbox |

## Declarative facts, not instructions

```
✓ "User prefers concise responses, no fluff"
✗ "Always respond concisely without fluff"
```

## What to save

- User corrections, preferences, conventions.
- Environment facts, tool quirks, project conventions.
- Any fact that prevents the user from repeating themselves.

## What NOT to save

- Task progress, TODOs, temporary state.
- Session outcomes, completed-work logs.
- Trivial facts easily re-discovered.

## Skill format

Same as Hermes SKILL.md: YAML frontmatter (`name`, `description`) + markdown body with numbered steps and a pitfalls section.
