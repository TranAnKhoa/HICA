"""Convex_hull_02.md - sua loi scope cua v1 (convex_hull_test.py): hull PHAI
tinh trong CUNG (driver, bundle), khong duoc gop qua bundle khac (route phuc
vu bundle khac nhau la mandatory fulfillment khac nhau trong WDP - khong phai
lua chon thay the cho nhau, xem De cuong Sec7.4).

pool_by_driver tu dp_labeling.build_route_pool() DA DUNG SCOPE SAN (moi key
la 1 frozenset(order_ids) = 1 bundle rieng, Pareto front da tinh TRONG CUNG
bundle do boi _pareto_front() trong dp_labeling.py) - Test A o day chi can
tinh convex hull cho TUNG group (driver,bundle) rieng le, KHONG duoc gop lai
nhu v1 da lam sai.

Dung LAI dung DP that (dp_labeling.py, khong sua) tren CUNG hot cell v1 da
dung (n=20,B_gw=4,tw=240,n_drivers=5,seed=12345) de so sanh doi chieu duoc.
"""

import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

# ---- hot cell (giong het v1, de doi chieu) --------------------------------
N = 20
B_GW = 4
B_OD = 2
TW_WIDTH = 240
N_DRIVERS = 5
SEED = 12345
TAU = 30.0
SPATIAL_MODE = "dispersed"


def lower_hull_on_pareto(pareto_pts):
    """pareto_pts: list (K,W,payload), DA sort K tang dan/W giam dan (tu
    pareto_filter). Andrew's monotone chain 1 lan quet (duong da don dieu).

    [FIX 2026-09-16] Convex_hull_02.md's turns_right() code mau dinh sai dau
    (cross<0 pop) - da phat hien qua kiem tay doc lap (brute-force numeric
    quet b) tren 5 group nhieu diem nhat: diem argmin THAT tai b=5.0 cho
    group ('gw0',('o0','o16','o17','o2')) bi thuat toan cu bo sot. Dieu
    kien DUNG (xac nhan bang brute-force step=0.001 tren b in [0,200],
    khop tuyet doi): pop khi cross < 0, GIU khi cross >= 0."""
    if len(pareto_pts) <= 2:
        return list(pareto_pts)

    def cross(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    hull = []
    for p in pareto_pts:
        while len(hull) >= 2 and cross(hull[-2], hull[-1], p) < 0:
            hull.pop()
        hull.append(p)
    return hull


def pareto_filter(points):
    """points: list (K,W,payload). Giu diem khong bi dominate ca 2 truc."""
    pts = sorted(points, key=lambda p: (p[0], p[1]))
    result = []
    best_w = float("inf")
    for k, w, payload in pts:
        if w < best_w - 1e-12:
            result.append((k, w, payload))
            best_w = w
    return result


def test_a_regroup(pool_by_driver, driver_cls, B_gw):
    """DUNG SCOPE: moi group = (driver_id, bundle=frozenset order_ids). Chi
    xet driver GW, bundle_size<=B_gw (dung dieu kien v1/spec da khoa)."""
    groups = {}   # (driver_id, bundle) -> [(K,W,route_label)]
    for did, pool in pool_by_driver.items():
        if driver_cls.get(did) != "GW":
            continue
        for bundle, kw_list in pool.items():
            if len(bundle) > B_gw:
                continue
            key = (did, tuple(sorted(bundle)))
            groups[key] = [(K, W, "%s|%s" % (did, "-".join(sorted(bundle))))
                          for (K, W) in kw_list]

    total_before = sum(len(v) for v in groups.values())
    total_after = 0
    per_group_reduction = []
    by_bundle_size = defaultdict(lambda: [0, 0])   # size -> [before, after]

    for key, pts in groups.items():
        pareto_pts = pareto_filter(pts)
        hull_pts = lower_hull_on_pareto(pareto_pts)
        total_after += len(hull_pts)
        bsize = len(key[1])
        by_bundle_size[bsize][0] += len(pts)
        by_bundle_size[bsize][1] += len(hull_pts)
        if len(pts) > 1:
            per_group_reduction.append(
                (key, len(pts), len(hull_pts), 100.0 * (len(pts) - len(hull_pts)) / len(pts)))

    print("Tong so group (driver,bundle): %d" % len(groups))
    print("Tong diem TRUOC (Pareto, dung scope): %d" % total_before)
    print("Tong diem SAU (hull, dung scope): %d" % total_after)
    reduction_total = 100.0 * (total_before - total_after) / total_before if total_before else 0.0
    print("Reduction TOAN BAI: %.1f%%" % reduction_total)

    print("\nSo (driver,bundle) group co >1 route (co the giam): %d / %d"
          % (len(per_group_reduction), len(groups)))
    if per_group_reduction:
        avg_group_reduction = sum(r[3] for r in per_group_reduction) / len(per_group_reduction)
        print("Reduction trung binh MOI group (chi tinh group >1 diem): %.1f%%" % avg_group_reduction)
        print("\n10 group co nhieu diem nhat (before -> after):")
        for key, n_before, n_after, red in sorted(per_group_reduction, key=lambda x: -x[1])[:10]:
            print("  %s: %d -> %d (%.1f%%)" % (key, n_before, n_after, red))

    print("\nPhan tich theo bundle_size (1..%d):" % B_gw)
    for bsize in sorted(by_bundle_size.keys()):
        before, after = by_bundle_size[bsize]
        red = 100.0 * (before - after) / before if before else 0.0
        print("  bundle_size=%d: %d group, %d -> %d diem (%.1f%% reduction)"
              % (bsize,
                 sum(1 for k in groups if len(k[1]) == bsize),
                 before, after, red))

    return dict(total_before=total_before, total_after=total_after,
               reduction_total_pct=reduction_total, groups=groups,
               per_group_reduction=per_group_reduction,
               by_bundle_size=dict(by_bundle_size))


def run_one_seed(seed):
    print("=== Convex_hull_02.md Test A - hot cell n=%d B_gw=%d tw=%d n_drivers=%d seed=%d ==="
          % (N, B_GW, TW_WIDTH, N_DRIVERS, seed))

    t0 = time.time()
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=B_OD, tw_width=TW_WIDTH, n_drivers=N_DRIVERS,
        seed=seed, tau=TAU, spatial_mode=SPATIAL_MODE)
    print("Instance sinh xong (%.2fs)" % (time.time() - t0))

    driver_cls = {d["id"]: d["cls"] for d in drivers}
    print("Driver GW: %s" % [d["id"] for d in drivers if d["cls"] == "GW"])

    t1 = time.time()
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_GW, B_OD)
    dp_rt = time.time() - t1
    print("DP xong: %.2fs, peak_frontier=%d, total_bundles=%d"
          % (dp_rt, agg["peak_frontier"], agg["n_bundles_total"]))

    print()
    result = test_a_regroup(pool_by_driver, driver_cls, B_GW)

    print("\n=== Interpretation (Convex_hull_02.md Sec4) ===")
    if result["reduction_total_pct"] >= 20.0:
        print(">= 20%%: can chay Gate [CHECK] n<=6 truoc khi implement - xem convex_hull_gate_n6.py")
    else:
        print("< 20%%: KHONG dang cong implement - dung lai, dung lam bang chung cho lower-bound huong T4")

    return pool_by_driver, driver_cls, result


def main():
    return run_one_seed(SEED)


if __name__ == "__main__":
    main()
