# Governance

Versioning, provenance, CI gating, and security for the skill-doctor keep-or-revert loop.

## Contents

- [Immutable versions](#immutable-versions)
- [External ledger schema](#external-ledger-schema)
- [Ledger example](#ledger-example)
- [CHANGELOG](#changelog)
- [Merge-blocking CI gate](#merge-blocking-ci-gate)
- [Kill switch](#kill-switch)
- [Security pass](#security-pass)

## Immutable versions

- `version_id = sha256(canonical_skill_bundle)[:12]` — content-addressed, never reused. Re-deriving the hash detects tampering.
- One git commit per challenger; commit subject = `version_id`. Author the commit on a dedicated branch `skill-doctor/<skill>/<version_id>` — never on `main`.
- Champion = current shipped version. Challenger = the single edit under test. Promotion = fast-forward champion ref to a kept challenger.
- A reverted challenger stays in history (commit + ledger row); its edit is appended to the rejected-edit buffer so the operator library does not re-propose it.

## External ledger schema

Append-only JSON Lines file `ledger.jsonl` OUTSIDE the skill bundle (provenance must survive a revert that rewrites the bundle). One object per line:

| field | type | note |
|---|---|---|
| `version_id` | str | content hash (12 hex) of the challenger bundle |
| `content_hash` | str | full sha256 of the bundle; `version_id` is its prefix |
| `parent` | str | `version_id` this challenger forked from (champion at propose time) |
| `timestamp` | str | RFC3339 UTC |
| `proposing_agent` | str | agent/run that emitted the edit |
| `operator` | str | operator-library transform applied |
| `rationale` | str | one-line why, traced to a failure cluster |
| `model_id` | str | exact model id that produced the edit |
| `eval_run_id` | str | id of the paired eval batch (champion+challenger on same prompts/seeds) |
| `scores` | obj | `pass_at_k`, `pass_pow_k` (pass^k, all-k-pass), `tokens_mean_sd` `[mean,sd]`, `latency_mean_sd` `[mean,sd]` |
| `decision` | enum | `keep` \| `revert` \| `crash` (`crash` = eval errored, no valid scores) |

## Ledger example

```json
{"version_id":"a3f9c1e0b2d4","content_hash":"a3f9c1e0b2d4f8a7c6e5d4b3a2918077665544332211ffeeddccbbaa99887766","parent":"7e1b4c9d0a55","timestamp":"2026-06-15T14:22:01Z","proposing_agent":"skill-doctor/proposer","operator":"add-negative-example","rationale":"cluster #3: agent misclassified empty-input as error","model_id":"claude-opus-4-8[1m]","eval_run_id":"evr-2026-06-15-0007","scores":{"pass_at_k":0.94,"pass_pow_k":0.71,"tokens_mean_sd":[1820.4,210.7],"latency_mean_sd":[3.91,0.62]},"decision":"keep"}
```

## CHANGELOG

- Keep `CHANGELOG.md` as a SIBLING of `SKILL.md`, not inside it — a version string is provenance, not a spec field, and embedding it churns the prompt the model reads.
- One entry per kept promotion: `version_id`, date, operator, one-line effect, and the `pass_at_k` delta vs prior champion.
- Reverts/crashes are NOT changelog entries (no shipped change); they live only in the ledger.

## Merge-blocking CI gate

`ci_gate.py` (see scripts) blocks the merge unless ALL hold:

1. Paired CI gate: lower bound of the paired challenger−champion pass-rate CI > 0 (challenger is non-inferior/better, not noise).
2. Absolute floor: challenger `pass_at_k` CI lower bound ≥ `--threshold` (e.g. 0.90) — guards against both regressing together.
3. No `crash` decision in the run.

Gate exits non-zero on failure → branch protection prevents promotion. Only a passing gate may fast-forward the champion ref.

## Kill switch

- `champion.lock` (or env `SKILL_DOCTOR_PIN=<version_id>`) repoints the active skill to the last-known-good version on the next load.
- Setting it does NOT rewrite history; it overrides resolution. Loader prefers the pin over the branch head until cleared.
- Trip it on any post-promotion regression alarm; the ledger row that triggered it records the regression context.

## Security pass

The loop edits and ships executable code, so every challenger runs a security scan BEFORE it is shippable; failure forces `decision=revert` regardless of scores:

- Bundled scripts: flag `eval`, `exec`, `subprocess`/`os.system`, `pickle`, dynamic import of attacker-controlled names.
- Deps: stdlib-only is the contract — fail on any third-party import or added requirement.
- Network instructions: flag added URLs, `curl`/`wget`/`pip install`, or prose telling the agent to fetch/exfiltrate — these are not allowed to enter the skill via an auto-proposed edit.
