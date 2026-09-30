"""Test_min_max.md - Min-Max Bound Pruning (cross-driver alternative covering).

Dieu kien (Sec0):
  prune(r) := c_ir(b_min) >= Alt(S, i; b_max)

  c_ir(b_min) = K_ir + b_min * W_ir   (chi phi cua r tai kich ban CO LOI NHAT)
  Alt(S, i; b_max) = chi phi re nhat de phu DUNG tap order S bang driver KHAC
                      i (moi route ung vien dinh gia tai b_max - kich ban BAT
                      LOI NHAT cho doi thu) hoac FD, KHONG dung driver i.

An toan (necessary condition): neu ngay o kich ban loi nhat cho r ma van thua
kich ban bat loi nhat cho doi thu, khong ton tai b nao khien r thang that.

KHONG doi logic sinh route (Algorithm A nguyen ven) - day la buoc POST-FILTER
apply SAU khi pool da sinh xong.
"""

import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import testC2_activation_rate as T

THETA_MIN = RC.THETA_MIN
THETA_MAX = RC.THETA_MAX


def _min_cost_to_cover(S, candidates, fd_costs):
    """Sec1: DP tren bitmask cua S (|S|<=B<=5 => 2^5=32 trang thai toi da).
    candidates: list (bundle_frozenset, cost) - route cua driver KHAC da dinh
    gia san (tai b_max). Tra chi phi re nhat de phu DUNG S bang candidates +
    FD cho phan con lai."""
    order_list = sorted(S)
    n = len(order_list)
    idx = {o: k for k, o in enumerate(order_list)}
    full_mask = (1 << n) - 1

    dp = [float("inf")] * (1 << n)
    dp[0] = 0.0

    cand_masks = []
    for bundle, cost in candidates:
        mask = 0
        valid = True
        for o in bundle:
            if o not in idx:
                valid = False
                break
            mask |= (1 << idx[o])
        if valid and mask != 0:
            cand_masks.append((mask, cost))

    for mask in range(1, 1 << n):
        first_bit = mask & (-mask)
        first_order = order_list[first_bit.bit_length() - 1]
        dp[mask] = min(dp[mask], dp[mask ^ first_bit] + fd_costs[first_order])
        for cmask, cost in cand_masks:
            if (cmask & first_bit) and (cmask & mask) == cmask:
                dp[mask] = min(dp[mask], dp[mask ^ cmask] + cost)

    return dp[full_mask]


def alt_cost(S, exclude_driver, routes_by_driver, fd_costs, b_max):
    """Sec1: chi phi re nhat de phu TOAN BO S bang driver != exclude_driver +
    FD. Candidate route: MOI route cua driver khac co bundle LA SUBSET cua S
    (khong xet route "du", bundle chua S - don gian hoa AN TOAN, co the lam
    Alt tinh CAO hon that => prune kem aggressive hon, KHONG mat an toan)."""
    candidates = []
    for driver, routes in routes_by_driver.items():
        if driver == exclude_driver:
            continue
        for (rid, order_set, K, W) in routes:
            if order_set <= S:
                cost_at_bmax = K + b_max * W
                candidates.append((order_set, cost_at_bmax))
    return _min_cost_to_cover(S, candidates, fd_costs)


def build_routes_by_driver(all_routes):
    """all_routes: {rid: (did, order_set, K, W)} tu testC2_activation_rate.
    route_ids_for_pool. Tra {driver_id: [(rid, order_set, K, W), ...]}."""
    out = {}
    for rid, (did, order_set, K, W) in all_routes.items():
        out.setdefault(did, []).append((rid, order_set, K, W))
    return out


# ---------------------------------------------------------------------------
# [CHECK][STOP] Buoc 1 - Audit tren ground truth DA CO (Sec2)
# ---------------------------------------------------------------------------

def audit_against_ground_truth(all_routes, fd_costs, activated_real,
                               b_min=THETA_MIN, b_max=THETA_MAX):
    """Tra list violation: route DA activate that (activated_real) nhung
    dieu kien prune() lai noi NEN loai bo - vi pham an toan."""
    routes_by_driver = build_routes_by_driver(all_routes)
    violations = []
    n_would_prune = 0

    for rid, (did, order_set, K, W) in all_routes.items():
        alt = alt_cost(order_set, did, routes_by_driver, fd_costs, b_max)
        c_bmin = K + b_min * W
        would_prune = (c_bmin >= alt - 1e-9)
        if would_prune:
            n_would_prune += 1
        if would_prune and rid in activated_real:
            violations.append(dict(rid=rid, driver=did, bundle=sorted(order_set),
                                   c_bmin=c_bmin, alt=alt))

    return violations, n_would_prune


def run_audit_on_instance(n, B_gw, B_od, tw_width, n_drivers, seed, tau,
                          n_bid_vectors=1000):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=tau, spatial_mode="dispersed")
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
    all_routes = T.route_ids_for_pool(pool_by_driver)
    fd_costs = RC.assign_q_o(orders, tt)

    # Ground truth activated_real - DUNG LAI logic da co (khong doi), giai
    # WDP that qua LHS sampling (giong het testC2_activation_rate.py).
    res = T.run_activation_rate(n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width,
                                n_drivers=n_drivers, seed=seed, tau=tau,
                                n_bid_vectors=n_bid_vectors)
    activated_real = res["activated_route_names"]
    pool_size = len(all_routes)

    violations, n_would_prune = audit_against_ground_truth(
        all_routes, fd_costs, activated_real, THETA_MIN, THETA_MAX)

    print("\n=== [Buoc 1] Audit ground truth: n=%d n_drivers=%d seed=%d ===" % (n, n_drivers, seed))
    print("pool_size=%d  activated_real=%d  n_would_prune(dieu kien)=%d (%.2f%% cua pool)"
         % (pool_size, len(activated_real), n_would_prune, 100.0*n_would_prune/pool_size))
    print("violations (route activated that nhung bi prune sai) = %d" % len(violations))
    if violations:
        print("  [FAIL - dieu kien KHONG an toan tren instance nay]")
        for v in violations[:10]:
            print("   ", v)
    else:
        print("  [PASS] Khong vi pham - dieu kien AN TOAN tren instance nay.")

    return dict(pool_size=pool_size, n_activated=len(activated_real),
               n_would_prune=n_would_prune, n_violations=len(violations),
               violations=violations)


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
        r = run_audit_on_instance(tw_width=120, tau=30.0, n_bid_vectors=1000, **cfg)
        all_results.append((cfg, r))

    print("\n\n=== TONG HOP BUOC 1 ===")
    total_violations = 0
    for cfg, r in all_results:
        print("n=%d n_drivers=%d seed=%d: pool=%d activated=%d would_prune=%d(%.2f%%) violations=%d"
             % (cfg["n"], cfg["n_drivers"], cfg["seed"], r["pool_size"], r["n_activated"],
                r["n_would_prune"], 100.0*r["n_would_prune"]/r["pool_size"], r["n_violations"]))
        total_violations += r["n_violations"]

    print("\nTONG violations qua %d instance = %d" % (len(all_results), total_violations))
    if total_violations == 0:
        print("[PASS TOAN BO - Buoc 1] Dieu kien AN TOAN tren toan bo 5 instance. "
             "Duoc phep tiep tuc Buoc 2 (Gate n<=6).")
    else:
        print("[FAIL - Buoc 1] Dieu kien KHONG an toan - DUNG, khong chay Buoc 2/3.")
