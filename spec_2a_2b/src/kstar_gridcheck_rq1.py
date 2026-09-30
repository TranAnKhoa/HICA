"""Add_test.md Sec1, phan (B): doc lap re-implementation check tren instance
RQ1 THAT (Python 3.7.7 + CPLEX moi truong, dung lai dp_labeling.build_route_pool).

So kstar_rule.py (kink-based) voi kstar_gridcheck.py (grid brute-force, doc
lap ve cau truc tinh toan -- xem T4_audit_scripts/T4_audit/kstar_gridcheck.py)
tren CUNG 5 instance da dung trong kstar_rq1_crosscheck.py (khop voi log
activation-rate cu).

Gate: hai tap kept phai khop TUYET DOI tren MOI driver cua MOI instance.
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
import kstar_rule as KR
import kstar_gridcheck as GC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "kstar_gridcheck_rq1.csv")

LO, HI = RC.THETA_MIN, RC.THETA_MAX
N_GRID = 5000

# Cung 5 instance voi kstar_rq1_crosscheck.py (khop log activation-rate cu).
INSTANCES = [
    dict(n=12, n_drivers=5, seed=42),
    dict(n=10, n_drivers=4, seed=1),
    dict(n=15, n_drivers=5, seed=7),
    dict(n=12, n_drivers=6, seed=123),
    dict(n=10, n_drivers=4, seed=999),
]


def route_tuples_by_driver(pool_by_driver):
    """dp_labeling.build_route_pool output: {did: {order_set: [(K,W), ...]}}
    -> {did: [(rid, order_set, K, W), ...]}, dung DUNG scheme sinh rid cua
    rq1_wdp.build_wdp_drivers (khong doi, de doi chieu duoc voi cac script
    khac neu can)."""
    out = {}
    for did, pool in pool_by_driver.items():
        routes = []
        rid_ctr = 0
        for order_set, kw_list in pool.items():
            for (K, W) in kw_list:
                rid = "%s_r%d" % (did, rid_ctr)
                rid_ctr += 1
                routes.append((rid, order_set, K, W))
        out[did] = routes
    return out


def run_one(n, n_drivers, seed, n_grid=N_GRID):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=n_drivers, seed=seed,
        tau=30.0, spatial_mode="dispersed")
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw=3, B_od=3)
    q_o_by_order = RC.assign_q_o(orders, tt)

    routes_by_driver = route_tuples_by_driver(pool_by_driver)

    rows = []
    for did, routes in routes_by_driver.items():
        if not routes:
            continue
        kept_kink, _ = KR.local_frontier(routes, q_o_by_order, LO, HI)
        kept_grid, _ = GC.kstar_gridcheck(routes, q_o_by_order, LO, HI, n_grid=n_grid)
        match = set(kept_kink) == set(kept_grid)
        rows.append(dict(n=n, n_drivers=n_drivers, seed=seed, driver=did,
                         pool=len(routes), kept_kink=len(kept_kink),
                         kept_grid=len(kept_grid), match=match,
                         only_kink=sorted(set(kept_kink) - set(kept_grid)),
                         only_grid=sorted(set(kept_grid) - set(kept_kink))))
    return rows


def main():
    all_rows = []
    print("=" * 100)
    print("Independent re-implementation check (RQ1 that): kstar_rule vs kstar_gridcheck")
    print("Theta = [%.1f, %.1f], n_grid=%d" % (LO, HI, N_GRID))
    print("=" * 100)
    for spec in INSTANCES:
        rows = run_one(**spec)
        all_rows.extend(rows)
        for r in rows:
            ok = "OK" if r["match"] else "MISMATCH"
            print("n=%2d n_drivers=%d seed=%-4d driver=%-6s pool=%4d kept_kink=%4d kept_grid=%4d [%s]"
                 % (r["n"], r["n_drivers"], r["seed"], r["driver"], r["pool"],
                    r["kept_kink"], r["kept_grid"], ok))
            if not r["match"]:
                print("      only_kink:", r["only_kink"])
                print("      only_grid:", r["only_grid"])

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "n_drivers", "seed", "driver", "pool", "kept_kink",
                   "kept_grid", "match", "only_kink", "only_grid"])
        for r in all_rows:
            w.writerow([r["n"], r["n_drivers"], r["seed"], r["driver"], r["pool"],
                       r["kept_kink"], r["kept_grid"], r["match"],
                       ";".join(r["only_kink"]), ";".join(r["only_grid"])])
    print("\n-> %s" % OUT_CSV)

    n_fail = sum(1 for r in all_rows if not r["match"])
    print("\n[Gate Add_test.md Sec1.3, RQ1 that] %d/%d driver-pool khop tuyet doi -> %s"
         % (len(all_rows) - n_fail, len(all_rows), "PASS" if n_fail == 0 else "FAIL"))


if __name__ == "__main__":
    main()
