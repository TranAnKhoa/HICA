"""Test4.md Sec5.4 - Rule an toan thay the (chi chay vi Viec4 da ra >1%):
LB_Ra(T) >= UB_Rb(T)  =>  R_b xoa duoc, ∀T subset Rem(S), |T|<=d.

UB_R(T) = min_{j in T} sigma_j(R)          (san co qua compute_gamma)
LB_R(T) = slack cua 1 nhan chung GREEDY: chen LAN LUOT tung order trong T
          vao R, MOI BUOC chon vi tri maximin slack (tuc vi tri (a,b) cho
          slack CUA CA WALK MOI lon nhat trong so cac vi tri hop le).

Do DUY NHAT activation_rate = % cap (R_a, R_b) ma rule kich hoat, tai
GW, B=4, k=2, tw_width in {120,240} (dung spec Sec5.4).

DUNG: Output/Test4/activation_rate.csv (1 dong/instance) + in tong ket.
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

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL
SEEDS_PER_CELL = G.SEEDS_PER_CELL
B_FIXED = 4
TW_TARGET = (120, 240)
D_MAX = 2   # d = B - k = 4 - 2 = 2


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def _insert_positions_walk(walk, has_home):
    upper = len(walk) - 1 if has_home else len(walk)
    return range(1, upper + 1)


def _best_insert_maximin_slack(travel_time, driver, walk, p, d):
    """Chen (pickup p, delivery d) vao walk tai vi tri (a,b) HOP LE cho
    slack(walk_moi) LON NHAT (maximin). Tra (walk_moi, slack) hoac
    (None, -inf) neu khong chen duoc vi tri nao."""
    has_home = walk[-1].kind == "home"
    best_walk = None
    best_slack = float("-inf")
    for a in _insert_positions_walk(walk, has_home):
        R1 = walk[:a] + [p] + walk[a:]
        for b in _insert_positions_walk(R1, has_home):
            if b <= a:
                continue
            R2 = R1[:b] + [d] + R1[b:]
            ok, slack, sched = C.is_feasible(travel_time, driver, R2)
            if ok and slack > best_slack:
                best_slack = slack
                best_walk = R2
    return best_walk, best_slack


def LB_greedy(travel_time, driver, walk, pd, T):
    """LB_R(T): chen LAN LUOT tung order trong T (theo 1 thu tu CO DINH -
    sorted(T), deterministic khong doc bid), moi buoc maximin slack. Neu
    bat ky buoc nao khong chen duoc, LB = -inf (chan tren vo dung - qua an
    toan, KHONG kich hoat rule, dung huong)."""
    cur = walk
    for j in sorted(T):
        p, d = pd[j]
        cur, slack = _best_insert_maximin_slack(travel_time, driver, cur, p, d)
        if cur is None:
            return float("-inf")
    return slack


def UB_of(gamma, T):
    """UB_R(T) = min_{j in T} sigma_j(R), sigma_j = max slack trong A_j(R)."""
    vals = []
    for j in T:
        vals.append(P.sigma_j(gamma.get(j, [])))
    return min(vals) if vals else float("inf")


def run_cell(rng, n, tw, seed_idx):
    B = B_FIXED
    cls = "GW"
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, None, B)
    order_ids = sorted(orders.keys())
    start, pd, home = C.build_walk_nodes(driver, orders)
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)

    n_pairs_total = 0
    n_pairs_activated = 0

    for S_tuple in itertools.combinations(order_ids, 2):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        if len(entries) < 2:
            continue
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        if not rem:
            continue

        # tap T can xet: |T|<=D_MAX, T subset rem
        T_list = []
        for tsize in range(1, D_MAX + 1):
            T_list.extend(itertools.combinations(rem, tsize))

        walks = [w for c, s, w in entries]
        gammas = []
        for walk in walks:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            gammas.append(gamma)

        for ia in range(len(walks)):
            for ib in range(len(walks)):
                if ia == ib:
                    continue
                n_pairs_total += 1
                activated = True
                for T in T_list:
                    Tset = frozenset(T)
                    ub_b = UB_of(gammas[ib], Tset)
                    lb_a = LB_greedy(tt, driver, walks[ia], pd, Tset)
                    if not (lb_a >= ub_b - 1e-9):
                        activated = False
                        break
                if activated:
                    n_pairs_activated += 1

    return n_pairs_total, n_pairs_activated


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    t0 = time.time()
    total_pairs = 0
    total_activated = 0
    for n in N_ORDERS_SMALL:
        if n < B_FIXED:
            continue
        for tw in TW_TARGET:
            for sd in range(SEEDS_PER_CELL):
                rng = random.Random(seed_from(n, B_FIXED, "GW", tw, None, sd, "t4viec54"))
                try:
                    n_total, n_act = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                total_pairs += n_total
                total_activated += n_act
                rows.append(dict(n=n, B=B_FIXED, tw_width=tw, seed=sd,
                                  pairs_total=n_total, pairs_activated=n_act,
                                  activation_rate=(n_act / n_total) if n_total else None))
        print("  n=%d done, %.1fs, pairs=%d activated=%d" % (n, time.time() - t0, total_pairs, total_activated))

    with open(os.path.join(OUT, "activation_rate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "seed", "pairs_total",
                                           "pairs_activated", "activation_rate"])
        w.writeheader()
        w.writerows(rows)

    rate = total_activated / total_pairs if total_pairs else 0.0
    print("\n=== SEC5.4 SUMMARY ===")
    print("total pairs (Ra,Rb): %d, activated: %d, activation_rate=%.4f%%"
          % (total_pairs, total_activated, rate * 100))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
