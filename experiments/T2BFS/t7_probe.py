"""
Test7 — Probe: Component Decomposition cho VCG Payment (Algorithm B/C).

Bản thăm dò, KHONG phai bo test day du. 3 case dung tay, so lieu literal, brute-force
liet ke moi allocation hop le (khong solver). Tra loi cau hoi: khi loai winner i de
tinh Z*_{-i}, co the CHI giai lai sub-instance gioi han trong connected component chua i
(cua conflict graph tren route pool) ma van ra dung ket qua khong?

Chay:  "C:\\Users\\An Khoa\\anaconda3\\python.exe" experiments\\T2BFS\\t7_probe.py
"""

from itertools import product


# ---------------------------------------------------------------------------
# 0.2  Ham chung
# ---------------------------------------------------------------------------

def solve_wdp_bruteforce(drivers, orders, fd_cost, excluded_driver=None):
    """
    Liet ke MOI to hop (driver -> route_id hoac None=idle), loc to hop nao phu moi order
    DUNG 1 LAN (qua route hoac FD), tra ve (Z*, allocation tot nhat).

    allocation: dict {driver_id: (route_id, frozenset(orders), cost)} chi cho driver
    thang mot route; cong them key "_FD": frozenset(cac order duoc phu boi FD).

    excluded_driver: driver do bi loai hoan toan (moi route coi nhu khong ton tai).
    """
    order_set = set(orders)
    driver_ids = [d for d in drivers if d != excluded_driver]

    # moi driver: list cac lua chon (None = idle) hoac (rid, orders_fs, cost)
    choices = []
    for d in driver_ids:
        opts = [None]
        for (rid, ofs, cost) in drivers[d]["routes"]:
            opts.append((rid, ofs, cost))
        choices.append(opts)

    best_z = None
    best_alloc = None

    for combo in product(*choices):
        covered = {}          # order -> count phu boi route
        route_cost = 0.0
        feasible = True
        alloc = {}
        for d, pick in zip(driver_ids, combo):
            if pick is None:
                continue
            rid, ofs, cost = pick
            for o in ofs:
                covered[o] = covered.get(o, 0) + 1
            route_cost += cost
            alloc[d] = (rid, ofs, cost)

        # order nao bi route phu >= 2 lan -> loai ngay
        if any(c >= 2 for c in covered.values()):
            continue
        # order route phu phai nam trong tap order hop le
        if any(o not in order_set for o in covered):
            continue

        fd_orders = order_set - set(covered.keys())   # phan con lai -> FD
        total = route_cost + sum(fd_cost[o] for o in fd_orders)

        if best_z is None or total < best_z - 1e-9:
            best_z = total
            alloc["_FD"] = frozenset(fd_orders)
            best_alloc = alloc

    return best_z, best_alloc


def build_conflict_graph(drivers):
    """
    adjacency: driver i, k noi nhau neu ton tai route cua i va route cua k (BAT KY route
    nao trong route pool) co chung it nhat 1 order. FD KHONG tham gia do thi nay.
    """
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
    """BFS chuan, tra ve list cac component (moi cai la 1 set driver id)."""
    seen = set()
    comps = []
    for start in graph:
        if start in seen:
            continue
        stack = [start]
        comp = set()
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
# 1.  Quy trinh chung cho 1 case
# ---------------------------------------------------------------------------

def orders_covered_by_component(drivers, comp):
    """hop cua moi order xuat hien trong route cua BAT KY driver nao trong comp."""
    s = set()
    for d in comp:
        for (_rid, ofs, _c) in drivers[d]["routes"]:
            s |= set(ofs)
    return s


def component_contribution_in_Zstar(alloc_star, comp, orders_P, fd_cost):
    """
    Z*_P = phan dong gop cua component P trong Z* goc:
      + cost route cua cac driver trong P thang trong alloc*
      + FD cost cua cac order thuoc orders_P ma alloc* dat vao FD
    """
    z_p = 0.0
    for d in comp:
        if d in alloc_star and d != "_FD":
            z_p += alloc_star[d][2]
    for o in alloc_star["_FD"]:
        if o in orders_P:
            z_p += fd_cost[o]
    return z_p


