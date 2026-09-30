"""Checklist_diagnosis.md - Phan D: warm-start co giup Algorithm C (VCG payment
loop, giai lai WDP -{i} cho tung winner) nhanh hon naive khong, DOC LAP voi
component decomposition (T5/Test8). Dung instance nho nhan tao nhu Test8
(t8_gen.make_instance) - khong dung route pool that cua 2b_v2_raw (qua lon,
xem quyet dinh nguoi dung 2026-09-16).

Y tuong warm-start: giai WDP goc (khong loai driver nao) 1 lan, lay nghiem x*
lam MIP start cho tung lan giai -{i} sau do (chi can tat bien x cua route
thuoc driver i bi loai, giu nguyen cac bien khac lam goi y ban dau cho solver).

Gate bat buoc: payment(naive) phai khop payment(warm-start) <= 1e-6 tren MOI
winner, MOI cell - neu khong khop, DUNG lai, KHONG bao cao so toc do.
"""

import csv
import os
import statistics
import sys
import time

sys.path.insert(0, r"K:\Programing Hardware\Cplex\cplex\python\3.7\x64_win64")
sys.path.insert(0, os.path.dirname(__file__))

import cplex  # noqa: E402
from t8_gen import make_instance  # noqa: E402
from t8_cplex import build_model, _sanitize  # noqa: E402

OUT_CSV = os.path.join(os.path.dirname(__file__), "tD_warmstart_results.csv")

N_COMPONENTS_GRID = [2, 4, 8, 16, 32]
SEEDS = [0, 1, 2]


def solve_cold(drivers, orders, fd_cost, excluded_driver=None):
    c, names = build_model(drivers, orders, fd_cost, excluded_driver=excluded_driver)
    t_det0 = c.get_dettime()
    t0 = time.perf_counter()
    c.solve()
    wall = time.perf_counter() - t0
    det = c.get_dettime() - t_det0
    obj = c.solution.get_objective_value() if c.solution.is_primal_feasible() else None
    c.end()
    return obj, wall, det


def solve_warmstart(drivers, orders, fd_cost, excluded_driver, warm_names, warm_vals):
    c, names = build_model(drivers, orders, fd_cost, excluded_driver=excluded_driver)
    name_set = set(names)
    # loc lai MIP start: chi giu bien con ton tai trong model nay (driver i da bi
    # loai khoi build_model nen bien x cua i khong con trong `names` - CPLEX se
    # bao loi neu dua ten bien khong ton tai vao MIP start)
    eff_names, eff_vals = [], []
    for n, v in zip(warm_names, warm_vals):
        if n in name_set:
            eff_names.append(n)
            eff_vals.append(v)
    if eff_names:
        c.MIP_starts.add(cplex.SparsePair(ind=eff_names, val=eff_vals),
                         c.MIP_starts.effort_level.repair)

    t_det0 = c.get_dettime()
    t0 = time.perf_counter()
    c.solve()
    wall = time.perf_counter() - t0
    det = c.get_dettime() - t_det0
    obj = c.solution.get_objective_value() if c.solution.is_primal_feasible() else None
    c.end()
    return obj, wall, det


def get_full_solution(drivers, orders, fd_cost):
    c, names = build_model(drivers, orders, fd_cost, excluded_driver=None)
    c.solve()
    vals = c.solution.get_values()
    obj = c.solution.get_objective_value()
    c.end()
    return obj, names, vals


def run_cell(nc, seed):
    inst = make_instance(nc, seed=seed)
    drivers, orders, fd = inst["drivers"], inst["orders"], inst["fd_cost"]

    full_obj, full_names, full_vals = get_full_solution(drivers, orders, fd)
    # winners = tat ca driver co bien x=1 trong loi giai goc (dung logic Test8)
    name_to_driver = {}
    for d, dv in drivers.items():
        for (rid, ofs, cost) in dv["routes"]:
            name_to_driver["x_" + _sanitize(rid)] = d
    winners = sorted({name_to_driver[n] for n, v in zip(full_names, full_vals)
                      if n.startswith("x_") and v > 0.5})

    cold_res, cold_wall, cold_det = {}, 0.0, 0.0
    warm_res, warm_wall, warm_det = {}, 0.0, 0.0
    for i in winners:
        o1, w1, d1 = solve_cold(drivers, orders, fd, excluded_driver=i)
        cold_res[i] = o1; cold_wall += w1; cold_det += d1

        o2, w2, d2 = solve_warmstart(drivers, orders, fd, i, full_names, full_vals)
        warm_res[i] = o2; warm_wall += w2; warm_det += d2

    max_diff = max(abs(cold_res[i] - warm_res[i]) for i in winners) if winners else 0.0

    return {
        "n_components": nc, "seed": seed, "n_drivers": len(drivers),
        "n_orders": len(orders), "n_winners": len(winners),
        "t_cold_wall": cold_wall, "t_warm_wall": warm_wall,
        "t_cold_det": cold_det, "t_warm_det": warm_det,
        "speedup_wall": (cold_wall / warm_wall) if warm_wall > 0 else float("nan"),
        "speedup_det": (cold_det / warm_det) if warm_det > 0 else float("nan"),
        "max_abs_diff": max_diff,
    }


def main():
    rows = []
    gate_fail = 0
    for nc in N_COMPONENTS_GRID:
        for seed in SEEDS:
            r = run_cell(nc, seed)
            rows.append(r)
            status = "OK" if r["max_abs_diff"] <= 1e-6 else "GATE FAIL"
            if status == "GATE FAIL":
                gate_fail += 1
            print("nc=%2d seed=%d n_winners=%3d  cold=%.4fs warm=%.4fs  "
                  "speedup_wall=%.3fx speedup_det=%.3fx  max_diff=%.2e  [%s]"
                  % (nc, seed, r["n_winners"], r["t_cold_wall"], r["t_warm_wall"],
                     r["speedup_wall"], r["speedup_det"], r["max_abs_diff"], status))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\n-> %s" % OUT_CSV)

    print("\n=== GATE: correctness (naive/cold vs warm-start), tolerance 1e-6 ===")
    print("Cells PASS: %d / %d   Cells FAIL: %d" % (len(rows) - gate_fail, len(rows), gate_fail))

    if gate_fail == 0:
        sw = [r["speedup_wall"] for r in rows]
        sd = [r["speedup_det"] for r in rows]
        print("\n=== Speedup summary (GATE PASS - so lieu dang tin) ===")
        print("median(speedup_wall)=%.3fx  median(speedup_det)=%.3fx"
              % (statistics.median(sw), statistics.median(sd)))
        print("theo n_components:")
        for nc in N_COMPONENTS_GRID:
            sub = [r for r in rows if r["n_components"] == nc]
            print("  nc=%2d  median(speedup_wall)=%.3fx  median(speedup_det)=%.3fx"
                  % (nc, statistics.median([r["speedup_wall"] for r in sub]),
                     statistics.median([r["speedup_det"] for r in sub])))
    else:
        print("\nGATE FAIL o mot so cell - KHONG bao cao speedup, can debug MIP start truoc.")


if __name__ == "__main__":
    main()
