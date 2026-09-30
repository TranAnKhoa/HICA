"""Convex_hull.md - Quick test: convex-hull dominance filtering co cat duoc
nhieu Pareto point khong tren hot cell (n=20, B_gw=4, tw=240, n_drivers=5).

KHONG dung scipy/numpy (khong co tren Python 3.7.7 cua may nay, mang bi chan
khong cai duoc) - tu viet lower convex hull thuan Python (Andrew's monotone
chain, chi lay nua duoi vi ca K va W deu MINIMIZE - day chinh la phan hull
can cho linear scalarization cost=K+b*W, b>=0).

Chay DP THAT qua dp_labeling.py (goi nguyen t6_dp.run_dp, KHONG sua) tren hot
cell, lay toan bo Pareto front cua driver GW (bundle_size<=B_gw), roi post-
process convex hull + audit Sec3 cua spec.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

# ---------------------------------------------------------------------------
# Sec1: hot cell params (dung dung nhu Convex_hull.md khoa)
# ---------------------------------------------------------------------------
N = 20
B_GW = 4
B_OD = 2          # khong khoa rieng trong spec goc (spec dung B chung cu) -
                  # dat mot gia tri hop ly, KHONG anh huong ket qua GW (loc
                  # rieng driver_class=='GW' o duoi, giong spec Sec1)
TW_WIDTH = 240
N_DRIVERS = 5
SEED = 12345      # seed co dinh, khong random (dung yeu cau Sec1)
TAU = 30.0        # khong dung cho GW (khong co rang buoc tau) - dat mac dinh
SPATIAL_MODE = "dispersed"


def lower_hull(points):
    """Convex hull cua PHAN DUOI-TRAI (lower-left staircase) - dung cho bai
    toan minimize CA HAI truc (K,W) qua linear scalarization cost=K+b*W,
    b>=0. Day KHONG PHAI lower-hull tieu chuan cua Andrew's monotone chain
    (hull duoi tu trai-thap den phai-thap theo x) - vi bai toan nay can toan
    bo bien Pareto-efficient (ca hai dau mut truc K va truc W), tuong duong
    "hull cua vung {(K,W) : khong bi diem nao khac dominate ca 2 truc}".

    Thuat toan: chi giu cac diem Pareto-efficient (khong bi diem khac
    dominate ca K va W - CHINH LA dinh nghia dominance that cua Algorithm A,
    xem Algorithm_A_Description.md Sec2.5), roi tinh convex hull cua tap do
    bang Andrew's monotone chain nhung xay dung ca 2 canh (duoi VA TREN cua
    tap Pareto, vi tap Pareto sap theo K tang -> W giam, hull cua no la 1
    duong cong don dieu - khong can phan biet tren/duoi, chi can 1 lan quet).

    Tra list index (vao mang points goc) nam tren hull, sap theo K tang dan."""
    n = len(points)
    if n <= 2:
        return list(range(n))

    # Buoc 1: loc Pareto-efficient truoc (bat buoc - hull cua toan bo point
    # cloud se sai neu con diem bi dominate ca 2 truc lam nhieu monotone
    # chain). Sort theo K tang, W giam dan (tie-break) - giu diem co W nho
    # nhat cho moi K, roi quet giu prefix-min cua W.
    order = sorted(range(n), key=lambda i: (points[i][0], points[i][1]))
    pareto = []
    best_w = float("inf")
    for idx in order:
        w = points[idx][1]
        if w < best_w - 1e-12:
            pareto.append(idx)
            best_w = w
    # pareto: K tang dan, W giam dan tuyet doi (strictly) - day la duong
    # Pareto-efficient THAT (khong bi diem nao khac dominate).

    if len(pareto) <= 2:
        return pareto

    # Buoc 2: convex hull cua duong Pareto don dieu (K tang, W giam) - vi da
    # don dieu, TOAN BO diem tren duong nay nam tren 1 duong cong loi ke tu
    # 2 dau mut CHI KHI duong cong loi (convex) that su; neu khong, mot so
    # diem Pareto van co the nam "trong" theo nghia scalarization (khong bao
    # gio la argmin cho bat ky b>=0 nao) - can loc convex hull that su.
    def cross(o, a, b):
        return (points[a][0] - points[o][0]) * (points[b][1] - points[o][1]) - \
               (points[a][1] - points[o][1]) * (points[b][0] - points[o][0])

    # Quet tu trai sang phai (K tang), giu convex (turn phai, tuc cross<=0
    # loai diem giua) - dung cho duong don dieu giam W.
    hull = []
    for idx in pareto:
        while len(hull) >= 2 and cross(hull[-2], hull[-1], idx) <= 0:
            hull.pop()
        hull.append(idx)
    return hull


def main():
    print("=== Convex_hull.md - hot cell n=%d B_gw=%d tw=%d n_drivers=%d seed=%d ==="
          % (N, B_GW, TW_WIDTH, N_DRIVERS, SEED))

    t0 = time.time()
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=B_OD, tw_width=TW_WIDTH, n_drivers=N_DRIVERS,
        seed=SEED, tau=TAU, spatial_mode=SPATIAL_MODE)
    print("Instance sinh xong: %d order, %d driver (%.2fs)"
          % (N, len(drivers), time.time() - t0))

    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    print("Driver GW: %s" % [d["id"] for d in gw_drivers])

    t1 = time.time()
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_GW, B_OD)
    dp_rt = time.time() - t1
    print("DP xong: %.2fs, peak_frontier=%d, total_bundles=%d"
          % (dp_rt, agg["peak_frontier"], agg["n_bundles_total"]))

    # ---- gop toan bo (K,W) cua GW, bundle_size <= B_gw (luon dung vi capacity=B_gw) ---
    points = []
    route_labels = []   # (driver_id, bundle_orders_tuple, K, W) - de audit/in
    for did in [d["id"] for d in gw_drivers]:
        pool = pool_by_driver.get(did, {})
        for order_set, kw_list in pool.items():
            if len(order_set) > B_GW:
                continue
            for (K, W) in kw_list:
                points.append((K, W))
                route_labels.append((did, tuple(sorted(order_set)), K, W))

    n_total = len(points)
    print("\nTotal Pareto points (GW, bundle_size<=%d): %d" % (B_GW, n_total))

    if n_total < 3:
        print("Qua it diem (<3) de tinh convex hull - ghi note degenerate, dung.")
        return

    # ---- Sec2: lower convex hull -------------------------------------------
    hull_idx = lower_hull(points)
    hull_set = set(hull_idx)
    n_hull = len(hull_idx)
    n_inside = n_total - n_hull
    reduction_pct = 100.0 * n_inside / n_total

    print("Points on (lower) convex hull: %d" % n_hull)
    print("Points INSIDE hull (co the cat an toan): %d" % n_inside)
    print("Reduction: %.1f%%" % reduction_pct)

    print("\nConvex hull points (K, W) - sample toi da 20 diem dau:")
    for i, idx in enumerate(hull_idx[:20]):
        did, bset, K, W = route_labels[idx]
        print("  driver=%s bundle=%s K=%.2f W=%.4f" % (did, bset, K, W))
    if n_hull > 20:
        print("  ... (%d diem con lai khong in)" % (n_hull - 20))

    # ---- Sec3: audit - moi bid b trong [theta_min,theta_max] chon diem tren hull? ---
    print("\n=== Audit: linear scalarization cost=K+b*W, b~Uniform[18,25] (100 mau) ===")
    import random
    rng = random.Random(42)
    n_bid = 100
    n_on_hull = 0
    violations = []
    for _ in range(n_bid):
        b = rng.uniform(18.0, 25.0)
        best_idx = min(range(n_total), key=lambda i: points[i][0] + b * points[i][1])
        on_hull = best_idx in hull_set
        if on_hull:
            n_on_hull += 1
        else:
            violations.append((b, best_idx, points[best_idx]))

    print("%d/%d bid chon diem tren hull" % (n_on_hull, n_bid))
    if violations:
        print("CANH BAO: %d bid chon diem KHONG tren hull (khong duoc xay ra neu hull dung):"
              % len(violations))
        for b, idx, pt in violations[:10]:
            print("  b=%.2f  chon idx=%d  (K,W)=%s" % (b, idx, pt))
    else:
        print("[OK] 100%% bid deu chon diem tren hull - hull tinh dung, khong co vi pham.")

    # ---- Sec4: interpretation guide -----------------------------------------
    print("\n=== Interpretation (theo Convex_hull.md Sec4) ===")
    if reduction_pct >= 50.0:
        verdict = "Reduction >= 50%: hull filtering RAT MANH - dang implement vao Algorithm A"
    elif reduction_pct >= 20.0:
        verdict = "Reduction 20-50%: tam duoc, can do them hot cell khac de xac nhan consistent"
    else:
        verdict = ("Reduction < 20%: KHONG dang cong, frontier qua day (gan het tren hull) - "
                   "dung lai, dung ket qua nay de thiet ke worst-case instance cho lower-bound T4")
    print(verdict)

    print("\n=== Tong ket ===")
    print("n_total=%d  n_hull=%d  n_inside=%d  reduction=%.1f%%  n_bid_violations=%d/100"
          % (n_total, n_hull, n_inside, reduction_pct, len(violations)))


if __name__ == "__main__":
    main()