def run_case(name, drivers, orders, fd_cost):
    print("=" * 78)
    print(f"CASE {name}")
    print("=" * 78)

    z_star, alloc_star = solve_wdp_bruteforce(drivers, orders, fd_cost)
    print(f"Z* = {z_star}")
    winners = sorted(d for d in alloc_star if d != "_FD")
    for d in winners:
        rid, ofs, cost = alloc_star[d]
        print(f"  {d} -> {rid} {sorted(ofs)}  cost={cost}")
    print(f"  FD -> {sorted(alloc_star['_FD'])}  "
          f"cost={sum(fd_cost[o] for o in alloc_star['_FD'])}")

    graph = build_conflict_graph(drivers)
    comps = connected_components(graph)
    print(f"\nConflict graph adjacency: "
          f"{ {k: sorted(v) for k, v in graph.items()} }")
    print(f"Connected components: {[sorted(c) for c in comps]}  "
          f"({len(comps)} component)")

    all_match = True
    rows = []
    for i in winners:
        # (a) Z*_{-i} tren TOAN BO instance  (Algorithm C goc)
        z_full, _ = solve_wdp_bruteforce(drivers, orders, fd_cost, excluded_driver=i)

        # (b) sub-instance gioi han o component P chua i
        P = next(c for c in comps if i in c)
        orders_P = orders_covered_by_component(drivers, P)
        sub_drivers = {d: drivers[d] for d in P}
        z_sub, _ = solve_wdp_bruteforce(sub_drivers, sorted(orders_P), fd_cost,
                                        excluded_driver=i)

        # phan ngoai P: dung CHINH alloc* goc, khong giai lai
        z_sub_rest = 0.0
        for d in drivers:
            if d in P:
                continue
            if d in alloc_star and d != "_FD":
                z_sub_rest += alloc_star[d][2]
        for o in alloc_star["_FD"]:
            if o not in orders_P:
                z_sub_rest += fd_cost[o]

        z_decomposed = z_sub + z_sub_rest

        # (c) so sanh delta:  (Z_full - Z*)  vs  (Z_sub - Z*_P)
        z_star_P = component_contribution_in_Zstar(alloc_star, P, orders_P, fd_cost)
        delta_full = z_full - z_star
        delta_sub = z_sub - z_star_P
        match_delta = abs(delta_full - delta_sub) < 1e-6
        match_level = abs(z_full - z_decomposed) < 1e-6

        p_full = alloc_star[i][2] + z_full - z_star
        p_decomp = alloc_star[i][2] + z_decomposed - z_star

        all_match = all_match and match_delta and match_level
        rows.append(dict(
            winner=i, comp=sorted(P), orders_P=sorted(orders_P),
            z_full=z_full, z_sub=z_sub, z_sub_rest=z_sub_rest,
            z_decomposed=z_decomposed, z_star_P=z_star_P,
            delta_full=delta_full, delta_sub=delta_sub,
            abs_diff_delta=abs(delta_full - delta_sub),
            abs_diff_level=abs(z_full - z_decomposed),
            p_full=p_full, p_decomp=p_decomp,
            match_delta=match_delta, match_level=match_level,
        ))

    print(f"\n{'winner':<7}{'component':<16}{'Z_full':>9}{'Z_decomp':>10}"
          f"{'|d delta|':>11}{'|d level|':>11}{'p_full':>9}{'p_dec':>9}  match")
    for r in rows:
        print(f"{r['winner']:<7}{str(r['comp']):<16}{r['z_full']:>9.3f}"
              f"{r['z_decomposed']:>10.3f}{r['abs_diff_delta']:>11.6f}"
              f"{r['abs_diff_level']:>11.6f}{r['p_full']:>9.3f}{r['p_decomp']:>9.3f}"
              f"  {'OK' if (r['match_delta'] and r['match_level']) else 'MISMATCH'}")

    print(f"\nCASE {name}: {'KHOP TUYET DOI' if all_match else '>>> KHONG KHOP <<<'}")
    print()
    return all_match, rows


