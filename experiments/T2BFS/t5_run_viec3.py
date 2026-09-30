"""Test5.md Viec 3 - prune_rate that (con so quyet dinh). Do tren dung 3 o
trong tam (Sec3, CO CHU Y k KHAC Test4 Sec3 - Test5 co dinh d=2 xuyen suot):

  GW, B=4, k=2 (d=2), tw=120
  GW, B=4, k=2 (d=2), tw=240
  GW, B=3, k=1 (d=2), tw=240

Ca grid nho (n<=6, N_ORDERS_SMALL cua t2_gen = (4,5,6), du cho k=2/k=1 voi
B=4/B=3) VA doi chung tai n=10 (dung ly do Test4.1: 1 diem ngoai grid nho
truoc khi ket luan). Vi Viec2 da xac dinh UB1 du (extra_prune_by_UB2=0),
CHI dung UB1 o day (dung khuyen nghi Viec2, khong tinh UB2 lai cho ton kem).

DUNG: Output/Test5/viec3_prune_rate.csv
"""

import csv
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t5_ub as U
import t5_run_viec1 as V1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test5")

# (B, k, tw_width) - 3 o trong tam, d=B-k=2 xuyen suot
CELLS = [(4, 2, 120), (4, 2, 240), (3, 1, 240)]
N_ORDERS_SMALL = (4, 5, 6)   # can n>=B; B=4 can n>=4
N_ORDERS_N10 = (10,)
SEEDS_SMALL = G.SEEDS_PER_CELL       # 8, giu dung grid nho nhu Viec1
SEEDS_N10 = 3                        # doi chung, dung nhu Test4.1


def run_cell(rng, n, B, k, tw, seed_idx):
    d = B - k
    driver, orders, tt, meta = G.build_instance(rng, V1.SESSION, n, "GW", tw, None, B)
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    rows = []
    for S_tuple in itertools.combinations(order_ids, k):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        seq_count = len(entries)
        if seq_count == 0:
            continue
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        m_rem = len(rem)
        if m_rem < d:
            continue

        n_pruned = 0
        for canon, slack, walk in entries:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            ub1 = U.UB1(gamma, rem, d)
            if ub1 < 0:
                n_pruned += 1

        rows.append(dict(
            n=n, B=B, k=k, d=d, tw_width=tw, seed=seed_idx,
            subset_id="|".join(sorted(S)), m_rem=m_rem, seq_count=seq_count,
            n_pruned=n_pruned, prune_rate=n_pruned / seq_count,
        ))
    return rows


FIELDS = ["n", "B", "k", "d", "tw_width", "seed", "subset_id", "m_rem",
          "seq_count", "n_pruned", "prune_rate"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    t0 = time.time()

    for (B, k, tw) in CELLS:
        for n in N_ORDERS_SMALL:
            if n < B:
                continue
            for sd in range(SEEDS_SMALL):
                rng = random.Random(V1.seed_from(n, B, "GW", tw, None, sd, "t5viec3"))
                try:
                    rows = run_cell(rng, n, B, k, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                all_rows.extend(rows)
        for n in N_ORDERS_N10:
            for sd in range(SEEDS_N10):
                rng = random.Random(V1.seed_from(n, B, "GW", tw, None, sd, "t5viec3_n10"))
                try:
                    rows = run_cell(rng, n, B, k, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                all_rows.extend(rows)
        print("  B=%d k=%d tw=%d done, %.1fs, rows=%d" % (B, k, tw, time.time() - t0, len(all_rows)))

    with open(os.path.join(OUT, "viec3_prune_rate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    print("\n=== VIEC3 SUMMARY (median prune_rate) ===")
    for (B, k, tw) in CELLS:
        for scope, ns in (("n<=6", N_ORDERS_SMALL), ("n=10", N_ORDERS_N10)):
            vals = sorted(r["prune_rate"] for r in all_rows
                          if r["B"] == B and r["k"] == k and r["tw_width"] == tw and r["n"] in ns)
            if vals:
                med = vals[len(vals) // 2]
                print("  B=%d k=%d tw=%d [%s]: median prune_rate=%.4f (n=%d subsets)"
                      % (B, k, tw, scope, med, len(vals)))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
