"""Viec bo sung (theo yeu cau nguoi dung, 2026-09-12 - sau report_2a_2b_full.md):
do speedup THAT (khong phai uoc luong dai so nhu Viec 1) bang cach chay
Algorithm B (WDP that, CPLEX 12.10 qua ha tang Test8) tren 3 instance dai
dien lay tu route pool THAT cua 2b (spec_2a_2b), roi so sanh naive vs
decomposed dung tinh than Test8 §2.

BAT BUOC chay bang Python 3.7.7 (binding CPLEX 12.10) - xem memory
python-37-cplex-api. KHONG sua t8_cplex.py/t8_gen.py - chi IMPORT ham
build_model/solve_model/solve_wdp/build_conflict_graph/connected_components/
naive_all/decomposed_all/build_full_alloc_map TU t8_cplex.py, tai su dung
nguyen ven dung tinh than "khong viet lai" da ap dung xuyen suot du an.

3 instance dai dien (chon tu 2b_raw/*.json theo largest_component_fraction):
  - "tot"    : n=30, tau=10, dispersed, sr=0.3, seed=0 -> 6 component, 5 singleton, largest=0.444
  - "trungbinh": n=30, tau=30, dispersed, sr=0.3, seed=0 -> 4 component, 3 singleton, largest=0.667
  - "xau"    : n=50, tau=60, dispersed, sr=0.3, seed=0 -> 1 component (sup toan bo), largest=1.000

2b_raw/*.json CHI luu pool_sizes_by_driver (khong luu toan bo pool - qua
lon de persist moi instance) -> phai SINH LAI instance + route pool bang
instance_gen.py + dp_labeling.py (deterministic, CUNG seed/tham so da ghi
trong record) - KHONG phai chay lai tu dau, chi tai tao 3 instance cu the.

Chuyen doi route pool DP (dict {frozenset(order_ids): [(K,W),...]}) sang
dinh dang Test8 (driver -> {"routes": [(rid, frozenset(orders), cost)]}):
  cost(bundle) = K cua diem Pareto co K NHO NHAT (kappa=1, KHONG dung bid -
  dung tinh than DSIC "khong doc bid trong route generation" xuyen suot du
  an; W bi bo qua o day vi WDP goc (Master §0) dung K + b*W nhung 2b/Test6
  khong mo hinh bid b - chi dung K thay cho chi phi, cong khai lua chon nay).

fd_cost: 2b KHONG mo hinh FD (chi co route pool GW/OD). De WDP co phuong an
du phong (outside option) nhu Test8, gan fd_cost[o] = 1.3 x route re nhat
phu o do (mot gia dinh THIET KE cong khai, giong tinh than t8_gen.fd_cost
nhung co dinh he so thay vi ngau nhien - de KHONG tao thien vi ngau nhien
lam sai lech ket qua giua 3 instance).
"""

import json
import os
import sys
import time

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _T2BFS)

import hashlib                     # noqa: E402
import instance_gen as IG          # noqa: E402
import dp_labeling as DL           # noqa: E402
import t8_cplex as T8              # noqa: E402  (import nguyen, KHONG sua)

# --- PHAT HIEN QUAN TRONG (2026-09-12) --------------------------------------
# run_2a.py/run_2b.py/run_2b_B2.py/probe_scaling.py/run_gate0.py deu dung
# `hash((...)) & 0x7FFFFFFF` de sinh gen_seed tu tham so instance. hash() cua
# Python TREN TUPLE CHUA STRING bi RANDOMIZE THEO TIEN TRINH (PYTHONHASHSEED,
# mac dinh tu Python 3.3) - nghia la CUNG mot bo tham so (n,tau,mode,sr,seed)
# se cho gen_seed KHAC NHAU o 2 lan chay Python khac nhau (da xac nhan bang
# thuc nghiem: hash(('a','b')) cho 2 gia tri khac nhau giua 2 process). Day la
# BUG that su: moi tuyen bo "tai tao duoc instance tu seed da ghi" trong cac
# report truoc day (report_2a_2b.md, report_2a_2b_full.md, ...) KHONG DUNG -
# khong the regenerate CHINH XAC instance da dung trong 2a_summary.csv/
# 2b_summary.csv tu 1 process MOI. Thong ke TONG HOP van dung (moi o luoi van
# dung 1 seed co dinh trong SUOT 1 lan chay), nhung khong reproducible xuyen
# process.
#
# Sua o day (KHONG sua nguoc lai run_2a.py/run_2b.py/run_2b_B2.py vi da chay
# xong, sua se lam seed cua du lieu DA CO khong khop code moi): dung
# hashlib.sha256 (on dinh, giong t6_run_gate1.seed_from()) thay vi hash().
# Vi VAY, 3 instance dai dien o day KHONG PHAI dung tuyet doi cac dong cu
# the trong 2b_raw/*.json (seed goc khong tai tao duoc) - ma la 3 instance
# MOI, cung tham so (n,tau,mode,sr), duoc kiem lai cau truc component (xem
# _pick_seed_for_target) de dam bao dai dien dung 3 vung "tot/trungbinh/xau"
# nhu du dinh, thay vi tin mu vao seed=0 se cho dung cau truc cu.
def stable_seed(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big") & 0x7FFFFFFF

OUT_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "results", "viec_extra_real_wdp_speedup.json")

