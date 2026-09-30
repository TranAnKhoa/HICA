"""Compare_result.md Phien ban A (Sec1) - CPLEX PDPTW lien khoi (co cap B, dung
test_compact_arc_milp.build_compact_model) vs Algorithm A + B (decomposed, dung
dp_labeling.build_route_pool + t8_cplex WDP), CUNG mot bo input (drivers, orders,
travel_time, theta, q_o) va CUNG mot gia tri B cho ca hai nhanh.

Ghi lai Z*, status, runtime -> dien vao bang §1.3 cua Compare_result.md.

CHAY BANG PYTHON 3.7 (can CPLEX Python API bundled 12.10):
  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \\
      spec_2a_2b\\src\\compare_monolithic_vs_decomposed.py
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
_CPLEX_PATH = os.path.join("K:" + os.sep, "Programing Hardware", "Cplex", "cplex",
                           "python", "3.7", "x64_win64")
if _CPLEX_PATH not in sys.path:
    sys.path.insert(0, _CPLEX_PATH)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import t8_cplex as T8  # decomposed WDP branch (CPLEX in-process)
import test_compact_arc_milp as CM  # monolithic+cap-B branch (CPLEX in-process)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "compare_monolithic_vs_decomposed.csv")

# (n, B, tw_width, n_drivers, seed) - B dung CHUNG cho ca cap monolithic va Algorithm A
# (B_gw = B_od = B trong phep so sanh nay, de "cung mot B" khong mo ho theo §1.1)
INSTANCES = [
    (4, 2, 120, 3, 0),
    (8, 2, 120, 4, 2),
    (10, 3, 120, 5, 3),
    (15, 3, 120, 6, 4),
    (20, 3, 180, 8, 5),
]
TAU = 20.0
SPATIAL = "dispersed"
MONO_TIME_LIMIT_S = 3600.0


def build_wdp_drivers(pool_by_driver, theta_by_driver):
    out = {}
    for did, pool in pool_by_driver.items():
        theta_i = theta_by_driver[did]
        routes = []
        rid_ctr = 0
        for order_set, kw_list in pool.items():
            for (K, W) in kw_list:
                rid = "%s_r%d" % (did, rid_ctr)
                rid_ctr += 1
                cost = K + theta_i * W
                routes.append((rid, order_set, cost))
        out[did] = {"routes": routes}
    return out


def run_instance(n, B, tw_width, n_drivers, seed):
    rng = random.Random(seed)
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=TAU, spatial_mode=SPATIAL)

    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    # --- Nhanh 2: Algorithm A (route pool, B_gw=B_od=B) + Algorithm B (WDP CPLEX) ---
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw=B, B_od=B)
    wdp_drivers = build_wdp_drivers(pool_by_driver, theta_by_driver)
    order_ids = list(orders.keys())
    fd_cost = {oid: q_o_by_order[oid] for oid in order_ids}
    route_pool_size = sum(len(dv["routes"]) for dv in wdp_drivers.values())

    t0 = time.perf_counter()
    r_ab = T8.solve_wdp(wdp_drivers, order_ids, fd_cost)
    t_ab = time.perf_counter() - t0

    # --- Nhanh 1: CPLEX monolithic + cap B (test_compact_arc_milp) ---
    # Time limit de tranh treo vo thoi han o n lon (arc-based big-M model da
    # do n=8 mat 341s) - neu cham gioi han, status se la "time limit exceeded"
    # (khong phai OPTIMAL), gate se tu dong loai hang do (dung §1.3/§3
    # Compare_result.md: khong dung ket qua TIME_LIMIT de so sanh).
    c, meta = CM.build_compact_model(drivers, orders, fd_cost, tt, theta_by_driver)
    c.parameters.timelimit.set(MONO_TIME_LIMIT_S)
    t0 = time.perf_counter()
    c.solve()
    t_mono = time.perf_counter() - t0
    st_mono = c.solution.get_status_string()
    z_mono = c.solution.get_objective_value() if c.solution.is_primal_feasible() else None
    gap_mono = None
    if c.solution.is_primal_feasible():
        try:
            gap_mono = c.solution.MIP.get_mip_relative_gap()
        except Exception:
            gap_mono = None
    c.end()

    z_ab = r_ab["z"]
    st_ab = r_ab["status"]
    delta = None
    if z_mono is not None and z_ab is not None:
        delta = abs(z_mono - z_ab)

    return {
        "n": n, "B": B, "route_pool_size": route_pool_size,
        "Z_monolithic_capB": z_mono, "Z_decomposed_AB": z_ab, "delta_Z": delta,
        "status_monolithic": st_mono, "status_decomposed": st_ab,
        "gap_monolithic": gap_mono,
        "runtime_monolithic_s": t_mono, "runtime_AB_s": t_ab,
    }


def main():
    rows = []
    print("=" * 100)
    print("Phien ban A: CPLEX monolithic+cap B  vs  Algorithm A+B (decomposed, cung B)")
    print("=" * 100)
    for (n, B, tw, ndrv, seed) in INSTANCES:
        r = run_instance(n, B, tw, ndrv, seed)
        rows.append(r)
        timed_out = "time limit" in (r["status_monolithic"] or "").lower()
        if timed_out:
            gate = "TIME_LIMIT (chua toi uu, gap=%s)" % (
                "%.4f%%" % (r["gap_monolithic"] * 100) if r["gap_monolithic"] is not None else "N/A")
        elif r["delta_Z"] is not None and r["delta_Z"] < 1e-6:
            gate = "PASS"
        else:
            gate = "CHECK"
        print("n=%2d B=%d pool=%4d  Z_mono=%s  Z_AB=%s  dZ=%s  "
              "status=(%s,%s)  t_mono=%.2fs t_AB=%.3fs  [%s]"
              % (r["n"], r["B"], r["route_pool_size"],
                 r["Z_monolithic_capB"], r["Z_decomposed_AB"], r["delta_Z"],
                 r["status_monolithic"], r["status_decomposed"],
                 r["runtime_monolithic_s"], r["runtime_AB_s"], gate))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s" % OUT_CSV)

    both_optimal = [r for r in rows
                    if "optimal" in (r["status_monolithic"] or "").lower()
                    and "optimal" in (r["status_decomposed"] or "").lower()]
    if not both_optimal:
        print("\n[Phien ban A gate] khong co hang nao ca hai status=OPTIMAL -> khong the ket luan")
    else:
        worst = max(r["delta_Z"] for r in both_optimal)
        print("\n[Phien ban A gate] tren %d/%d hang OPTIMAL ca hai ben: max |Z_mono - Z_AB| = %.2e -> %s"
              % (len(both_optimal), len(rows), worst, "PASS" if worst < 1e-6 else "FAIL"))


if __name__ == "__main__":
    main()
