"""Rq1.md Sec7/Sec10 buoc5 - Dry run gate BAT BUOC truoc khi chay main grid:
n<=6, 1 alignment level, so JOINT (va toan bo 5 treatment) voi brute-force,
xac nhan hai treatment tuan tu (code path MOI, rq1_treatments.py run_sequential)
cho dung ket qua brute-force.

Oracle doc lap:
  - Route pool: brute_force.brute_pool_for_driver (da audit doc lap, dung o
    Gate 0/616/160 va Testb_hull_final.md Gate Sec3 - KHONG dung lai
    dp_labeling.run_pool/t6_dp cho oracle, tranh "tu kiem tra minh").
  - WDP: brute-force THAT (khong dung CPLEX cho oracle) - vi n<=6, B<=3, so
    driver nho (4-6), khong gian to hop (route-per-driver + FD-per-order) đủ
    nho de duyet het bang exhaustive search thuan Python.

So sanh true_cost (Sec6: K + theta_i*W) cua oracle voi rq1_treatments.py (dung
CPLEX qua t8_cplex.solve_wdp) cho CA 5 treatment tren cung instance/theta/q_o.
"""

import itertools
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import brute_force as BF
import rq1_cost_gen as RC
import rq1_treatments as RT

EPS = 1e-6


# ---------------------------------------------------------------------------
# Oracle: exhaustive WDP (khong CPLEX) tren pool da cho boi brute_force.py
# ---------------------------------------------------------------------------

def _driver_route_options(pool, theta_i):
    """pool: {frozenset(bundle): [(K,W)...]} (tu brute_pool_for_driver, DA
    Pareto-filtered - an toan cho WDP vi diem toi uu true-cost luon nam tren
    Pareto front). Tra list (bundle_frozenset, true_cost) - MOI diem (K,W) la
    1 option rieng (co the >1 option cung bundle, WDP se tu chon re nhat khi
    duyet exhaustive)."""
    opts = []
    for bundle, kw_list in pool.items():
        if not bundle:
            continue
        for (K, W) in kw_list:
            opts.append((bundle, K + theta_i * W))
    return opts


def exhaustive_wdp(pools_by_driver, theta_by_driver, order_ids, q_o_by_order,
                   driver_ids=None, restrict_orders=None):
    """Duyet TOAN BO to hop (chon <=1 route/driver, phan con lai cua
    restrict_orders di FD, MOI order trong restrict_orders phai duoc phu dung
    1 lan - route hoac FD) - KHONG heuristic, dung cho n<=6 (khong gian nho).

    driver_ids: gioi han tap driver duoc dua vao (None = tat ca trong
    pools_by_driver) - dung cho GW-ONLY/OD-ONLY/sequential pass.
    restrict_orders: gioi han tap order PHAI duoc phu (None = toan bo
    order_ids) - dung cho sequential pass 2.

    Tra (best_cost, best_assignment) voi best_assignment =
    {driver_id: (bundle_frozenset, route_true_cost) hoac None} (None = driver
    khong nhan route). LUU CA route_true_cost o day (khong chi bundle) vi 1
    bundle co the co NHIEU diem Pareto (K,W) khac cost - chi biet bundle
    khong du de suy nguoc dung cost route da duoc CHON (BUG da tung mac phai:
    tra ve bundle roi tra cuu lai theo bundle se lay nham diem Pareto dau
    tien thay vi diem THAT SU duoc chon trong loi giai toi uu)."""
    if driver_ids is None:
        driver_ids = list(pools_by_driver.keys())
    target_orders = set(order_ids) if restrict_orders is None else set(restrict_orders)

    # options[d] = list (bundle, cost) CHI gom bundle <= target_orders (route
    # "lan" ra ngoai target_orders khong hop le trong Pass2/subset-restricted).
    options = {}
    for d in driver_ids:
        theta_i = theta_by_driver[d]
        opts = [(b, c) for (b, c) in _driver_route_options(pools_by_driver[d], theta_i)
               if set(b) <= target_orders]
        options[d] = [(None, 0.0)] + opts   # None = driver khong lam gi

    best_cost = None
    best_assign = None
    driver_list = list(driver_ids)

    def rec(idx, covered, assign, cost_so_far):
        nonlocal best_cost, best_assign
        if best_cost is not None and cost_so_far >= best_cost - EPS:
            pass  # khong prune manh (n nho, uu tien dung/de doc hon toc do)
        if idx == len(driver_list):
            remaining = target_orders - covered
            total = cost_so_far + sum(q_o_by_order[o] for o in remaining)
            if best_cost is None or total < best_cost - EPS:
                best_cost = total
                best_assign = dict(assign)
            return
        d = driver_list[idx]
        for (bundle, cost) in options[d]:
            if bundle is not None:
                if bundle & covered:
                    continue   # order da duoc driver khac lay trong nhanh nay
                assign[d] = (bundle, cost)
                rec(idx + 1, covered | set(bundle), assign, cost_so_far + cost)
                del assign[d]
            else:
                assign[d] = None
                rec(idx + 1, covered, assign, cost_so_far)
                del assign[d]

    rec(0, frozenset(), {}, 0.0)
    return best_cost, best_assign


