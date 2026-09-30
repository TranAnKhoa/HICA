"""Testb_hull_final.md Sec3 - Gate BAT BUOC truoc khi tin bat ky con so
reduction nao tu Test B (hull filter tai DP intermediate state). So sanh
output cua t6_dp_hull.run_dp(use_hull_filter=True) voi HULL CUA BRUTE-FORCE
(khong phai toan bo Pareto set brute-force - dung theo Proposition Sec0:
hull filter CO Y bo unsupported point, so voi Pareto set day du se luon
"fail" mot cach vo nghia).

n<=6, dung brute_force.py (doc lap voi t6_dp*, khong import chung logic).
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import brute_force as BF

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp_hull as DH
from convex_hull_test_v2 import lower_hull_on_pareto, pareto_filter


def hull_of_bundle_pareto(kw_list):
    """kw_list: [(K,W)] (da la Pareto front, tu brute_pool_for_driver). Tra
    hull (list (K,W)) - dung LAI ham da audit doc lap (0 mismatch)."""
    tagged = [(k, w, None) for (k, w) in kw_list]
    pareto_pts = pareto_filter(tagged)
    hull = lower_hull_on_pareto(pareto_pts)
    return set((round(k, 6), round(w, 6)) for k, w, _ in hull)


def dp_hull_pool_for_driver(travel_time, driver, orders, B):
    """Chay t6_dp_hull.run_dp(use_hull_filter=True) cho 1 driver, tra
    {frozenset(bundle): [(K,W)...]} (SAU hull filter, dung finalize_KW nhu
    dp_labeling.py da lam)."""
    res = DH.run_dp(travel_time, driver, orders, B, use_dominance=True,
                    use_hull_filter=True)
    pool = {}
    for Cset, labs in res["complete_by_C"].items():
        if not Cset:
            continue
        kw = [DH.finalize_KW(driver, lab) for lab in labs]
        pool[Cset] = kw
    return pool


def gate_one_instance(n, B_gw, B_od, tw_width, n_drivers, seed, tau, spatial_mode):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=tau, spatial_mode=spatial_mode)

    violations = []
    for drv in drivers:
        B = B_gw if drv["cls"] == "GW" else B_od

        bf_pool = BF.brute_pool_for_driver(tt, drv, orders, B_gw, B_od)
        dp_pool = dp_hull_pool_for_driver(tt, drv, orders, B)

        for bundle, bf_kw in bf_pool.items():
            bf_hull = hull_of_bundle_pareto(bf_kw)
            if not bf_hull:
                continue
            dp_kw = dp_pool.get(bundle, [])
            dp_set = set((round(k, 6), round(w, 6)) for (k, w) in dp_kw)

            missing = bf_hull - dp_set
            if missing:
                violations.append(dict(
                    driver=drv["id"], bundle=sorted(bundle),
                    missing_points=sorted(missing),
                    bf_hull_size=len(bf_hull), dp_pool_size=len(dp_set),
                ))
    return violations


def main():
    print("=== Testb_hull_final.md Sec3 - Gate n<=6 (hull cua brute-force vs t6_dp_hull) ===")

    grid = []
    for n in (3, 4, 5, 6):
        for B in (2, 3):
            for tw in (60, 120):
                for spatial_mode in ("dispersed", "clustered"):
                    for seed in (0, 1, 2):
                        grid.append(dict(n=n, B_gw=B, B_od=B, tw_width=tw,
                                         n_drivers=max(2, n // 2), seed=seed,
                                         tau=30.0, spatial_mode=spatial_mode))

    print("Tong so instance se kiem: %d" % len(grid))

    total_violations = []
    n_checked = 0
    for cfg in grid:
        gen_seed = IG.stable_seed(cfg["n"], cfg["B_gw"], cfg["B_od"], cfg["tau"],
                                  cfg["spatial_mode"], cfg["seed"], "gate_hull_n6")
        viol = gate_one_instance(cfg["n"], cfg["B_gw"], cfg["B_od"], cfg["tw_width"],
                                 cfg["n_drivers"], gen_seed, cfg["tau"], cfg["spatial_mode"])
        n_checked += 1
        if viol:
            print("[FAIL] cfg=%s -> %d violation(s)" % (cfg, len(viol)))
            for v in viol[:3]:
                print("    driver=%s bundle=%s missing=%s (bf_hull=%d, dp_pool=%d)"
                      % (v["driver"], v["bundle"], v["missing_points"],
                         v["bf_hull_size"], v["dp_pool_size"]))
            total_violations.extend(viol)

    print("\n=== KET QUA GATE ===")
    print("Instance da kiem: %d" % n_checked)
    print("Tong violation: %d" % len(total_violations))
    if not total_violations:
        print("[PASS] Moi supported point (hull) cua brute-force deu co mat trong t6_dp_hull output.")
        print("       Test B duoc phep tiep tuc - co the tin cac con so reduction se do.")
    else:
        print("[FAIL] Gate KHONG PASS - KHONG duoc tin bat ky con so reduction nao tu Test B.")
        print("       Uu tien debug: logic partial-cost tai state trung gian co khac ")
        print("       route cost cuoi theo cach nao do chua tinh toi (xem Sec3 ghi chu).")

    return total_violations


if __name__ == "__main__":
    main()
