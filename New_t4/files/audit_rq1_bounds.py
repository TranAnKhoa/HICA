"""Final_t4_Speedup.md Sec2 -- completion-level bound audit of dp_fast.py (the timed
implementation) on the 5 real RQ1 instances, after the RQ1 patches.

For every rule firing (label L, dropped order j, bound dK, dW), every feasible complete route
rho with prefix L is checked: K(rho)-K(rho minus j) >= dK and W(rho)-W(rho minus j) >= dW.
Also: (0) dp_fast without rule == brute-force set of feasible sequences; (K*) K* identical
with/without rule.

Usage: python audit_rq1_bounds.py [B] [seed,seed,...] [mutation|legacy|fixed]
"""
import itertools, sys, time
import dp_fast_rq1 as X
import dp_fast as DF
import dp_rules as DR
from hica_core import pareto, Route, kstar, sequences, simulate

LO, HI = 18.0, 25.0
ALL = {42: (12, 5), 1: (10, 4), 7: (15, 5), 123: (12, 6), 999: (10, 4)}


def to_routes(dr, triples):
    by = {}
    for seq, K, W in triples:
        by.setdefault(frozenset(o for o, _ in seq), []).append((K, W, seq))
    pool = []
    for S, pts in by.items():
        for K, W, s in pareto(pts):
            pool.append(Route(dr.id, S, K, W, s))
    for k, r in enumerate(pool):
        r.rid = "%s_r%d" % (dr.id, k)
    return pool


def sig(r):
    return (r.bundle, round(r.K, 9), round(r.W, 9))


def audit_driver(dr, orders, B, brute_check=True):
    full, st0 = DF.enumerate_fast(dr, orders, B, LO, use_rule=False)
    if brute_check:
        brute = {s for k in range(1, B + 1) for S in itertools.combinations(sorted(orders), k)
                 for s in sequences(S) if simulate(dr, orders, s) is not None}
        assert {s for s, _, _ in full} == brute, "dp_fast (no rule) != brute force on " + dr.id
    log = []
    red, st = DF.enumerate_fast(dr, orders, B, LO, use_rule=True, log=log)
    index = {}
    for s, _, _ in full:
        for k in range(1, len(s) + 1):
            index.setdefault(s[:k], []).append(s)
    viol = checked = 0
    worst = 0.0
    for L, j, dK, dW, qj in log:
        for s in index.get(L, []):
            K1, W1 = DR.path_cost(dr, orders, s)
            K2, W2 = DR.path_cost(dr, orders, tuple(x for x in s if x[0] != j))
            checked += 1
            gap = max(dK - (K1 - K2), dW - (W1 - W2))
            if gap > 1e-9:
                viol += 1
                worst = max(worst, gap)
    R, Rp = to_routes(dr, full), to_routes(dr, red)
    kfull = {sig(r) for r in kstar(R, orders, LO, HI)}
    kred = {sig(r) for r in kstar(Rp, orders, LO, HI)}
    return dict(driver=dr.id, cls=dr.cls, seqs=len(full), firings=len(log),
                checked=checked, viol=viol, worst=worst,
                pool_full=len(R), pool_red=len(Rp), kstar=len(kfull),
                kstar_equal=(kfull == kred))


def main():
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seeds = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else list(ALL)
    mode = sys.argv[3] if len(sys.argv) > 3 else "fixed"
    DF.MUT.clear()
    legacy = mode == "legacy"
    DF.LEGACY["exclude_own_delivery"] = legacy
    DF.LEGACY["shortcut_ignores_e_d"] = legacy
    if mode in ("no_absorb", "no_junction"):
        DF.MUT.add(mode)
    print("B=%d mode=%s seeds=%s" % (B, mode, seeds))
    tot = dict(checked=0, viol=0, firings=0, kstar_bad=0)
    for seed in seeds:
        n, nd = ALL[seed]
        drivers, orders = X.build_hica_instance(n, nd, seed, B=B)
        for dr in drivers:
            t0 = time.time()
            r = audit_driver(dr, orders, B, brute_check=(mode == "fixed"))
            tot["checked"] += r["checked"]; tot["viol"] += r["viol"]
            tot["firings"] += r["firings"]; tot["kstar_bad"] += (not r["kstar_equal"])
            print("  n=%d seed=%d %s %s seqs=%d firings=%d checked=%d viol=%d worst=%.3g "
                  "pool %d->%d K*=%d kstar_equal=%s (%.1fs)"
                  % (n, seed, r["driver"], r["cls"], r["seqs"], r["firings"], r["checked"],
                     r["viol"], r["worst"], r["pool_full"], r["pool_red"], r["kstar"],
                     r["kstar_equal"], time.time() - t0))
            sys.stdout.flush()
    print("TOTAL B=%d mode=%s: firings=%d completions_checked=%d violations=%d kstar_changed_drivers=%d"
          % (B, mode, tot["firings"], tot["checked"], tot["viol"], tot["kstar_bad"]))


if __name__ == "__main__":
    main()
