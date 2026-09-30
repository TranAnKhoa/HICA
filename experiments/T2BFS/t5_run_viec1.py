"""Test5.md Viec 1 - Gate exactness BAT BUOC cho UB1_R(d) va UB2_R(d): rule
"XOA R neu UB<0" TUYET DOI khong duoc xoa nham 1 route thuc su cuu duoc.

actually_survives(S,R,d) = BRUTE FORCE: co ton tai >=1 to hop d order tu
Rem(S) va 1 cach CHEN TUAN TU (route sau bien doi lam nen cho chen tiep theo -
Sec1.1, KHONG chen song song vao R goc) khien ket qua kha thi (slack>=0)?

Dung t4_run_viec4.bfs_from_front lam dong co chen tuan tu (DA la BFS level-
wise dung logic cua bfs_generate goc, KHONG viet lai insertion tu dau - dung
canh bao Sec1.1/Sec7.3), bat dau tu front = {S: [R]} (chi 1 route duy nhat),
sinh toi |S|+d, roi kiem bat ky S' (|S'|=|S|+d, S subset S') co ket qua khong
rong hay khong.

Grid Viec 1 (Sec5): n_orders in {3,4,5,6} (khac N_ORDERS_SMALL cua t2_gen la
(4,5,6) - Test5 can them n=3 vi B=3,k=1,d=2 dung duoc voi n=3), B in {3,4},
tw_width in {30,60,120,240}, SEEDS_PER_CELL=8, class=GW (trong tam, Sec5).

DUNG: Output/Test5/gate_viec1.csv
"""

import csv
import hashlib
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t4_run_viec4 as V4
import t5_ub as U

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test5")
SESSION = 5

N_ORDERS_VIEC1 = (3, 4, 5, 6)
B_GRID = (3, 4)
TW_WIDTH_GRID = G.TW_WIDTH_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL
CLS = "GW"


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def actually_survives(tt, driver, pd, order_ids, S, walk, rem, d):
    """True neu TON TAI >=1 to hop d order tu rem va 1 chuoi chen TUAN TU
    khien ket qua kha thi. Dung bfs_from_front (dong co BFS goc), chi giu
    walk lam front duy nhat cua S, sinh toi |S|+d, kiem bat ky S' dich co
    entry khong rong."""
    target_k = len(S) + d
    gen = V4.bfs_from_front(tt, driver, pd, [walk], S, order_ids, target_k)
    for Sp_tuple in itertools.combinations(rem, d):
        Sp = frozenset(set(S) | set(Sp_tuple))
        if gen.get(Sp):
            return True
    return False


def run_cell(rng, n, B, tw, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, CLS, tw, None, B)
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    rows = []
    for k in range(1, B):   # d = B-k >= 1, nen k <= B-1
        d = B - k
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            entries = seq.get(S, [])
            if not entries:
                continue
            rem = [o for o in order_ids if o not in S and o in reach_ids]
            if len(rem) < d:
                continue   # khong du order de chen du d, ca UB va thuc te deu -inf/False, bo qua

            for canon, slack, walk in entries:
                _, _, sched_full = C.is_feasible(tt, driver, walk)
                gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)

                ub1 = U.UB1(gamma, rem, d)
                ub2 = U.UB2(gamma, rem, d)
                survives = actually_survives(tt, driver, pd, order_ids, S, walk, rem, d)

                viol1 = (ub1 < 0) and survives
                viol2 = (ub2 < 0) and survives

                rows.append(dict(
                    n=n, B=B, tw_width=tw, seed=seed_idx, subset_id="|".join(sorted(S)),
                    k=k, d=d, m_rem=len(rem), route_canon=str(canon),
                    ub1=ub1, ub2=ub2, actually_survives=survives,
                    violation_UB1=viol1, violation_UB2=viol2,
                ))
                if viol1 or viol2:
                    print("!!! VIOLATION n=%d B=%d tw=%d seed=%d S=%s d=%d ub1=%.4f ub2=%.4f survives=%s"
                          % (n, B, tw, seed_idx, sorted(S), d, ub1, ub2, survives))
                    print("    walk:", canon)
                    print("    rem:", rem)
    return rows


FIELDS = ["n", "B", "tw_width", "seed", "subset_id", "k", "d", "m_rem", "route_canon",
          "ub1", "ub2", "actually_survives", "violation_UB1", "violation_UB2"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    t0 = time.time()
    for n in N_ORDERS_VIEC1:
        for B in B_GRID:
            if n < B:
                continue
            for tw in TW_WIDTH_GRID:
                for sd in range(SEEDS_PER_CELL):
                    rng = random.Random(seed_from(n, B, CLS, tw, None, sd, "t5viec1"))
                    try:
                        rows = run_cell(rng, n, B, tw, sd)
                    except SystemExit as e:
                        print("  [skip] %s" % e)
                        continue
                    all_rows.extend(rows)
        print("  n=%d done, %.1fs, rows=%d" % (n, time.time() - t0, len(all_rows)))

    with open(os.path.join(OUT, "gate_viec1.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    n_total = len(all_rows)
    n_v1 = sum(1 for r in all_rows if r["violation_UB1"])
    n_v2 = sum(1 for r in all_rows if r["violation_UB2"])
    print("\n=== VIEC1 GATE SUMMARY ===")
    print("total (S,R) checked: %d" % n_total)
    print("violation_UB1: %d, violation_UB2: %d" % (n_v1, n_v2))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
