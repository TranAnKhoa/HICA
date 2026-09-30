"""Spec 2a - DP label-setting.

TAI DUNG NGUYEN MODULE Test6 (experiments/T2BFS/t6_dp.py) - KHONG viet lai
dominance, KHONG noi long feasibility. O day chi bo sung:
  - run_pool(): goi t6_dp.run_dp() cho MOT driver, tra route pool duoi dang
    {frozenset(S_orders): [ (K,W), ... ]} (Pareto front tung bundle) + cac
    metric dem label (peak frontier, states generated/surviving).
  - build_route_pool(): lap run_pool() qua toan bo driver cua instance.

Vi t6_dp da PASS Gate 1.A/B/C (0/616) + Test6.1 adversarial (0 vi ph.) +
Test6.2 (2D counterexample) - xem Guideline/Test6_report.md, Test6.1_report.md,
Test6.2_report.md. Gate 0 cua Spec nay van chay lai (brute_force.py doc lap)
vi instance_gen.py la code MOI.
"""

import os
import sys

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import t6_dp as D   # noqa: E402  (module Test6, dung nguyen)

EPS = 1e-6


def _pareto_front(kw_list):
    """kw_list: [(K,W)]. Tra tap con Pareto-optimal (minimize K, W)."""
    n = len(kw_list)
    dom = [False] * n
    for i in range(n):
        Ki, Wi = kw_list[i]
        for j in range(n):
            if i == j or dom[j]:
                continue
            Kj, Wj = kw_list[j]
            if Kj <= Ki + EPS and Wj <= Wi + EPS and (Kj < Ki - EPS or Wj < Wi - EPS):
                dom[i] = True
                break
    out = []
    seen = set()
    for i in range(n):
        if dom[i]:
            continue
        key = (round(kw_list[i][0], 6), round(kw_list[i][1], 6))
        if key in seen:
            continue
        seen.add(key)
        out.append(kw_list[i])
    return out


def run_pool(travel_time, driver, orders, B_gw, B_od, compat_graph=None):
    """Chay DP cho 1 driver. [PATCH new_03] B tach lop: chon B hieu luc theo
    driver["cls"] (KHONG con dung 1 gia tri B chung - xem new03.md Viec 1).
    compat_graph (tuy chon): PCF precompute tu instance_gen.build_compat_graph,
    dung lai NGUYEN cho moi driver (khong tinh lai per-driver).

    Tra dict:
      pool          : {frozenset(order_ids): [(K,W), ...]}  (Pareto front / bundle)
      n_generated   : tong label tao (truoc dominance)
      n_surviving   : tong label song sau dominance
      peak_frontier : max so label frontier dong thoi (t6_dp.frontier_sizes)
      n_bundles     : so bundle hoan chinh (|pool|)
      k_values      : set cac |S| xuat hien (de tinh theoretical cap)
    """
    B = B_gw if driver["cls"] == "GW" else B_od
    res = D.run_dp(travel_time, driver, orders, B, use_dominance=True,
                   compat_graph=compat_graph)
    complete_by_C = res["complete_by_C"]

    pool = {}
    k_values = set()
    for Cset, labs in complete_by_C.items():
        if not Cset:
            continue
        kw = []
        for lab in labs:
            K, W = D.finalize_KW(driver, lab)
            kw.append((K, W))
        front = _pareto_front(kw)
        if front:
            pool[Cset] = front
            k_values.add(len(Cset))

    fs = res.get("frontier_sizes", [])
    peak_frontier = max((cnt for _lvl, cnt in fs), default=0)

    return dict(
        pool=pool,
        n_generated=res["n_labels_created"],
        n_surviving=res["n_labels_survived"],
        peak_frontier=peak_frontier,
        n_bundles=len(pool),
        k_values=k_values,
    )


def build_route_pool(travel_time, drivers, orders, B_gw, B_od, compat_graph=None):
    """Lap run_pool qua toan bo driver. Tra:
      pool_by_driver : {driver_id: {frozenset(order_ids): [(K,W)]}}
      agg            : dict tong hop metric toan instance (cong don qua driver)
    """
    pool_by_driver = {}
    n_generated = n_surviving = 0
    peak_frontier = 0
    n_bundles_total = 0
    k_values = set()

    for drv in drivers:
        r = run_pool(travel_time, drv, orders, B_gw, B_od, compat_graph=compat_graph)
        pool_by_driver[drv["id"]] = r["pool"]
        n_generated += r["n_generated"]
        n_surviving += r["n_surviving"]
        peak_frontier = max(peak_frontier, r["peak_frontier"])
        n_bundles_total += r["n_bundles"]
        k_values |= r["k_values"]

    agg = dict(
        n_generated=n_generated,
        n_surviving=n_surviving,
        peak_frontier=peak_frontier,   # max qua cac driver (khong cong don)
        n_bundles_total=n_bundles_total,
        k_values=sorted(k_values),
    )
    return pool_by_driver, agg
