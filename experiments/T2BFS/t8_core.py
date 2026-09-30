"""
Test8 core — set-partitioning WDP giai bang CBC 2.10.12 (bundled trong folder Cplex).

Vi sao CBC chu khong CPLEX Python API: binding CPLEX 12.10 cai san chi co
py37_cplex12100.pyd (Python 3.7), may khong co Python 3.7, mang bi chan nen khong tao
duoc env 3.7 / khong pip install duoc gi. CBC binary co san, co -preprocess off/on
(cho §4) va tu in solve time -> van tra loi duoc cau hoi Test8 ("presolve co tu tach
khoi khong") voi mot MILP solver that. Caveat: CBC != CPLEX, presolve khac engine.

Model (dung §8.1 de cuong goc):
  min  Σ cost_r x_r  +  Σ fd_o z_o
  s.t. Σ_{r ni o} x_r + z_o = 1     ∀o
       Σ_{r cua i} x_r <= 1          ∀i
       x_r, z_o ∈ {0,1}
"""

import os
import re
import subprocess
import tempfile
import time

CBC_EXE = r"K:\Programing Hardware\Cplex\Cbc-releases.2.10.12-w64-msvc16-md (1)\bin\cbc.exe"
_SCRATCH = os.environ.get("T8_SCRATCH") or tempfile.gettempdir()
os.makedirs(_SCRATCH, exist_ok=True)


# ---------------------------------------------------------------------------
# conflict graph  (giong Test7, FD KHONG tham gia canh)
# ---------------------------------------------------------------------------

def build_conflict_graph(drivers):
    ids = list(drivers)
    orders_of = {}
    for d in ids:
        s = set()
        for (_rid, ofs, _c) in drivers[d]["routes"]:
            s |= set(ofs)
        orders_of[d] = s
    adj = {d: set() for d in ids}
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, k = ids[a], ids[b]
            if orders_of[i] & orders_of[k]:
                adj[i].add(k)
                adj[k].add(i)
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
            seen.add(n)
            comp.add(n)
            stack.extend(graph[n] - seen)
        comps.append(comp)
    return comps


# ---------------------------------------------------------------------------
# LP writer + CBC runner
# ---------------------------------------------------------------------------

_SAN = re.compile(r"[^A-Za-z0-9_]")


def _san(name):
    return _SAN.sub("_", name)


def _write_lp(path, drivers, orders, fd_cost, excluded_driver=None,
              restrict_orders=None):
    """
    restrict_orders: neu set, chi dua cac order trong tap nay + route nao NAM TRON
    trong tap nay (route co order ngoai tap bi bo). Dung cho decomposed sub-instance.
    """
    order_set = set(orders) if restrict_orders is None else set(restrict_orders)

    x_terms = []          # (varname, cost)
    cover = {o: [] for o in order_set}     # order -> [xvar]
    driver_vars = {}                       # driver -> [xvar]

    for d, dv in drivers.items():
        if d == excluded_driver:
            continue
        for (rid, ofs, cost) in dv["routes"]:
            if not set(ofs) <= order_set:
                continue
            v = "x_" + _san(rid)
            x_terms.append((v, cost))
            driver_vars.setdefault(d, []).append(v)
            for o in ofs:
                cover[o].append(v)

    z_vars = {o: "z_" + _san(o) for o in order_set}

    lines = ["\\ Test8 WDP", "Minimize", " obj: " + " + ".join(
        [f"{c:g} {v}" for v, c in x_terms]
        + [f"{fd_cost[o]:g} {z_vars[o]}" for o in order_set]
    )]
    lines.append("Subject To")
    for o in sorted(order_set):
        terms = cover[o] + [z_vars[o]]
        lines.append(f" cov_{_san(o)}: " + " + ".join(terms) + " = 1")
    for d, vs in driver_vars.items():
        if len(vs) >= 1:
            lines.append(f" one_{_san(d)}: " + " + ".join(vs) + " <= 1")
    all_bins = [v for v, _ in x_terms] + [z_vars[o] for o in order_set]
    lines.append("Binaries")
    lines.append(" " + " ".join(all_bins))
    lines.append("End")
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(lines))
    return len(all_bins)


_RE_OBJ = re.compile(r"Objective value:\s*([-\d.eE+]+)")
_RE_OBJ2 = re.compile(r"Optimal - objective value\s*([-\d.eE+]+)")
_RE_TOTCPU = re.compile(r"Total time \(CPU seconds\):\s*([\d.]+)")
_RE_INFEAS = re.compile(r"infeasible", re.I)


def solve_lp_cbc(lp_path, sol_path, preprocess=True):
    """
    Chay CBC. Tra ve dict: z (objective), solve_time_cpu (CBC tu in, chi phan solve),
    wall (wall-clock cua subprocess, gom ca I/O + parse cua CBC), status.
    """
    args = [CBC_EXE, lp_path]
    args += ["-preprocess", "on" if preprocess else "off"]
    args += ["-solve", "-solution", sol_path]
    t0 = time.perf_counter()
    p = subprocess.run(args, capture_output=True, text=True, timeout=600)
    wall = time.perf_counter() - t0
    out = p.stdout

    z = None
    if os.path.exists(sol_path):
        with open(sol_path) as f:
            head = f.readline()
        m = _RE_OBJ2.search(head)
        if m:
            z = float(m.group(1))
    if z is None:
        m = _RE_OBJ.search(out)
        if m:
            z = float(m.group(1))

    m = _RE_TOTCPU.search(out)
    solve_cpu = float(m.group(1)) if m else None

    if "Optimal solution found" in out or (z is not None and "Optimal" in out):
        status = "OPTIMAL"
    elif _RE_INFEAS.search(out):
        status = "INFEASIBLE"
    else:
        status = "UNKNOWN"
    return {"z": z, "solve_time_cpu": solve_cpu, "wall": wall,
            "status": status, "stdout": out}


# ---------------------------------------------------------------------------
# WDP wrappers  (tra ve them alloc de tinh Z*_P goc)
# ---------------------------------------------------------------------------

_counter = [0]


def _tmp(prefix):
    _counter[0] += 1
    base = os.path.join(_SCRATCH, f"{prefix}_{os.getpid()}_{_counter[0]}")
    return base + ".lp", base + ".sol"


def solve_wdp(drivers, orders, fd_cost, excluded_driver=None,
              restrict_orders=None, preprocess=True):
    lp, sol = _tmp("wdp")
    nvars = _write_lp(lp, drivers, orders, fd_cost, excluded_driver, restrict_orders)
    r = solve_lp_cbc(lp, sol, preprocess=preprocess)
    r["n_vars"] = nvars
    # doc allocation tu sol file
    alloc_x = set()
    if os.path.exists(sol):
        with open(sol) as f:
            next(f, None)
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[1].startswith("x_"):
                    if abs(float(parts[2]) - 1.0) < 1e-6:
                        alloc_x.add(parts[1])
    r["alloc_x"] = alloc_x
    try:
        os.remove(lp); os.remove(sol)
    except OSError:
        pass
    return r


def build_full_alloc_map(drivers, alloc_x):
    """tu tap ten bien x_... -> {driver: (rid, ofs, cost)}."""
    name_to = {}
    for d, dv in drivers.items():
        for (rid, ofs, cost) in dv["routes"]:
            name_to["x_" + _san(rid)] = (d, rid, ofs, cost)
    out = {}
    for v in alloc_x:
        if v in name_to:
            d, rid, ofs, cost = name_to[v]
            out[d] = (rid, ofs, cost)
    return out
