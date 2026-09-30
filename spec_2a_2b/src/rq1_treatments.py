"""Rq1.md Sec5/Sec10 buoc4 - 5 treatment, dung tren top cua Algorithm A
(dp_labeling.build_route_pool) + Algorithm B (t8_cplex.solve_wdp qua
rq1_wdp.py). Hai treatment tuan tu (OD-FIRST->GW, GW-FIRST->OD) la code path
MOI (Rq1.md Sec5 dong 138) - can unit test/dry-run gate (Sec7) truoc khi dua
vao main grid, CHUA lam o day.

Metric (Sec6): true cost = K + theta_i * W (theta THAT). Moi treatment tra ve
tong true cost cua allocation cuoi cung (bao gom FD cost cho order di FD),
dung objective CPLEX tra ve truc tiep (model da dung true cost lam obj coeff -
xem rq1_wdp.build_wdp_drivers) - KHONG can tinh lai rieng.

KHONG import cplex truc tiep o day - lazy import trong t8_cplex (qua
rq1_wdp.solve_wdp_for_instance), de module nay import duoc tren may khong co
CPLEX active (vd unit test khong can giai that).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import dp_labeling as DL
import rq1_wdp as RW


def _pool_restricted_to_ids(pool_by_driver, driver_ids):
    return {did: pool_by_driver[did] for did in driver_ids if did in pool_by_driver}


def _ids_by_cls(drivers, cls):
    return [d["id"] for d in drivers if d["cls"] == cls]


def build_joint_pool(travel_time, drivers, orders, B_gw, B_od, compat_graph=None):
    """Algorithm A tren TOAN BO driver, MOT LAN. dp_labeling.run_pool tinh
    route pool cho MOI driver DOC LAP voi cac driver khac (chi phu thuoc
    driver do + orders + B) - da xac nhan bang thuc nghiem (pool cua 1 driver
    giong het du chay rieng hay chay cung driver khac). Vi vay pool cua tap
    con (vd chi GW) LUON giong het slice tuong ung cua pool day du - KHONG
    can chay lai run_pool rieng cho GW-ONLY/OD-ONLY/tung pass cua sequential,
    chi can loc pool_by_driver theo driver_ids. Toi uu nay KHONG doi ket qua
    (da verify: dp_labeling pool cho driver rieng le == slice cua pool chung),
    chi tranh goi build_route_pool lai nhieu lan/replication (truoc: 4
    lan/replication - JOINT, GW-ONLY, OD-ONLY, 2 pool cua sequential - la
    nguon chinh cua chi phi thoi gian o main grid n=20)."""
    return DL.build_route_pool(travel_time, drivers, orders, B_gw, B_od,
                               compat_graph=compat_graph)


def _build_pool_for_drivers(travel_time, drivers, orders, B_gw, B_od, compat_graph=None):
    """[GIU LAI de tuong thich nguoc / dung rieng le khi CAN chay lai that su
    (vd unit test doc lap). Main grid nen dung build_joint_pool() 1 lan roi
    slice qua cac ham run_*_from_pool ben duoi thay vi goi ham nay lap lai."""
    pool_by_driver, agg = DL.build_route_pool(travel_time, drivers, orders, B_gw, B_od,
                                              compat_graph=compat_graph)
    return pool_by_driver, agg


# ---------------------------------------------------------------------------
# Treatment 1: JOINT
# ---------------------------------------------------------------------------

def run_joint(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
             B_gw, B_od, compat_graph=None, presolve=True):
    """A(G∪C) -> B(full pool + FD). drivers = TOAN BO (GW+OD)."""
    pool_by_driver, agg = build_joint_pool(travel_time, drivers, orders, B_gw, B_od,
                                           compat_graph=compat_graph)
    return run_joint_from_pool(pool_by_driver, orders, theta_by_driver, q_o_by_order,
                               presolve=presolve, agg=agg)


def run_joint_from_pool(pool_by_driver, orders, theta_by_driver, q_o_by_order,
                        presolve=True, agg=None):
    r = RW.solve_wdp_for_instance(pool_by_driver, orders, theta_by_driver, q_o_by_order,
                                  presolve=presolve)
    return dict(true_cost=r["z"], alloc_x=r["alloc_x"], status=r["status"],
               pool_by_driver=pool_by_driver, agg=agg)


# ---------------------------------------------------------------------------
# Treatment 2/3: GW-ONLY / OD-ONLY
# ---------------------------------------------------------------------------

def run_single_class(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                     B_gw, B_od, cls, compat_graph=None, presolve=True):
    """cls in {"GW","OD"}. Driver cua lop kia bi LOAI HAN khoi input truoc khi
    chay Algorithm A (khong phai chi loc pool sau khi da sinh - Sec5 dong
    142-144 + [CHECK] dong 150-151)."""
    assert cls in ("GW", "OD")
    sub_drivers = [d for d in drivers if d["cls"] == cls]
    pool_by_driver, agg = _build_pool_for_drivers(travel_time, sub_drivers, orders, B_gw, B_od,
                                                  compat_graph=compat_graph)
    sub_theta = {d["id"]: theta_by_driver[d["id"]] for d in sub_drivers}
    r = RW.solve_wdp_for_instance(pool_by_driver, orders, sub_theta, q_o_by_order,
                                  presolve=presolve)
    return dict(true_cost=r["z"], alloc_x=r["alloc_x"], status=r["status"],
               pool_by_driver=pool_by_driver, agg=agg)


def run_single_class_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                               q_o_by_order, cls, presolve=True):
    """Ban toi uu: dung SLICE cua joint_pool_by_driver (build_joint_pool)
    thay vi chay lai Algorithm A rieng - dung khi joint_pool_by_driver DA
    duoc build tu TOAN BO drivers (bao gom ca lop cls va lop kia); slice ra
    CHI driver co cls tuong ung roi giai WDP CHI tren cac driver do (driver
    lop kia hoan toan khong xuat hien trong model - dung tinh than Sec5
    [CHECK] dong 150-151, day la ve MAT MO HINH WDP, khong phai ve viec pool
    cua 1 driver co doc lap voi driver khac hay khong - da xac nhan doc lap)."""
    assert cls in ("GW", "OD")
    sub_drivers = [d for d in drivers if d["cls"] == cls]
    sub_ids = [d["id"] for d in sub_drivers]
    pool_by_driver = _pool_restricted_to_ids(joint_pool_by_driver, sub_ids)
    sub_theta = {d["id"]: theta_by_driver[d["id"]] for d in sub_drivers}
    r = RW.solve_wdp_for_instance(pool_by_driver, orders, sub_theta, q_o_by_order,
                                  presolve=presolve)
    return dict(true_cost=r["z"], alloc_x=r["alloc_x"], status=r["status"],
               pool_by_driver=pool_by_driver)


def run_gw_only(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                B_gw, B_od, compat_graph=None, presolve=True):
    return run_single_class(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                            B_gw, B_od, "GW", compat_graph=compat_graph, presolve=presolve)


def run_od_only(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                B_gw, B_od, compat_graph=None, presolve=True):
    return run_single_class(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                            B_gw, B_od, "OD", compat_graph=compat_graph, presolve=presolve)


# ---------------------------------------------------------------------------
# Treatment 4/5: sequential (OD-FIRST->GW, GW-FIRST->OD) - CODE PATH MOI
# ---------------------------------------------------------------------------

def _orders_won_by_class(alloc_x, pool_by_driver_cls, drivers_cls):
    """Tu alloc_x (set ten bien x_<route_id> thang trong Pass 1, dinh dang
    t8_cplex 'x_<sanitized rid>'), suy nguoc ra tap order_id ma driver cua lop
    nay da nhan (dung lai rq1_wdp.build_wdp_drivers de tao lai anh xa rid->
    order_set, giu nguyen thu tu sinh rid nhu luc solve, dam bao khop 1-1)."""
    theta_dummy = {d["id"]: 0.0 for d in drivers_cls}   # chi can order_set, khong can cost dung
    wdp_drivers = RW.build_wdp_drivers(pool_by_driver_cls, theta_dummy)
    won = set()
    for did, dv in wdp_drivers.items():
        for (rid, order_set, _cost) in dv["routes"]:
            vname = "x_" + "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in rid)
            if vname in alloc_x:
                won |= set(order_set)
    return won


def run_sequential(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                   B_gw, B_od, first_cls, compat_graph=None, presolve=True):
    """first_cls = "OD" -> OD-FIRST->GW (Rq1.md Sec5 muc 4).
    first_cls = "GW" -> GW-FIRST->OD (muc 5, doi xung).

    Pass 1: B({first_cls routes} + FD) tren TOAN BO order -> O_first (order
      lop first_cls nhan).
    Pass 2: A(lop con lai) da co san (KHONG doi theo pass 1 - dung dung pool
      da sinh mot lan cho lop con lai, khong sinh lai) -> B({lop con lai
      routes} + FD) CHI tren O \\ O_first.
    Final: O_first (lop first_cls) hop ket qua pass 2 (lop con lai hoac FD)
      cho phan con lai.
    """
    assert first_cls in ("GW", "OD")
    second_cls = "OD" if first_cls == "GW" else "GW"

    drivers_first = [d for d in drivers if d["cls"] == first_cls]
    drivers_second = [d for d in drivers if d["cls"] == second_cls]

    pool_first, agg_first = _build_pool_for_drivers(travel_time, drivers_first, orders,
                                                     B_gw, B_od, compat_graph=compat_graph)
    pool_second, agg_second = _build_pool_for_drivers(travel_time, drivers_second, orders,
                                                       B_gw, B_od, compat_graph=compat_graph)

    return _run_sequential_with_pools(pool_first, pool_second, drivers_first, drivers_second,
                                      orders, theta_by_driver, q_o_by_order, first_cls,
                                      presolve=presolve, agg_first=agg_first, agg_second=agg_second)


def run_sequential_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                             q_o_by_order, first_cls, presolve=True):
    """Ban toi uu: slice joint_pool_by_driver thay vi chay lai Algorithm A
    (xem docstring run_single_class_from_pool / build_joint_pool ve tinh doc
    lap cua pool tung driver)."""
    assert first_cls in ("GW", "OD")
    second_cls = "OD" if first_cls == "GW" else "GW"
    drivers_first = [d for d in drivers if d["cls"] == first_cls]
    drivers_second = [d for d in drivers if d["cls"] == second_cls]
    pool_first = _pool_restricted_to_ids(joint_pool_by_driver, [d["id"] for d in drivers_first])
    pool_second = _pool_restricted_to_ids(joint_pool_by_driver, [d["id"] for d in drivers_second])
    return _run_sequential_with_pools(pool_first, pool_second, drivers_first, drivers_second,
                                      orders, theta_by_driver, q_o_by_order, first_cls,
                                      presolve=presolve)


def _run_sequential_with_pools(pool_first, pool_second, drivers_first, drivers_second,
                               orders, theta_by_driver, q_o_by_order, first_cls,
                               presolve=True, agg_first=None, agg_second=None):
    theta_first = {d["id"]: theta_by_driver[d["id"]] for d in drivers_first}
    theta_second = {d["id"]: theta_by_driver[d["id"]] for d in drivers_second}

    # Pass 1: toan bo order, chi route cua first_cls + FD
    r1 = RW.solve_wdp_for_instance(pool_first, orders, theta_first, q_o_by_order,
                                   presolve=presolve)
    O_first = _orders_won_by_class(r1["alloc_x"], pool_first, drivers_first)

    # Pass 2: A(lop con lai) da co san, chi giai tren O \ O_first
    O_remaining = set(orders.keys()) - O_first
    if O_remaining:
        r2 = RW.solve_wdp_for_instance(pool_second, orders, theta_second, q_o_by_order,
                                       restrict_orders=O_remaining, presolve=presolve)
        cost2 = r2["z"]
        alloc2 = r2["alloc_x"]
        status2 = r2["status"]
    else:
        cost2 = 0.0
        alloc2 = set()
        status2 = "no_remaining_orders"

    # Final true cost = cost cua Pass1 CHI PHAN O_first (khong phai r1["z"]
    # toan bo, vi r1 giai tren TOAN BO order kem FD cho phan con lai - phan do
    # se bi Pass2 giai lai) + cost Pass2 (da bao gom FD cho phan con lai neu
    # co). Lay lai tu alloc_x cua Pass1, CHI cac route/FD-var lien quan toi
    # order trong O_first, dung nguyen gia tri objective coefficient da dung
    # khi build model Pass1 cho cac bien do (khong uoc luong lai).
    cost_first_part = _true_cost_of_alloc_subset(pool_first, theta_first, q_o_by_order,
                                                  r1["alloc_x"], O_first)

    total_true_cost = cost_first_part + cost2

    return dict(true_cost=total_true_cost, first_cls=first_cls,
               O_first=O_first, O_remaining=O_remaining,
               pass1=r1, pass2=dict(z=cost2, alloc_x=alloc2, status=status2),
               pool_first=pool_first, pool_second=pool_second,
               agg_first=agg_first, agg_second=agg_second)


def _true_cost_of_alloc_subset(pool_by_driver_cls, theta_by_driver_cls, q_o_by_order,
                               alloc_x, order_subset):
    """Cong true cost CHINH XAC cua cac bien trong alloc_x ma order_set cua no
    nam TRON VEN trong order_subset (route/FD chi gan order thuoc O_first se
    luon co dang nay vi cover constraint dam bao moi order chi 1 bien active -
    khong co truong hop route "lan" ca order trong va ngoai subset)."""
    wdp_drivers = RW.build_wdp_drivers(pool_by_driver_cls, theta_by_driver_cls)
    total = 0.0
    for did, dv in wdp_drivers.items():
        for (rid, order_set, cost) in dv["routes"]:
            vname = "x_" + "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in rid)
            if vname in alloc_x and set(order_set) <= order_subset:
                total += cost
    for o in order_subset:
        vname = "z_" + "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in o)
        if vname in alloc_x:
            total += q_o_by_order[o]
    return total


def run_od_first(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                 B_gw, B_od, compat_graph=None, presolve=True):
    return run_sequential(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                          B_gw, B_od, "OD", compat_graph=compat_graph, presolve=presolve)


def run_gw_first(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                 B_gw, B_od, compat_graph=None, presolve=True):
    return run_sequential(travel_time, drivers, orders, theta_by_driver, q_o_by_order,
                          B_gw, B_od, "GW", compat_graph=compat_graph, presolve=presolve)


def run_od_first_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                           q_o_by_order, presolve=True):
    return run_sequential_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                                    q_o_by_order, "OD", presolve=presolve)


def run_gw_first_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                           q_o_by_order, presolve=True):
    return run_sequential_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                                    q_o_by_order, "GW", presolve=presolve)


def run_gw_only_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                          q_o_by_order, presolve=True):
    return run_single_class_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                                      q_o_by_order, "GW", presolve=presolve)


def run_od_only_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                          q_o_by_order, presolve=True):
    return run_single_class_from_pool(joint_pool_by_driver, drivers, orders, theta_by_driver,
                                      q_o_by_order, "OD", presolve=presolve)


# ---------------------------------------------------------------------------
# Metric (Rq1.md Sec6)
# ---------------------------------------------------------------------------

def complementarity_gain(c_joint, c_gw_only, c_od_only):
    best_single = min(c_gw_only, c_od_only)
    if best_single == 0:
        return None
    return (best_single - c_joint) / best_single


if __name__ == "__main__":
    # Smoke test nho, KHONG can CPLEX active de kiem tra cac ham build/filter
    # (chi phan solve_wdp_for_instance moi can CPLEX that).
    import random
    import instance_gen as IG
    import rq1_cost_gen as RC

    rng = random.Random(7)
    drivers, orders, tt, meta = IG.generate_instance(
        n=6, B_gw=3, B_od=2, tw_width=120, n_drivers=4, seed=123,
        tau=30.0, spatial_mode="dispersed")

    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    gw_ids = _ids_by_cls(drivers, "GW")
    od_ids = _ids_by_cls(drivers, "OD")
    print("n_orders=%d  GW drivers=%s  OD drivers=%s" % (len(orders), gw_ids, od_ids))
    print("[OK] rq1_treatments.py import + helper functions chay khong loi "
         "(chua goi solve_wdp_for_instance - can CPLEX active).")
