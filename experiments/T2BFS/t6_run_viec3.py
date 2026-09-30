"""Test6.md Viec 3 - CHI chay neu Viec2 cho tin hieu nen tot. Do wall-clock
that: t_DP vs t_BFS_current (Test2/t2_core.bfs_generate) TREN CUNG instance,
tai n<=6 (doi chung) VA n=10, n=15 (theo bai hoc Test4.1 - khong tin so do o
n nho).

DUNG: Output/Test6/viec3_speedup.csv
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t6_dp as D
import t6_run_gate1 as G1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")

B_FIXED = 4
TW_TARGET = (120, 240)
N_ORDERS_SMALL = (4, 5, 6)
N_ORDERS_BIG = (10, 15)
SEEDS_SMALL = G.SEEDS_PER_CELL
SEEDS_BIG = 3   # theo tien le Test4.1


def run_cell(rng, n, tw, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, G1.SESSION, n, "GW", tw, None, B_FIXED)

    t0 = time.perf_counter()
    dp_result = D.run_dp(tt, driver, orders, B_FIXED, use_dominance=True)
    t_dp = time.perf_counter() - t0

    t0 = time.perf_counter()
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B_FIXED, use_filter=True)
    t_bfs = time.perf_counter() - t0

    return dict(
        n=n, B=B_FIXED, tw_width=tw, seed=seed_idx,
        t_dp_s=t_dp, t_bfs_s=t_bfs,
        speedup=(t_bfs / t_dp if t_dp > 0 else None),
    )


FIELDS = ["n", "B", "tw_width", "seed", "t_dp_s", "t_bfs_s", "speedup"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    t0 = time.time()
    for tw in TW_TARGET:
        for n in N_ORDERS_SMALL:
            for sd in range(SEEDS_SMALL):
                rng = random.Random(G1.seed_from(n, B_FIXED, "GW", tw, None, sd, "t6viec3"))
                try:
                    row = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                rows.append(row)
        for n in N_ORDERS_BIG:
            for sd in range(SEEDS_BIG):
                rng = random.Random(G1.seed_from(n, B_FIXED, "GW", tw, None, sd, "t6viec3_big"))
                try:
                    row = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                rows.append(row)
                print("  n=%d tw=%d seed=%d done, t_dp=%.3fs t_bfs=%.3fs speedup=%.2fx"
                      % (n, tw, sd, row["t_dp_s"], row["t_bfs_s"], row["speedup"] or 0))
        print("  tw=%d done, %.1fs, rows=%d" % (tw, time.time() - t0, len(rows)))

    with open(os.path.join(OUT, "viec3_speedup.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print("\n=== VIEC3 SUMMARY ===")
    for n in N_ORDERS_SMALL + N_ORDERS_BIG:
        vals = [r["speedup"] for r in rows if r["n"] == n and r["speedup"] is not None]
        if vals:
            med = sorted(vals)[len(vals) // 2]
            print("  n=%d: median speedup=%.2fx (samples=%d)" % (n, med, len(vals)))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
