"""Test dieu kien pruning re cho activation rate thap (Report_ActivationRate.md).

Y tuong (suy luan cau truc, kiem chung thuc nghiem o day):

  Voi 1 driver i, WDP chi chon TOI DA 1 route trong TOAN BO pool cua driver
  do (moi bundle khac nhau la 1 lua chon loai tru lan nhau, khong phai bo
  sung). true_cost(route r) = K_r + theta_i * W_r - MOT HAM AFFINE theo
  theta_i voi slope W_r, intercept K_r.

  Route r CHI co the la lua chon toi uu cua driver i (voi MOT theta_i nao do)
  khi va chi khi no la ARGMIN cua ho duong thang {K_r + theta*W_r} tren TOAN
  BO pool cua driver i, tai MOT diem theta nao do - tuc la r phai nam tren
  LOWER ENVELOPE (lower convex hull theo (K,W), giong Convex_hull_02.md,
  nhung o day KHONG gioi han trong 1 bundle - gop TOAN BO pool cua 1 driver,
  vi driver chon 1 route DUY NHAT bat ke bundle nao).

  Hon nua, activation chi tinh trong RANGE theta da khoa [theta_min,
  theta_max] (Uniform[18,25]) - khong phai toan bo [0,inf). Moi diem tren
  lower hull co 1 "khoang slope hoat dong" [b_left, b_right] (b = theta) -
  khoang theta ma tai do diem nay la argmin. DIEU KIEN PRUNING RE:

    route r activatable trong [theta_min, theta_max]
      <=> r nam tren lower hull CUA POOL DRIVER (khong can biet WDP toan
          instance, chi can pool 1 driver)
      VA [b_left(r), b_right(r)] giao khac rong voi [theta_min, theta_max]

  Day la dieu kien CAN (route KHONG thoa dieu kien nay chac chan KHONG BAO
  GIO toi uu cho driver do voi bat ky theta_i trong range, boi vi neu no
  khong phai argmin cua CHINH POOL cua no thi khong the la optimal choice
  cua driver do trong WDP, bat ke driver khac bid gi). Dieu kien nay CHUA
  chac la DU (con phu thuoc driver khac + FD cost trong WDP toan instance)
  - nhung neu dung, day la 1 upper bound RE (khong can giai WDP) cho tap
  route co the activatable.

  Kiem chung: so sanh {route qua duoc dieu kien pruning nay} voi {route THAT
  SU duoc activate qua 1000 bid vector LHS + giai WDP that} (da co san tu
  testC2_activation_rate.py) - neu MOI route activated (that) deu nam trong
  tap qua-dieu-kien (candidate), dieu kien la AN TOAN (khong bo sot). Neu tap
  candidate nho hon nhieu so pool_size, day la 1 pruning re + an toan that.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import testC2_activation_rate as T
from convex_hull_test_v2 import lower_hull_on_pareto, pareto_filter

THETA_MIN = RC.THETA_MIN
THETA_MAX = RC.THETA_MAX


def hull_active_slope_ranges(hull_pts):
    """hull_pts: list (K,W,payload) DA la lower hull (sorted K tang, W giam -
    tu lower_hull_on_pareto). Voi moi diem, tinh khoang slope theta ma tai do
    diem nay la argmin cua K+theta*W trong CHINH tap hull nay (tuong duong
    toan bo pool, vi non-hull point khong bao gio la argmin o bat ky theta
    nao - tinh chat co ban cua lower envelope).

    slope bien doi giua 2 diem hull ke nhau (Ki,Wi) va (Kj,Wj) (Wi>Wj, hull
    sort W giam dan) tai theta* = (Kj-Ki)/(Wi-Wj) (diem 2 duong thang cat
    nhau). Diem dau tien hull active tren [0, theta*_01), diem cuoi active
    tren [theta*_{n-2,n-1}, +inf), diem giua active tren khoang giua 2 diem
    cat lan can.

    Tra list (K,W,payload,b_left,b_right)."""
    n = len(hull_pts)
    if n == 1:
        K, W, payload = hull_pts[0]
        return [(K, W, payload, 0.0, float("inf"))]

    breakpoints = [0.0]
    for i in range(n - 1):
        K1, W1, _ = hull_pts[i]
        K2, W2, _ = hull_pts[i + 1]
        # K1 + b*W1 = K2 + b*W2  =>  b = (K2-K1)/(W1-W2)
        assert W1 > W2 + 1e-12, "[STOP] hull khong don dieu giam W - loi hull"
        b_star = (K2 - K1) / (W1 - W2)
        breakpoints.append(b_star)
    breakpoints.append(float("inf"))

    out = []
    for i in range(n):
        K, W, payload = hull_pts[i]
        b_left = breakpoints[i]
        b_right = breakpoints[i + 1]
        out.append((K, W, payload, b_left, b_right))
    return out


def pruning_candidates_for_driver(routes_this_driver):
    """routes_this_driver: list (rid, K, W) TOAN BO route cua 1 driver (gop
    het bundle - khac Convex_hull_02.md chi hull trong 1 bundle). Tra set rid
    thoa dieu kien pruning (nam tren lower hull VA active-range giao voi
    [THETA_MIN, THETA_MAX])."""
    tagged = [(K, W, rid) for (rid, K, W) in routes_this_driver]
    pareto_pts = pareto_filter(tagged)
    hull = lower_hull_on_pareto(pareto_pts)
    ranges = hull_active_slope_ranges(hull)

    candidates = set()
    for (K, W, rid, b_left, b_right) in ranges:
        if b_left <= THETA_MAX and b_right >= THETA_MIN:   # giao khac rong
            candidates.add(rid)
    return candidates


def check_instance(n, B_gw, B_od, tw_width, n_drivers, seed, tau, n_bid_vectors=1000):
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=tau, spatial_mode="dispersed")
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
    all_routes = T.route_ids_for_pool(pool_by_driver)

    # --- (A) dieu kien pruning re (KHONG giai WDP nao) ---
    routes_by_driver = {}
    for rid, (did, order_set, K, W) in all_routes.items():
        routes_by_driver.setdefault(did, []).append((rid, K, W))

    candidates = set()
    for did, routes in routes_by_driver.items():
        candidates |= pruning_candidates_for_driver(routes)

    # --- (B) activation THAT (giai WDP that qua N bid vector, da co san logic) ---
    res = T.run_activation_rate(n=n, B_gw=B_gw, B_od=B_od, tw_width=tw_width,
                                n_drivers=n_drivers, seed=seed, tau=tau,
                                n_bid_vectors=n_bid_vectors)
    activated_real = res["activated_route_names"]

    missing = activated_real - candidates   # route THAT SU activated nhung KHONG qua duoc dieu kien
    pool_size = len(all_routes)

    print("\n=== Doi chieu dieu kien pruning vs activation that ===")
    print("pool_size                 = %d" % pool_size)
    print("|candidates| (dieu kien)  = %d  (%.2f%% cua pool)"
         % (len(candidates), 100.0 * len(candidates) / pool_size))
    print("|activated| (WDP that)    = %d  (%.2f%% cua pool)"
         % (len(activated_real), 100.0 * len(activated_real) / pool_size))
    print("missing (activated that nhung KHONG trong candidates) = %d" % len(missing))
    if missing:
        print("  [FAIL - dieu kien KHONG an toan] missing routes:", sorted(missing))
    else:
        print("  [PASS - dieu kien AN TOAN tren instance nay] moi route activated that "
             "deu nam trong candidates")

    reduction = 1.0 - len(candidates) / float(pool_size)
    print("Giam so route can xet (candidates vs pool_size) = %.2f%%" % (100 * reduction))

    return dict(pool_size=pool_size, n_candidates=len(candidates),
               n_activated=len(activated_real), n_missing=len(missing),
               candidates=candidates, activated_real=activated_real)


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
        r = check_instance(tw_width=120, tau=30.0, n_bid_vectors=1000, **cfg)
        all_results.append((cfg, r))

    print("\n\n=== TONG HOP ===")
    total_missing = 0
    for cfg, r in all_results:
        print("n=%d n_drivers=%d seed=%d: pool=%d candidates=%d(%.2f%%) activated=%d(%.2f%%) missing=%d"
             % (cfg["n"], cfg["n_drivers"], cfg["seed"], r["pool_size"], r["n_candidates"],
                100.0*r["n_candidates"]/r["pool_size"], r["n_activated"],
                100.0*r["n_activated"]/r["pool_size"], r["n_missing"]))
        total_missing += r["n_missing"]
    print("\nTONG missing qua %d instance = %d" % (len(all_results), total_missing))
    if total_missing == 0:
        print("[PASS TOAN BO] Dieu kien pruning AN TOAN tren toan bo 5 instance da kiem.")
    else:
        print("[FAIL] Dieu kien pruning KHONG an toan - can xem lai gia thuyet.")
