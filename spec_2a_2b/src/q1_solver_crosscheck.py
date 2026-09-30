"""Compare_result.md Sec1 (Q1) - solver correctness: giai CUNG MOT MILP (sinh tu
route_pool cua Algorithm A, model §8.1) bang hai solver doc lap - CBC (qua file
.lp dung chung, t8_core._write_lp/solve_lp_cbc) va CPLEX (in-process, t8_cplex).

Quy trinh dung dung §1.2 cua Compare_result.md:
  1. Chay Algorithm A MOT LAN / instance -> route_pool (dp_labeling.build_route_pool).
  2. Build MOT file .lp tu route_pool do (t8_core._write_lp) - dung file nay cho CA
     HAI nhanh, khong build lai model rieng cho tung solver.
  3. Nhanh CBC: solve_lp_cbc(lp_path, ...).
  4. Nhanh CPLEX: doc lai CUNG file .lp bang cplex.Cplex().read(lp_path) (KHONG
     build lai tu route_pool bang tay) - dam bao hai nhanh solve dung 1 bai toan.
  5. So Z* (dung sai 1e-6) va assignment (tap bien x_ir=1, sau khi bo z_o).

CHAY BANG PYTHON 3.7 (can CPLEX Python API bundled 12.10):
  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \\
      spec_2a_2b\\src\\q1_solver_crosscheck.py
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

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import t8_core as T8C  # _write_lp, solve_lp_cbc (CBC branch)

sys.path.insert(0, r"K:\Programing Hardware\Cplex\cplex\python\3.7\x64_win64")
import cplex  # noqa: E402  (CPLEX branch)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "q1_solver_crosscheck.csv")
SCRATCH = os.path.join(ROOT, "results", "q1_lp_scratch")
os.makedirs(SCRATCH, exist_ok=True)

INSTANCES = [
    # (n, B_gw, B_od, tw_width, n_drivers, seed)
    (5, 2, 2, 120, 3, 1),
    (8, 2, 2, 120, 4, 2),
    (10, 3, 2, 120, 5, 3),
    (15, 3, 2, 120, 6, 4),
    (20, 3, 2, 120, 8, 5),
]
TAU = 20.0
SPATIAL = "dispersed"


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


def solve_cplex_from_lp(lp_path):
    c = cplex.Cplex()
    c.set_results_stream(None)
    c.set_log_stream(None)
    c.set_warning_stream(None)
    c.set_error_stream(None)
    c.read(lp_path)
    c.parameters.threads.set(1)
    c.parameters.mip.tolerances.mipgap.set(0.0)
    c.parameters.mip.tolerances.absmipgap.set(0.0)

    t0 = time.perf_counter()
    c.solve()
    wall = time.perf_counter() - t0

    st = c.solution.get_status_string()
    obj = None
    alloc = set()
    if c.solution.is_primal_feasible():
        obj = c.solution.get_objective_value()
        names = c.variables.get_names()
        vals = c.solution.get_values()
        for n, v in zip(names, vals):
            if n.startswith("x_") and v > 0.5:
                alloc.add(n)
    c.end()
    return obj, alloc, wall, st


def run_instance(n, B_gw, B_od, tw_width, n_drivers, seed):
    rng = random.Random(seed)
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=TAU, spatial_mode=SPATIAL)

    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw=B_gw, B_od=B_od)
    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    wdp_drivers = build_wdp_drivers(pool_by_driver, theta_by_driver)
    order_ids = list(orders.keys())
    fd_cost = {oid: q_o_by_order[oid] for oid in order_ids}

    route_pool_size = sum(len(dv["routes"]) for dv in wdp_drivers.values())

    lp_path = os.path.join(SCRATCH, "q1_n%d_B%d_seed%d.lp" % (n, B_gw, seed))
    sol_path = lp_path[:-3] + ".sol"
    T8C._write_lp(lp_path, wdp_drivers, order_ids, fd_cost)

    t0 = time.perf_counter()
    cbc = T8C.solve_lp_cbc(lp_path, sol_path)
    cbc_wall = time.perf_counter() - t0
    alloc_cbc = set()
    if os.path.exists(sol_path):
        with open(sol_path) as f:
            next(f, None)
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[1].startswith("x_"):
                    if abs(float(parts[2]) - 1.0) < 1e-6:
                        alloc_cbc.add(parts[1])

    cplex_z, alloc_cplex, cplex_wall, cplex_status = solve_cplex_from_lp(lp_path)

    z_cbc = cbc["z"]
    delta = None
    if z_cbc is not None and cplex_z is not None:
        delta = abs(z_cbc - cplex_z)

    return {
        "n": n, "B_gw": B_gw, "route_pool_size": route_pool_size,
        "Z_cbc": z_cbc, "Z_cplex": cplex_z, "delta_Z": delta,
        "status_cbc": cbc["status"], "status_cplex": cplex_status,
        "runtime_cbc_s": cbc_wall, "runtime_cplex_s": cplex_wall,
        "assignment_match": alloc_cbc == alloc_cplex,
        "n_vars": len(order_ids) + route_pool_size,
    }


def main():
    rows = []
    print("=" * 100)
    print("Q1 solver crosscheck: Algorithm B model (§8.1) solved by CBC vs CPLEX on THE SAME .lp file")
    print("=" * 100)
    for (n, B_gw, B_od, tw, ndrv, seed) in INSTANCES:
        r = run_instance(n, B_gw, B_od, tw, ndrv, seed)
        rows.append(r)
        gate = "PASS" if (r["delta_Z"] is not None and r["delta_Z"] < 1e-6) else "CHECK"
        print("n=%2d B=%d pool=%4d  Z_cbc=%s  Z_cplex=%s  dZ=%s  "
              "status=(%s,%s)  match=%s  [%s]"
              % (r["n"], r["B_gw"], r["route_pool_size"],
                 r["Z_cbc"], r["Z_cplex"], r["delta_Z"],
                 r["status_cbc"], r["status_cplex"], r["assignment_match"], gate))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s" % OUT_CSV)

    worst = max((r["delta_Z"] for r in rows if r["delta_Z"] is not None), default=None)
    all_optimal = all(
        r["status_cbc"] == "OPTIMAL" and "optimal" in r["status_cplex"].lower()
        for r in rows)
    if worst is None:
        print("\n[Q1 gate] khong co hang nao ca hai status=OPTIMAL -> khong the ket luan")
    else:
        print("\n[Q1 gate] max |Z_cbc - Z_cplex| = %.2e (all OPTIMAL=%s) -> %s"
              % (worst, all_optimal, "PASS" if worst < 1e-6 else "FAIL"))


if __name__ == "__main__":
    main()