# ---------------------------------------------------------------------------
# 5 treatment, ban ORACLE (exhaustive, khong CPLEX)
# ---------------------------------------------------------------------------

def oracle_joint(pools_by_driver, theta_by_driver, order_ids, q_o_by_order):
    cost, assign = exhaustive_wdp(pools_by_driver, theta_by_driver, order_ids, q_o_by_order)
    return cost


def oracle_single_class(pools_by_driver, theta_by_driver, order_ids, q_o_by_order,
                        drivers, cls):
    ids = [d["id"] for d in drivers if d["cls"] == cls]
    cost, assign = exhaustive_wdp(pools_by_driver, theta_by_driver, order_ids, q_o_by_order,
                                  driver_ids=ids)
    return cost


def oracle_sequential(pools_by_driver, theta_by_driver, order_ids, q_o_by_order,
                      drivers, first_cls):
    second_cls = "OD" if first_cls == "GW" else "GW"
    first_ids = [d["id"] for d in drivers if d["cls"] == first_cls]
    second_ids = [d["id"] for d in drivers if d["cls"] == second_cls]

    cost1, assign1 = exhaustive_wdp(pools_by_driver, theta_by_driver, order_ids, q_o_by_order,
                                    driver_ids=first_ids)
    O_first = set()
    for d, entry in assign1.items():
        if entry:
            bundle, _cost = entry
            O_first |= set(bundle)
    # true cost phan O_first: CHI cac route trong assign1 (FD trong Pass1 cho
    # order thuoc O_remaining se BI BO, Pass2 giai lai phan do) - vi assign1
    # la assignment TOI UU cho toan bo order_ids, phan FD cua no cho order
    # KHONG thuoc O_first khong duoc tinh vao day. Dung THANG cost da luu
    # trong assign1 (khong tra cuu lai theo bundle - tranh bug lay nham diem
    # Pareto khi 1 bundle co nhieu diem (K,W) khac cost).
    cost_first_part = sum(cost for entry in assign1.values() if entry for (_b, cost) in [entry])
    O_remaining = set(order_ids) - O_first
    if O_remaining:
        cost2, assign2 = exhaustive_wdp(pools_by_driver, theta_by_driver, order_ids,
                                        q_o_by_order, driver_ids=second_ids,
                                        restrict_orders=O_remaining)
    else:
        cost2 = 0.0
    return cost_first_part + cost2, O_first


