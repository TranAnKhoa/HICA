"""Kiem tra nhanh (theo yeu cau nguoi dung 2026-09-16, TRUOC khi dua finding
phu 'OD-FIRST tot hon GW-FIRST' vao bai chinh thuc): do kich thuoc route pool
trung binh (so bundle/driver) cua GW vs OD tren CHINH cac instance RQ1 da
dung o alignment=0.70 va 0.90 (khong phai hot cell T5 rieng biet truoc do).

Dung LAI CHINH XAC cong thuc seed da khoa (rq1_main_grid.py: instance_seed_
formula) de tai tao DUNG instance da chay trong main grid - KHONG logic moi,
chi them 1 buoc dem (n_bundles/driver) vao pool da co san tu Algorithm A.
"""

import os
import sys
import statistics

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import rq1_main_grid as MG

N_GRID = [10, 15, 20]
SUPPLY_RATIOS = [(2, 2), (3, 2), (2, 3), (3, 3)]
REPLICATIONS = 25
ALIGN_TARGETS_TO_CHECK = [0.70, 0.90]


def main():
    params = MG.load_locked_params()
    MG.verify_hash(params)

    print("=== Kiem tra kich thuoc route pool GW vs OD - alignment=0.70 va 0.90 ===")
    print("(Dung DUNG seed formula + tham so da khoa cua RQ1 main grid, tai tao")
    print(" CHINH XAC cac instance da chay - khong logic moi, chi them dem pool)\n")

    for align in ALIGN_TARGETS_TO_CHECK:
        cs, cb, deviation = MG.get_corridor_params(params, align)
        print("--- alignment=%.2f (corridor_share=%.2f corridor_buffer_km=%.2f) ---"
             % (align, cs, cb))

        gw_bundle_counts_all = []
        od_bundle_counts_all = []

        for n in N_GRID:
            for (n_gw, n_od) in SUPPLY_RATIOS:
                cell_gw = []
                cell_od = []
                for rep in range(REPLICATIONS):
                    n_drivers = n_gw + n_od
                    gen_seed = IG.stable_seed(n, MG.B_GW, MG.B_OD, align, n_gw, n_od, rep,
                                              "rq1_main_grid")
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=MG.B_GW, B_od=MG.B_OD, tw_width=MG.TW_WIDTH,
                        n_drivers=n_drivers, seed=gen_seed, tau=MG.TAU,
                        spatial_mode="dispersed", corridor_share=cs, corridor_buffer_km=cb,
                        gw_od_ratio=n_gw / float(n_drivers))

                    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders,
                                                              MG.B_GW, MG.B_OD)
                    for drv in drivers:
                        n_bundles = len(pool_by_driver[drv["id"]])
                        if drv["cls"] == "GW":
                            cell_gw.append(n_bundles)
                        else:
                            cell_od.append(n_bundles)

                gw_bundle_counts_all.extend(cell_gw)
                od_bundle_counts_all.extend(cell_od)
                print("  n=%2d supply=(%d,%d): GW mean_bundles/driver=%7.2f (n_driver=%3d)  "
                     "OD mean_bundles/driver=%7.2f (n_driver=%3d)  ratio(OD/GW)=%.4f"
                     % (n, n_gw, n_od, statistics.mean(cell_gw), len(cell_gw),
                        statistics.mean(cell_od), len(cell_od),
                        statistics.mean(cell_od) / statistics.mean(cell_gw)))

        print("\n  [TONG HOP alignment=%.2f]" % align)
        print("  GW: mean=%.2f  median=%.2f  min=%d  max=%d  (n_driver=%d)"
             % (statistics.mean(gw_bundle_counts_all), statistics.median(gw_bundle_counts_all),
                min(gw_bundle_counts_all), max(gw_bundle_counts_all), len(gw_bundle_counts_all)))
        print("  OD: mean=%.2f  median=%.2f  min=%d  max=%d  (n_driver=%d)"
             % (statistics.mean(od_bundle_counts_all), statistics.median(od_bundle_counts_all),
                min(od_bundle_counts_all), max(od_bundle_counts_all), len(od_bundle_counts_all)))
        print("  ratio OD/GW (mean bundles/driver) = %.4f\n"
             % (statistics.mean(od_bundle_counts_all) / statistics.mean(gw_bundle_counts_all)))


if __name__ == "__main__":
    main()
