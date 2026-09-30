"""
Test8 — backend CPLEX 12.10 (Python API, in-process). Chay bang Python 3.7:

  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \
      experiments\\T2BFS\\t8_cplex.py

Khac t8_core.py (CBC, subprocess) o cho: build model TRONG RAM, do rieng c.solve()
(perf_counter quanh dung loi goi solve) + deterministic ticks (get_dettime, doc lap
may) + wall CPLEX (get_time). Toggle presolve bang parameters.preprocessing.presolve
-> dung §4 spec, khong phai -preprocess CLI cua CBC.

Reuse: t8_gen.make_instance, va logic conflict-graph/decompose viet lai o day (khong
import t8_core vi t8_core import subprocess CBC path, khong can).
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

OUT_CSV = os.path.join(os.path.dirname(__file__), "t8_results_cplex.csv")
PRESOLVE_CSV = os.path.join(os.path.dirname(__file__), "t8_presolve_cplex.csv")

N_COMPONENTS_GRID = [2, 4, 8, 16, 32]
SEEDS = [0, 1, 2]


# ---------------------------------------------------------------------------
# conflict graph (giong Test7 / t8_core)
# ---------------------------------------------------------------------------

def build_conflict_graph(drivers):
    ids = list(drivers)
    orders_of = {d: set().union(*[set(o) for (_r, o, _c) in drivers[d]["routes"]])
                 if drivers[d]["routes"] else set() for d in ids}
    adj = {d: set() for d in ids}
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, k = ids[a], ids[b]
            if orders_of[i] & orders_of[k]:
                adj[i].add(k); adj[k].add(i)
    return adj


def connected_components(graph):
    seen, comps = set(), []
    for start in graph:
        if start in seen:
            continue
        stack, comp = [start], set()
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n); comp.add(n)
            stack.extend(graph[n] - seen)
        comps.append(comp)
    return comps


# ---------------------------------------------------------------------------
# build + solve MILP in-process
# ---------------------------------------------------------------------------

def _sanitize(s):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def build_model(drivers, orders, fd_cost, excluded_driver=None,
                restrict_orders=None, presolve=True):
    order_set = set(orders) if restrict_orders is None else set(restrict_orders)

    c = cplex.Cplex()
    c.set_results_stream(None)
    c.set_log_stream(None)
    c.set_warning_stream(None)
    c.set_error_stream(None)
    c.parameters.threads.set(1)
    c.parameters.preprocessing.presolve.set(1 if presolve else 0)
    c.parameters.mip.tolerances.mipgap.set(0.0)
    c.parameters.mip.tolerances.absmipgap.set(0.0)
    c.objective.set_sense(c.objective.sense.minimize)

    names, objs = [], []
    cover = {o: [] for o in order_set}
    driver_vars = {}

    for d, dv in drivers.items():
        if d == excluded_driver:
            continue
        for (rid, ofs, cost) in dv["routes"]:
            if not set(ofs) <= order_set:
                continue
            v = "x_" + _sanitize(rid)
            names.append(v); objs.append(float(cost))
            driver_vars.setdefault(d, []).append(v)
            for o in ofs:
                cover[o].append(v)

    z_of = {}
    for o in order_set:
        v = "z_" + _sanitize(o)
        z_of[o] = v
        names.append(v); objs.append(float(fd_cost[o]))
        cover[o].append(v)

    c.variables.add(obj=objs, lb=[0.0] * len(names), ub=[1.0] * len(names),
                    types=["B"] * len(names), names=names)

    rows, senses, rhs, rnames = [], [], [], []
    for o in sorted(order_set):
        rows.append([cover[o], [1.0] * len(cover[o])])
        senses.append("E"); rhs.append(1.0); rnames.append("cov_" + _sanitize(o))
    for d, vs in driver_vars.items():
        rows.append([vs, [1.0] * len(vs)])
        senses.append("L"); rhs.append(1.0); rnames.append("one_" + _sanitize(d))
    c.linear_constraints.add(lin_expr=rows, senses=senses, rhs=rhs, names=rnames)

    return c, names


def solve_model(c, names):
    """Tra ve (obj, alloc_x set, solve_wall_sec, solve_dettime_ticks, status)."""
    t_det0 = c.get_dettime()
    t0 = time.perf_counter()
    c.solve()
    solve_wall = time.perf_counter() - t0
    solve_det = c.get_dettime() - t_det0

    st = c.solution.get_status_string()
    obj = None
    alloc = set()
    if c.solution.is_primal_feasible():
        obj = c.solution.get_objective_value()
        vals = c.solution.get_values()
        for n, v in zip(names, vals):
            if n.startswith("x_") and v > 0.5:
                alloc.add(n)
    return obj, alloc, solve_wall, solve_det, st


# ---------------------------------------------------------------------------
# WDP wrapper
# ---------------------------------------------------------------------------

def solve_wdp(drivers, orders, fd_cost, excluded_driver=None,
              restrict_orders=None, presolve=True):
    c, names = build_model(drivers, orders, fd_cost, excluded_driver,
                           restrict_orders, presolve)
    obj, alloc, sw, sd, st = solve_model(c, names)
    c.end()
    return {"z": obj, "alloc_x": alloc, "solve_wall": sw, "solve_det": sd,
            "status": st, "n_vars": len(names)}


def build_full_alloc_map(drivers, alloc_x):
    name_to = {}
    for d, dv in drivers.items():
        for (rid, ofs, cost) in dv["routes"]:
            name_to["x_" + _sanitize(rid)] = (d, rid, ofs, cost)
    out = {}
    for v in alloc_x:
        if v in name_to:
            d, rid, ofs, cost = name_to[v]
            out[d] = (rid, ofs, cost)
    return out


# ---------------------------------------------------------------------------
# naive / decomposed  (§2)
# ---------------------------------------------------------------------------

def naive_all(instance, winners, presolve=True):
    d, o, fd = instance["drivers"], instance["orders"], instance["fd_cost"]
    res, sw, sd = {}, 0.0, 0.0
    for i in winners:
        r = solve_wdp(d, o, fd, excluded_driver=i, presolve=presolve)
        res[i] = r["z"]; sw += r["solve_wall"]; sd += r["solve_det"]
    return res, sw, sd


def decomposed_all(instance, winners, alloc_map, alloc_fd_orders, presolve=True):
    drivers, fd = instance["drivers"], instance["fd_cost"]

    t_step1_0 = time.perf_counter()
    graph = build_conflict_graph(drivers)
    comps = connected_components(graph)
    comp_of, orders_of_comp, zP_star = {}, {}, {}
    for idx, P in enumerate(comps):
        for dd in P:
            comp_of[dd] = idx
        oP = set()
        for dd in P:
            for (_r, ofs, _c) in drivers[dd]["routes"]:
                oP |= set(ofs)
        orders_of_comp[idx] = oP
        z = sum(alloc_map[dd][2] for dd in P if dd in alloc_map)
        z += sum(fd[x] for x in alloc_fd_orders if x in oP)
        zP_star[idx] = z
    t_step1 = time.perf_counter() - t_step1_0

    res, sw, sd = {}, 0.0, 0.0
    for i in winners:
        idx = comp_of[i]
        P = comps[idx]
        oP = orders_of_comp[idx]
        sub = {dd: drivers[dd] for dd in P}
        r = solve_wdp(sub, sorted(oP), fd, excluded_driver=i,
                      restrict_orders=oP, presolve=presolve)
        rest = sum(zP_star[j] for j in range(len(comps)) if j != idx)
        res[i] = r["z"] + rest
        sw += r["solve_wall"]; sd += r["solve_det"]
    return res, sw + t_step1, sd, t_step1


# ---------------------------------------------------------------------------
# cell
# ---------------------------------------------------------------------------

def run_cell(nc, seed):
    inst = make_instance(nc, seed=seed)
    graph = build_conflict_graph(inst["drivers"])
    got = len(connected_components(graph))
    if got != inst["n_components_designed"]:
        raise SystemExit(f"[STOP §6.3] designed {inst['n_components_designed']} "
                         f"nhung tim ra {got} component")

    full = solve_wdp(inst["drivers"], inst["orders"], inst["fd_cost"])
    alloc_map = build_full_alloc_map(inst["drivers"], full["alloc_x"])
    covered = set()
    for _d, (_r, ofs, _c) in alloc_map.items():
        covered |= set(ofs)
    fd_orders = set(inst["orders"]) - covered
    winners = sorted(alloc_map.keys())

    n_res, n_sw, n_sd = naive_all(inst, winners)
    d_res, d_sw, d_sd, t1 = decomposed_all(inst, winners, alloc_map, fd_orders)

    max_diff = max(abs(n_res[i] - d_res[i]) for i in winners)
    return {
        "n_components": nc, "seed": seed,
        "n_drivers": len(inst["drivers"]), "n_orders": len(inst["orders"]),
        "n_winners": len(winners), "Z_star": full["z"],
        "t_naive_solve_wall": n_sw, "t_decomp_solve_wall": d_sw,
        "t_naive_solve_det": n_sd, "t_decomp_solve_det": d_sd,
        "t_step1": t1,
        "speedup_wall": (n_sw / d_sw) if d_sw > 0 else float("nan"),
        "speedup_det": (n_sd / d_sd) if d_sd > 0 else float("nan"),
        "max_abs_diff": max_diff,
    }


def run_presolve_probe(nc=32, seed=0):
    inst = make_instance(nc, seed=seed)
    graph = build_conflict_graph(inst["drivers"])
    if len(connected_components(graph)) != inst["n_components_designed"]:
        raise SystemExit("[STOP] component mismatch")
    full = solve_wdp(inst["drivers"], inst["orders"], inst["fd_cost"])
    alloc_map = build_full_alloc_map(inst["drivers"], full["alloc_x"])
    covered = set()
    for _d, (_r, ofs, _c) in alloc_map.items():
        covered |= set(ofs)
    fd_orders = set(inst["orders"]) - covered
    winners = sorted(alloc_map.keys())

    _, on_sw, on_sd = naive_all(inst, winners, presolve=True)
    _, off_sw, off_sd = naive_all(inst, winners, presolve=False)
    _, d_sw, d_sd, _ = decomposed_all(inst, winners, alloc_map, fd_orders,
                                      presolve=True)
    return {
        "n_components": nc, "seed": seed, "n_winners": len(winners),
        "naive_presolve_on_solve_wall": on_sw, "naive_presolve_off_solve_wall": off_sw,
        "naive_presolve_on_solve_det": on_sd, "naive_presolve_off_solve_det": off_sd,
        "decomp_presolve_on_solve_wall": d_sw, "decomp_presolve_on_solve_det": d_sd,
    }


def main():
    print("=" * 78)
    print("TEST8 backend CPLEX 12.10 (Python API, in-process, threads=1)")
    print("Do: c.solve() wall (perf_counter) + deterministic ticks (get_dettime)")
    print("=" * 78)

    rows = []
    for nc in N_COMPONENTS_GRID:
        for sd in SEEDS:
            t0 = time.perf_counter()
            r = run_cell(nc, sd)
            rows.append(r)
            print("  nc=%2d seed=%d winners=%3d  "
                  "naive_wall=%.3fs decomp_wall=%.3fs  spd_wall=%.2fx  "
                  "spd_det=%.2fx  |d|=%.2e  (%.1fs)"
                  % (nc, sd, r["n_winners"], r["t_naive_solve_wall"],
                     r["t_decomp_solve_wall"], r["speedup_wall"],
                     r["speedup_det"], r["max_abs_diff"],
                     time.perf_counter() - t0))

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\n-> %s" % OUT_CSV)

    worst = max(r["max_abs_diff"] for r in rows)
    print("\n[§2.3 gate] max |Z_naive - Z_decomposed| = %.2e -> %s"
          % (worst, "PASS" if worst < 1e-6 else "FAIL"))

    print("\n[§3.1] median 3 seed:")
    print("%7s %16s %17s %13s %15s %16s %12s"
          % ("n_comp", "naive_solve_wall", "decomp_solve_wall", "spd_wall",
             "naive_solve_det", "decomp_solve_det", "spd_det"))
    for nc in N_COMPONENTS_GRID:
        sub = [r for r in rows if r["n_components"] == nc]
        m = lambda k: statistics.median(r[k] for r in sub)
        print("%7d %16.3f %17.3f %13.2f %15.1f %16.1f %12.2f"
              % (nc, m("t_naive_solve_wall"), m("t_decomp_solve_wall"),
                 m("speedup_wall"), m("t_naive_solve_det"),
                 m("t_decomp_solve_det"), m("speedup_det")))

    print("\n[§4] presolve on/off, naive only, nc=32 seed=0:")
    pr = run_presolve_probe(32, 0)
    with open(PRESOLVE_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pr.keys()))
        w.writeheader(); w.writerow(pr)
    print("  naive presolve ON  : wall=%.3fs  det=%.1f ticks"
          % (pr["naive_presolve_on_solve_wall"], pr["naive_presolve_on_solve_det"]))
    print("  naive presolve OFF : wall=%.3fs  det=%.1f ticks"
          % (pr["naive_presolve_off_solve_wall"], pr["naive_presolve_off_solve_det"]))
    print("  decomp presolve ON : wall=%.3fs  det=%.1f ticks"
          % (pr["decomp_presolve_on_solve_wall"], pr["decomp_presolve_on_solve_det"]))
    print("  -> %s" % PRESOLVE_CSV)


if __name__ == "__main__":
    main()