def main():
    print("=== Rq1.md Sec7/Buoc5 - Dry-run gate n<=6, so JOINT+4 treatment voi brute-force ===\n")

    N_GRID = [3, 4, 5, 6]
    B_GRID = [(2, 2), (3, 2), (2, 3)]
    TW_GRID = [60, 120]
    SEEDS = [0, 1, 2]

    total = 0
    violations = []

    for n in N_GRID:
        for (B_gw, B_od) in B_GRID:
            for tw in TW_GRID:
                for seed in SEEDS:
                    total += 1
                    gen_seed = IG.stable_seed(n, B_gw, B_od, tw, seed, "rq1_dryrun_gate")
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=4,
                        seed=gen_seed, tau=30.0, spatial_mode="dispersed")

                    rng = random.Random(gen_seed)
                    theta_by_driver = RC.assign_theta(rng, drivers)
                    q_o_by_order = RC.assign_q_o(orders, tt)
                    order_ids = list(orders.keys())

                    pools_by_driver = {}
                    for drv in drivers:
                        B = B_gw if drv["cls"] == "GW" else B_od
                        pools_by_driver[drv["id"]] = BF.brute_pool_for_driver(
                            tt, drv, orders, B_gw, B_od)

                    # --- oracle (exhaustive, khong CPLEX) ---
                    oc_joint = oracle_joint(pools_by_driver, theta_by_driver, order_ids, q_o_by_order)
                    oc_gw = oracle_single_class(pools_by_driver, theta_by_driver, order_ids,
                                                q_o_by_order, drivers, "GW")
                    oc_od = oracle_single_class(pools_by_driver, theta_by_driver, order_ids,
                                                q_o_by_order, drivers, "OD")
                    oc_odfirst, _ = oracle_sequential(pools_by_driver, theta_by_driver, order_ids,
                                                      q_o_by_order, drivers, "OD")
                    oc_gwfirst, _ = oracle_sequential(pools_by_driver, theta_by_driver, order_ids,
                                                      q_o_by_order, drivers, "GW")

                    # --- pipeline that (rq1_treatments.py, dung CPLEX) - dung
                    # DUNG DUONG DAN toi uu (build_joint_pool 1 lan + cac ham
                    # *_from_pool) MA rq1_main_grid.py thuc su se dung, khong
                    # phai duong chua toi uu - gate phai kiem tra CHINH XAC
                    # code path se chay tren main grid. ---
                    joint_pool, joint_agg = RT.build_joint_pool(tt, drivers, orders, B_gw, B_od)
                    pl_joint = RT.run_joint_from_pool(joint_pool, orders, theta_by_driver,
                                                      q_o_by_order, agg=joint_agg)["true_cost"]
                    pl_gw = RT.run_gw_only_from_pool(joint_pool, drivers, orders, theta_by_driver,
                                                     q_o_by_order)["true_cost"]
                    pl_od = RT.run_od_only_from_pool(joint_pool, drivers, orders, theta_by_driver,
                                                     q_o_by_order)["true_cost"]
                    pl_odfirst = RT.run_od_first_from_pool(joint_pool, drivers, orders,
                                                           theta_by_driver, q_o_by_order)["true_cost"]
                    pl_gwfirst = RT.run_gw_first_from_pool(joint_pool, drivers, orders,
                                                           theta_by_driver, q_o_by_order)["true_cost"]

                    checks = [
                        ("JOINT", oc_joint, pl_joint),
                        ("GW-ONLY", oc_gw, pl_gw),
                        ("OD-ONLY", oc_od, pl_od),
                        ("OD-FIRST", oc_odfirst, pl_odfirst),
                        ("GW-FIRST", oc_gwfirst, pl_gwfirst),
                    ]
                    for name, oc, pl in checks:
                        if abs(oc - pl) > 1e-3:
                            violations.append(dict(
                                n=n, B_gw=B_gw, B_od=B_od, tw=tw, seed=seed,
                                treatment=name, oracle=oc, pipeline=pl, diff=abs(oc - pl)))

    print("Tong instance: %d  (x 5 treatment = %d check)" % (total, total * 5))
    if violations:
        print("\n[FAIL] %d/%d violation:" % (len(violations), total * 5))
        for v in violations[:30]:
            print("  n=%d B=(%d,%d) tw=%d seed=%d treatment=%s oracle=%.4f pipeline=%.4f diff=%.6f"
                 % (v["n"], v["B_gw"], v["B_od"], v["tw"], v["seed"], v["treatment"],
                    v["oracle"], v["pipeline"], v["diff"]))
    else:
        print("\n[PASS] 0/%d violation - ca 5 treatment (bao gom 2 sequential code path MOI) "
             "khop CHINH XAC voi oracle exhaustive tren toan bo grid n<=6." % (total * 5))
    return violations


if __name__ == "__main__":
    main()
