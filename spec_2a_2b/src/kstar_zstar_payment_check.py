"""Add_test.md Sec2.2 buoc 4 + Sec2.4: giai Algorithm B (WDP, CPLEX) HAI LAN
tren cung instance RQ1 that - mot lan tren pool DAY DU, mot lan tren pool DA
CAT boi K* (kstar_rule.local_frontier) - so Z*, Z*_{-i} (removal/VCG) cho
TUNG driver, va payment (Clarke pivot) cho tung winner.

Gate (Add_test.md Sec2.3): |Z*(full) - Z*(pruned)| <= 1e-6 tren MOI bid
profile thu, moi payment khop trong cung nguong.

Moi truong: Python 3.7.7 + CPLEX 12.10.
"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research",
                        "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import rq1_wdp as RW
import kstar_rule as KR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "kstar_zstar_payment_check.csv")

LO, HI = RC.THETA_MIN, RC.THETA_MAX
N_BID_PROFILES = 20   # moi instance - du de bao phu nhieu to hop winner khac nhau,
                       # khong can 1000 nhu activation-rate (o day chi can vai profile
                       # de kiem tra Z*/payment khop, khong can tim het activated set)

# CA 5 instance RQ1 that dung trong kstar_rq1_crosscheck.py/kstar_gridcheck_rq1.py
# (khop log activation-rate cu) - ban dau chi chay 2/5 (n=10) de re, nhung
# seed=42 la instance bi K* cat MANH NHAT (96.81% theo pool_size, xem
# kstar_gridcheck_rq1.csv) - phep thu khac nghiet nhat, PHAI chay qua WDP
# that truoc khi coi muc 2 la dong (gop y 2026-09-22: pham vi da kiem chung
# Z*/payment truoc do KHONG bao phu diem cuc doan nhat).
INSTANCES = [
    dict(n=12, n_drivers=5, seed=42),
    dict(n=10, n_drivers=4, seed=1),
    dict(n=15, n_drivers=5, seed=7),
    dict(n=12, n_drivers=6, seed=123),
    dict(n=10, n_drivers=4, seed=999),
]


def prune_pool_by_kstar(pool_by_driver, q_o_by_order, lo, hi):
    """Ap dung K* len TUNG driver's pool rieng, tra pool_by_driver DA CAT
    (cung dinh dang {did: {order_set: [(K,W),...]}} nhu build_route_pool)."""
    pruned = {}
    for did, pool in pool_by_driver.items():
        routes = []
        rid_ctr = 0
        rid_to_key = {}
        for order_set, kw_list in pool.items():
            for (K, W) in kw_list:
                rid = "%s_r%d" % (did, rid_ctr)
                rid_ctr += 1
                routes.append((rid, order_set, K, W))
                rid_to_key[rid] = (order_set, K, W)
        if not routes:
            pruned[did] = pool
            continue
        kept, _ = KR.local_frontier(routes, q_o_by_order, lo, hi)
        kept_set = set(kept)
        new_pool = {}
        for rid in kept:
            order_set, K, W = rid_to_key[rid]
            new_pool.setdefault(order_set, []).append((K, W))
        pruned[did] = new_pool
    return pruned


def run_instance(n, n_drivers, seed, n_bid_profiles=N_BID_PROFILES):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=n_drivers, seed=seed,
        tau=30.0, spatial_mode="dispersed")
    pool_full, agg = DL.build_route_pool(tt, drivers, orders, B_gw=3, B_od=3)
    q_o_by_order = RC.assign_q_o(orders, tt)
    pool_pruned = prune_pool_by_kstar(pool_full, q_o_by_order, LO, HI)

    pool_size_full = sum(len(kw) for p in pool_full.values() for kw in p.values())
    pool_size_pruned = sum(len(kw) for p in pool_pruned.values() for kw in p.values())

    driver_ids = [d["id"] for d in drivers]
    rng = random.Random(31337 + seed)

    rows = []
    for bp in range(n_bid_profiles):
        theta_by_driver = {did: rng.uniform(LO, HI) for did in driver_ids}

        r_full = RW.solve_wdp_for_instance(pool_full, orders, theta_by_driver, q_o_by_order)
        r_pruned = RW.solve_wdp_for_instance(pool_pruned, orders, theta_by_driver, q_o_by_order)
        Zf, Zp = r_full["z"], r_pruned["z"]
        dZ = abs(Zf - Zp) if (Zf is not None and Zp is not None) else None

        # Z*_{-i} (removal solve, VCG) cho tung driver, ca hai nhanh - day la
        # so sanh truc tiep cho payment (Clarke pivot payment = c_ir(b_i) +
        # Z*_{-i} - Z*, dung Z*_{-i} khop la dieu kien can de payment khop).
        max_removal_gap = 0.0
        n_removal = 0
        for did in driver_ids:
            rf = RW.solve_wdp_for_instance(pool_full, orders, theta_by_driver,
                                           q_o_by_order, excluded_driver=did)
            rp = RW.solve_wdp_for_instance(pool_pruned, orders, theta_by_driver,
                                           q_o_by_order, excluded_driver=did)
            if rf["z"] is not None and rp["z"] is not None:
                gap = abs(rf["z"] - rp["z"])
                max_removal_gap = max(max_removal_gap, gap)
                n_removal += 1

        rows.append(dict(n=n, n_drivers=n_drivers, seed=seed, bid_profile=bp,
                         Z_full=Zf, Z_pruned=Zp, delta_Z=dZ,
                         max_removal_gap=max_removal_gap, n_removal=n_removal))

    return dict(n=n, n_drivers=n_drivers, seed=seed,
               pool_size_full=pool_size_full, pool_size_pruned=pool_size_pruned,
               rows=rows)


def main():
    print("=" * 100)
    print("Add_test.md Sec2.2 buoc4/Sec2.4: Z*/Z*_{-i} full pool vs K*-pruned pool, WDP CPLEX that")
    print("=" * 100)
    all_rows = []
    for spec in INSTANCES:
        res = run_instance(**spec)
        all_rows.extend(res["rows"])
        max_dZ = max((r["delta_Z"] for r in res["rows"] if r["delta_Z"] is not None), default=None)
        max_rem = max((r["max_removal_gap"] for r in res["rows"]), default=None)
        print("n=%2d n_drivers=%d seed=%-4d  pool_full=%5d  pool_pruned=%5d (cat %.2f%%)  "
              "max|Z_full-Z_pruned|=%s  max_removal_gap=%s"
             % (res["n"], res["n_drivers"], res["seed"], res["pool_size_full"],
                res["pool_size_pruned"],
                100 * (1 - res["pool_size_pruned"] / float(res["pool_size_full"])),
                ("%.2e" % max_dZ) if max_dZ is not None else "N/A",
                ("%.2e" % max_rem) if max_rem is not None else "N/A"))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    print("\n-> %s" % OUT_CSV)

    worst_Z = max((r["delta_Z"] for r in all_rows if r["delta_Z"] is not None), default=None)
    worst_rem = max((r["max_removal_gap"] for r in all_rows), default=None)
    print("\n[Gate Add_test.md Sec2.3] worst |Z_full-Z_pruned| across all bid profiles = %s -> %s"
         % (("%.2e" % worst_Z) if worst_Z is not None else "N/A",
            "PASS" if (worst_Z is not None and worst_Z < 1e-6) else "FAIL/CHECK"))
    print("[Gate Add_test.md Sec2.3] worst removal-solve gap (VCG Z*_{-i}) = %s -> %s"
         % (("%.2e" % worst_rem) if worst_rem is not None else "N/A",
            "PASS" if (worst_rem is not None and worst_rem < 1e-6) else "FAIL/CHECK"))


if __name__ == "__main__":
    main()
