"""Test4.2 - doi chung Viec 2 (compression) tai n=20, CHI 3 o trong tam cua
Test4_report.md Sec3 (khong toan bo k=1..B nhu t4_run_viec2.py goc - tiet
kiem thoi gian, chi tra loi dung cau hoi: compression co doi huong dang ke
khi m=|Rem(S)| lon hon that hay khong).

3 o: (B=4,k=3,tw=120), (B=4,k=3,tw=240), (B=3,k=2,tw=240) - GW, n=20.

DUNG: Output/Test4/compression_n20.csv
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
import t4_run_viec2 as R2

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3
N_TARGET = 20
SEEDS = R2.VIEC2_SEEDS_PER_CELL   # dung SO SEED giong Viec 2 goc (3) de so sanh cong bang

# (B, k, tw_width) - 3 o trong tam
CELLS = [(4, 3, 120), (4, 3, 240), (3, 2, 240)]


def run_cell_targeted(rng, n, B, k, tw, seed_idx):
    """Giong t4_run_viec2.run_cell nhung CHI tinh compression cho dung
    subset co |S|=k (bo qua k khac) - it viec hon."""
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, "GW", tw, None, B)
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
        if m_rem == 0:
            continue

        entries_with_gamma = []
        for canon, slack, walk in entries:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            entries_with_gamma.append((canon, walk, sched_full, gamma))

        fronts = {}
        for variant in ("D1", "D2", "D3"):
            fronts[variant] = P.filter_dominated(entries_with_gamma, rem, variant)

        rows.append(dict(
            n=n, B=B, tw_width=tw, seed=seed_idx, subset_id="|".join(sorted(S)), k=k, m_rem=m_rem,
            seq_count=seq_count,
            compression_D1=len(fronts["D1"]) / seq_count,
            compression_D2=len(fronts["D2"]) / seq_count,
            compression_D3=len(fronts["D3"]) / seq_count,
        ))
    return rows


FIELDS = ["n", "B", "tw_width", "seed", "subset_id", "k", "m_rem", "seq_count",
          "compression_D1", "compression_D2", "compression_D3"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    t0 = time.time()
    for (B, k, tw) in CELLS:
        for sd in range(SEEDS):
            rng = random.Random(R2.seed_from(N_TARGET, B, "GW", tw, None, sd, "t4viec2_n20"))
            try:
                rows = run_cell_targeted(rng, N_TARGET, B, k, tw, sd)
            except SystemExit as e:
                print("  [skip] %s" % e)
                continue
            all_rows.extend(rows)
        print("  B=%d k=%d tw=%d done, %.1fs, rows=%d" % (B, k, tw, time.time() - t0, len(all_rows)))

    with open(os.path.join(OUT, "compression_n20.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    print("\nTONG: %d rows, %.1fs" % (len(all_rows), time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