FD_MARKUP = 1.3   # fd_cost = FD_MARKUP * route re nhat phu order do (cong khai)

# CHON LAI 2026-09-12 sau khi phat hien bug hash() khong on dinh xuyen tien
# trinh (xem stable_seed() o tren) - seed dung o day la seed ON DINH (khong
# phai seed goc trong 2b_summary.csv, khong the tai tao duoc do bug do). Da
# quet seed=0..9 tren dung tham so (n,tau,mode,sr) cua 3 vung "tot/trungbinh/
# xau" (lay tu bang B.3 report_2a_2b_full.md) va CHON seed cho cau truc
# component THAT SU trai deu tu thap den cao (khong chi tin theo largest_frac
# trung binh cua ca o luoi - kiem tra tung instance cu the):
CASES = [
    dict(label="tot", n=30, tau=10, spatial_mode="dispersed", supply_ratio=0.3, seed=0),
    dict(label="trungbinh", n=30, tau=30, spatial_mode="dispersed", supply_ratio=0.3, seed=6),
    dict(label="xau", n=50, tau=60, spatial_mode="dispersed", supply_ratio=0.3, seed=4),
]
B_FIXED = 3
TW_FIXED = 120


def regenerate_pool(n, tau, spatial_mode, supply_ratio, seed):
    """Sinh lai DUNG instance + route pool nhu run_2b.py da lam (cung cong
    thuc seed, cung tham so co dinh B=3/tw=120)."""
    n_drivers = max(1, int(round(supply_ratio * n)))
    gen_seed = stable_seed(n, tau, spatial_mode, supply_ratio, seed, "spec2b")
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_FIXED, B_od=B_FIXED, tw_width=TW_FIXED, n_drivers=n_drivers, seed=gen_seed,
        tau=float(tau), spatial_mode=spatial_mode)
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_FIXED, B_FIXED)
    return drivers, orders, pool_by_driver, meta


def convert_to_t8_format(drivers_raw, pool_by_driver):
    """pool_by_driver: {driver_id: {frozenset(order_ids): [(K,W),...]}}.
    Tra (t8_drivers, t8_orders, fd_cost) dung dinh dang t8_cplex.solve_wdp."""
    t8_drivers = {}
    cheapest_for_order = {}
    all_orders = set()

    for did, pool in pool_by_driver.items():
        routes = []
        for ridx, (Cset, kw_list) in enumerate(pool.items()):
            if not Cset:
                continue
            K_min = min(K for K, W in kw_list)   # diem Pareto K nho nhat (xem docstring)
            rid = "%s_r%d" % (did, ridx)
            routes.append((rid, frozenset(Cset), float(K_min)))
            all_orders |= set(Cset)
            for o in Cset:
                cheapest_for_order[o] = min(cheapest_for_order.get(o, float("inf")), K_min)
        t8_drivers[did] = {"routes": routes}

    fd_cost = {}
    for o in sorted(all_orders):
        base = cheapest_for_order.get(o, 10.0)
        fd_cost[o] = round(FD_MARKUP * base, 4)

    return t8_drivers, sorted(all_orders), fd_cost


