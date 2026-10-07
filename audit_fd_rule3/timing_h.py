"""Timing of the dead-end filter: C1 vs C5 vs C5h (= C5 + dead-end filter) vs C8h (= C5h + Layer 3).

Usage: python timing_h.py <setting> <set> [reps]
  setting = orig   : every variant uses the generator's travel_time function; C8h builds its rule tables
                     inside its own timed region.
            matrix : every variant uses one precomputed travel-time table (built once per instance, outside
                     the timed region); C8h reads the same table.
  set     = label  : five label instances, B = 3 and 4
            grid   : main-grid sample, n = 15, supply (3,3), alignment 0.90 / 0.50, reps 0-9, B = 3
            scale  : n = 20: label-style seeds 42, 7, 123 at B = 3 and 4 (C1 only at B = 3), and main grid
                     alignment 0.90, reps 0-4, B = 3; 3 repetitions
Protocol as timing_c8.py (warm-up, alternating order, gc disabled, 5 repetitions if a C1 run exceeds 20 s).
Every entry is the time to K* (post-hoc frontier included for C1).
"""
import gc
import json
import statistics
import sys
import time

import paths  # noqa: F401
import fastrule as FR
import variants_h as VH
from variants_h import build_all
from common import label_instance, sig, kstar_pool
import rq_common as RQ
from common import LABEL_INSTANCES


def runners(setting, tt, drivers, orders, q, B, with_c1=True):
    if setting == "orig":
        f = tt

        def c8h():
            TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
            return VH.build_all_c8h(tt, drivers, orders, q, B, (TT, KK))
    else:
        TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
        f = FR.matrix_tt(TT)

        def c8h():
            return VH.build_all_c8h(f, drivers, orders, q, B, (TT, KK))

    def c1():
        pool, per = build_all("C1", f, drivers, orders, q, B)
        return kstar_pool(pool, q), per
    R = {}
    if with_c1:
        R["C1"] = c1
    R["C5"] = lambda: build_all("C5", f, drivers, orders, q, B)
    R["C5h"] = lambda: build_all("C5h", f, drivers, orders, q, B)
    R["C8h"] = c8h
    return list(R), R


def timed(fn):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    r = fn()
    x = time.perf_counter() - t0
    gc.enable()
    return r, x


def _pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def measure(setting, tag, tt, drivers, orders, q, B, reps, with_c1=True):
    names, R = runners(setting, tt, drivers, orders, q, B, with_c1)
    first, warm = {}, {}
    for nm in names:
        (p, per), x = timed(R[nm])
        first[nm] = (p, per)
        warm[nm] = x
    if with_c1 and warm["C1"] > 20.0:
        reps = min(reps, 5)
    T = {nm: [] for nm in names}
    for r in range(reps):
        for nm in (names if r % 2 == 0 else list(reversed(names))):
            _r, x = timed(R[nm])
            T[nm].append(x)
    ref = sig(first["C5"][0])
    row = dict(tag=tag, B=B, reps=reps, setting=setting)
    for nm in names:
        p, per = first[nm]
        sm = lambda k: sum(c.get(k, 0) for _, c in per.values())
        row[nm] = dict(t=statistics.median(T[nm]), t_iqr=(_pct(T[nm], .25), _pct(T[nm], .75)), raw=T[nm],
                       ext=sm("ext_attempts"), dead=sm("killed_dead"), rule=sm("killed_rule"),
                       ext_OD=sum(c["ext_attempts"] for cl, c in per.values() if cl == "OD"),
                       kstar_equal=(sig(p) == ref))
    for nm in names:
        row[nm]["x_vs_C5"] = statistics.median([a / b for a, b in zip(T["C5"], T[nm])])
        row[nm]["x_vs_C5_iqr"] = (_pct([a / b for a, b in zip(T["C5"], T[nm])], .25),
                                  _pct([a / b for a, b in zip(T["C5"], T[nm])], .75))
        if with_c1:
            row[nm]["x_vs_C1"] = statistics.median([a / b for a, b in zip(T["C1"], T[nm])])
    print("%s %-18s B=%d reps=%d | " % (setting, tag, B, reps) + " | ".join(
        "%s %.3fs ext %d%s x%.2f vs C5" % (nm, row[nm]["t"], row[nm]["ext"],
                                         (" x%.2f vs C1" % row[nm]["x_vs_C1"]) if with_c1 else "",
                                         row[nm]["x_vs_C5"]) for nm in names),
        "| K* equal:", all(row[nm]["kstar_equal"] for nm in names))
    sys.stdout.flush()
    return row


def main():
    setting, which = sys.argv[1], sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    rows = []
    path = "../audit_logs3/timing_h_%s_%s.json" % (setting, which)
    if which == "label":
        for B in (3, 4):
            for (n, nd, seed) in LABEL_INSTANCES:
                d, o, tt, q = label_instance(n, nd, seed, B)
                rows.append(measure(setting, "n%d_s%d" % (n, seed), tt, d, o, q, B, reps))
    elif which == "grid":
        for align in (0.90, 0.50):
            for rep in range(10):
                d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
                r = measure(setting, "a%.2f_rep%d" % (align, rep), tt, d, o, q, 3, reps)
                r["alignment"] = align
                rows.append(r)
    else:
        for B in (3, 4):
            for seed in (42, 7, 123):
                d, o, tt, q = label_instance(20, 6, seed, B)
                rows.append(measure(setting, "label n20_s%d" % seed, tt, d, o, q, B, reps, with_c1=(B == 3)))
                json.dump(rows, open(path, "w"), indent=1, default=str)
        for rep in range(5):
            d, o, tt, meta, th, q = RQ.make_rq1_instance(0.90, 20, 3, 3, rep, B=3)
            r = measure(setting, "grid a0.90_n20_rep%d" % rep, tt, d, o, q, 3, reps)
            r["alignment"] = 0.90
            rows.append(r)
    json.dump(rows, open(path, "w"), indent=1, default=str)
    print("saved " + path)


main()
