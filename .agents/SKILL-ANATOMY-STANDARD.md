# The Copilot Skill Anatomy Standard

> Authoritative, checkable standard for authoring and grading `SKILL.md` files for VS Code Copilot Agent Skills (also loaded by Copilot from `.claude/skills` and `.agents/skills`). Every rule below is either quoted from the official VS Code Agent Skills documentation or marked **[council inference]** where the docs set no numeric limit and the value is derived from the platform's token-economy model. Grounded against `https://code.visualstudio.com/docs/agent-customization/agent-skills`.

## 0. Governing principle: pay tokens where they buy behavior

Progressive disclosure has **three tiers**, and each tier is paid on a different schedule. Author every byte against the tier that pays for it:

| Tier | What loads | When it is paid | Cost profile |
|---|---|---|---|
| **1. Discovery** | `name` + `description` only | Scanned on **every relevant agent turn**, for **every installed skill** | Most expensive recurring real estate in the system |
| **2. Instructions** | Full `SKILL.md` body | Loaded in full **whenever the skill triggers / is invoked** | Recurring per-activation |
| **3. Resources** | Files under `references/`, `scripts/`, etc. | Loaded **only when the body links them by relative Markdown path**; unreferenced files **never load** | On-demand, conditional |

The single design rule that follows: **put a byte in the cheapest tier that still makes it work.** A fact needed on *every* run is tier-2 body. A fact needed *sometimes* is a tier-3 linked file. A routing/trigger signal is tier-1 description. Anything that changes no behavior at all (version strings, benchmarks, marketing) belongs in **none** of the tiers — move it to a `CHANGELOG.md`/design doc *outside* the skill folder, or to git history.

---

## 1. Location & identity (preconditions — a misplaced skill never loads)

1.1 `SKILL.md` MUST live at one of the documented roots, in a folder named for the skill:
- Project: `.github/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`, or `.agents/skills/<name>/SKILL.md`
- Personal: `~/.copilot/skills/<name>/`, `~/.claude/skills/<name>/`, or `~/.agents/skills/<name>/`

1.2 **One skill = one folder.** The folder name is the skill's identity.

1.3 `name` MUST satisfy `^[a-z0-9-]{1,64}$` (lowercase letters, numbers, hyphens; max 64 chars) **and** be byte-for-byte equal to the parent directory name. No uppercase, spaces, underscores, dots, colons, slashes, or namespace prefixes (`myorg/skill` is invalid). Invalid characters or folder mismatch cause **silent load failure**.

1.4 The `name` SHOULD itself carry trigger signal: prefer task-domain words (`webapp-testing`, `github-actions-debugging`) over opaque codenames (`ponytail`, `conductor`) that force the description to do all routing work.

---

## 2. Frontmatter (closed schema — no invented fields)

2.1 The frontmatter key set MUST be a **subset of exactly these six documented fields**:

| Field | Required | Default | Purpose |
|---|---|---|---|
| `name` | **Yes** | — | Identity; must equal folder name |
| `description` | **Yes** | — | Tier-1 routing signal (WHAT + WHEN) |
| `argument-hint` | No | none | Hint text for slash-command args |
| `user-invocable` | No | `true` | Slash-menu visibility |
| `disable-model-invocation` | No | `false` | Blocks automatic agent loading |
| `context` | No | `inline` | `fork` runs in an isolated subagent |

2.2 **No keys outside this set.** Do not add `version`, `author`, `tags`, `license`, `source`, `model`, `changelog`, `metadata`, etc. The docs never define them; the loader does not consume them; they are pure recurring parse cost and a rot signal.

2.3 **Omit any optional field set to its default.** Writing `user-invocable: true`, `disable-model-invocation: false`, or `context: inline` adds inert bytes without changing behavior.

2.4 **Never disable both invocation paths.** Assert `NOT (user-invocable == false AND disable-model-invocation == true)` — that combination makes the skill uninvocable (infinite cost-per-effect).

2.5 Set `context: fork` **only** when the body describes a self-contained, context-heavy, multi-step procedure whose intermediate reasoning should not pollute the parent agent. Otherwise leave it absent (inline). This is the docs' sanctioned escape hatch for an inherently verbose procedure — it is not a substitute for slimming the body.

---

## 3. Description — the tier-1 routing contract

The description + name are the **only** signals scanned during discovery. The description is the single highest-leverage byte budget in the skill.

3.1 **Structure: WHAT then WHEN, in that order.** Follow the official template shape:
> `<Capability statement>. Use this when <concrete trigger>.`

Official exemplars (verbatim):
> "Guide for testing web applications using Playwright. Use this when asked to create or run browser-based tests."
> "Guide for debugging failing GitHub Actions workflows. Use this when asked to debug failing GitHub Actions workflows."

