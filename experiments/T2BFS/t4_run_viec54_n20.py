"""Test4.2 - diem thu 3 (n=20) cho Sec5.4, tiep noi Test4.1 (n=10). Muc tieu:
activation_rate co tiep tuc giam qua nguong 10% khi m=|Rem(S)| lon hon nua
hay dang on dinh - can >=3 diem (n<=6, n=10, n=20) de khop duong cong.

Tai su dung LOGIC goc t4_run_viec54.run_cell (khong sua) nhung goi lai o
day voi mot ban sao co ghi them m_rem (=|Rem(S)|) cho tung subset S, de
CSV co the group theo m thay vi chi theo n. Cung 3 o trong tam / cau hinh
seed nhu t4_run_viec54_n10.py: GW, B=4, k=2, tw_width in {120,240}, 8 seed.

DUNG: Output/Test4/activation_rate_n20.csv (per-seed) va
      Output/Test4/activation_rate_n20_by_m.csv (per-subset, co cot m_rem)
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
import t4_run_viec54 as R54

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3
N_TARGET = 20
TW_TARGET = (120, 240)
SEEDS_PER_CELL = R54.SEEDS_PER_CELL
B_FIXED = R54.B_FIXED
D_MAX = R54.D_MAX


def run_cell_with_m(rng, n, tw, seed_idx):
    """Ban sao cua R54.run_cell, GIU NGUYEN toan bo logic tinh
    activation (khong doi cong thuc/threshold), chi THEM: ghi lai m_rem
    va (pairs_total, pairs_activated) THEO TUNG SUBSET S rieng, thay vi
    chi cong don toan bo instance nhu ban goc."""
    B = B_FIXED
    cls = "GW"
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, None, B)
    order_ids = sorted(orders.keys())
    start, pd, home = C.build_walk_nodes(driver, orders)
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)

    n_pairs_total = 0
    n_pairs_activated = 0
    per_subset_rows = []

    for S_tuple in itertools.combinations(order_ids, 2):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        if len(entries) < 2:
            continue
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        if not rem:
            continue
        m_rem = len(rem)

        T_list = []
        for tsize in range(1, D_MAX + 1):
            T_list.extend(itertools.combinations(rem, tsize))

        walks = [w for c, s, w in entries]
        gammas = []
        for walk in walks:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            gammas.append(gamma)

        sub_total = 0
        sub_activated = 0
        for ia in range(len(walks)):
            for ib in range(len(walks)):
                if ia == ib:
                    continue
                sub_total += 1
                activated = True
                for T in T_list:
                    Tset = frozenset(T)
                    ub_b = R54.UB_of(gammas[ib], Tset)
                    lb_a = R54.LB_greedy(tt, driver, walks[ia], pd, Tset)
                    if not (lb_a >= ub_b - 1e-9):
                        activated = False
                        break
                if activated:
                    sub_activated += 1

        n_pairs_total += sub_total
        n_pairs_activated += sub_activated
        per_subset_rows.append(dict(
            n=n, B=B, tw_width=tw, seed=seed_idx, subset_id="|".join(sorted(S)),
            m_rem=m_rem, pairs_total=sub_total, pairs_activated=sub_activated,
        ))

    return n_pairs_total, n_pairs_activated, per_subset_rows


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    by_m_rows = []
    t0 = time.time()
    total_pairs = 0
    total_activated = 0
    for tw in TW_TARGET:
        for sd in range(SEEDS_PER_CELL):
            rng = random.Random(R54.seed_from(N_TARGET, B_FIXED, "GW", tw, None, sd, "t4viec54_n10"))
            try:
                n_total, n_act, sub_rows = run_cell_with_m(rng, N_TARGET, tw, sd)
            except SystemExit as e:
                print("  [skip] %s" % e)
                continue
            total_pairs += n_total
            total_activated += n_act
            by_m_rows.extend(sub_rows)
            rows.append(dict(n=N_TARGET, B=B_FIXED, tw_width=tw, seed=sd,
                              pairs_total=n_total, pairs_activated=n_act,
                              activation_rate=(n_act / n_total) if n_total else None))
            print("  tw=%d seed=%d done, %.1fs, pairs=%d activated=%d"
                  % (tw, sd, time.time() - t0, total_pairs, total_activated))

    with open(os.path.join(OUT, "activation_rate_n20.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "seed", "pairs_total",
                                           "pairs_activated", "activation_rate"])
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(OUT, "activation_rate_n20_by_m.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "seed", "subset_id",
                                           "m_rem", "pairs_total", "pairs_activated"])
        w.writeheader()
        w.writerows(by_m_rows)

    rate = total_activated / total_pairs if total_pairs else 0.0
    print("\n=== SEC5.4 @ n=20 SUMMARY ===")
    print("total pairs (Ra,Rb): %d, activated: %d, activation_rate=%.4f%%"
          % (total_pairs, total_activated, rate * 100))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
