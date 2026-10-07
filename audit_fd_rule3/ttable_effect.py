"""Implementation detail for the final Algorithm A: what does a precomputed travel-time table buy?
The generator's travel_time(a, b) recomputes a Euclidean distance at every call. A table built once per
instance returns bit-identical values (same function, evaluated once per pair). Interleaved timing of
C1 (+ post-hoc frontier) and C5 with the function, and C5 with the table (C5t); table construction is
counted inside C5t. Every entry is the time to K*.
10 alternating repetitions (5 if a C1 run exceeds 20 s). Writes ../audit_logs3/ttable_effect.json."""
import gc
import json
import statistics
import time

import paths  # noqa: F401
import fastrule as FR
from variants3 import build_all
from common import label_instance, sig, kstar_pool, LABEL_INSTANCES


def timed(f):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    r = f()
    x = time.perf_counter() - t0
    gc.enable()
    return r, x


def main(reps=10):
    rows = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)

            def c5t():
                TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
                return build_all("C5", FR.matrix_tt(TT), drivers, orders, q, B)
            def c1_total():
                pool, per = build_all("C1", tt, drivers, orders, q, B)
                return kstar_pool(pool, q), per
            R = {"C1": c1_total,
                 "C5": lambda: build_all("C5", tt, drivers, orders, q, B),
                 "C5t": c5t}
            names = list(R)
            out = {}
            for nm in names:
                (p, per), x = timed(R[nm])
                out[nm] = dict(t=[], sig=sig(p), warm=x)
            r_ = 5 if out["C1"]["warm"] > 20 else reps
            for r in range(r_):
                for nm in (names if r % 2 == 0 else list(reversed(names))):
                    _r, x = timed(R[nm])
                    out[nm]["t"].append(x)
            # every entry is the time to K*: C1 includes its post-hoc frontier, C5/C5t compute it in the loop
            row = dict(tag="n%d_s%d" % (n, seed), B=B, reps=r_,
                       same_output=out["C1"]["sig"] == out["C5"]["sig"] == out["C5t"]["sig"])
            for nm in names:
                row[nm] = statistics.median(out[nm]["t"])
            row["C5t_vs_C5"] = statistics.median([a / b for a, b in zip(out["C5"]["t"], out["C5t"]["t"])])
            row["C5t_vs_C1"] = statistics.median([a / b for a, b in zip(out["C1"]["t"], out["C5t"]["t"])])
            rows.append(row)
            print("%-9s B=%d same=%s | C1 %.3fs | C5 %.3fs | C5t %.3fs | C5t x%.2f vs C5, x%.2f vs C1 (time to K*)"
                  % (row["tag"], B, row["same_output"], row["C1"], row["C5"], row["C5t"], row["C5t_vs_C5"],
                     row["C5t_vs_C1"]))
    json.dump(rows, open("../audit_logs3/ttable_effect.json", "w"), indent=1)


main()
