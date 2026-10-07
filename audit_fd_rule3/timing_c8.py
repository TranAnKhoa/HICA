"""Timing of C8 (= C5 + Layer 3) against C1, C4, C5 (and C3, C7 for continuity).

Usage: python timing_c8.py <setting> <set> [reps]
  setting = orig   : every variant uses the generator's travel_time function (as EXPERIMENT_REPORT.md);
                     C8f builds its travel-time tables inside its own timed region.
            matrix : every variant uses one precomputed travel-time table (built once per instance,
                     outside the timed region); C8f reads the same table directly.
  set     = label  : five label instances, B = 3 and 4
            grid   : main-grid sample, n = 15, supply (3,3), alignment 0.90 / 0.50, reps 0-9, B = 3

Protocol (same as audit_fd_rule2/timing.py): one warm-up run per variant (discarded), then `reps` timed
runs per variant, alternating the order (forward on even repetitions, reversed on odd ones), gc collected
before and disabled during each run, 5 repetitions if a C1 run exceeds 20 s. t_total = t_A + t_F, where
t_F is the post-hoc frontier (0 for in-loop variants, whose frontier is inside t_A).
"""
import gc
import json
import statistics
import sys
import time

import paths  # noqa: F401
import fastrule as FR
from variants3 import build_all, INLOOP
from common import label_instance, sig, kstar_pool, LABEL_INSTANCES
import rq_common as RQ


def runners(setting, tt, drivers, orders, q, B):
    if setting == "orig":
        def c8f():
            TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
            return FR.build_all_fast(tt, drivers, orders, q, B, (TT, KK))
        names = ["C1", "C3", "C4", "C5", "C7", "C8", "C8f"]
        R = {nm: (lambda nm=nm: build_all(nm, tt, drivers, orders, q, B)) for nm in names if nm != "C8f"}
        R["C8f"] = c8f
        return names, R
    TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
    ttm = FR.matrix_tt(TT)
    names = ["C1", "C4", "C5", "C8f"]
    R = {nm: (lambda nm=nm: build_all(nm, ttm, drivers, orders, q, B)) for nm in names if nm != "C8f"}
    R["C8f"] = lambda: FR.build_all_fast(ttm, drivers, orders, q, B, (TT, KK))
    return names, R


def run_cfg(nm, fn, q):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    pool, per = fn()
    tA = time.perf_counter() - t0
    tF = 0.0
    if nm in INLOOP or nm == "C8f":
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


def measure(setting, tag, tt, drivers, orders, q, B, reps):
    names, R = runners(setting, tt, drivers, orders, q, B)
    first = {}
    warm = {}
    for nm in names:
        pool, kp, per, tA, tF = run_cfg(nm, R[nm], q)
        warm[nm] = tA + tF
        first[nm] = (pool, kp, per)
    if warm["C1"] > 20.0:
        reps = min(reps, 5)
    T = {nm: dict(A=[], F=[]) for nm in names}
    for r in range(reps):
        for nm in (names if r % 2 == 0 else list(reversed(names))):
            _p, _k, _c, tA, tF = run_cfg(nm, R[nm], q)
            T[nm]["A"].append(tA); T[nm]["F"].append(tF)
    kref = sig(first["C1"][1])
    row = dict(tag=tag, B=B, reps=reps, setting=setting)
    tot = {}
    for nm in names:
        pool, kp, per = first[nm]
        sm = lambda k: sum(c[k] for _, c in per.values())
        tot[nm] = [a + f for a, f in zip(T[nm]["A"], T[nm]["F"])]
        row[nm] = dict(ext=sm("ext_attempts"), created=sm("labels_created"), killed_L1=sm("killed_layer1"),
                       killed_rule=sm("killed_rule"), routes_kept=sm("routes_kept"), a_evals=sm("a_evals"),
                       kstar=len(sig(kp)), kstar_equal_C1=(sig(kp) == kref),
                       tA=statistics.median(T[nm]["A"]), tF=statistics.median(T[nm]["F"]),
                       tTot=statistics.median(tot[nm]), tTot_iqr=(_pct(tot[nm], .25), _pct(tot[nm], .75)),
                       raw_A=T[nm]["A"], raw_F=T[nm]["F"])
    for nm in names:
        sp = [a / b for a, b in zip(tot["C1"], tot[nm])]
        row[nm]["speedup_vs_C1"] = statistics.median(sp)
        row[nm]["speedup_iqr"] = (_pct(sp, .25), _pct(sp, .75))
        sp5 = [a / b for a, b in zip(tot["C5"], tot[nm])]
        row[nm]["speedup_vs_C5"] = statistics.median(sp5)
        row[nm]["speedup_vs_C5_iqr"] = (_pct(sp5, .25), _pct(sp5, .75))
    print("%s %s B=%d reps=%d | " % (setting, tag, B, reps) + " | ".join(
        "%s %.3fs x%.2f(vsC1) x%.2f(vsC5) ext %d" % (nm, row[nm]["tTot"], row[nm]["speedup_vs_C1"],
                                                      row[nm]["speedup_vs_C5"], row[nm]["ext"]) for nm in names),
        "| K* equal:", all(row[nm]["kstar_equal_C1"] for nm in names))
    sys.stdout.flush()
    return row


def main():
    setting, which = sys.argv[1], sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    rows = []
    if which == "label":
        for B in (3, 4):
            for (n, nd, seed) in LABEL_INSTANCES:
                drivers, orders, tt, q = label_instance(n, nd, seed, B)
                rows.append(measure(setting, "n%d_s%d" % (n, seed), tt, drivers, orders, q, B, reps))
    else:
        for align in (0.90, 0.50):
            for rep in range(10):
                d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
                r = measure(setting, "a%.2f_rep%d" % (align, rep), tt, d, o, q, 3, reps)
                r["alignment"] = align
                rows.append(r)
    json.dump(rows, open("../audit_logs3/timing_%s_%s.json" % (setting, which), "w"), indent=1, default=str)
    print("saved ../audit_logs3/timing_%s_%s.json" % (setting, which))


main()
