"""Test5.md Viec 2 - so sanh do chat va chi phi UB1 vs UB2, tren CUNG grid
da chay Viec1 (doc lai gate_viec1.csv, KHONG chay lai instance - tiet kiem,
va dam bao dung CHINH XAC cung du lieu da qua gate).

Chi xet cac dong ma CA HAI deu PRUNE duoc (ub1<0 AND ub2<0) - tinh tight_ratio
va extra_prune_by_UB2 (ub2<0 nhung ub1>=0) tren TOAN BO gate_viec1.csv.

cost_ratio do RIENG bang mot lan quet timing (khong lay tu gate_viec1.csv vi
file do khong luu timing rieng UB1/UB2).

DUNG: Output/Test5/viec2_ub_compare.csv (tong hop) + in ra console.
"""

import csv
import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t5_ub as U
import t5_run_viec1 as V1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test5")
IN_CSV = os.path.join(OUT, "gate_viec1.csv")


def analyze_from_csv():
    rows = []
    with open(IN_CSV, "r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)

    n_total = len(rows)
    n_ub1_prune = 0
    n_ub2_prune = 0
    n_both_prune = 0
    n_extra_by_ub2 = 0   # ub2<0 nhung ub1>=0
    tight_ratios = []

    for row in rows:
        ub1 = float(row["ub1"])
        ub2 = float(row["ub2"])
        p1 = ub1 < 0
        p2 = ub2 < 0
        if p1:
            n_ub1_prune += 1
        if p2:
            n_ub2_prune += 1
        if p1 and p2:
            n_both_prune += 1
        if p2 and not p1:
            n_extra_by_ub2 += 1
        # tight_ratio chi tinh khi ca hai cung dau (khac 0, tranh chia 0) va
        # ca hai deu huu han (khong -inf tu thieu order)
        if ub1 != float("-inf") and ub2 != float("-inf") and ub1 != 0:
            if (ub1 > 0) == (ub2 > 0):
                tight_ratios.append(ub2 / ub1)

    return dict(
        n_total=n_total, n_ub1_prune=n_ub1_prune, n_ub2_prune=n_ub2_prune,
        n_both_prune=n_both_prune, n_extra_by_ub2=n_extra_by_ub2,
        extra_prune_rate=(n_extra_by_ub2 / n_total if n_total else 0.0),
        tight_ratios=tight_ratios,
    )


def measure_cost_ratio(n_samples=200):
    """Do rieng t(UB1) vs t(UB2) tren mot mau nho lay tu grid Viec1 (cung
    seed_from), vi gate_viec1.csv khong luu timing tung dong."""
    rng = random.Random(V1.seed_from(6, 4, "GW", 240, None, 0, "t5viec1_costsample"))
    driver, orders, tt, meta = G.build_instance(rng, V1.SESSION, 6, "GW", 240, None, 4)
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, 4, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    samples = []
    for k in range(1, 4):
        d = 4 - k
        import itertools
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            entries = seq.get(S, [])
            if not entries:
                continue
            rem = [o for o in order_ids if o not in S and o in reach_ids]
            if len(rem) < d:
                continue
            for canon, slack, walk in entries:
                _, _, sched_full = C.is_feasible(tt, driver, walk)
                gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
                samples.append((gamma, rem, d))
            if len(samples) >= n_samples:
                break
        if len(samples) >= n_samples:
            break

    t0 = time.perf_counter()
    for gamma, rem, d in samples:
        U.UB1(gamma, rem, d)
    t_ub1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    for gamma, rem, d in samples:
        U.UB2(gamma, rem, d)
    t_ub2 = time.perf_counter() - t0

    return dict(n_samples=len(samples), t_ub1=t_ub1, t_ub2=t_ub2,
                cost_ratio=(t_ub2 / t_ub1 if t_ub1 > 0 else None))


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    if not os.path.exists(IN_CSV):
        print("ERROR: %s khong ton tai - chay t5_run_viec1.py truoc." % IN_CSV)
        return 1

    stats = analyze_from_csv()
    cost = measure_cost_ratio()

    tight = stats["tight_ratios"]
    tight_median = sorted(tight)[len(tight) // 2] if tight else None

    print("=== VIEC2: UB1 vs UB2 ===")
    print("total (S,R): %d" % stats["n_total"])
    print("UB1 prune: %d (%.4f%%)" % (stats["n_ub1_prune"], 100 * stats["n_ub1_prune"] / stats["n_total"]))
    print("UB2 prune: %d (%.4f%%)" % (stats["n_ub2_prune"], 100 * stats["n_ub2_prune"] / stats["n_total"]))
    print("both prune: %d" % stats["n_both_prune"])
    print("extra_prune_by_UB2 (ub2<0, ub1>=0): %d (%.4f%% of total)"
          % (stats["n_extra_by_ub2"], 100 * stats["extra_prune_rate"]))
    print("tight_ratio median (ub2/ub1, same-sign only, n=%d): %s" % (len(tight), tight_median))
    print("cost: t_ub1=%.4fs t_ub2=%.4fs cost_ratio=%.2fx (n_samples=%d)"
          % (cost["t_ub1"], cost["t_ub2"], cost["cost_ratio"], cost["n_samples"]))

    with open(os.path.join(OUT, "viec2_ub_compare.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in stats.items():
            if k == "tight_ratios":
                continue
            w.writerow([k, v])
        w.writerow(["tight_ratio_median", tight_median])
        for k, v in cost.items():
            w.writerow([k, v])

    return 0


if __name__ == "__main__":
    sys.exit(main())