Both halves MUST be present: a capability clause AND a `Use when` / `Use this when` trigger clause. Per the docs: *"Be specific about both capabilities and use cases to help Copilot decide when to load the skill."*

3.2 **Trigger vocabulary mirrors user words.** Embed 2–5 concrete trigger phrases (verb + object) that echo the literal words a user would type — `create or run browser-based tests`, `debug failing GitHub Actions workflows` — not internal jargon or abstract capability nouns. Selection is a semantic match of the user request against the description.

3.3 **Front-load the most distinctive term.** The single most distinctive domain/action term MUST appear within the first 80 characters (it may be truncated/down-weighted by position in long skill lists).

3.4 **Negative scope for siblings.** When two installed skills share ≥3 significant trigger nouns/verbs, at least one MUST carry a disambiguation clause: `NOT for X (use <other-skill>)`. There is no separate exclusion field in frontmatter — this is the only lever against over-triggering.

3.5 **Length budget:** hard ceiling **1024 characters** (platform max — exceeding it is invalid). Target **120–300 characters** (the official exemplars are ~95–115). **[council inference for the 120–300 target; only the 1024 cap is documented.]**

3.6 The description MUST NOT contain:
- **Version / changelog** — `vX.Y.Z`, `iterNN`, `now supports`, `adds`, `release`, `changelog`. (No user request contains a version number.)
- **Implementation mechanics** — file/script names, file extensions (`.py`/`.js`/`.ts`/`.sh`), CLI flags (`--watch`), bracket-token payloads (`[REMEMBER/...]`), or an arrow-chain of ≥3 pipeline stages (`a → b → c`). These are tier-2/tier-3 content.
- **Marketing / persona** — `powerful`, `ultra`, `rigorous(ly)`, `brain`, `seamless`, `blazing`, `world-class`, `elite`, `state-of-the-art`, `best-in-class`, `revolutionary`. The first word should be a capability verb or `Guide for`, not an adjective.
- **How-to detail** — numbered steps, `first… then…`, relative paths (`references/`, `scripts/`, `.md`). The description is WHAT+WHEN only; HOW lives in the body.

---

## 4. Body — tier-2 (paid on every activation)

The body is *"instructions, guidelines, and examples that Copilot should follow"* including step-by-step procedures and references to included resources. It is loaded **in full** on every trigger, so every body token is recurring.

4.1 **Length budget [council inference — the docs set NO body length limit]:** target **≤ 200 lines / ≤ 500 words / ≤ ~2,000 tokens** of recurring content; treat **> 3,000 tokens (or > ~5 KB)** as a smell that forces a body-vs-references audit.

4.2 **Inline ONLY what every invocation needs:**
- the trigger / when-to-use framing,
- the ordered core procedure / steps,
- hard gates and rules phrased as `MUST` / `NEVER` / `ALWAYS`,
- the relative-path links to deeper resources.

The test for every body line: *"Is this needed on EVERY run?"* If yes → body. If sometimes → tier-3 link. There is **no** "inline it for safety" middle ground — the only way to lose needed tier-3 content is to forget the link, which is mechanically checkable.

4.3 **Telegraphic imperatives, not narrative.** Each rule = directive + (only if non-obvious) a one-clause *why*. Cut hedging, restatement, and multi-sentence "Classic failure:" stories; compress a load-bearing example to a single `pattern → fix` clause. Flag any single bullet > 60 words.

4.4 **Move to `references/` (tier-3):** long worked examples (> ~15 lines), language/framework-specific deep-dives, large lookup tables, rarely-needed edge cases, templates, and scripts. **Anything conditional belongs behind a link** — a body section gated on a condition true < 100% of the time (`if you are using…`, `for <language>…`) MUST be a link, so a Python run does not pay for Go content.

4.5 **Single source of truth.** No paragraph/example/rule appears in both the body and a referenced file, and the body does not restate the description. The prompt-files docs endorse this: *"Use Markdown links to reference custom instructions rather than duplicating guidelines."* In particular, do not ship both a "condensed" summary block and an expanded section covering the same rules.

4.6 **Example-code hygiene.** Comments inside fenced example code blocks follow WHY-only discipline (never WHAT, never task references) — the agent copies sample comments into generated output, so redundant ones are double waste. If the skill states its own comment policy, examples must obey it.

---

## 5. References & scripts — tier-3 (paid only on demand)

5.1 **Link form.** Reference every tier-3 file with **relative Markdown link syntax**: `[descriptive text](./references/foo.md)`, `[split tool](./scripts/bar.py)`. Absolute paths or bare filenames are not the documented form and risk silent non-loading.

