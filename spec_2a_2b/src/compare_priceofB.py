"""Compare_result.md Phien ban B (Sec2) - "price of range B": CPLEX monolithic
KHONG cap B (capacity = tong so order, tu do chon bundle size bat ky) vs
Algorithm A + B decomposed CO cap B (giu nguyen ket qua Phien ban A).

Dung KET QUA DA CO cua Algorithm A+B tu Phien ban A (Z_decomposed(B)) - KHONG
chay lai Algorithm A - chi chay them nhanh moi: monolithic KHONG cap B.

CHAY BANG PYTHON 3.7 (can CPLEX Python API bundled 12.10):
  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \\
      spec_2a_2b\\src\\compare_priceofB.py
"""

import copy
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
import t8_cplex as T8
import test_compact_arc_milp as CM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "compare_priceofB.csv")

# Dung LAI DUNG instance/seed cua Phien ban A de Z_decomposed(B) khop 100%
# voi bang §1.3 da co (khong lech input).
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


def uncap_drivers(drivers, n_orders):
    """Tra ban sao cua drivers voi capacity = n_orders (khong con cap B thuc
    su - moi driver co the phuc vu toi da toan bo don, chi bi chan boi time
    window/travel nhu binh thuong)."""
    dl = drivers if isinstance(drivers, list) else list(drivers.values())
    out = []
    for d in dl:
        d2 = dict(d)
        d2["capacity"] = float(n_orders)
        out.append(d2)
    return out


def max_bundle_size_from_solution(c, meta):
    """Doc served_of (B-cap that su - TANG khi pickup, KHONG GIAM khi giao
    hang) cua MOI driver duoc dung trong loi giai, tra max qua toan bo
    driver. served_of[node] = tong so don DA pickup toi node do -> gia tri
    LON NHAT trong toan bo node cua 1 driver = bundle size driver do phuc vu."""
    best = 0
    for did, pd in meta["per_driver"].items():
        served_of = pd["served_of"]
        names = list(served_of.values())
        if not names:
            continue
        vals = c.solution.get_values(names)
        d_max = max(vals) if vals else 0.0
        if d_max > best:
            best = d_max
    return best


def run_instance(n, B, tw_width, n_drivers, seed, z_decomposed_from_A):
    rng = random.Random(seed)
    drivers, orders, tt, meta_inst = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=TAU, spatial_mode=SPATIAL)

    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    # nhanh moi: monolithic KHONG cap B (capacity = n, tu do chon bundle)
    drivers_uncap = uncap_drivers(drivers, n)
    c, meta = CM.build_compact_model(drivers_uncap, orders, q_o_by_order, tt, theta_by_driver)
    c.parameters.timelimit.set(MONO_TIME_LIMIT_S)
    t0 = time.perf_counter()
    c.solve()
    t_mono = time.perf_counter() - t0
    st_mono = c.solution.get_status_string()
    z_mono_uncap = c.solution.get_objective_value() if c.solution.is_primal_feasible() else None
    max_bundle = max_bundle_size_from_solution(c, meta) if c.solution.is_primal_feasible() else None
    c.end()

    delta = None
    price_pct = None
    if z_mono_uncap is not None and z_decomposed_from_A is not None:
        delta = z_decomposed_from_A - z_mono_uncap
        if z_mono_uncap != 0:
            price_pct = 100.0 * delta / z_mono_uncap

    return {
        "n": n, "B_nhanh2": B,
        "Z_monolithic_unbounded": z_mono_uncap, "Z_decomposed_B": z_decomposed_from_A,
        "max_bundle_unbounded": max_bundle, "delta": delta, "price_of_B_pct": price_pct,
        "status_monolithic_unbounded": st_mono, "runtime_monolithic_unbounded_s": t_mono,
    }


def main():
    # Z_decomposed(B) da co san tu Phien ban A - lay lai TU FILE KET QUA (khong
    # chay lai Algorithm A+B) de dam bao dung 1 con so da duoc bao cao.
    prevA = os.path.join(ROOT, "results", "compare_monolithic_vs_decomposed.csv")
    z_ab_by_n = {}
    with open(prevA, newline="") as f:
        for row in csv.DictReader(f):
            z_ab_by_n[int(row["n"])] = float(row["Z_decomposed_AB"])

    rows = []
    print("=" * 100)
    print("Phien ban B: CPLEX monolithic KHONG cap B  vs  Algorithm A+B decomposed (B nhanh 1)")
    print("=" * 100)
    for (n, B, tw, ndrv, seed) in INSTANCES:
        z_ab = z_ab_by_n.get(n)
        r = run_instance(n, B, tw, ndrv, seed, z_ab)
        rows.append(r)
        print("n=%2d B=%d  Z_mono_unbounded=%s  Z_AB(B)=%s  max_bundle_unbounded=%s  "
              "delta=%s  price_of_B=%s%%  status=%s  t_mono=%.2fs"
              % (r["n"], r["B_nhanh2"], r["Z_monolithic_unbounded"], r["Z_decomposed_B"],
                 r["max_bundle_unbounded"], r["delta"], r["price_of_B_pct"],
                 r["status_monolithic_unbounded"], r["runtime_monolithic_unbounded_s"]))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\n-> %s" % OUT_CSV)


if __name__ == "__main__":
    main()
