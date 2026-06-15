#!/usr/bin/env python3
"""Paired keep-or-revert statistical gate for skill-doctor champion vs challenger.

Reads trial-level pass booleans per prompt for both sides, computes the paired
per-prompt difference on the validation set, its 95% CI, pass@k / pass^k, checks
regressions on previously-passing prompts and side-effects, then emits a
keep/revert decision as JSON.
"""
import argparse
import json
import math
import sys


# ---- constants (each documents its modeling assumption) --------------------
Z_95 = 1.96  # normal-approx z for a two-sided 95% CI; assumes paired-diff mean is ~Gaussian (CLT over prompts)
# k for pass@k / pass^k = number of trials per prompt. We assume every prompt is
# run the same fixed number of trials; k is inferred per-side as that trial count.


def _trials(side):
    """Map prompt_id -> list[bool] of trial outcomes, coercing to bools."""
    return {pid: [bool(x) for x in trials] for pid, trials in (side or {}).items()}


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def _pass_rate(trials):
    """Per-prompt pass rate = fraction of trials that passed."""
    return _mean([1.0 if t else 0.0 for t in trials])


def _infer_k(side):
    """k = trials per prompt. Assumes uniform trial count; use the max seen."""
    counts = [len(t) for t in side.values() if t]
    return max(counts) if counts else 0


def pass_at_k(side):
    """pass@k: fraction of prompts with at least one passing trial (any-success)."""
    if not side:
        return 0.0
    return _mean([1.0 if any(t) else 0.0 for t in side.values()])


def pass_pow_k(side):
    """pass^k: fraction of prompts where ALL trials pass (all-success / reliability)."""
    if not side:
        return 0.0
    return _mean([1.0 if (t and all(t)) else 0.0 for t in side.values()])