# ---------------------------------------------------------------------------
# 2.  Ba case cu the — so lieu cho san
# ---------------------------------------------------------------------------

def case_A():
    orders = ["o1", "o2", "o3", "o4"]
    fd_cost = {"o1": 50, "o2": 50, "o3": 50, "o4": 50}
    drivers = {
        "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                         ("rA2", frozenset({"o2"}), 12),
                         ("rA3", frozenset({"o1", "o2"}), 18)]},
        "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                         ("rB2", frozenset({"o2"}), 9),
                         ("rB3", frozenset({"o1", "o2"}), 19)]},
        "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                         ("rC2", frozenset({"o4"}), 14),
                         ("rC3", frozenset({"o3", "o4"}), 20)]},
        "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                         ("rD2", frozenset({"o4"}), 13),
                         ("rD3", frozenset({"o3", "o4"}), 21)]},
    }
    return "A", drivers, orders, fd_cost


def case_B():
    orders = ["o1", "o2", "o3", "o4", "o5"]
    fd_cost = {"o1": 50, "o2": 50, "o3": 50, "o4": 50, "o5": 50}
    drivers = {
        "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                         ("rA2", frozenset({"o2"}), 12),
                         ("rA3", frozenset({"o1", "o2"}), 18),
                         ("rA4", frozenset({"o1", "o5"}), 15)]},
        "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                         ("rB2", frozenset({"o2"}), 9),
                         ("rB3", frozenset({"o1", "o2"}), 19)]},
        "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                         ("rC2", frozenset({"o4"}), 14),
                         ("rC3", frozenset({"o3", "o4"}), 20),
                         ("rC4", frozenset({"o3", "o5"}), 12)]},
        "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                         ("rD2", frozenset({"o4"}), 13),
                         ("rD3", frozenset({"o3", "o4"}), 21)]},
    }
    return "B", drivers, orders, fd_cost


def case_C():
    orders = ["o1", "o2", "o3", "o4"]
    fd_cost = {"o1": 50, "o2": 50, "o3": 5, "o4": 50}   # o3: FD re hon moi route
    drivers = {
        "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                         ("rA2", frozenset({"o2"}), 12),
                         ("rA3", frozenset({"o1", "o2"}), 18)]},
        "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                         ("rB2", frozenset({"o2"}), 9),
                         ("rB3", frozenset({"o1", "o2"}), 19)]},
        "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                         ("rC2", frozenset({"o4"}), 14),
                         ("rC3", frozenset({"o3", "o4"}), 20)]},
        "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                         ("rD2", frozenset({"o4"}), 13),
                         ("rD3", frozenset({"o3", "o4"}), 21)]},
    }
    return "C", drivers, orders, fd_cost


if __name__ == "__main__":
    results = {}
    for builder in (case_A, case_B, case_C):
        name, drivers, orders, fd_cost = builder()
        ok, rows = run_case(name, drivers, orders, fd_cost)
        results[name] = ok

    print("=" * 78)
    print("TONG KET")
    print("=" * 78)
    for name, ok in results.items():
        print(f"  Case {name}: {'KHOP' if ok else 'KHONG KHOP'}")
    if all(results.values()):
        print("\n-> Ca 3 case khop tuyet doi: tin hieu tot, dang viet Test8.md day du.")
    elif results["A"] and results["B"] and not results["C"]:
        print("\n-> Khop A,B nhung KHONG khop C: da tim ra dieu kien ranh gioi (FD "
              "separability).")
    elif not any(results.values()):
        print("\n-> Khong khop o tat ca: huong nay khong dang dau tu them.")
    else:
        print("\n-> Ket qua hon hop: xem bang chi tiet tung case o tren.")
