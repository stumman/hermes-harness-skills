# Skill Reshape Benchmark — Old (flat `.github/skills/*.md`) vs New (`.agents/skills/*/SKILL.md`)

Measured with `.agents/score.py` against the [Copilot Skill Anatomy Standard](./SKILL-ANATOMY-STANDARD.md). "Old" = the files at git HEAD before reshaping; "New" = the conformant Agent-Skill folders. Token counts are estimates (`bytes / 4`).

## Tier-2 inline body — tokens loaded on EVERY activation

This is the recurring cost that matters most: the full body loads whenever a skill triggers.

| Skill | Old | New | Δ | Rubric score old→new |
|---|--:|--:|--:|:--|
| ponytail | 875 | 851 | −3% | 74.3 → 100.0 |
| ponytail-audit | 11,331 | 1,343 | −88% | 39.4 → 100.0 |
| nerd-code | 13,145 | 3,047 | −77% | 45.1 → 97.3 |
| conductor | 3,325 | 905 | −73% | 47.9 → 100.0 |
| critical-review | 410 | 409 | −0% | 77.5 → 100.0 |
| security-sentinel | 1,381 | 493 | −64% | 62.2 → 100.0 |
| copilot-memory-harness | 4,273 | 897 | −79% | 57.7 → 100.0 |
| **TOTAL** | **34,740** | **7,945** | **−77%** | **avg 57.7 → 99.6** |

No guidance was deleted — bulk content moved to tier-3 `references/` files that load **only on demand** when the body links them (progressive disclosure). Total preserved reference content across all skills: ~30k+ words now off the hot path.

## Tier-1 description chars — scanned every relevant turn, for every installed skill

| Skill | Old | New |
|---|--:|--:|
| ponytail | 447 | 298 |
| ponytail-audit | 710 | 256 |
| nerd-code | 392 | 268 |
| conductor | 707 | 270 |
| critical-review | 276 | 235 |
| security-sentinel | 438 | 284 |
| copilot-memory-harness | 306 | 288 |
| **TOTAL** | **3,276** | **1,899** (−42%) |

All descriptions now sit in the 120–300 char target band with explicit WHAT + "Use when" trigger clauses.

## Hygiene defects (dangling refs + non-standard frontmatter keys + version/benchmark/marketing tokens)

| Skill | Old | New |
|---|--:|--:|
| ponytail | 7 | 0 |
| ponytail-audit | 49 | 0 |
| nerd-code | 19 | 0 |
| conductor | 20 | 0 |
| critical-review | 3 | 0 |
| security-sentinel | 4 | 0 |
| copilot-memory-harness | 10 | 0 |
| **TOTAL** | **112** | **0** |

## Headline

- **−77%** recurring per-activation token cost (34.7k → 7.9k).
- **−42%** always-scanned description cost.
- **112 → 0** hygiene defects (broken links, invalid frontmatter, provenance/marketing fluff).
- Avg rubric score **57.7 → 99.6 / 100**.

> Reproduce: `for s in ponytail ponytail-audit nerd-code conductor critical-review security-sentinel copilot-memory-harness; do python3 .agents/score.py .agents/skills/$s/SKILL.md; done`
