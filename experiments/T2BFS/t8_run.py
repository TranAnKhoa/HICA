"""
Test8 §3 — quet n_components, do TONG thoi gian tinh n payment: naive vs decomposed.

§1.3 logic: giu NGUYEN kich thuoc 1 component (4 driver), chi tang SO LUONG component
doc lap khong lien quan. Neu naive cham dan theo n_components (du moi payment ve ban
chat chi lien quan 1 component 4-driver co dinh) trong khi decomposed phang -> bang
chung that cho gia tri decomposition. Neu naive cung phang -> presolve tu lo, T5 khong
tao them gia tri.

Chay:
  set T8_SCRATCH=<scratch>   (tuy chon)
  "C:\\Users\\An Khoa\\anaconda3\\python.exe" experiments\\T2BFS\\t8_run.py
"""

import csv
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from t8_gen import make_instance
from t8_core import (build_conflict_graph, connected_components, solve_wdp,
                     build_full_alloc_map, CBC_EXE)

OUT_CSV = os.path.join(os.path.dirname(__file__), "t8_results.csv")
PRESOLVE_CSV = os.path.join(os.path.dirname(__file__), "t8_presolve.csv")

N_COMPONENTS_GRID = [2, 4, 8, 16, 32]
SEEDS = [0, 1, 2]


# ---------------------------------------------------------------------------
# oracle check §1.2 : build_conflict_graph tim ra dung n_components?
# ---------------------------------------------------------------------------

def check_component_count(instance):
    graph = build_conflict_graph(instance["drivers"])
    comps = connected_components(graph)
    got = len(comps)
    want = instance["n_components_designed"]
    return got == want, got, want, comps, graph


# ---------------------------------------------------------------------------
# §2.1 naive : moi winner -> build model TOAN BO instance, ub=0 cho route winner
# ---------------------------------------------------------------------------

def naive_payment_all_winners(instance, winners, preprocess=True):
    drivers = instance["drivers"]
    orders = instance["orders"]
    fd_cost = instance["fd_cost"]
    res = {}
    t_solve_sum = 0.0
    t_wall_sum = 0.0
    for i in winners:
        r = solve_wdp(drivers, orders, fd_cost, excluded_driver=i,
                      preprocess=preprocess)
        res[i] = r["z"]
        t_solve_sum += (r["solve_time_cpu"] or 0.0)
        t_wall_sum += r["wall"]
    return res, t_solve_sum, t_wall_sum


# ---------------------------------------------------------------------------
# §2.2 decomposed : component 1 lan, cache Z_P*; moi winner giai sub-instance P
# ---------------------------------------------------------------------------

def component_star_contribution(alloc_map, alloc_fd_orders, comp, orders_P, fd_cost):
    z = 0.0
    for d in comp:
        if d in alloc_map:
            z += alloc_map[d][2]
    for o in alloc_fd_orders:
        if o in orders_P:
            z += fd_cost[o]
    return z


def decomposed_payment_all_winners(instance, winners, Z_star, alloc_map,
                                   alloc_fd_orders, preprocess=True):
    drivers = instance["drivers"]
    fd_cost = instance["fd_cost"]

    # BUOC 1 (1 lan): component + cache Z_P* tu alloc_star (khong giai lai)
    t_step1_0 = time.perf_counter()
    graph = build_conflict_graph(drivers)
    comps = connected_components(graph)
    comp_of = {}
    orders_of_comp = {}
    zP_star = {}
    for idx, P in enumerate(comps):
        for d in P:
            comp_of[d] = idx
        oP = set()
        for d in P:
            for (_rid, ofs, _c) in drivers[d]["routes"]:
                oP |= set(ofs)
        orders_of_comp[idx] = oP
        zP_star[idx] = component_star_contribution(alloc_map, alloc_fd_orders, P,
                                                   oP, fd_cost)
    t_step1 = time.perf_counter() - t_step1_0

    # BUOC 2: moi winner -> chi giai sub-instance P
    res = {}
    t_solve_sum = 0.0
    t_wall_sum = 0.0
    for i in winners:
        idx = comp_of[i]
        P = comps[idx]
        oP = orders_of_comp[idx]
        sub_drivers = {d: drivers[d] for d in P}
        r = solve_wdp(sub_drivers, sorted(oP), fd_cost, excluded_driver=i,
                      restrict_orders=oP, preprocess=preprocess)
        z_P_minus_i = r["z"]
        rest = sum(zP_star[j] for j in range(len(comps)) if j != idx)
        res[i] = z_P_minus_i + rest
        t_solve_sum += (r["solve_time_cpu"] or 0.0)
        t_wall_sum += r["wall"]

    return res, t_solve_sum + t_step1, t_wall_sum + t_step1, t_step1


# ---------------------------------------------------------------------------
# 1 cell (n_components, seed)
# ---------------------------------------------------------------------------

