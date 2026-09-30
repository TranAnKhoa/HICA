"""Kiem chung kstar_rule.py (T4_audit_scripts/T4_audit/kstar_rule.py) TREN
INSTANCE RQ1 THAT (khong phai instance tong hop cua hica_core.py), doi chieu
voi log activation-rate da co (Test_EJOR_direction/Report_ActivationRate.md
Sec2) - cung 5 instance, cung seed.

Hai viec:
  1. Chay kstar_rule.local_frontier() tren route pool THAT cua tung driver
     (Algorithm A qua dp_labeling.build_route_pool, khong phai
     hica_core.enumerate_pool tong hop) -> bao cao ty le route bi cat.
  2. Doi chieu VOI activated_route_names (route tung active qua 1000 bid
     vector LHS + WDP CPLEX that, dung lai testC2_activation_rate.py nguyen
     ven) - MOI route active PHAI nam trong K* (Dinh ly 4(a) cua T4). Neu co
     route active ma lai bi K* cat -> BUG (o dau do, khong phai o chung minh).

Moi truong: Python 3.7.7 + CPLEX 12.10 (can cho Algorithm B qua rq1_wdp -
testC2_activation_rate.py da doi hoi dung moi truong nay). kstar_rule.py tu
no la pure Python, khong can them thu vien.

Chay:
  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \\
      spec_2a_2b\\src\\kstar_rq1_crosscheck.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research",
                        "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import testC2_activation_rate as ACT
import kstar_rule as KR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "kstar_rq1_crosscheck.csv")

# Dung DUNG 5 instance da bao cao trong Report_ActivationRate.md Sec2 (cung
# n, n_drivers, seed - de doi chieu activated_route_names 1-1). B_gw=B_od=3,
# tw_width=120, tau=30.0, spatial_mode="dispersed" la default cua
# testC2_activation_rate.run_activation_rate(), KHOP voi cach 5 instance do
# da duoc sinh (script goc khong doi tham so nay giua cac instance, chi doi
# n/n_drivers/seed).
INSTANCES = [
    dict(n=12, n_drivers=5, seed=42),
    dict(n=10, n_drivers=4, seed=1),
    dict(n=15, n_drivers=5, seed=7),
    dict(n=12, n_drivers=6, seed=123),
    dict(n=10, n_drivers=4, seed=999),
]

# Theta range da khoa (Dinh ly 4 phat bieu cho b trong [lo,hi] = Theta) -
# LAY TU CUNG NOI testC2_activation_rate.py lay (rq1_cost_gen.THETA_MIN/MAX),
# khong hardcode rieng o day.
LO, HI = ACT.THETA_MIN, ACT.THETA_MAX


def run_one(n, n_drivers, seed, n_bid_vectors=1000):
    # --- buoc 1: sinh instance + route pool THAT (Algorithm A that, khong
    # phai hica_core.enumerate_pool) + chay activation-rate that (WDP that
    # qua CPLEX, dung lai testC2_activation_rate nguyen ven khong doi logic) ---
    act = ACT.run_activation_rate(n=n, n_drivers=n_drivers, seed=seed,
                                  n_bid_vectors=n_bid_vectors)
    all_routes = act["all_routes"]                 # {rid: (did, order_set, K, W)}
    activated = act["activated_route_names"]        # set(rid) tung active that

    # --- buoc 2: gom route THEO TUNG DRIVER (K* la local per-driver rule -
    # local_frontier() chi nhan route CUA 1 driver / lan goi, dung dung
    # semantics cua Dinh ly 4: K*_i tinh rieng cho tung driver i) ---
    by_driver = {}
    for rid, (did, order_set, K, W) in all_routes.items():
        by_driver.setdefault(did, []).append((rid, order_set, K, W))

    # q: dict order_id -> FD price, DUNG LAI q_o_by_order (Algorithm B da
    # dung), khong tinh lai cong thuc rieng o day.
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=n_drivers, seed=seed,
        tau=30.0, spatial_mode="dispersed")
    q_o_by_order = RC.assign_q_o(orders, tt)

    kept_all = set()
    per_driver_rows = []
    for did, routes in by_driver.items():
        kept, margin = KR.local_frontier(routes, q_o_by_order, LO, HI)
        kept_all.update(kept)
        per_driver_rows.append((did, len(routes), len(kept)))

    pool_size = len(all_routes)
    n_kept = len(kept_all)
    prune_rate = 1.0 - n_kept / float(pool_size)

    # --- buoc 3: doi chieu voi log activation-rate cu - MOI route active
    # PHAI nam trong K* (Dinh ly 4(a): pruning K* an toan, khong bao gio cat
    # mot route dang/se toi uu that). Neu khong -> bug, ghi ro danh sach vi
    # pham de truy nguyen, KHONG bao che. ---
    violations = sorted(activated - kept_all)

    return dict(
        n=n, n_drivers=n_drivers, seed=seed,
        pool_size=pool_size, n_kept=n_kept, prune_rate=prune_rate,
        n_activated=len(activated), n_violations=len(violations),
        violations=violations, per_driver=per_driver_rows,
    )


def main():
    rows = []
    print("=" * 100)
    print("kstar_rule.py tren instance RQ1 that - doi chieu voi log activation-rate cu")
    print("Theta = [%.1f, %.1f]" % (LO, HI))
    print("=" * 100)
    for spec in INSTANCES:
        r = run_one(**spec)
        rows.append(r)
        gate = "PASS (Dinh ly 4(a) giu vung)" if r["n_violations"] == 0 else "FAIL - BUG, xem violations"
        print("n=%2d n_drivers=%d seed=%-4d  pool=%5d  kept(K*)=%5d  prune_rate=%6.2f%%  "
              "activated=%3d  violations=%d  [%s]"
              % (r["n"], r["n_drivers"], r["seed"], r["pool_size"], r["n_kept"],
                 100 * r["prune_rate"], r["n_activated"], r["n_violations"], gate))
        if r["violations"]:
            print("    VI PHAM:", r["violations"])

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "n_drivers", "seed", "pool_size", "n_kept", "prune_rate",
                   "n_activated", "n_violations", "violations"])
        for r in rows:
            w.writerow([r["n"], r["n_drivers"], r["seed"], r["pool_size"], r["n_kept"],
                       "%.6f" % r["prune_rate"], r["n_activated"], r["n_violations"],
                       ";".join(r["violations"])])
    print("\n-> %s" % OUT_CSV)

    total_viol = sum(r["n_violations"] for r in rows)
    print("\n[Gate Dinh ly 4(a)] tong violations tren %d instance = %d -> %s"
          % (len(rows), total_viol, "PASS" if total_viol == 0 else "FAIL"))


if __name__ == "__main__":
    main()
