"""Rq1.md Sec2 - Algorithm B (WDP MILP that, CPLEX) cho instance cua
instance_gen.py. Cau noi con THIEU: pool_by_driver (dp_labeling.build_route_pool,
dang {frozenset(order_ids): [(K,W)]}) khong the dua thang vao MILP - moi diem
Pareto (K,W) can quy ve MOT cost so bang true cost = K + theta_i * W (Rq1.md
Sec6 "Dung true cost, khong dung reported cost").

Tai su dung build_model()/solve_model() tu experiments/T2BFS/t8_cplex.py
(cung dinh dang bien x_<route_id> covering + z_<order_id> cho FD) - KHONG viet
lai logic MILP, chi doi ham chuan bi input (route/order/fd_cost dict).

KHONG dung/import cplex truc tiep o day - de goi duoc tu may khong co CPLEX
(vd script test khac chi can ham chuan bi du lieu), import cplex xay ra o
noi goi solve that (main() / script vec1_speedup hay tuong tu).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)


def route_true_cost(K, W, theta_i):
    """Rq1.md Sec6: true cost = K + theta_i * W (theta THAT, khong phai gia
    bid/reported)."""
    return K + theta_i * W


def build_wdp_drivers(pool_by_driver, theta_by_driver):
    """Chuyen pool_by_driver (dp_labeling.build_route_pool output) + theta
    (rq1_cost_gen.assign_theta output) -> dinh dang t8_cplex.build_model can:
      {driver_id: {"routes": [(route_id, order_frozenset, true_cost), ...]}}

    MOI diem Pareto (K,W) trong pool tro thanh MOT route rieng (co the co
    NHIEU route cung bundle order neu Pareto front co >1 diem - dung, vi day
    la cac phuong an chi-phi-vs-thoi-gian khac nhau THAT su cho cung 1 tap
    order, WDP duoc chon route nao re nhat theo true cost).
    """
    out = {}
    for did, pool in pool_by_driver.items():
        theta_i = theta_by_driver[did]
        routes = []
        rid_ctr = 0
        for order_set, kw_list in pool.items():
            for (K, W) in kw_list:
                rid = "%s_r%d" % (did, rid_ctr)
                rid_ctr += 1
                cost = route_true_cost(K, W, theta_i)
                routes.append((rid, order_set, cost))
        out[did] = {"routes": routes}
    return out


def build_wdp_orders_fdcost(orders, q_o_by_order):
    """orders: dict tu instance_gen (keys = order id). q_o_by_order: tu
    rq1_cost_gen.assign_q_o. Tra (order_id_list, fd_cost_dict) dung dinh dang
    t8_cplex.build_model/solve_wdp can (orders la list/iterable ten order,
    fd_cost la dict ten order -> cost)."""
    order_ids = list(orders.keys())
    fd_cost = {oid: q_o_by_order[oid] for oid in order_ids}
    return order_ids, fd_cost


def solve_wdp_for_instance(pool_by_driver, orders, theta_by_driver, q_o_by_order,
                           excluded_driver=None, restrict_orders=None, presolve=True):
    """Ham tien ich goi thang t8_cplex.solve_wdp voi du lieu da chuyen doi.
    CAN CPLEX (import o day, chi khi ham nay duoc goi - de module import duoc
    tren may khong co CPLEX, chi loi khi THAT SU can giai)."""
    import t8_cplex as T8  # noqa: E402  (import cham - chi khi can CPLEX that)

    wdp_drivers = build_wdp_drivers(pool_by_driver, theta_by_driver)
    order_ids, fd_cost = build_wdp_orders_fdcost(orders, q_o_by_order)

    return T8.solve_wdp(wdp_drivers, order_ids, fd_cost,
                        excluded_driver=excluded_driver,
                        restrict_orders=restrict_orders, presolve=presolve)


if __name__ == "__main__":
    # smoke test nho: n=6, khong can CPLEX that o day - chi kiem tra
    # build_wdp_drivers/build_wdp_orders_fdcost tao dung dinh dang, KHONG
    # goi solve_wdp_for_instance (de chay duoc ca khi may goi khong active
    # CPLEX path).
    import random
    import instance_gen as IG
    import dp_labeling as DL
    import rq1_cost_gen as RC

    rng = random.Random(7)
    drivers, orders, tt, meta = IG.generate_instance(
        n=6, B_gw=3, B_od=2, tw_width=120, n_drivers=4, seed=123,
        tau=30.0, spatial_mode="dispersed")

    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw=3, B_od=2)
    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    wdp_drivers = build_wdp_drivers(pool_by_driver, theta_by_driver)
    order_ids, fd_cost = build_wdp_orders_fdcost(orders, q_o_by_order)

    print("n_drivers=%d  n_orders=%d" % (len(wdp_drivers), len(order_ids)))
    for did, dv in wdp_drivers.items():
        print("  %s: %d routes, theta=%.3f" % (did, len(dv["routes"]), theta_by_driver[did]))
    print("fd_cost sample:", dict(list(fd_cost.items())[:3]))
    print("\n[OK] build_wdp_drivers/build_wdp_orders_fdcost chay khong loi.")
