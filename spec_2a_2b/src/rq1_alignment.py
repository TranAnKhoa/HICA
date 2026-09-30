"""Rq1.md Sec3 - alignment metric + calibration curve. Cong thuc da khoa:

  corridor_k = doan thang origin_k -> destination_k, cho OD k
  dist(o, corridor_k) = khoang cach diem-den-doan tu pickup cua o toi corridor_k
  alignment(instance) = (1/|O|) * Sum_o 1[ min_k dist(o, corridor_k) <= r0 ]

r0: [LOCK] tinh MOT LAN tu percentile-25 cua phan phoi pairwise distance
(driver corridor, order pickup) tren 1 PILOT INSTANCE TRUNG LAP (KHONG phai
instance dung cho RQ1 that) - Sec3 dong 107-110.

Su dung meta['node_xy'] (moi them vao instance_gen.generate_instance(), xem
Sec3 lich su thay doi) de tinh khoang cach diem-den-doan CHINH XAC (khong
xap xi qua travel_time).

corridor_share (instance_gen.py, tham so MOI them o buoc truoc, mac dinh
None = dung CORRIDOR_SHARE=0.7 cu) la "tham so dieu khien" dung de dat
alignment target - calibration curve quet corridor_share, do alignment thuc
te, fit quan he, khoa gia tri cho tung target level.
"""

import math
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

# ---------------------------------------------------------------------------
# Pilot instance TRUNG LAP cho r0 - KHONG dung lai cho main RQ1 grid. Tham so
# khac han main grid (n, supply ratio) de tranh trung/gan giong bat ky cell
# nao se dung tra loi RQ1 that.
# ---------------------------------------------------------------------------
R0_PILOT_N = 18
R0_PILOT_B_GW = 3
R0_PILOT_B_OD = 3
R0_PILOT_TW = 120
R0_PILOT_N_DRIVERS = 5   # (n_gw=2 or 3, n_od phan con lai) - khac
                         # {(2,2),(3,2),(2,3),(3,3)} cua main grid Sec4
R0_PILOT_TAU = 30.0
R0_PILOT_SEED_TAG = "rq1_r0_pilot_neutral"


def dist_point_to_segment(p, a, b):
    """Khoang cach Euclid diem p toi doan thang a-b (2D). p,a,b: (x,y)."""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


def get_od_corridors(drivers, meta):
    """Tra list (start_xy, home_xy) cho MOI driver OD trong instance (dung
    'corridor' theo dinh nghia Sec3: doan thang start_node->home_node)."""
    node_xy = meta["node_xy"]
    corridors = []
    for dv in drivers:
        if dv["cls"] != "OD":
            continue
        s_xy = node_xy[dv["start_node"]]
        h_xy = node_xy[dv["home_node"]]
        corridors.append((s_xy, h_xy))
    return corridors


def pairwise_pickup_corridor_distances(drivers, orders, meta):
    """Tra list TOAN BO khoang cach (pickup_o, corridor_k) cho MOI cap
    (order, corridor OD) - dung de tinh r0 (percentile-25) tren pilot
    instance. Neu instance khong co OD nao, tra list rong."""
    node_xy = meta["node_xy"]
    corridors = get_od_corridors(drivers, meta)
    if not corridors:
        return []
    dists = []
    for oid, o in orders.items():
        p_xy = node_xy[o["pickup_node"]]
        for (s_xy, h_xy) in corridors:
            dists.append(dist_point_to_segment(p_xy, s_xy, h_xy))
    return dists


def alignment(drivers, orders, meta, r0):
    """Cong thuc chinh Sec3: ty le order co pickup gan (<=r0) MOT corridor OD
    nao do NHAT (min qua cac corridor). Neu khong co OD nao trong instance,
    alignment = 0.0 (khong co corridor nao de "gan")."""
    node_xy = meta["node_xy"]
    corridors = get_od_corridors(drivers, meta)
    n_orders = len(orders)
    if n_orders == 0:
        return 0.0
    if not corridors:
        return 0.0
    count = 0
    for oid, o in orders.items():
        p_xy = node_xy[o["pickup_node"]]
        min_d = min(dist_point_to_segment(p_xy, s_xy, h_xy) for (s_xy, h_xy) in corridors)
        if min_d <= r0:
            count += 1
    return count / n_orders


# ---------------------------------------------------------------------------
# [LOCK] r0 - tinh MOT LAN, TRUOC RQ1, tu pilot instance TRUNG LAP
# ---------------------------------------------------------------------------

def compute_r0():
    """Sinh 1 pilot instance trung lap (corridor_share=None -> dung default
    0.7 cua generator, KHONG can dieu chinh gi rieng cho pilot nay - pilot
    chi can 'trung lap' theo nghia KHAC tham so main grid, khong can alignment
    dac biet), lay percentile-25 cua toan bo pairwise (pickup, corridor)
    distance. Tra (r0_km, sample_dists) de ghi log."""
    gen_seed = IG.stable_seed(R0_PILOT_N, R0_PILOT_B_GW, R0_PILOT_B_OD,
                              R0_PILOT_TAU, R0_PILOT_N_DRIVERS, R0_PILOT_SEED_TAG)
    drivers, orders, tt, meta = IG.generate_instance(
        n=R0_PILOT_N, B_gw=R0_PILOT_B_GW, B_od=R0_PILOT_B_OD, tw_width=R0_PILOT_TW,
        n_drivers=R0_PILOT_N_DRIVERS, seed=gen_seed, tau=R0_PILOT_TAU,
        spatial_mode="dispersed", gw_od_ratio=0.4)   # 0.4*5=2 GW, 3 OD

    dists = pairwise_pickup_corridor_distances(drivers, orders, meta)
    if not dists:
        raise RuntimeError("[STOP] Pilot instance khong co OD nao - doi gw_od_ratio/n_drivers")

    dists_sorted = sorted(dists)
    r0 = _percentile(dists_sorted, 25.0)
    return r0, dists_sorted


