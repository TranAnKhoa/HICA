"""Test3.md Viec 2 - kiem Pareto-dominance co pha completeness cua BFS khong.

Chi chay tren bo instance NHO da co ground truth (n<=6, giong grid gate cua
Test2.md Sec4.1/Sec5), dung lai t2_gen.build_instance + t2_core.brute_force.

Thuat toan BFS_PARETO (Test3.md Viec2):
    Seq[S]    = day du, giong bfs_generate goc (KHONG bi cat)
    Pareto[S] = loc Pareto tren Seq[S]
    LEVEL SAU CHI DUOC CHEN TU Pareto[P], khong phai Seq[P]

Vi Seq[S] van duoc tinh day du (chen tu Pareto[P] cua parent), completeness
cua CHINH BAN THAN Seq[S] so voi BRUTE_FORCE[S] la cau hoi can do: neu chen
tu Pareto[P] (thay vi Seq[P]) van sinh du moi sequence brute-force tim duoc,
Pareto khong pha gi ca.

VIOLATION(S) dinh nghia dung Test3.md: for each R' in BRUTE_FORCE[S], BFS_
PARETO (tuc Seq[S] duoc sinh tu Pareto[P]) phai sinh duoc it nhat 1 sequence
cung canonical(). Neu thieu, kiem tiep 1 level xa hon (S hop them 1 order j2
bat ky con lai) xem thieu sot do co lam mat mot superset kha thi hay khong -
neu co, dem violation "sau" (nghiem trong hon); neu superset van sinh du (vi
co the sinh tu nhanh khac), dem violation "nong" (sequence bi thieu o S
nhung khong lam mat completeness o superset ke tiep - dang duoc de van ghi
nhan, vi spec yeu cau bao cao ca 2 muc).
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

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test3")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL     # (4,5,6) - dung lai grid gate cua Test2
B_GRID = G.B_GRID                     # (2,3,4)
DRIVER_CLASS = G.DRIVER_CLASS
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def run_cell(rng, n, B, cls, tw, tau, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    bf, bf_stats = C.brute_force(tt, driver, orders, B)
    Seq, Pareto, sstar, pruned = C.bfs_generate_pareto(tt, driver, orders, B, use_filter=True)

    order_ids = sorted(orders.keys())
    all_subsets = {}
    for k in range(1, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            all_subsets[frozenset(S_tuple)] = k

    rows = []
    violation_sets = set()
    for S, k in all_subsets.items():
        bf_canons = set(x[0] for x in bf.get(S, []))
        pareto_canons = set(x[0] for x in Seq.get(S, []))   # Seq[S] sinh TU Pareto[P]
        missing = bf_canons - pareto_canons
        violated = len(missing) > 0
        if violated:
            violation_sets.add(S)

        seq_count = len(bf.get(S, []))     # dung brute force lam "seq_count" chuan
        # (Seq[S] cua BFS goc = bf neu khong co bug - nhung o day ta so sanh
        # Pareto-BFS voi ground truth truc tiep, seq_count = |BRUTE_FORCE[S]|)
        pareto_count = len(Pareto.get(S, []))
        ratio = (pareto_count / seq_count) if seq_count > 0 else None

        rows.append(dict(
            n=n, B=B, cls=cls, tw_width=tw, tau=tau, k=k,
            subset_id="|".join(sorted(S)),
            seq_count=seq_count, pareto_count=pareto_count,
            compression_ratio=ratio,
            violation=violated,
            violation_detail=("missing=%d/%d" % (len(missing), len(bf_canons))) if violated else "",
        ))

    # Level-further check: neu S bi violation, xem co lam mat mot superset S+j2
    # kha thi hay khong (superset ma o do Pareto-BFS[S+j2] thieu mot sequence
    # ma BRUTE_FORCE[S+j2] co, VA nguyen nhan la do thieu tu S).
    deep_violation_sets = set()
    for S in violation_sets:
        k = all_subsets[S]
        if k >= B:
            continue
        remaining = [o for o in order_ids if o not in S]
        for j2 in remaining:
            Sp = frozenset(set(S) | {j2})
            if Sp not in all_subsets:
                continue
            bf_sp = set(x[0] for x in bf.get(Sp, []))
            pareto_sp = set(x[0] for x in Seq.get(Sp, []))
            if bf_sp - pareto_sp:
                deep_violation_sets.add(S)
                break

    for row in rows:
        S = frozenset(row["subset_id"].split("|")) if row["subset_id"] else frozenset()
        row["violation_deep"] = S in deep_violation_sets

    return rows, len(violation_sets), len(deep_violation_sets), len(all_subsets)


FIELDS = ["n", "B", "cls", "tw_width", "tau", "k", "subset_id",
          "seq_count", "pareto_count", "compression_ratio",
          "violation", "violation_deep", "violation_detail"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    total_violations = 0
    total_deep_violations = 0
    total_subsets = 0
    t0 = time.time()
    cell_id = 0
    for n in N_ORDERS_SMALL:
        for B in B_GRID:
            if B > n:
                continue
            for cls in DRIVER_CLASS:
                for tw in TW_WIDTH_GRID:
                    taus = TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t3pareto"))
                            try:
                                rows, n_viol, n_deep, n_sub = run_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            all_rows.extend(rows)
                            total_violations += n_viol
                            total_deep_violations += n_deep
                            total_subsets += n_sub
                        cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs)" % (n, cell_id, time.time() - t0))

    with open(os.path.join(OUT, "pareto_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    violation_rate = total_violations / total_subsets if total_subsets else 0.0
    deep_rate = total_deep_violations / total_subsets if total_subsets else 0.0
    ratios = [r["compression_ratio"] for r in all_rows if r["compression_ratio"] is not None]
    ratios.sort()
    median_ratio = ratios[len(ratios) // 2] if ratios else None

    print("\n=== VIEC 2 SUMMARY ===")
    print("total_subsets=%d  violations=%d (%.4f%%)  deep_violations=%d (%.4f%%)"
          % (total_subsets, total_violations, violation_rate * 100,
             total_deep_violations, deep_rate * 100))
    print("median compression_ratio (pareto/seq, seq>0)=%s" % median_ratio)
    print("elapsed=%.1fs  rows=%d" % (time.time() - t0, len(all_rows)))

    with open(os.path.join(OUT, "pareto_summary.txt"), "w", encoding="utf-8") as f:
        f.write("total_subsets=%d\nviolations=%d\nviolation_rate=%.6f\n"
                "deep_violations=%d\ndeep_violation_rate=%.6f\n"
                "median_compression_ratio=%s\nelapsed_s=%.1f\nrows=%d\n"
                % (total_subsets, total_violations, violation_rate,
                   total_deep_violations, deep_rate, median_ratio,
                   time.time() - t0, len(all_rows)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
