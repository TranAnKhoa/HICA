"""LP_dual.md - LP-Dual Reduced-Cost Fixing.

Khac ban chat voi 3 huong da REJECTED (hull trong-driver, hull toan cuc,
min-max cross-driver): LP relaxation KHONG xap xi su canh tranh toan cuc -
no giai DUNG bai toan toan cuc that (moi driver, moi rang buoc covering,
cung luc), chi noi bien 0/1 thanh [0,1]. Dual price tu dong gom het tuong
tac giua driver, khong can mo hinh hoa tay.

Dieu kien (Sec0):
  rc_ir(b) = c_ir(b_i) - Sum_{o in S} pi_o(b)   (reduced cost cua route r tai
                                                  bid vector b)
  prune(r) := rc_ir(b*) > 0   voi b* = (b_i=theta_min, b_j=theta_max moi j!=i)

RUI RO RIENG (khac 3 lan truoc): shortcut chi kiem 1 diem bien b* dua tren
GIA DINH CHUA KIEM CHUNG "rc_ir don dieu, nho nhat tai b*". Buoc 0 (Sec1) BAT
BUOC kiem gia dinh nay TRUOC khi tin shortcut.

Dung lai t8_cplex.build_model logic (constraint names cov_<order>/one_<driver>)
nhung DOI type bien tu "B" (binary) sang continuous [0,1] (LP relaxation that
su) - khong sua t8_cplex.py goc, viet ham build rieng o day.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import rq1_wdp as RW
import testC2_activation_rate as T

THETA_MIN = RC.THETA_MIN
THETA_MAX = RC.THETA_MAX


def _sanitize(s):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def build_lp_relaxation(wdp_drivers, order_ids, fd_cost, excluded_driver=None,
                        restrict_orders=None):
    """Giong t8_cplex.build_model NHUNG bien continuous [0,1] (LP that, khong
    phai MIP) - de lay dual price qua get_dual_values(). wdp_drivers dinh
    dang rq1_wdp.build_wdp_drivers output ({driver_id: {"routes": [(rid,
    order_set, cost), ...]}})."""
    _CPLEX_PATH = os.path.join("K:" + os.sep, "Programing Hardware", "Cplex", "cplex",
                               "python", "3.7", "x64_win64")
    if _CPLEX_PATH not in sys.path:
        sys.path.insert(0, _CPLEX_PATH)
    import cplex  # noqa: E402 - lazy import, chi can khi giai LP that

    order_set = set(order_ids) if restrict_orders is None else set(restrict_orders)

    c = cplex.Cplex()
    c.set_results_stream(None)
    c.set_log_stream(None)
    c.set_warning_stream(None)
    c.set_error_stream(None)
    c.parameters.threads.set(1)
    c.objective.set_sense(c.objective.sense.minimize)

    names, objs = [], []
    cover = {o: [] for o in order_set}
    driver_vars = {}
    rid_to_varname = {}

    for d, dv in wdp_drivers.items():
        if d == excluded_driver:
            continue
        for (rid, ofs, cost) in dv["routes"]:
            if not set(ofs) <= order_set:
                continue
            v = "x_" + _sanitize(rid)
            rid_to_varname[rid] = v
            names.append(v); objs.append(float(cost))
            driver_vars.setdefault(d, []).append(v)
            for o in ofs:
                cover[o].append(v)

    for o in order_set:
        v = "z_" + _sanitize(o)
        names.append(v); objs.append(float(fd_cost[o]))
        cover[o].append(v)

    # LP relaxation: continuous [0,1], KHONG dat types="B" (khac t8_cplex.build_model)
    c.variables.add(obj=objs, lb=[0.0] * len(names), ub=[1.0] * len(names), names=names)

    rows, senses, rhs, rnames = [], [], [], []
    for o in sorted(order_set):
        rows.append([cover[o], [1.0] * len(cover[o])])
        senses.append("E"); rhs.append(1.0); rnames.append("cov_" + _sanitize(o))
    for d, vs in driver_vars.items():
        rows.append([vs, [1.0] * len(vs)])
        senses.append("L"); rhs.append(1.0); rnames.append("one_" + _sanitize(d))
    c.linear_constraints.add(lin_expr=rows, senses=senses, rhs=rhs, names=rnames)

    return c, rid_to_varname


def solve_lp_get_duals(wdp_drivers, order_ids, fd_cost, excluded_driver=None,
                       restrict_orders=None):
    """Giai LP relaxation, tra (z_lp, pi_by_order dict, rid_to_varname)."""
    c, rid_to_varname = build_lp_relaxation(wdp_drivers, order_ids, fd_cost,
                                            excluded_driver, restrict_orders)
    c.solve()
    z_lp = c.solution.get_objective_value()

    order_set = set(order_ids) if restrict_orders is None else set(restrict_orders)
    pi_by_order = {}
    for o in order_set:
        cname = "cov_" + _sanitize(o)
        idx = c.linear_constraints.get_indices(cname)
        pi_by_order[o] = c.solution.get_dual_values(idx)

    c.end()
    return z_lp, pi_by_order, rid_to_varname


def compute_reduced_cost(pool_by_driver, orders, fd_cost, driver_id, order_set, K, W, theta_i,
                         theta_others):
    """rc_ir(b) = c_ir(b_i) - Sum_{o in S} pi_o(b). theta_others: {driver_id:
    theta} cho MOI driver KHAC driver_id (dung de giai LP relaxation tai bid
    vector b nay, chinh route r VAN nam trong pool - LP tu quyet dinh co
    dung no hay khong, dual price la SAN PHAM PHU cua viec giai LP nay)."""
    order_ids = list(orders.keys())
    theta_full = dict(theta_others)
    theta_full[driver_id] = theta_i
    wdp_drivers = RW.build_wdp_drivers(pool_by_driver, theta_full)

    z_lp, pi_by_order, rid_to_varname = solve_lp_get_duals(wdp_drivers, order_ids, fd_cost)

    c_ir = K + theta_i * W
    rc = c_ir - sum(pi_by_order[o] for o in order_set)
    return rc, z_lp, pi_by_order


# ---------------------------------------------------------------------------
# [CHECK][STOP] Buoc 0 - Kiem gia dinh don dieu TRUOC KHI tin shortcut (Sec1)
# ---------------------------------------------------------------------------

def check_monotonicity_for_route(pool_by_driver, orders, fd_cost, driver_id, order_set, K, W,
                                  driver_ids, n_grid_points=8, seed=0):
    """Sec1: kiem rc_ir(b*) co la MIN tren toan dai hay khong (quet luoi tho
    tren cac chieu theta cua driver KHAC). Tra list violation (b_test, rc_test
    < rc_at_star)."""
    import random
    rng = random.Random(seed)

    others = [d for d in driver_ids if d != driver_id]
    theta_star_others = {d: THETA_MAX for d in others}
    rc_star, z_star, _ = compute_reduced_cost(pool_by_driver, orders, fd_cost, driver_id,
                                              order_set, K, W, THETA_MIN, theta_star_others)

    violations = []
    for _ in range(n_grid_points):
        theta_test_others = {d: rng.uniform(THETA_MIN, THETA_MAX) for d in others}
        theta_i_test = rng.uniform(THETA_MIN, THETA_MAX)
        rc_test, z_test, _ = compute_reduced_cost(pool_by_driver, orders, fd_cost, driver_id,
                                                   order_set, K, W, theta_i_test,
                                                   theta_test_others)
        if rc_test < rc_star - 1e-6:
            violations.append(dict(theta_i=theta_i_test, theta_others=theta_test_others,
                                   rc_test=rc_test, rc_star=rc_star))

    return rc_star, violations


def run_step0_monotonicity_check(n, B_gw, B_od, tw_width, n_drivers, seed, tau,
                                 n_routes_to_check=20, n_grid_points=8):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=tau, spatial_mode="dispersed")
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
    fd_cost = RC.assign_q_o(orders, tt)
    all_routes = T.route_ids_for_pool(pool_by_driver)
    driver_ids = [d["id"] for d in drivers]

    # Uu tien route GAN bien prune (rc_ir(b*) gan 0) - can rc_star truoc, nen
    # lam 1 pass nhanh de xep hang, roi chi kiem monotonicity ky tren top N.
    print("Buoc 0.1: tinh rc_star cho toan bo pool de xep hang route gan bien...")
    all_rc_star = []
    for rid, (did, order_set, K, W) in all_routes.items():
        others = [d for d in driver_ids if d != did]
        theta_star_others = {d: THETA_MAX for d in others}
        rc_star, _, _ = compute_reduced_cost(pool_by_driver, orders, fd_cost, did, order_set,
                                             K, W, THETA_MIN, theta_star_others)
        all_rc_star.append((abs(rc_star), rid, did, order_set, K, W, rc_star))

    all_rc_star.sort(key=lambda x: x[0])
    top_routes = all_rc_star[:n_routes_to_check]

    print("Buoc 0.2: kiem monotonicity cho %d route gan bien nhat..." % len(top_routes))
    all_violations = []
    for (_, rid, did, order_set, K, W, rc_star) in top_routes:
        rc_star2, violations = check_monotonicity_for_route(
            pool_by_driver, orders, fd_cost, did, order_set, K, W, driver_ids,
            n_grid_points=n_grid_points)
        if violations:
            print("  [VIOLATION] rid=%s driver=%s rc_star=%.4f -> %d violation"
                 % (rid, did, rc_star2, len(violations)))
            for v in violations[:3]:
                print("      rc_test=%.4f < rc_star=%.4f  theta_i=%.2f"
                     % (v["rc_test"], v["rc_star"], v["theta_i"]))
            all_violations.append(dict(rid=rid, driver=did, rc_star=rc_star2, violations=violations))

    print("\n=== Buoc 0 ket qua: n=%d n_drivers=%d seed=%d ===" % (n, n_drivers, seed))
    print("Route kiem: %d/%d (uu tien gan bien)" % (len(top_routes), len(all_routes)))
    print("Route co vi pham monotonicity: %d" % len(all_violations))
    if all_violations:
        print("[FAIL - Buoc 0] Gia dinh don dieu SAI - KHONG dung shortcut 1-diem.")
    else:
        print("[PASS - Buoc 0] Gia dinh don dieu dung tren mau da kiem.")

    return dict(n_checked=len(top_routes), n_violations=len(all_violations),
               violations=all_violations)


if __name__ == "__main__":
    configs = [
        dict(n=12, B_gw=3, B_od=3, n_drivers=5, seed=42),
        dict(n=10, B_gw=3, B_od=3, n_drivers=4, seed=1),
        dict(n=15, B_gw=3, B_od=3, n_drivers=5, seed=7),
        dict(n=12, B_gw=3, B_od=3, n_drivers=6, seed=123),
        dict(n=10, B_gw=3, B_od=3, n_drivers=4, seed=999),
    ]
    all_results = []
    for cfg in configs:
        print("\n" + "=" * 70)
        print("Config:", cfg)
        r = run_step0_monotonicity_check(tw_width=120, tau=30.0, n_routes_to_check=20,
                                         n_grid_points=8, **cfg)
        all_results.append((cfg, r))

    print("\n\n=== TONG HOP BUOC 0 ===")
    total_violations = 0
    for cfg, r in all_results:
        print("n=%d n_drivers=%d seed=%d: checked=%d violations=%d"
             % (cfg["n"], cfg["n_drivers"], cfg["seed"], r["n_checked"], r["n_violations"]))
        total_violations += r["n_violations"]
    print("\nTONG violations qua %d instance = %d" % (len(all_results), total_violations))
    if total_violations == 0:
        print("[PASS TOAN BO - Buoc 0] Duoc phep tiep tuc Buoc 1 (audit shortcut).")
    else:
        print("[FAIL - Buoc 0] Chuyen sang phuong an du phong Sec4, KHONG dung shortcut 1-diem.")
