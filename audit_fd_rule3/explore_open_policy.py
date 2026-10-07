"""EXPLORATORY (not part of the pre-planned comparison): apply Layer 3 only to labels that can still pick
up an order (|IV|+|C| < B). Labels with |IV|+|C| = B, and all their descendants, carry no shortcut
triples and are never tested. The rule may be applied to "some or all" labels (Theorem 3), so K* is
unchanged; the question is only whether testing fewer labels pays off. This policy was chosen after
seeing that 97-98% of the kills are at |IV|+|C| = B (kill_depth.py); it is reported as exploratory.
Precomputed travel-time table for every variant; 5 alternating repetitions, medians.
Writes ../audit_logs3/explore_open_policy.json."""
import gc
import json
import statistics
import time

import paths  # noqa: F401
import fastrule as FR
from variants3 import build_all
from common import label_instance, sig, LABEL_INSTANCES

SRC = open(FR.__file__).read()
OPEN_SRC = SRC.replace("""            if l.action is None:
                out.append(l)
                continue""", """            if l.action is None or len(l.IV) + len(l.Cd) >= B:
                out.append(l)
                continue""")
assert OPEN_SRC != SRC
NS = {"__name__": "fastrule_open"}
exec(compile(OPEN_SRC, "fastrule_open", "exec"), NS)
build_open = NS["build_all_fast"]


def timed(f):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    r = f()
    x = time.perf_counter() - t0
    gc.enable()
    return r, x


def main(reps=5):
    rows = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
            ttm = FR.matrix_tt(TT)
            R = {"C5": lambda: build_all("C5", ttm, drivers, orders, q, B),
                 "C8f": lambda: FR.build_all_fast(ttm, drivers, orders, q, B, (TT, KK)),
                 "C8open": lambda: build_open(ttm, drivers, orders, q, B, (TT, KK))}
            names = list(R)
            res = {}
            for nm in names:                      # warm-up, also counters and K*
                (p, per), _x = timed(R[nm])
                res[nm] = dict(t=[], ext=sum(c["ext_attempts"] for _, c in per.values()),
                               kills=sum(c["killed_rule"] for _, c in per.values()), sig=sig(p))
            for r in range(reps):
                for nm in (names if r % 2 == 0 else list(reversed(names))):
                    _r, x = timed(R[nm])
                    res[nm]["t"].append(x)
            row = dict(tag="n%d_s%d" % (n, seed), B=B, kstar_equal=res["C5"]["sig"] == res["C8f"]["sig"] == res["C8open"]["sig"])
            for nm in names:
                row[nm] = dict(t=statistics.median(res[nm]["t"]), ext=res[nm]["ext"], kills=res[nm]["kills"])
            row["C8open_vs_C5"] = statistics.median([a / b for a, b in zip(res["C5"]["t"], res["C8open"]["t"])])
            row["C8f_vs_C5"] = statistics.median([a / b for a, b in zip(res["C5"]["t"], res["C8f"]["t"])])
            rows.append(row)
            print("%-9s B=%d K*eq=%s | C5 %.3fs ext %d | C8f %.3fs ext %d kills %d (x%.2f vs C5) | "
                  "C8open %.3fs ext %d kills %d (x%.2f vs C5)" % (
                      row["tag"], B, row["kstar_equal"], row["C5"]["t"], row["C5"]["ext"], row["C8f"]["t"],
                      row["C8f"]["ext"], row["C8f"]["kills"], row["C8f_vs_C5"], row["C8open"]["t"],
                      row["C8open"]["ext"], row["C8open"]["kills"], row["C8open_vs_C5"]))
    json.dump(rows, open("../audit_logs3/explore_open_policy.json", "w"), indent=1)


main()
