"""Phase 4 timing. Usage: python timing.py label|grid [reps]
Protocol: single thread, one warm-up run per variant (discarded), then `reps` timed runs per variant,
alternating the order (forward on even repetitions, reversed on odd ones), gc collected before and disabled
during each run. Runs longer than 20 s use 5 repetitions. t_total = t_A + t_F; for C5/C7 t_F = 0 by
construction and the in-loop frontier is counted inside t_A."""
import sys, json, gc, time, statistics
from variants import *
import rq_common as RQ

CFG = ["C1", "C3", "C4", "C5", "C6", "C7"]


def run_cfg(nm, tt, drivers, orders, q, B):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    pool, per = build_all(nm, tt, drivers, orders, q, B)
    tA = time.perf_counter() - t0
    tF = 0.0
    if nm in INLOOP:
        kp = pool
    else:
        t0 = time.perf_counter()
        kp = kstar_pool(pool, q)
        tF = time.perf_counter() - t0
    gc.enable()
    return pool, kp, per, tA, tF


def _pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def q3(xs):
    return _pct(xs, 0.25), _pct(xs, 0.75)


def measure(tag, tt, drivers, orders, q, B, reps):
    first = {}
    warm = {}
    for nm in CFG:                                  # warm-up (discarded for timing, used for work counters)
        t0 = time.perf_counter()
        pool, kp, per, tA, tF = run_cfg(nm, tt, drivers, orders, q, B)
        warm[nm] = tA + tF
        first[nm] = (pool, kp, per)
    if warm["C1"] > 20.0:
        reps = min(reps, 5)
    T = dict((nm, dict(A=[], F=[])) for nm in CFG)
    for r in range(reps):
        for nm in (CFG if r % 2 == 0 else list(reversed(CFG))):
            _p, _k, _c, tA, tF = run_cfg(nm, tt, drivers, orders, q, B)
            T[nm]["A"].append(tA); T[nm]["F"].append(tF)
    kref = sig(first["C1"][1])
    row = dict(tag=tag, B=B, reps=reps)
    tot = {}
    for nm in CFG:
        pool, kp, per = first[nm]
        sm = lambda k: sum(c[k] for _, c in per.values())
        row[nm] = dict(ext=sm("ext_attempts"), created=sm("labels_created"), killed_L1=sm("killed_layer1"),
                       killed_rule=sm("killed_rule"), complete=sm("complete_labels"), routes_kept=sm("routes_kept"),
                       a_evals=sm("a_evals"), fd_lookups=sm("fd_lookups"), fd_tests=sm("fd_tests"),
                       kstar=len(sig(kp)), kstar_equal_C1=(sig(kp) == kref),
                       fired_GW=sum(1 for _, (cl, c) in per.items() if cl == "GW" and c["killed_rule"] > 0),
                       fired_OD=sum(1 for _, (cl, c) in per.items() if cl == "OD" and c["killed_rule"] > 0),
                       n_GW=sum(1 for _, (cl, c) in per.items() if cl == "GW"),
                       n_OD=sum(1 for _, (cl, c) in per.items() if cl == "OD"),
                       tA=statistics.median(T[nm]["A"]), tF=statistics.median(T[nm]["F"]))
        tot[nm] = [a + f for a, f in zip(T[nm]["A"], T[nm]["F"])]
        row[nm]["tTot"] = statistics.median(tot[nm])
        row[nm]["tTot_iqr"] = q3(tot[nm])
        row[nm]["raw_A"] = T[nm]["A"]; row[nm]["raw_F"] = T[nm]["F"]
    for nm in CFG:
        sp = [a / b for a, b in zip(tot["C1"], tot[nm])]
        row[nm]["speedup_vs_C1"] = statistics.median(sp)
        row[nm]["speedup_iqr"] = q3(sp)
    print("%s B=%d reps=%d | " % (tag, B, reps) + " | ".join(
        "%s tot %.3f x%.2f ext %d" % (nm, row[nm]["tTot"], row[nm]["speedup_vs_C1"], row[nm]["ext"]) for nm in CFG),
        "| K* equal:", all(row[nm]["kstar_equal_C1"] for nm in CFG))
    sys.stdout.flush()
    return row


def main():
    which = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    rows = []
    if which in ("label", "label3"):
        for B in ((3,) if which == "label3" else (3, 4)):
            for (n, nd, seed) in LABEL_INSTANCES:
                drivers, orders, tt, q = label_instance(n, nd, seed, B)
                rows.append(measure("n%d_s%d" % (n, seed), tt, drivers, orders, q, B, reps))
    else:
        for align in (0.90, 0.50):
            for rep in range(10):
                d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
                r = measure("a%.2f_rep%d" % (align, rep), tt, d, o, q, 3, reps)
                r["alignment"] = align
                rows.append(r)
    json.dump(rows, open("../audit_logs2/timing_%s.json" % which, "w"), indent=1, default=str)
    print("saved ../audit_logs2/timing_%s.json" % which)


main()
