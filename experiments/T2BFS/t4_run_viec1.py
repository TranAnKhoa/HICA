"""Test4.md Viec 1 - Gate exactness tai d=1 (k=B-1), cho ca D1/D2/D3.

DUNG: Output/Test4/exactness_d1.csv

DUNG: neu D2 hoac D3 fail Gate 1.A hoac 1.B -> in phan vi du day du, dung
TOAN BO Test4 (khong chay Viec 2).
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
import t3_check_k1 as K1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL
B_GRID = G.B_GRID
DRIVER_CLASS = G.DRIVER_CLASS
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL

EPS = 1e-9


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def pareto_front_KW(points):
    """points: list of (K,W). Tra Pareto-front (khong bi dominate boi diem
    khac trong CHINH points nay) theo (K,W), ca hai chieu MIN."""
    front = []
    for i, (K, W) in enumerate(points):
        dominated = False
        for jx, (K2, W2) in enumerate(points):
            if i == jx:
                continue
            if K2 <= K + EPS and W2 <= W + EPS and (K2 < K - EPS or W2 < W - EPS):
                dominated = True
                break
        if not dominated:
            front.append((K, W))
    return front


def run_cell(rng, n, B, cls, tw, tau, seed_idx):
    """Tra list[dict] (1 dong/subset S, |S|=B-1) + so bug/violation."""
    if B < 2:
        return [], [], 0   # k=B-1=0 vo nghia

    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    if cls == "OD":
        rate, ok = K1.check_and_warn(driver, orders, tt,
            label="n=%d B=%d %s tw=%d tau=%s seed=%d" % (n, B, cls, tw, tau, seed_idx))
        if not ok:
            return [], [], 0

    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    k = B - 1
    rows = []
    n_bundle_loss = 0
    n_pareto_loss = 0
    violations = []

    for S_tuple in itertools.combinations(order_ids, k):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        if not entries:
            continue
        # Rem(S) dung dinh nghia Test4.md Sec0.3: CHI order reachable-don-le,
        # KHONG PHAI toan bo order con lai (voi OD, phan lon order khong
        # reachable don le - xem Test3 - dua vao Rem sai se lam m qua lon
        # va tinh Gamma cho nhung order chac chan khong chen duoc).
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        if not rem:
            continue

        # Gamma(R) cho moi R trong Seq_full
        entries_with_gamma = []
        for canon, slack, walk in entries:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            entries_with_gamma.append((canon, walk, sched_full, gamma))

        seq_count = len(entries_with_gamma)
        fronts = {}
        for variant in ("D1", "D2", "D3"):
            fronts[variant] = P.filter_dominated(entries_with_gamma, rem, variant)

        # sinh level B tu moi nguon (Seq_full + 3 front), cho MOI j in rem
        bundle_loss = {"D1": False, "D2": False, "D3": False}
        pareto_loss = {"D1": False, "D2": False, "D3": False}
        detail = {"D1": None, "D2": None, "D3": None}

        for j in rem:
            Sp = frozenset(set(S) | {j})
            # bundles/pareto tu Seq_full (ground truth cho gate nay - KHONG
            # can brute force rieng, vi Seq_full CHINH LA BFS da validated
            # o Test2 - dung no lam chuan cho Viec 1 nhu spec noi ro (2.2))
            pts_full = []
            for (canon, walk, sched_full, gamma) in entries_with_gamma:
                for (K, W, slack) in gamma[j]:
                    pts_full.append((K, W))
            bundle_full_feasible = len(pts_full) > 0
            pareto_full = pareto_front_KW(pts_full) if pts_full else []

            for variant in ("D1", "D2", "D3"):
                pts_x = []
                for (canon, walk, sched_full, gamma) in fronts[variant]:
                    for (K, W, slack) in gamma[j]:
                        pts_x.append((K, W))
                bundle_x_feasible = len(pts_x) > 0

                if bundle_full_feasible and not bundle_x_feasible:
                    bundle_loss[variant] = True
                    if detail[variant] is None:
                        detail[variant] = dict(kind="bundle_loss", j=j, S=sorted(S))

                if variant in ("D2", "D3") and bundle_full_feasible:
                    pareto_x = pareto_front_KW(pts_x) if pts_x else []
                    for (K, W) in pareto_full:
                        covered = any(Kp <= K + EPS and Wp <= W + EPS for (Kp, Wp) in pareto_x)
                        if not covered:
                            pareto_loss[variant] = True
                            if detail[variant] is None or detail[variant]["kind"] != "pareto_loss":
                                detail[variant] = dict(kind="pareto_loss", j=j, S=sorted(S),
                                                       K=K, W=W, pareto_x=pareto_x[:5])

        for variant in ("D1", "D2", "D3"):
            if bundle_loss[variant]:
                n_bundle_loss += 1
            if pareto_loss[variant]:
                n_pareto_loss += 1
            if (variant in ("D2", "D3")) and (bundle_loss[variant] or pareto_loss[variant]):
                violations.append(dict(
                    n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
                    S=sorted(S), variant=variant, detail=detail[variant]))

        rows.append(dict(
            n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
            subset_id="|".join(sorted(S)), k=k,
            seq_count=seq_count,
            front_D1=len(fronts["D1"]), front_D2=len(fronts["D2"]), front_D3=len(fronts["D3"]),
            bundle_loss_D1=bundle_loss["D1"], bundle_loss_D2=bundle_loss["D2"], bundle_loss_D3=bundle_loss["D3"],
            pareto_loss_D1=pareto_loss["D1"], pareto_loss_D2=pareto_loss["D2"], pareto_loss_D3=pareto_loss["D3"],
            violation_detail=str(detail) if any(bundle_loss.values()) or any(pareto_loss.values()) else "",
        ))

    return rows, violations, len(rows)


FIELDS = ["n", "B", "class", "tw_width", "tau", "seed", "subset_id", "k",
          "seq_count", "front_D1", "front_D2", "front_D3",
          "bundle_loss_D1", "bundle_loss_D2", "bundle_loss_D3",
          "pareto_loss_D1", "pareto_loss_D2", "pareto_loss_D3", "violation_detail"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    all_violations = []
    t0 = time.time()
    cell_id = 0
    for n in N_ORDERS_SMALL:
        for B in B_GRID:
            if B > n or B < 2:
                continue
            for cls in DRIVER_CLASS:
                for tw in TW_WIDTH_GRID:
                    taus = TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t4viec1"))
                            try:
                                rows, viols, n_sub = run_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            for r in rows:
                                r["class"] = r.pop("cls")
                            all_rows.extend(rows)
                            all_violations.extend(viols)
                            if viols:
                                for v in viols:
                                    print("  VIOLATION %s n=%d B=%d %s tw=%s tau=%s seed=%d S=%s :: %s"
                                          % (v["variant"], v["n"], v["B"], v["cls"], v["tw_width"],
                                             v["tau"], v["seed"], v["S"], v["detail"]))
                        cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs, rows=%d, violations=%d)"
              % (n, cell_id, time.time() - t0, len(all_rows), len(all_violations)))

    with open(os.path.join(OUT, "exactness_d1.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    n_d2_viol = sum(1 for v in all_violations if v["variant"] == "D2")
    n_d3_viol = sum(1 for v in all_violations if v["variant"] == "D3")
    n_d1_bundle_loss = sum(1 for r in all_rows if r["bundle_loss_D1"])

    print("\n=== VIEC 1 SUMMARY ===")
    print("total subsets checked: %d" % len(all_rows))
    print("D1 bundle_loss count (informational, expected>0 OK): %d" % n_d1_bundle_loss)
    print("D2 violations (gate 1.A/1.B, MUST be 0): %d" % n_d2_viol)
    print("D3 violations (gate 1.A/1.B, MUST be 0): %d" % n_d3_viol)
    print("elapsed=%.1fs" % (time.time() - t0))

    if n_d2_viol > 0 or n_d3_viol > 0:
        print("\n*** GATE 1.A/1.B FAIL for D2 or D3. DUNG TOAN BO TEST4. Xem violation o tren. ***")
        return 1

    print("\nGATE 1: PASS (D2, D3 both 0 violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