5.2 **When-to-follow text.** The link is the agent's only signal about a file it cannot yet see. Make link text say *when* to follow it: `[Python-specific rules](./references/python.md) — read before editing .py files`.

5.3 **No orphans.** Every file in the skill folder other than `SKILL.md` MUST be reachable via a relative link from the body. The docs: *"If a file isn't referenced in the instructions, it won't be loaded."* An unreferenced file is invisible to the agent forever — pure repo rot. (A `CHANGELOG.md` inside `<name>/` is the canonical violation: never linked, never loads — move it up out of the skill folder.)

5.4 **No dangling links.** Every relative path the body names MUST resolve to an existing file (`test -f`). A dangling link is an instruction the agent cannot follow: it costs tier-2 tokens and misleads the model into believing deeper guidance exists.

5.5 **Externalization bar.** Create a reference file only when it is **(a) linked from the body AND (b)** either large (> ~15 lines) or conditionally needed. Do not split content so small that the link costs more attention than inlining; do not embed a script/template's full contents in a fenced body block when it also exists as a linked file.

---

## 6. Anti-patterns — content that belongs in NO tier (zero behavioral effect)

These change no generated output. Move them to a `CHANGELOG`/design doc outside the skill folder, or delete.

6.1 **Self-evolution / provenance metadata** anywhere in frontmatter or body: version strings (`vX.Y.Z`), iteration markers (`iterNN`), `— NEW` / `— UPDATED` annotations, "version history", "release notes". There is no version field in the schema.

6.2 **Benchmarks, statistics, and internal-project lore:** `~3x faster`, `40% of findings`, `99%+ reduction`, `100% repro rate`, `26-49% better across N audits`, named internal projects/benchmarks. The agent cannot "be 3x faster"; it can only follow an imperative. State the rule; drop the justifying statistic and its source.

6.3 **Internal TODOs / aspirational notes:** `TODO`, `FIXME`, `XXX`, `WIP`, `implement later`, `for now`. A skill is executed every activation; a maintainer's backlog note is unactionable and goes stale. (Acceptable exception: tokens like `TODO` appearing as *content categories the skill operates on*, e.g. "remember TODO items," not as author backlog.)

6.4 **Marketing / self-congratulation** in name, description, or body (see 3.6 banned list). Superlatives consume budget without improving the relevance match.

---

## 7. Audit procedure (deterministic, runnable)

```bash
# strip frontmatter and measure body
awk 'f;/^---$/{f++}' SKILL.md > /tmp/body.md        # body only (after 2nd ---)
wc -w /tmp/body.md   # target <=500; smell >3000 tokens (~ >5KB)

# frontmatter key whitelist (fail if any key outside the six)
# name regex + folder match
test "$(basename "$(dirname SKILL.md)")" = "<name field>"  # must be true

# description length (chars) — fail >1024, warn >300
# anti-pattern grep across description+body (each match = a failure):
grep -nE 'v[0-9]+\.[0-9]+\.[0-9]+|iter[0-9]+|— NEW|— UPDATED|[0-9]+%|~[0-9]+x|faster|benchmark|repro rate|TODO|FIXME|world-class|blazing|elite|seamless|powerful|ultra' SKILL.md

# orphans: every folder file (except SKILL.md) must be linked
for F in $(find . -type f ! -name SKILL.md ! -name .DS_Store); do grep -q "$(basename "$F")" SKILL.md || echo "ORPHAN: $F"; done

# dangling: every ./references|scripts path in body must resolve
grep -oE '\./[A-Za-z0-9._/-]+' SKILL.md | while read p; do test -f "$p" || echo "DANGLING: $p"; done
```

---

## 8. Conformance checklist (quick gate)

- [ ] Path is a documented root; folder name == `name`; `name` matches `^[a-z0-9-]{1,64}$`.
- [ ] Frontmatter keys ⊆ the six; no defaults written explicitly; not both invocation paths disabled.
- [ ] `description` ≤ 1024 chars (target 120–300); has a capability clause AND a `Use when` clause; ≥2 concrete trigger phrases; distinctive term in first 80 chars; `NOT for` clause if a sibling overlaps; no version/mechanics/marketing/how-to.
- [ ] Body ≤ ~200 lines / ~500 words / ~2,000 tokens; ordered procedure; gates as MUST/NEVER; imperatives not narrative; no bullet > 60 words.
- [ ] Conditional/large content externalized to linked tier-3 files; no body block > 15 lines needed by < 100% of runs.
- [ ] Every tier-3 file is linked (no orphans); every link resolves (no dangling); links are `./` relative with when-to-follow text.
- [ ] No duplication across tiers; description not restated in body.
- [ ] Zero version/benchmark/TODO/marketing tokens anywhere.
