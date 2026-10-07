"""Does Layer 3 start to pay off on larger instances?  The C8f/C5 ratio rose with size on the label
instances (n <= 15). Here: n = 20 instances, C5 vs C8f (rule) and C1 for reference, every variant with
the same precomputed travel-time table (the fair "matrix" setting). 3 alternating timed repetitions
after one warm-up (runs are long). Sets:
  label-style generator (as LABEL_INSTANCES): n = 20, 6 drivers, seeds 42, 7, 123; B = 3 and B = 4
  main grid: n = 20, supply (3,3), alignment 0.90, reps 0-4, B = 3
Writes ../audit_logs3/scale_c8.json."""
import gc
import json
import statistics
import sys
import time

import paths  # noqa: F401
import fastrule as FR
from variants3 import build_all
from common import label_instance, sig, kstar_pool
import rq_common as RQ


def timed(f):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    r = f()
    x = time.perf_counter() - t0
    gc.enable()
    return r, x


def measure(tag, drivers, orders, tt, q, B, reps=3, with_c1=True):
    TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
    ttm = FR.matrix_tt(TT)

    def c1():
        pool, per = build_all("C1", ttm, drivers, orders, q, B)
        return kstar_pool(pool, q), per
    R = {}
    if with_c1:
        R["C1"] = c1
    R["C5"] = lambda: build_all("C5", ttm, drivers, orders, q, B)
    R["C8f"] = lambda: FR.build_all_fast(ttm, drivers, orders, q, B, (TT, KK))
    names = list(R)
    out = {}
    for nm in names:
        (p, per), x = timed(R[nm])
        out[nm] = dict(t=[], warm=x, sig=sig(p), ext=sum(c["ext_attempts"] for _, c in per.values()),
                       kills=sum(c["killed_rule"] for _, c in per.values()))
    for r in range(reps):
        for nm in (names if r % 2 == 0 else list(reversed(names))):
            _r, x = timed(R[nm])
            out[nm]["t"].append(x)
    row = dict(tag=tag, B=B, reps=reps, kstar_equal=len(set(frozenset(out[nm]["sig"]) for nm in names)) == 1)
    for nm in names:
        row[nm] = dict(t=statistics.median(out[nm]["t"]), ext=out[nm]["ext"], kills=out[nm]["kills"],
                       raw=out[nm]["t"])
    row["C8f_vs_C5"] = statistics.median([a / b for a, b in zip(out["C5"]["t"], out["C8f"]["t"])])
    if with_c1:
        row["C5_vs_C1"] = statistics.median([a / b for a, b in zip(out["C1"]["t"], out["C5"]["t"])])
    print("%-14s B=%d K*eq=%s | " % (tag, B, row["kstar_equal"]) + " | ".join(
        "%s %.2fs ext %d" % (nm, row[nm]["t"], row[nm]["ext"]) for nm in names) +
        " | C8f x%.2f vs C5" % row["C8f_vs_C5"] + (" | C5 x%.2f vs C1" % row["C5_vs_C1"] if with_c1 else ""))
    sys.stdout.flush()
    return row


def main():
    rows = []
    for B in (3, 4):
        for seed in (42, 7, 123):
            drivers, orders, tt, q = label_instance(20, 6, seed, B)
            rows.append(measure("label n20_s%d" % seed, drivers, orders, tt, q, B, with_c1=(B == 3)))
            json.dump(rows, open("../audit_logs3/scale_c8.json", "w"), indent=1)
    for rep in range(5):
        d, o, tt, meta, th, q = RQ.make_rq1_instance(0.90, 20, 3, 3, rep, B=3)
        rows.append(measure("grid a0.90_n20_rep%d" % rep, d, o, tt, q, 3))
        json.dump(rows, open("../audit_logs3/scale_c8.json", "w"), indent=1)


main()
