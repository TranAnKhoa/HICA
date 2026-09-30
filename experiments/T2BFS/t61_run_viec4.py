"""Test6.1.md Viec 4 (TUY CHON) - doi chung B=5, n in {5,6,7}, GW only.
Gate 1 (A/B/C) tai B=5, va do n_states_visited so voi tran ly thuyet
Sigma_{k=0}^{5} C(m,k)*2^k (m~n, uoc luong tho).

Khong bat buoc pass de Test6.1 ket luan thanh cong - thong tin bo sung.

DUNG: Output/Test6/viec4_B5_optional.csv
"""

import csv
import itertools
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t6_dp as D
import t6_run_gate1 as G1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")

# SAI LECH CONG KHAI (Viec 4 la TUY CHON, xem Test6.1.md Sec4 - khong chan
# ket luan chinh): brute_force() o B=5 la factorial tren (2*B)=10 phan tu -
# do that: n=5 mat 8.5s, n=6 mat 119s, n=7 mat 821s (~13.7 phut) CHO 1
# INSTANCE DUY NHAT. Chay het n in {5,6,7} x 4 tw x 8 seed se mat hang chuc
# gio - qua dat cho 1 phan TUY CHON. Gioi han: CHI n=5 (re, 8.5s/instance),
# CHI 2 tw (120,240), CHI 4 seed - du de co tin hieu bo sung ma khong chan
# tien do Test6.1 (da PASS Viec 1-3 bat buoc).
N_ORDERS = (5,)
B_TARGET = 5
TW_WIDTH_GRID = (120, 240)
SEEDS_PER_CELL = 4
EPS = 1e-6


def theoretical_upper(m, B):
    return sum(math.comb(m, k) * (2 ** k) for k in range(0, B + 1))


def run_cell(rng, n, tw, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, G1.SESSION, n, "GW", tw, None, B_TARGET)
    order_ids = sorted(orders.keys())
    start, pd, home = C.build_walk_nodes(driver, orders)
    reach_ids = P.reachable_orders(driver, tt, pd, order_ids)
    m = len(reach_ids)

    bf, bf_stats = C.brute_force(tt, driver, orders, B_TARGET)
    dp_result = D.run_dp(tt, driver, orders, B_TARGET, use_dominance=True)

    violations = []
    for k in range(1, B_TARGET + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            truth_entries = bf.get(S, [])
            truth_exists = len(truth_entries) > 0
            dp_labels = dp_result["complete_by_C"].get(S, [])
            dp_exists = len(dp_labels) > 0
            if truth_exists != dp_exists:
                violations.append(dict(S=sorted(S), issue="EXISTENCE_MISMATCH",
                                        truth_exists=truth_exists, dp_exists=dp_exists))
                continue
            if not truth_exists:
                continue
            truth_kw = []
            for canon, slack, walk in truth_entries:
                ok, slack2, sched = C.is_feasible(tt, driver, walk)
                K, W = P.K_W_of_route(driver, tt, walk, sched)
                truth_kw.append((K, W))
            dp_kw = [D.finalize_KW(driver, lab) for lab in dp_labels]

            def pareto(pts):
                keep = []
                for i, (K, W) in enumerate(pts):
                    dominated = False
                    for j, (K2, W2) in enumerate(pts):
                        if i == j:
                            continue
                        if K2 <= K + EPS and W2 <= W + EPS and (K2 < K - EPS or W2 < W - EPS):
                            dominated = True
                            break
                    if not dominated:
                        keep.append((K, W))
                return keep

            truth_pareto = pareto(truth_kw)
            dp_pareto = pareto(dp_kw)
            for (Kt, Wt) in truth_pareto:
                if not any(Kd <= Kt + EPS and Wd <= Wt + EPS for (Kd, Wd) in dp_pareto):
                    violations.append(dict(S=sorted(S), issue="TRUTH_MISSING", point=(Kt, Wt)))
            for (Kd, Wd) in dp_pareto:
                if not any(Kt <= Kd + EPS and Wt <= Wd + EPS for (Kt, Wt) in truth_pareto):
                    violations.append(dict(S=sorted(S), issue="DP_NOT_IN_TRUTH", point=(Kd, Wd)))

    theo_upper = theoretical_upper(m, B_TARGET)
    return dict(
        n=n, B=B_TARGET, tw_width=tw, seed=seed_idx, m_reach=m,
        n_states_created=dp_result["n_labels_created"],
        n_states_survived=dp_result["n_labels_survived"],
        theoretical_upper=theo_upper,
        ratio_survived_over_theo=(dp_result["n_labels_survived"] / theo_upper if theo_upper else None),
        n_violations=len(violations),
    ), violations


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    all_violations = []
    t0 = time.time()
    for n in N_ORDERS:
        for tw in TW_WIDTH_GRID:
            for sd in range(SEEDS_PER_CELL):
                rng = random.Random(G1.seed_from(n, B_TARGET, "GW", tw, None, sd, "t61viec4"))
                try:
                    row, violations = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                rows.append(row)
                if violations:
                    print("!!! B=5 VIOLATION n=%d tw=%d seed=%d: %d" % (n, tw, sd, len(violations)))
                    for v in violations[:5]:
                        print("    ", v)
                    all_violations.extend([dict(n=n, tw=tw, seed=sd, **v) for v in violations])
        print("  n=%d done, %.1fs, rows=%d" % (n, time.time() - t0, len(rows)))

    with open(os.path.join(OUT, "viec4_B5_optional.csv"), "w", newline="", encoding="utf-8") as f:
        fields = ["n", "B", "tw_width", "seed", "m_reach", "n_states_created",
                   "n_states_survived", "theoretical_upper", "ratio_survived_over_theo", "n_violations"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    n_total_viol = sum(r["n_violations"] for r in rows)
    print("\n=== VIEC4 (B=5, tuy chon) SUMMARY ===")
    print("instances: %d, total violations: %d" % (len(rows), n_total_viol))
    if rows:
        avg_ratio = sum(r["ratio_survived_over_theo"] for r in rows if r["ratio_survived_over_theo"]) / len(rows)
        print("avg ratio survived/theoretical_upper: %.6f" % avg_ratio)
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0 if n_total_viol == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