def _percentile(sorted_vals, pct):
    """Linear interpolation percentile (tuong duong numpy.percentile default),
    khong dung statistics.quantiles (chi co tu Python 3.8, may nay dung 3.7.7)."""
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (pct / 100.0) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[int(f)] + (sorted_vals[int(c)] - sorted_vals[int(f)]) * (k - f)


# ---------------------------------------------------------------------------
# [IMPLEMENT] calibration curve - quet corridor_share, do alignment thuc te
# ---------------------------------------------------------------------------

CALIB_N = 15
CALIB_B_GW = 3
CALIB_B_OD = 3
CALIB_TW = 120
CALIB_TAU = 30.0
CALIB_N_DRIVERS = 4   # (2,2) - giua main grid supply ratio
CALIB_SEEDS = range(8)   # 8 replication/to hop de lay mean on dinh

CORRIDOR_SHARE_GRID = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
# [PATCH 2026-09-16] them chieu dieu khien thu 2 - calibration 1D voi chi
# corridor_share KHONG du manh de phu target {0.10,...,0.90} (buffer co dinh
# 3.0km qua rong so voi r0~1.36km). Quet them corridor_buffer_km (nho hon =
# corridor "chat" hon quanh duong thang, gan r0 hon).
CORRIDOR_BUFFER_KM_GRID = [0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 5.0]


def measure_alignment_at(corridor_share, corridor_buffer_km, r0, n=CALIB_N,
                         n_drivers=CALIB_N_DRIVERS, seeds=CALIB_SEEDS):
    vals = []
    for sd in seeds:
        gen_seed = IG.stable_seed(n, CALIB_B_GW, CALIB_B_OD, CALIB_TAU, n_drivers,
                                  corridor_share, corridor_buffer_km, sd, "rq1_calib_alignment")
        drivers, orders, tt, meta = IG.generate_instance(
            n=n, B_gw=CALIB_B_GW, B_od=CALIB_B_OD, tw_width=CALIB_TW,
            n_drivers=n_drivers, seed=gen_seed, tau=CALIB_TAU,
            spatial_mode="dispersed", gw_od_ratio=0.5, corridor_share=corridor_share,
            corridor_buffer_km=corridor_buffer_km)
        vals.append(alignment(drivers, orders, meta, r0))
    return statistics.mean(vals), statistics.stdev(vals) if len(vals) > 1 else 0.0, vals


def run_calibration_curve(r0):
    print("=== Calibration curve 2D: (corridor_share, corridor_buffer_km) -> alignment (r0=%.4f km) ==="
          % r0)
    curve = []
    for cs in CORRIDOR_SHARE_GRID:
        for cb in CORRIDOR_BUFFER_KM_GRID:
            mean_a, std_a, vals = measure_alignment_at(cs, cb, r0)
            curve.append((cs, cb, mean_a, std_a))
            print("corridor_share=%.1f  corridor_buffer_km=%.1f  mean(alignment)=%.4f  std=%.4f"
                  % (cs, cb, mean_a, std_a))
    return curve


def lock_params_for_targets(curve, targets=(0.10, 0.30, 0.50, 0.70, 0.90), tol=0.05):
    """Voi moi target, chon (corridor_share, corridor_buffer_km) trong luoi 2D
    co mean(alignment) GAN NHAT target. Neu |gan nhat - target| > tol, ghi
    [DEVIATION] ro rang thay vi am tham chon (Sec3 dong 117-118)."""
    locked = {}
    for target in targets:
        best = min(curve, key=lambda row: abs(row[2] - target))
        cs, cb, mean_a, std_a = best
        deviation = abs(mean_a - target) > tol
        locked[target] = dict(corridor_share=cs, corridor_buffer_km=cb,
                              achieved_alignment=mean_a, achieved_std=std_a,
                              deviation=deviation)
        flag = " [DEVIATION > tol=%.2f]" % tol if deviation else ""
        print("target=%.2f -> corridor_share=%.1f corridor_buffer_km=%.1f (dat mean=%.4f, std=%.4f)%s"
              % (target, cs, cb, mean_a, std_a, flag))
    return locked


def main():
    print("=== Rq1.md Sec3 - r0 + calibration curve ===\n")

    r0, dists = compute_r0()
    print("[LOCK] r0 = %.4f km  (percentile-25 tu pilot instance trung lap, n_dists=%d)"
          % (r0, len(dists)))
    print("  pilot params: n=%d B_gw=%d B_od=%d tw=%d n_drivers=%d tau=%.0f gw_od_ratio=0.4"
          % (R0_PILOT_N, R0_PILOT_B_GW, R0_PILOT_B_OD, R0_PILOT_TW, R0_PILOT_N_DRIVERS, R0_PILOT_TAU))
    print("  min=%.4f  max=%.4f  median=%.4f\n" % (min(dists), max(dists), statistics.median(dists)))

    curve = run_calibration_curve(r0)

    print("\n=== [LOCK] Tham so corridor_share cho tung alignment target ===")
    locked = lock_params_for_targets(curve)

    return r0, curve, locked


if __name__ == "__main__":
    main()