def main():
    ap = argparse.ArgumentParser(description="Paired keep-or-revert gate (champion vs challenger).")
    ap.add_argument("input", nargs="?", help="JSON file path; reads stdin if omitted.")
    args = ap.parse_args()

    raw = open(args.input).read() if args.input else sys.stdin.read()
    data = json.loads(raw)

    champion = _trials(data.get("champion"))
    challenger = _trials(data.get("challenger"))
    validation_ids = list(data.get("validation_ids") or [])
    prev_passing = list(data.get("previously_passing_ids") or [])
    side_effects = data.get("side_effects") or {}
    se_champ = side_effects.get("champion") or {}
    se_chal = side_effects.get("challenger") or {}

    reasons = []

    # ---- paired per-prompt diff on VALIDATION ids only ----------------------
    # Pair = same prompt_id on both sides; diff = challenger_rate - champion_rate.
    diffs = []
    for pid in validation_ids:
        if pid in champion and pid in challenger:
            diffs.append(_pass_rate(challenger[pid]) - _pass_rate(champion[pid]))

    n = len(diffs)
    paired_mean_diff = _mean(diffs)

    if n >= 2:
        var = sum((d - paired_mean_diff) ** 2 for d in diffs) / (n - 1)  # sample variance (n-1, unbiased)
        sem = math.sqrt(var / n)  # SEM of the mean paired diff
    else:
        sem = 0.0  # too few pairs to estimate spread; CI collapses to the point estimate

    ci_low = paired_mean_diff - Z_95 * sem
    ci_high = paired_mean_diff + Z_95 * sem

    # ---- regressions on previously-passing prompts --------------------------
    # Regression = a prompt that previously passed now has a lower challenger rate
    # than champion (strictly worse on a prompt we must not break).
    regressions = []
    for pid in prev_passing:
        if pid in champion and pid in challenger:
            if _pass_rate(challenger[pid]) < _pass_rate(champion[pid]):
                regressions.append(pid)
    if regressions:
        reasons.append("regression on previously-passing ids: " + ",".join(map(str, regressions)))

    # ---- pass@k / pass^k ----------------------------------------------------
    pak = {"champion": pass_at_k(champion), "challenger": pass_at_k(challenger)}
    ppk = {"champion": pass_pow_k(champion), "challenger": pass_pow_k(challenger)}

    if ppk["challenger"] < ppk["champion"]:
        reasons.append("challenger pass^k {:.4f} < champion pass^k {:.4f}".format(ppk["challenger"], ppk["champion"]))

    # ---- overall pass rate (for body_tokens trade-off rule) -----------------
    champ_overall = _mean([_pass_rate(t) for t in champion.values()]) if champion else 0.0
    chal_overall = _mean([_pass_rate(t) for t in challenger.values()]) if challenger else 0.0
    rate_strictly_up = chal_overall > champ_overall

    # ---- side-effects: must not be worse ------------------------------------
    champ_tokens = se_champ.get("body_tokens")
    chal_tokens = se_chal.get("body_tokens")
    tokens_up = (champ_tokens is not None and chal_tokens is not None and chal_tokens > champ_tokens)
    if tokens_up and not rate_strictly_up:
        reasons.append("body_tokens increased ({} -> {}) without strict pass-rate gain".format(champ_tokens, chal_tokens))

    # safety_constraints / scope accept either a list of named items or an integer count.
    def _shrunk(champ_v, chal_v, label, direction):
        # direction "down" flags a decrease (removed safety); "up" flags an increase (widened scope)
        if isinstance(champ_v, (int, float)) or isinstance(chal_v, (int, float)):
            c, h = (champ_v or 0), (chal_v or 0)
            bad = h < c if direction == "down" else h > c
            return ["{} count {} {} -> {}".format(label, "dropped" if direction == "down" else "grew", c, h)] if bad else []
        cset, hset = set(champ_v or []), set(chal_v or [])
        delta = (cset - hset) if direction == "down" else (hset - cset)
        verb = "removed" if direction == "down" else "widened: added"
        return ["{} {}: {}".format(label, verb, ",".join(map(str, sorted(delta))))] if delta else []

    removed_safety = _shrunk(se_champ.get("safety_constraints"), se_chal.get("safety_constraints"), "safety_constraints", "down")
    scope_widened = _shrunk(se_champ.get("scope"), se_chal.get("scope"), "scope", "up")
    reasons.extend(removed_safety)
    reasons.extend(scope_widened)

    side_effects_worse = (tokens_up and not rate_strictly_up) or bool(removed_safety) or bool(scope_widened)

    # ---- decision -----------------------------------------------------------
    no_regression = not regressions
    ppk_ok = ppk["challenger"] >= ppk["champion"]
    se_ok = not side_effects_worse
    ci_excludes_zero_positive = ci_low > 0.0
    ci_includes_zero = (ci_low <= 0.0 <= ci_high)

    decision = "revert"
    if no_regression and ppk_ok and se_ok:
        if ci_excludes_zero_positive:
            decision = "keep"
            reasons.append("paired CI lower bound on validation > 0 (challenger reliably better)")
        elif ci_includes_zero:
            # Tie: keep only if challenger is strictly cheaper (fewer body_tokens).
            if (champ_tokens is not None and chal_tokens is not None and chal_tokens < champ_tokens):
                decision = "keep"
                reasons.append("tie (CI includes 0) broken by lower body_tokens ({} < {})".format(chal_tokens, champ_tokens))
            else:
                reasons.append("tie (CI includes 0) and no body_tokens reduction")
        else:
            reasons.append("paired CI lower bound <= 0 (no significant improvement)")

    out = {
        "decision": decision,
        "paired_mean_diff": paired_mean_diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "pass_at_k": pak,
        "pass_pow_k": ppk,
        "regressions": regressions,
        "reasons": reasons,
    }
    print(json.dumps(out, indent=2))
    # Exit non-zero on gate failure (revert) so the harness can branch on status.
    sys.exit(0 if decision == "keep" else 1)


if __name__ == "__main__":
    main()
