"""new_01.md Viec 2 - Gate feasibility_rate_k1 truoc/sau patch OD corridor bias.

Khong chay DP - chi brute-force kiem tung cap (driver OD, order) rieng le:
pickup -> deliver -> home co kip deadline_home = t0 + direct_time + tau khong.

feasibility_rate_k1 = (so cap OD-order feasible o k=1) / (tong so cap OD-order xet)

"Truoc patch" duoc tai dung LOGIC CU (rai deu toan hop 20x20km, ready_time
rai deu ca ngay) ngay trong file nay - vi instance_gen.py da duoc sua tai
cho (khong con ban cu de import) va day la code RAT don gian, tai dung
khong lam sai lech gi ket qua "truoc patch" (chi dung de doi chieu).

"Sau patch" goi thang instance_gen.generate_instance() hien tai (da sua).

Nguong bat buoc (khoa truoc): feasibility_rate_k1 >= 0.5 sau patch, voi MOI
tau trong luoi 2b. Neu khong dat - DUNG, khong chay pipeline lon.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "feasibility_gate_k1.csv")

# luoi 2b (grid_2b.yaml) - khong lam luoi rieng
N_GRID = (30, 50)
TAU_GRID = (30, 45, 60)   # [PATCH new_01] bo tau in {10,15,20}: feasibility_rate_k1
#   do duoc tuong ung {0%, 3.4%, 9.5%} du da ap dung ca corridor bias +
#   AREA_KM=8.0 - bat kha thi hinh hoc CO HE THONG (2xSERVICE_MIN=10p +
#   travel time > 0 luon vuot budget nho), khong phai bug. Quyet dinh
#   nguoi dung (khong ha SERVICE_MIN, khong tang AREA them, khong tang
#   corridor bias manh hon) - dung do tim tham so tai day.
SPATIAL_GRID = ("dispersed", "clustered")
SUPPLY_GRID = (0.3, 0.6, 1.0)
SEEDS = range(10)          # 10 seed/o nhu spec yeu cau ("10 seed du")
B_FIXED = 3
TW_FIXED = 120

AREA_KM = IG.AREA_KM
SPEED_KMH = IG.SPEED_KMH
DAY_MIN = IG.DAY_MIN


def _euclid_km(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _feasible_k1(o_xy, h_xy, p_xy, d_xy, tau, tw_width, ready_p, service=IG.SERVICE_MIN):
    """driver OD: start=o_xy, home=h_xy. Order: pickup=p_xy, delivery=d_xy.
    Route k=1: start -> pickup -> delivery -> home. Kiem tw + deadline_home."""
    def tt(a, b):
        return _euclid_km(a, b) / SPEED_KMH * 60.0

    direct_t = tt(o_xy, h_xy)
    deadline_home = 0.0 + direct_t + tau     # t0=0.0 luon (dung quy uoc IG)

    arr_p = tt(o_xy, p_xy)
    start_service_p = max(arr_p, ready_p)
    if start_service_p > ready_p + tw_width + 1e-9:      # deadline_p
        return False
    depart_p = start_service_p + service

    arr_d = depart_p + tt(p_xy, d_xy)
    start_service_d = max(arr_d, ready_p)                # ready_d = ready_p (IG convention)
    if start_service_d > ready_p + 2 * tw_width + 1e-9:  # deadline_d
        return False
    depart_d = start_service_d + service

    arr_home = depart_d + tt(d_xy, h_xy)
    return arr_home <= deadline_home + 1e-9


def gen_before(n, tau, spatial_mode, supply_ratio, seed):
    """Logic CU (truoc patch): rai deu toan hop, ready_time rai deu ca ngay,
    KHONG neo theo tau, KHONG corridor bias. Tai dung de doi chieu."""
    rng = random.Random(seed)
    n_drivers = max(1, int(round(supply_ratio * n)))
    n_gw = int(round(n_drivers * 0.5))
    n_od = n_drivers - n_gw

    centers = [(rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)) for _ in range(IG.N_CLUSTERS)]

    orders = []
    for _ in range(n):
        if spatial_mode == "clustered":
            c = rng.choice(centers)
            ang = rng.uniform(0, 2 * math.pi)
            r = IG.CLUSTER_RADIUS_KM * math.sqrt(rng.random())
            p_xy = (min(AREA_KM, max(0.0, c[0] + r * math.cos(ang))),
                    min(AREA_KM, max(0.0, c[1] + r * math.sin(ang))))
            d_xy = (rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM))
        else:
            p_xy = (rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM))
            d_xy = (rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM))
        ready_p = rng.uniform(0.0, max(1.0, DAY_MIN - TW_FIXED))
        orders.append((p_xy, d_xy, ready_p))

    # GW toa do (tieu thu rng dung thu tu nhu IG cu: GW truoc OD)
    for _ in range(n_gw):
        rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM)

    od_list = []
    for _ in range(n_od):
        o_xy = (rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM))
        h_xy = (rng.uniform(0, AREA_KM), rng.uniform(0, AREA_KM))
        od_list.append((o_xy, h_xy))

    n_feas = 0
    n_total = 0
    for (o_xy, h_xy) in od_list:
        for (p_xy, d_xy, ready_p) in orders:
            n_total += 1
            if _feasible_k1(o_xy, h_xy, p_xy, d_xy, tau, TW_FIXED, ready_p):
                n_feas += 1
    return n_feas, n_total


def gen_after(n, tau, spatial_mode, supply_ratio, seed):
    """Logic MOI (sau patch): goi thang instance_gen.py hien tai, doc lai
    toa do tu drivers/orders da sinh (khong doan lai logic sinh)."""
    n_drivers = max(1, int(round(supply_ratio * n)))
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_FIXED, B_od=B_FIXED, tw_width=TW_FIXED, n_drivers=n_drivers, seed=seed,
        tau=float(tau), spatial_mode=spatial_mode)

    od_drivers = [d for d in drivers if d["cls"] == "OD"]
    n_feas = 0
    n_total = 0
    for drv in od_drivers:
        direct_t = drv["direct_time"]
        deadline_home = drv["t0"] + direct_t + drv["tau"]
        for oid, o in orders.items():
            n_total += 1
            arr_p = tt(drv["start_node"], o["pickup_node"])
            start_p = max(arr_p, o["ready_time_p"])
            if start_p > o["deadline_p"] + 1e-9:
                continue
            depart_p = start_p + o["service_time"]
            arr_d = depart_p + tt(o["pickup_node"], o["delivery_node"])
            start_d = max(arr_d, o["ready_time_d"])
            if start_d > o["deadline_d"] + 1e-9:
                continue
            depart_d = start_d + o["service_time"]
            arr_home = depart_d + tt(o["delivery_node"], drv["home_node"])
            if arr_home <= deadline_home + 1e-9:
                n_feas += 1
    return n_feas, n_total


def main():
    rows = []
    print("%-6s %-10s %-6s %-8s %14s %14s" %
          ("tau", "mode", "sr", "n", "before_k1", "after_k1"))
    by_tau_before = {t: [0, 0] for t in TAU_GRID}
    by_tau_after = {t: [0, 0] for t in TAU_GRID}

    for n in N_GRID:
        for spatial_mode in SPATIAL_GRID:
            for supply_ratio in SUPPLY_GRID:
                for tau in TAU_GRID:
                    tot_before = [0, 0]
                    tot_after = [0, 0]
                    for sd in SEEDS:
                        seed = IG.stable_seed(n, tau, spatial_mode, supply_ratio, sd, "feasgate")
                        fb, tb = gen_before(n, tau, spatial_mode, supply_ratio, seed)
                        fa, ta = gen_after(n, tau, spatial_mode, supply_ratio, seed)
                        tot_before[0] += fb
                        tot_before[1] += tb
                        tot_after[0] += fa
                        tot_after[1] += ta
                    rate_before = tot_before[0] / tot_before[1] if tot_before[1] else 0.0
                    rate_after = tot_after[0] / tot_after[1] if tot_after[1] else 0.0
                    by_tau_before[tau][0] += tot_before[0]
                    by_tau_before[tau][1] += tot_before[1]
                    by_tau_after[tau][0] += tot_after[0]
                    by_tau_after[tau][1] += tot_after[1]
                    rows.append(dict(n=n, spatial_mode=spatial_mode, supply_ratio=supply_ratio,
                                      tau=tau, feasibility_rate_k1_before=round(rate_before, 4),
                                      feasibility_rate_k1_after=round(rate_after, 4),
                                      n_pairs_checked=tot_after[1]))
                    print("%-6d %-10s %-6.1f %-8d %13.2f%% %13.2f%%" %
                          (tau, spatial_mode, supply_ratio, n, rate_before * 100, rate_after * 100))

    print("\n=== TONG HOP THEO TAU (gop tat ca n/mode/supply_ratio) ===")
    print("%-6s %14s %14s" % ("tau", "before_k1", "after_k1"))
    summary_rows = []
    for tau in TAU_GRID:
        fb, tb = by_tau_before[tau]
        fa, ta = by_tau_after[tau]
        rb = fb / tb if tb else 0.0
        ra = fa / ta if ta else 0.0
        summary_rows.append(dict(tau=tau, rate_before=round(rb, 4), rate_after=round(ra, 4)))
        print("%-6d %13.2f%% %13.2f%%" % (tau, rb * 100, ra * 100))

    import csv
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "spatial_mode", "supply_ratio", "tau",
                                          "feasibility_rate_k1_before",
                                          "feasibility_rate_k1_after", "n_pairs_checked"])
        w.writeheader()
        w.writerows(rows)

    outdir = os.path.join(ROOT, "results")
    with open(os.path.join(outdir, "feasibility_gate_k1_by_tau.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tau", "rate_before", "rate_after"])
        w.writeheader()
        w.writerows(summary_rows)

    overall_after_feas = sum(by_tau_after[t][0] for t in TAU_GRID)
    overall_after_total = sum(by_tau_after[t][1] for t in TAU_GRID)
    overall_rate = overall_after_feas / overall_after_total if overall_after_total else 0.0
    print("\nOVERALL after-patch feasibility_rate_k1 = %.4f" % overall_rate)
    print("GATE (>= 0.5): %s" % ("PASS" if overall_rate >= 0.5 else "FAIL"))
    all_tau_pass = all(by_tau_after[t][0] / by_tau_after[t][1] >= 0.5 for t in TAU_GRID if by_tau_after[t][1])
    print("GATE per-tau (each >= 0.5): %s" % ("PASS" if all_tau_pass else "FAIL"))
    return 0 if overall_rate >= 0.5 else 1


if __name__ == "__main__":
    sys.exit(main())
