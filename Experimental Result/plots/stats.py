"""Figure.md §3.1 — shared statistics. Percentiles are linear-interpolated (numpy default),
identical to the helper used in the analysis scripts that produced MASTER.

The bootstrap is written with Python's `random` so that, called with the seed MASTER used,
it reproduces MASTER's CIs exactly (sanity checks); figures use seed 20260929 (§0.5)."""
import random
import statistics

import numpy as np

PLOT_SEED = 20260929
N_BOOT = 2000


def median_iqr(x):
    x = np.asarray(x, dtype=float)
    return float(np.median(x)), float(np.percentile(x, 25)), float(np.percentile(x, 75))


def _pct(sv, p):
    k = (len(sv) - 1) * p
    f = int(k)
    c = min(f + 1, len(sv) - 1)
    return sv[f] + (sv[c] - sv[f]) * (k - f)


def mean_boot_ci(x, n_boot=N_BOOT, alpha=0.05, seed=PLOT_SEED):
    """Mean and percentile bootstrap CI; resampling unit = element of x (= one instance)."""
    v = [float(a) for a in x]
    n = len(v)
    rng = random.Random(seed)
    means = sorted(statistics.mean([v[rng.randrange(n)] for _ in range(n)]) for _ in range(n_boot))
    return statistics.mean(v), _pct(means, alpha / 2), _pct(means, 1 - alpha / 2)


def paired_diff_boot_ci(base, treat, key, col_fn, seed=PLOT_SEED):
    """base/treat DataFrames; pair rows on `key`; diff = col_fn(treat) - col_fn(base), rows where
    either side is None are dropped. Order follows `treat` row order (as in the RQ5 analysis)."""
    b = {tuple(r[k] for k in key): r for _, r in base.iterrows()}
    diffs = []
    for _, r in treat.iterrows():
        k = tuple(r[c] for c in key)
        if k not in b:
            continue
        a, t = col_fn(b[k]), col_fn(r)
        if a is None or t is None:
            continue
        diffs.append(t - a)
    return mean_boot_ci(diffs, seed=seed), diffs


def speedup_median_per_instance(df, t_base, t_treat):
    return float(np.median(df[t_base] / df[t_treat]))


def speedup_pooled(df, t_base, t_treat):
    return float(df[t_base].sum() / df[t_treat].sum())
