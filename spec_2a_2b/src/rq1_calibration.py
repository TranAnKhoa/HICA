"""Rq1.md Sec1.4 - calibration pass cho q_o (base_fee, rate_per_km, free_radius).
Chay MOT LAN tren batch pilot NHO, KHONG phai instance se dung cho RQ1 that
(seed/tham so rieng, danh dau ro "pilot", khong tai su dung lai o main grid).

Muc tieu mem (Rq1.md dong 76-79):
  - FD rate (ty le order roi vao FD) trong khoang ~10-50%.
  - Khong lop nao (GW hay OD) thang 0% hoac 100% tuyet doi tren moi supply
    ratio da dinh o Sec4.

Quet vai gia tri base_fee/rate_per_km (giu free_radius co dinh o muc hop ly:
1.0km, ban kinh mien phi nho, khong anh huong nhieu toi cac dai dist thuc te
8x8km cua generator) - CHON BO DAU TIEN dat ca 2 tieu chi ROI DUNG LAI (khong
tiep tuc quet de "toi uu" - dung tinh than khoa tham so, khong phai tim diem
dep nhat).
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import rq1_wdp as RW

# ---------------------------------------------------------------------------
# Batch pilot - KHONG dung cho RQ1 that. Tag seed rieng "rq1_pilot_calib" de
# khong bao gio trung voi seed cua main grid (Rq1.md Sec4 seed policy).
# ---------------------------------------------------------------------------

PILOT_N = 12
PILOT_B_GW = 3
PILOT_B_OD = 3
PILOT_TW = 120
PILOT_TAU = 30.0
PILOT_SUPPLY = [(2, 2), (3, 2), (2, 3), (3, 3)]   # dung dung luoi Sec4
PILOT_SEEDS = range(5)   # 5 replication pilot / supply ratio - du de thay xu huong

FREE_RADIUS_FIXED = 1.0   # km - co dinh, khong dua vao grid quet

BASE_FEE_GRID = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 14.0]
RATE_PER_KM_GRID = [0.8, 1.2, 1.6, 2.0, 2.5, 3.0]

# Combo da chay o lan quet dau (khong chay lai - tiet kiem thoi gian, ket qua
# da co trong log truoc). Chi anh huong thu tu in/dung lai o combo PASS dau
# tien - KHONG bo qua bao cao, van in du toan bo grid khi tong hop cuoi.
_ALREADY_RUN = {
    (2.0, 0.8), (2.0, 1.2), (2.0, 1.6), (2.0, 2.0),
    (3.0, 0.8), (3.0, 1.2), (3.0, 1.6), (3.0, 2.0),
    (4.0, 0.8), (4.0, 1.2), (4.0, 1.6), (4.0, 2.0),
    (5.0, 0.8), (5.0, 1.2), (5.0, 1.6), (5.0, 2.0),
    (6.0, 0.8), (6.0, 1.2), (6.0, 1.6), (6.0, 2.0),
}
_PRIOR_RESULTS = [
    dict(base_fee=2.0, rate_per_km=0.8, free_radius=1.0, fd_rate=1.000, total_gw_wins=0, total_od_wins=0, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=4),
    dict(base_fee=2.0, rate_per_km=1.2, free_radius=1.0, fd_rate=1.000, total_gw_wins=0, total_od_wins=0, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=4),
    dict(base_fee=2.0, rate_per_km=1.6, free_radius=1.0, fd_rate=1.000, total_gw_wins=0, total_od_wins=0, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=4),
    dict(base_fee=2.0, rate_per_km=2.0, free_radius=1.0, fd_rate=0.992, total_gw_wins=0, total_od_wins=2, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=2),
    dict(base_fee=3.0, rate_per_km=0.8, free_radius=1.0, fd_rate=1.000, total_gw_wins=0, total_od_wins=0, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=4),
    dict(base_fee=3.0, rate_per_km=1.2, free_radius=1.0, fd_rate=0.996, total_gw_wins=0, total_od_wins=1, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=3),
    dict(base_fee=3.0, rate_per_km=1.6, free_radius=1.0, fd_rate=0.992, total_gw_wins=0, total_od_wins=2, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=2),
    dict(base_fee=3.0, rate_per_km=2.0, free_radius=1.0, fd_rate=0.979, total_gw_wins=0, total_od_wins=5, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=1),
    dict(base_fee=4.0, rate_per_km=0.8, free_radius=1.0, fd_rate=0.992, total_gw_wins=0, total_od_wins=2, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=2),
    dict(base_fee=4.0, rate_per_km=1.2, free_radius=1.0, fd_rate=0.988, total_gw_wins=0, total_od_wins=3, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=1),
    dict(base_fee=4.0, rate_per_km=1.6, free_radius=1.0, fd_rate=0.975, total_gw_wins=0, total_od_wins=6, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=1),
    dict(base_fee=4.0, rate_per_km=2.0, free_radius=1.0, fd_rate=0.963, total_gw_wins=0, total_od_wins=9, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=5.0, rate_per_km=0.8, free_radius=1.0, fd_rate=0.963, total_gw_wins=0, total_od_wins=9, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=5.0, rate_per_km=1.2, free_radius=1.0, fd_rate=0.958, total_gw_wins=0, total_od_wins=10, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=5.0, rate_per_km=1.6, free_radius=1.0, fd_rate=0.946, total_gw_wins=0, total_od_wins=13, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=5.0, rate_per_km=2.0, free_radius=1.0, fd_rate=0.929, total_gw_wins=1, total_od_wins=14, n_supply_cells_gw_zero=3, n_supply_cells_od_zero=0),
    dict(base_fee=6.0, rate_per_km=0.8, free_radius=1.0, fd_rate=0.938, total_gw_wins=0, total_od_wins=12, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=6.0, rate_per_km=1.2, free_radius=1.0, fd_rate=0.925, total_gw_wins=0, total_od_wins=15, n_supply_cells_gw_zero=4, n_supply_cells_od_zero=0),
    dict(base_fee=6.0, rate_per_km=1.6, free_radius=1.0, fd_rate=0.871, total_gw_wins=4, total_od_wins=16, n_supply_cells_gw_zero=1, n_supply_cells_od_zero=0),
    dict(base_fee=6.0, rate_per_km=2.0, free_radius=1.0, fd_rate=0.825, total_gw_wins=7, total_od_wins=19, n_supply_cells_gw_zero=1, n_supply_cells_od_zero=0),
]


def make_pilot_instance(n_gw, n_od, seed):
    n_drivers = n_gw + n_od
    gw_od_ratio = n_gw / n_drivers if n_drivers > 0 else 0.5
    gen_seed = IG.stable_seed(PILOT_N, PILOT_B_GW, PILOT_B_OD, PILOT_TAU,
                              "dispersed", n_gw, n_od, seed, "rq1_pilot_calib")
    drivers, orders, tt, meta = IG.generate_instance(
        n=PILOT_N, B_gw=PILOT_B_GW, B_od=PILOT_B_OD, tw_width=PILOT_TW,
        n_drivers=n_drivers, seed=gen_seed, tau=PILOT_TAU,
        spatial_mode="dispersed", gw_od_ratio=gw_od_ratio)
    return drivers, orders, tt, meta


def eval_params(base_fee, rate_per_km, free_radius=FREE_RADIUS_FIXED):
    """Chay tren toan bo batch pilot (4 supply ratio x 5 seed = 20 instance),
    tra {fd_rate, gw_win_rate, od_win_rate, n_cells_gw_all0, n_cells_od_all0}."""
    total_orders = 0
    total_fd = 0
    total_gw_wins = 0
    total_od_wins = 0
    per_supply_gw_win = {sr: [] for sr in PILOT_SUPPLY}
    per_supply_od_win = {sr: [] for sr in PILOT_SUPPLY}

    for (n_gw, n_od) in PILOT_SUPPLY:
        for seed in PILOT_SEEDS:
            drivers, orders, tt, meta = make_pilot_instance(n_gw, n_od, seed)
            pool_by_driver, agg = DL.build_route_pool(
                tt, drivers, orders, B_gw=PILOT_B_GW, B_od=PILOT_B_OD)

            rng = random.Random(IG.stable_seed(n_gw, n_od, seed, "theta_pilot"))
            theta_by_driver = RC.assign_theta(rng, drivers)
            q_o_by_order = RC.assign_q_o(orders, tt, base_fee=base_fee,
                                         rate_per_km=rate_per_km, free_radius=free_radius)

            r = RW.solve_wdp_for_instance(pool_by_driver, orders, theta_by_driver,
                                          q_o_by_order, presolve=True)

            wdp_drivers = RW.build_wdp_drivers(pool_by_driver, theta_by_driver)
            name_to_driver = {}
            for did, dv in wdp_drivers.items():
                for (rid, ofs, cost) in dv["routes"]:
                    name_to_driver["x_" + rid.replace("-", "_")] = did
            # t8_cplex._sanitize thay ky tu khong phai alnum/_ bang '_' - route
            # id o day chi gom chu+so+'_' nen khong can sanitize lai, nhung
            # phong truong hop driver id co ky tu la (khong co trong generator
            # nay - GW/OD id la "gwN"/"odN") giu nguyen mapping don gian.

            cls_by_driver = {dv["id"]: dv["cls"] for dv in drivers}
            n_orders_cell = len(orders)
            covered = set()
            gw_wins_cell = 0
            od_wins_cell = 0
            for vname in r["alloc_x"]:
                did = name_to_driver.get(vname)
                if did is None:
                    continue
                # dem 1 "win" cho driver (khong phai order) - dung cho
                # win rate theo Sec1.4 "win rate GW vs OD"
                if cls_by_driver[did] == "GW":
                    gw_wins_cell += 1
                else:
                    od_wins_cell += 1

            n_fd_cell = n_orders_cell   # se tru lai orders da duoc cover ben duoi
            # can biet orders nao duoc cover boi driver thang - dung
            # build_full_alloc_map tu t8_cplex qua rq1_wdp (khong co san ham
            # rieng - suy tu route id: route id chua thong tin order set qua
            # wdp_drivers, tra lai bang cach doi chieu ten bien)
            covered_orders = set()
            rid_to_orders = {}
            for did, dv in wdp_drivers.items():
                for (rid, ofs, cost) in dv["routes"]:
                    rid_to_orders["x_" + rid] = ofs
            for vname in r["alloc_x"]:
                if vname in rid_to_orders:
                    covered_orders |= set(rid_to_orders[vname])
            n_fd_cell = n_orders_cell - len(covered_orders)

            total_orders += n_orders_cell
            total_fd += n_fd_cell
            total_gw_wins += gw_wins_cell
            total_od_wins += od_wins_cell
            per_supply_gw_win[(n_gw, n_od)].append(gw_wins_cell)
            per_supply_od_win[(n_gw, n_od)].append(od_wins_cell)

    fd_rate = total_fd / total_orders if total_orders > 0 else None
    n_cells_gw_all0 = sum(1 for sr, vals in per_supply_gw_win.items() if sum(vals) == 0)
    n_cells_od_all0 = sum(1 for sr, vals in per_supply_od_win.items() if sum(vals) == 0)

    return dict(
        base_fee=base_fee, rate_per_km=rate_per_km, free_radius=free_radius,
        fd_rate=fd_rate, total_gw_wins=total_gw_wins, total_od_wins=total_od_wins,
        n_supply_cells_gw_zero=n_cells_gw_all0, n_supply_cells_od_zero=n_cells_od_all0,
    )


def main():
    print("=== Rq1 Sec1.4 calibration pass: quet base_fee x rate_per_km ===")
    print("Batch pilot: n=%d, B_gw=%d, B_od=%d, tau=%.0f, %d supply ratio x %d seed = %d instance/cell"
          % (PILOT_N, PILOT_B_GW, PILOT_B_OD, PILOT_TAU, len(PILOT_SUPPLY),
             len(list(PILOT_SEEDS)), len(PILOT_SUPPLY) * len(list(PILOT_SEEDS))))
    print()

    results = []
    chosen = None

    def _report(r):
        fd_ok = r["fd_rate"] is not None and 0.10 <= r["fd_rate"] <= 0.50
        no_zero = r["n_supply_cells_gw_zero"] == 0 and r["n_supply_cells_od_zero"] == 0
        status = "PASS" if (fd_ok and no_zero) else ""
        print("base_fee=%.1f rate_per_km=%.1f  fd_rate=%.3f  gw_wins=%3d od_wins=%3d  "
              "gw_zero_cells=%d od_zero_cells=%d  %s"
              % (r["base_fee"], r["rate_per_km"], r["fd_rate"], r["total_gw_wins"], r["total_od_wins"],
                 r["n_supply_cells_gw_zero"], r["n_supply_cells_od_zero"], status))
        return status == "PASS"

    for r in _PRIOR_RESULTS:
        results.append(r)
        if _report(r) and chosen is None:
            chosen = r

    for base_fee in BASE_FEE_GRID:
        for rate_per_km in RATE_PER_KM_GRID:
            if (base_fee, rate_per_km) in _ALREADY_RUN:
                continue
            r = eval_params(base_fee, rate_per_km)
            results.append(r)
            if _report(r) and chosen is None:
                chosen = r

    print()
    if chosen is not None:
        print("=== [LOCK] Bo tham so DAU TIEN dat ca 2 tieu chi (dung lai, khong quet tiep) ===")
        print("base_fee=%.2f  rate_per_km=%.2f  free_radius=%.2f"
              % (chosen["base_fee"], chosen["rate_per_km"], chosen["free_radius"]))
        print("fd_rate=%.3f  (muc tieu [0.10, 0.50])" % chosen["fd_rate"])
        print("gw_zero_cells=%d  od_zero_cells=%d  (muc tieu = 0 ca hai)"
              % (chosen["n_supply_cells_gw_zero"], chosen["n_supply_cells_od_zero"]))
    else:
        print("=== KHONG tim duoc bo tham so nao dat ca 2 tieu chi trong grid da quet ===")
        print("Can mo rong BASE_FEE_GRID/RATE_PER_KM_GRID (KHONG tu y chon so ngoai grid da")
        print("cong bo o day) - dung lai, bao nguoi dung truoc khi mo rong.")

    return results, chosen


if __name__ == "__main__":
    main()