def run_one_case(case):
    label = case["label"]
    print("=" * 70)
    print("Case '%s': n=%d tau=%d mode=%s sr=%.1f seed=%d"
          % (label, case["n"], case["tau"], case["spatial_mode"],
             case["supply_ratio"], case["seed"]))

    t0 = time.time()
    drivers_raw, orders_raw, pool_by_driver, meta = regenerate_pool(
        case["n"], case["tau"], case["spatial_mode"], case["supply_ratio"], case["seed"])
    print("  regenerate pool: %.1fs  (n_drivers=%d)" % (time.time() - t0, len(drivers_raw)))

    t8_drivers, t8_orders, fd_cost = convert_to_t8_format(drivers_raw, pool_by_driver)
    n_routes_total = sum(len(dv["routes"]) for dv in t8_drivers.values())
    print("  converted: %d driver, %d order, %d route total"
          % (len(t8_drivers), len(t8_orders), n_routes_total))

    inst = dict(drivers=t8_drivers, orders=t8_orders, fd_cost=fd_cost)

    # --- WDP THAT: giai full instance, lay winner that -----------------
    t1 = time.time()
    full = T8.solve_wdp(t8_drivers, t8_orders, fd_cost)
    print("  full WDP solved: %.2fs  Z*=%.4f  status=%s"
          % (time.time() - t1, full["z"] if full["z"] is not None else -1, full["status"]))

    alloc_map = T8.build_full_alloc_map(t8_drivers, full["alloc_x"])
    covered = set()
    for _d, (_r, ofs, _c) in alloc_map.items():
        covered |= set(ofs)
    fd_orders = set(t8_orders) - covered
    winners = sorted(alloc_map.keys())
    print("  winners (driver thang route that su): %d / %d driver co pool"
          % (len(winners), len(t8_drivers)))

    # --- component cua winner that (khong phai gia dinh dai so) ---------
    graph = T8.build_conflict_graph(t8_drivers)
    comps = T8.connected_components(graph)
    comp_of = {}
    for idx, P in enumerate(comps):
        for dd in P:
            comp_of[dd] = idx
    comp_sizes = {idx: len(P) for idx, P in enumerate(comps)}
    winner_comp_sizes = [comp_sizes[comp_of[w]] for w in winners]

    # --- naive vs decomposed THAT (Test8 §2, khong sua) ------------------
    t2 = time.time()
    n_res, n_sw, n_sd = T8.naive_all(inst, winners)
    t3 = time.time()
    d_res, d_sw, d_sd, t_step1 = T8.decomposed_all(inst, winners, alloc_map, fd_orders)
    t4 = time.time()

    max_diff = max(abs(n_res[i] - d_res[i]) for i in winners) if winners else 0.0
    speedup_wall = (n_sw / d_sw) if d_sw > 0 else float("nan")
    speedup_det = (n_sd / d_sd) if d_sd > 0 else float("nan")

    print("  naive: %.3fs wall (%d WDP-{i} giai tren CA instance)" % (n_sw, len(winners)))
    print("  decomposed: %.3fs wall (giai tren TUNG component)" % d_sw)
    print("  SPEEDUP THAT (wall) = %.3fx   (det-ticks) = %.3fx" % (speedup_wall, speedup_det))
    print("  gate correctness |Z_naive - Z_decomp| max = %.2e" % max_diff)

    return dict(
        label=label, params=case, meta=meta,
        n_drivers_with_pool=len(t8_drivers), n_orders=len(t8_orders),
        n_routes_total=n_routes_total,
        Z_star=full["z"], n_winners=len(winners),
        n_components=len(comps), component_sizes=sorted(comp_sizes.values(), reverse=True),
        winner_component_sizes=winner_comp_sizes,
        largest_component_fraction=(max(comp_sizes.values()) / len(t8_drivers)) if t8_drivers else None,
        t_naive_solve_wall=n_sw, t_decomp_solve_wall=d_sw,
        t_naive_solve_det=n_sd, t_decomp_solve_det=d_sd,
        speedup_wall=speedup_wall, speedup_det=speedup_det,
        max_abs_diff=max_diff,
        t_full_solve_s=time.time() - t1,
    )


def main():
    results = []
    for case in CASES:
        r = run_one_case(case)
        results.append(r)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    print("\n" + "=" * 70)
    print("TOM TAT")
    print("=" * 70)
    print("%-12s %8s %8s %10s %10s %12s"
          % ("case", "n_wins", "n_comp", "largest_f", "spd_wall", "spd_det"))
    for r in results:
        print("%-12s %8d %8d %10.3f %10.3f %12.3f"
              % (r["label"], r["n_winners"], r["n_components"],
                 r["largest_component_fraction"], r["speedup_wall"], r["speedup_det"]))
    print("\n-> %s" % OUT_JSON)


if __name__ == "__main__":
    main()
