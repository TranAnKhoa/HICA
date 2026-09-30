"""Test moi (chua co spec file, 2026-09-16, theo de xuat truc tiep cua nguoi
dung) - "activation rate": 1 phep do, 2 ket qua deu dung duoc.

Y tuong: lay 1 instance da co (n=10-15 cho re), sample NHIEU bid vector theta
tu range da khoa (Uniform[18,25] USD/h, rq1_cost_gen.THETA_MIN/THETA_MAX) qua
Latin Hypercube Sampling (LHS) tren [18,25]^m (m = so driver), giai WDP that
(Algorithm B, KHONG can Algorithm C/VCG) cho TUNG bid vector, dem:

  activation_rate = |{route tung xuat hien trong IT NHAT 1 loi giai toi uu}| / |pool|

Doc ket qua:
  - activation_rate CAO (vd >50%) -> bang chung thuc nghiem manh cho "tightness"
    (hau het route trong pool deu co the toi uu voi bid nao do) -> dang dau tu
    viet construction/proof cho dieu do, biet ro che do synergy can nham vao.
  - activation_rate RAT THAP (vd <5%) -> co 1 co hoi pruning that (phan lon
    route KHONG BAO GIO toi uu voi bat ky bid nao trong range) -> huong
    positive result moi - buoc tiep theo la tim dieu kien du kiem re de nhan
    ra route khong-activatable ma khong can giai het moi bid vector (LP
    relaxation/dual bound, hoac dieu kien "chi phi tang them khi them order j
    luon vuot q_j voi moi b trong range").

KHONG dung numpy (khong co tren may nay) - tu viet LHS bang pure Python.
Dung lai CHINH XAC ha tang RQ1 da co: dp_labeling.build_route_pool (Algorithm
A), rq1_wdp.solve_wdp_for_instance (Algorithm B qua CPLEX), rq1_cost_gen cho
theta range va q_o formula da khoa - KHONG logic tinh cost/route moi.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import rq1_wdp as RW

THETA_MIN = RC.THETA_MIN
THETA_MAX = RC.THETA_MAX

N_BID_VECTORS = 1000
LHS_SEED = 20260916  # tag rieng cho sampling bid vector, KHONG lien quan seed sinh instance


def latin_hypercube(m, n_samples, lo, hi, rng):
    """LHS thuan Python tren [lo,hi]^m: voi MOI chieu, chia [lo,hi] thanh
    n_samples khoang deu nhau, hoan vi ngau nhien thu tu khoang cho tung
    chieu (doc lap giua cac chieu), lay 1 diem ngau nhien trong khoang duoc
    gan. Tra list of tuple (list) do dai m."""
    cell_w = (hi - lo) / float(n_samples)
    cols = []
    for _d in range(m):
        perm = list(range(n_samples))
        rng.shuffle(perm)
        col = [lo + (perm[i] + rng.random()) * cell_w for i in range(n_samples)]
        cols.append(col)
    return [tuple(cols[d][i] for d in range(m)) for i in range(n_samples)]


def route_ids_for_pool(pool_by_driver):
    """Tra {route_id: (driver_id, order_set, K, W)} - THEO DUNG thu tu sinh
    rid cua rq1_wdp.build_wdp_drivers (rid_ctr tang dan theo thu tu duyet
    pool.items() - dict Python 3.7+ giu thu tu insertion, on dinh xuyen suot
    nhieu lan goi tren CUNG 1 pool_by_driver object khong doi)."""
    out = {}
    for did, pool in pool_by_driver.items():
        rid_ctr = 0
        for order_set, kw_list in pool.items():
            for (K, W) in kw_list:
                rid = "%s_r%d" % (did, rid_ctr)
                rid_ctr += 1
                out[rid] = (did, order_set, K, W)
    return out


def sanitize(s):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def run_activation_rate(n=12, B_gw=3, B_od=3, tw_width=120, n_drivers=5, seed=42,
                        tau=30.0, spatial_mode="dispersed", n_bid_vectors=N_BID_VECTORS,
                        lhs_seed=LHS_SEED):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=tau, spatial_mode=spatial_mode)

    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
    q_o_by_order = RC.assign_q_o(orders, tt)

    all_routes = route_ids_for_pool(pool_by_driver)
    total_pool_size = len(all_routes)
    driver_ids = [d["id"] for d in drivers]
    m = len(driver_ids)

    # anh xa ten bien CPLEX (x_<sanitized rid>) -> rid goc, dung KHOP CHINH
    # XAC dinh dang t8_cplex._sanitize dung khi build model (khong doi logic,
    # chi de doi chieu dung ten bien).
    vname_to_rid = {"x_" + sanitize(rid): rid for rid in all_routes}
    assert len(vname_to_rid) == total_pool_size, \
        "[STOP] xung dot ten bien sau sanitize - rid khong con duy nhat"

    print("Instance: n=%d B_gw=%d B_od=%d n_drivers=%d(m=%d) | pool_size=%d route"
         % (n, B_gw, B_od, n_drivers, m, total_pool_size))

    rng = random.Random(lhs_seed)
    bid_vectors = latin_hypercube(m, n_bid_vectors, THETA_MIN, THETA_MAX, rng)

    activated = set()
    n_solved = 0
    for bv in bid_vectors:
        theta_by_driver = {did: bv[i] for i, did in enumerate(driver_ids)}
        r = RW.solve_wdp_for_instance(pool_by_driver, orders, theta_by_driver, q_o_by_order)
        n_solved += 1
        for vname in r["alloc_x"]:
            if vname in vname_to_rid:   # bo qua bien z_<order> (FD), chi dem route x_*
                activated.add(vname_to_rid[vname])
        if n_solved % 200 == 0:
            print("  ...solved %d/%d bid vectors, |activated so far|=%d/%d (%.2f%%)"
                 % (n_solved, n_bid_vectors, len(activated), total_pool_size,
                    100.0 * len(activated) / total_pool_size))

    activation_rate = len(activated) / float(total_pool_size)

    print("\n=== KET QUA ===")
    print("pool_size (tong so route, ca driver)     = %d" % total_pool_size)
    print("n_bid_vectors sampled (LHS tren [%.0f,%.0f]^%d) = %d"
         % (THETA_MIN, THETA_MAX, m, n_bid_vectors))
    print("n_route_activated (>=1 loi giai toi uu)   = %d" % len(activated))
    print("activation_rate                            = %.4f (%.2f%%)"
         % (activation_rate, 100 * activation_rate))

    return dict(pool_size=total_pool_size, n_bid_vectors=n_bid_vectors,
               n_activated=len(activated), activation_rate=activation_rate,
               all_routes=all_routes, activated_route_names=activated)


if __name__ == "__main__":
    run_activation_rate()
