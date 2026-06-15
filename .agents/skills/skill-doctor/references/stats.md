# Statistics + Judge Protocol (keep-gate)

## Contents
- [Trials & per-prompt aggregation](#trials--per-prompt-aggregation)
- [Clustered SEs](#clustered-ses)
- [Paired-difference gate](#paired-difference-gate-primary)
- [Power analysis (up front)](#power-analysis-up-front)
- [pass@k vs pass^k](#passk-vs-passk)
- [Judge panel (PoLL)](#judge-panel-poll)
- [Bias controls](#bias-controls)
- [KEEP criterion](#keep-criterion-one-line)

## Trials & per-prompt aggregation
- Run `k>=3` trials per prompt (LLM output is stochastic; one trial estimates nothing).
- Score each trial in [0,1]; **average within prompt first** -> one number per prompt. The prompt is the unit of analysis, not the trial.
- Across n prompts: `mean`, `SD`, `SEM = SD/sqrt(n)`, `95% CI = mean +/- 1.96*SEM` (1.96 = normal quantile; fine for n>=30, else use t).

## Clustered SEs
- When prompts are scenario-variants of a few base scenarios, trials/variants within a cluster correlate.
- Naive SEs treat them as independent -> SEs can be **~3x too small** -> false "wins."
- Cluster by base scenario: `SE_cl = sqrt( sum_c (sum_i resid_ci)^2 ) / n` (CR0 sandwich), then CI off `SE_cl`. Report effective n = number of clusters, not rows.

## Paired-difference gate (PRIMARY)
- Same prompt set for champion and challenger. Compute per-prompt diff `d_p = challenger_p - champion_p`.
- Paired removes cross-prompt variance -> far more power than two-sample on small suites.
- **paired t**: `t = mean(d)/(SD(d)/sqrt(n))`; report CI on `mean(d)`.
- **sign test** (robust, no normality): count `d_p>0` vs `<0`, binomial p vs 0.5; use when n small or diffs skewed.
- Gate on the paired CI of `mean(d)`, not on two separately-reported means.

## Power analysis (up front)
- Before trusting any result, check the suite can detect the target delta. WARN (don't silently pass) when underpowered.
- Two-proportion rule of thumb: detecting **5% absolute** at 95% conf / 80% power ~ **400-600 cases/condition** (n per arm ~= 16*p*(1-p)/delta^2; p~0.5, delta=0.05 -> ~400-630).
- Paired/within-design needs far fewer (uses SD of diffs): `n ~= (1.96+0.84)^2 * SD(d)^2 / delta^2`. Report the minimum detectable effect (MDE) for the current n so small suites can't claim small wins.

## pass@k vs pass^k
- **pass@k** = P(>=1 of k trials correct) — *capability* (can it ever do it).
- **pass^k** = P(all k trials correct) — *reliability* (does it do it every time).
- Report BOTH per prompt and aggregated. A challenger that raises pass@k but drops pass^k traded reliability for luck — reject it.
- **KEEP requires pass^k not dropping** (within paired CI) on the protected suite.

## Judge panel (PoLL)
- No single judge — use a **Panel of LLM judges**: 3 judges across **different model families** (self-preference & family bias decorrelate across families).
- Cover **aspects**: {instruction correctness, trigger/CSO accuracy, safety, token-efficiency}.
- Cover **strategies**: {step-by-step, edge-case, adversarial}.
- Aggregate by **majority vote (BoN-MAV)**; on tie, fail closed (treat as not-better).
- **Calibrate** the panel against a small human-labeled holdout each run; if panel-vs-human agreement drops below threshold, the run is untrusted -> abort, don't KEEP.

## Bias controls
- **Position bias**: randomize A/B order per comparison; if the judge can't see which is champion, it can't favor a slot.
- **Verbosity bias**: penalize length unless the extra tokens are justified by the rubric; longer != better.
- **Self-preference**: the edit's author-model is NEVER a judge of that edit. Enforce mechanically (drop author family from panel).

## KEEP criterion (one line)
KEEP iff paired CI of mean(challenger - champion) lies **strictly above 0** (clustered SE) AND **pass^k does not drop** AND the calibrated judge panel majority rules challenger better AND no safety judge flags a regression; else REVERT (log to rejected-edit buffer + external ledger).