def run_cell(n_components, seed):
    instance = make_instance(n_components, seed=seed)

    ok, got, want, comps, graph = check_component_count(instance)
    if not ok:
        raise SystemExit(
            f"[STOP §6.3] n_components designed={want} nhung build_conflict_graph "
            f"tim ra {got}. Bug o buoc sinh hoac tim component. Khong do toc do.")

    # giai full 1 lan -> Z*, alloc*
    full = solve_wdp(instance["drivers"], instance["orders"], instance["fd_cost"])
    Z_star = full["z"]
    alloc_map = build_full_alloc_map(instance["drivers"], full["alloc_x"])
    covered_by_route = set()
    for d, (_rid, ofs, _c) in alloc_map.items():
        covered_by_route |= set(ofs)
    alloc_fd_orders = set(instance["orders"]) - covered_by_route
    winners = sorted(alloc_map.keys())

    naive_res, naive_solve, naive_wall = naive_payment_all_winners(instance, winners)
    dec_res, dec_solve, dec_wall, t_step1 = decomposed_payment_all_winners(
        instance, winners, Z_star, alloc_map, alloc_fd_orders)

    # §2.3 correctness gate
    max_diff = 0.0
    for i in winners:
        max_diff = max(max_diff, abs(naive_res[i] - dec_res[i]))

    return {
        "n_components": n_components,
        "seed": seed,
        "n_drivers": len(instance["drivers"]),
        "n_orders": len(instance["orders"]),
        "n_winners": len(winners),
        "Z_star": Z_star,
        "t_naive_solve": naive_solve,
        "t_decomp_solve": dec_solve,
        "t_naive_wall": naive_wall,
        "t_decomp_wall": dec_wall,
        "t_step1": t_step1,
        "speedup_solve": (naive_solve / dec_solve) if dec_solve > 0 else float("nan"),
        "speedup_wall": (naive_wall / dec_wall) if dec_wall > 0 else float("nan"),
        "max_abs_diff": max_diff,
    }


# ---------------------------------------------------------------------------
# §4 presolve on/off, chi naive, n_components=32
# ---------------------------------------------------------------------------

def run_presolve_probe(n_components=32, seed=0):
    instance = make_instance(n_components, seed=seed)
    ok, got, want, comps, graph = check_component_count(instance)
    if not ok:
        raise SystemExit(f"[STOP] component mismatch {got} != {want}")
    full = solve_wdp(instance["drivers"], instance["orders"], instance["fd_cost"])
    alloc_map = build_full_alloc_map(instance["drivers"], full["alloc_x"])
    winners = sorted(alloc_map.keys())

    _, on_solve, on_wall = naive_payment_all_winners(instance, winners, preprocess=True)
    _, off_solve, off_wall = naive_payment_all_winners(instance, winners, preprocess=False)

    # decomposed (presolve ON) de so voi naive ON o cung n_components
    covered = set()
    for d, (_rid, ofs, _c) in alloc_map.items():
        covered |= set(ofs)
    fd_orders = set(instance["orders"]) - covered
    _, dec_solve, dec_wall, _ = decomposed_payment_all_winners(
        instance, winners, full["z"], alloc_map, fd_orders, preprocess=True)

    return {
        "n_components": n_components, "seed": seed, "n_winners": len(winners),
        "naive_presolve_on_solve": on_solve, "naive_presolve_off_solve": off_solve,
        "naive_presolve_on_wall": on_wall, "naive_presolve_off_wall": off_wall,
        "decomp_presolve_on_solve": dec_solve, "decomp_presolve_on_wall": dec_wall,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(CBC_EXE):
        raise SystemExit(f"CBC khong tim thay: {CBC_EXE}")

    print("=" * 78)
    print("TEST8 — Component decomposition co tiet kiem THOI GIAN THAT khong?")
    print("Solver: CBC 2.10.12 (bundled). Do: solve time (CBC tu in) + wall (subprocess).")
    print("=" * 78)

    rows = []
    for nc in N_COMPONENTS_GRID:
        for sd in SEEDS:
            t0 = time.perf_counter()
            r = run_cell(nc, sd)
            dt = time.perf_counter() - t0
            rows.append(r)
            print(f"  nc={nc:>2} seed={sd}  winners={r['n_winners']:>3}  "
                  f"t_naive_solve={r['t_naive_solve']:.3f}s  "
                  f"t_decomp_solve={r['t_decomp_solve']:.3f}s  "
                  f"speedup_solve={r['speedup_solve']:.2f}x  "
                  f"|d|={r['max_abs_diff']:.2e}  ({dt:.1f}s wall)")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\n-> {OUT_CSV}")

    # §2.3 gate tong the
    worst = max(r["max_abs_diff"] for r in rows)
    print(f"\n[§2.3 correctness gate] max |Z_naive-Z_dec| tren MOI cell = "
          f"{worst:.2e}  ->  {'PASS' if worst < 1e-6 else 'FAIL — DUNG, khong doc toc do'}")

    # bang §3.1 median 3 seed
    print("\n[§3.1] median 3 seed:")
    print(f"{'n_comp':>7} {'t_naive_solve':>14} {'t_decomp_solve':>15} "
          f"{'speedup_solve':>14} {'t_naive_wall':>13} {'t_decomp_wall':>14} "
          f"{'speedup_wall':>13}")
    for nc in N_COMPONENTS_GRID:
        sub = [r for r in rows if r["n_components"] == nc]
        med = lambda k: statistics.median(r[k] for r in sub)
        print(f"{nc:>7} {med('t_naive_solve'):>14.3f} {med('t_decomp_solve'):>15.3f} "
              f"{med('speedup_solve'):>14.2f} {med('t_naive_wall'):>13.3f} "
              f"{med('t_decomp_wall'):>14.3f} {med('speedup_wall'):>13.2f}")

    # §4 presolve probe
    print("\n[§4] presolve on/off, naive only, n_components=32:")
    pr = run_presolve_probe(32, seed=0)
    with open(PRESOLVE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pr.keys()))
        w.writeheader()
        w.writerow(pr)
    print(f"  naive presolve ON  : solve={pr['naive_presolve_on_solve']:.3f}s  "
          f"wall={pr['naive_presolve_on_wall']:.3f}s")
    print(f"  naive presolve OFF : solve={pr['naive_presolve_off_solve']:.3f}s  "
          f"wall={pr['naive_presolve_off_wall']:.3f}s")
    print(f"  decomp presolve ON : solve={pr['decomp_presolve_on_solve']:.3f}s  "
          f"wall={pr['decomp_presolve_on_wall']:.3f}s")
    print(f"  -> {PRESOLVE_CSV}")


if __name__ == "__main__":
    main()
