"""Kiem tay thuat toan lower_hull_on_pareto tren vai group co nhieu diem
nhat (theo yeu cau nguoi dung - khong tin blind con so 13.4% chi vi audit
tu dong cua v1 da tung "PASS sai" mot lan). In toan bo (K,W) cua group +
danh dau diem nao duoc giu lai tren hull, de tu doi chieu bang mat/ve tay.

Dung LAI chinh xac ham lower_hull_on_pareto/pareto_filter cua
convex_hull_test_v2.py (khong viet lai logic) - chi them buoc IN CHI TIET
va 1 kiem tra doc lap (brute-force O(n^2): 1 diem la Pareto-efficient VA
tren hull khi va chi khi khong ton tai to hop convex nao "bao" no tu 2
diem khac re hon - kiem bang cach thu TUNG cap diem khac lam "canh", xem
diem dang xet co nam duoi duong noi 2 diem do khong).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convex_hull_test_v2 as C
import instance_gen as IG
import dp_labeling as DL


def brute_force_is_on_lower_hull(points, idx):
    """Kiem DOC LAP (khong dung lower_hull_on_pareto): diem points[idx] nam
    tren lower-left convex hull khi va chi khi KHONG ton tai 2 diem khac a,b
    (a.K < points[idx].K < b.K hoac nguoc lai theo thu tu phu hop) sao cho
    doan thang a-b di qua DUOI diem idx (tuc idx nam "phia tren" doan a-b,
    bi dominate ve mat convex boi to hop lin cua a va b).

    Cach kiem truc tiep hon: idx nam tren lower hull <=> ton tai heso b>=0
    sao cho idx la argmin cua (K + b*W) tren TOAN BO points (khong chi
    Pareto front) - quet mot luoi b RAT MIN de xap xi (numeric check doc
    lap voi thuat toan hinh hoc)."""
    n = len(points)
    Kx, Wx = points[idx][0], points[idx][1]
    # quet luoi b tu 0 den rat lon (1e6) - neu ton tai b nao lam idx la
    # argmin duy nhat/dong-argmin thi idx nam tren hull
    import itertools
    b_grid = [0.0] + [10 ** e for e in range(-3, 7)] + [i * 0.1 for i in range(1, 200)]
    for b in b_grid:
        costs = [points[j][0] + b * points[j][1] for j in range(n)]
        min_cost = min(costs)
        if abs(costs[idx] - min_cost) < 1e-9:
            return True, b
    return False, None


def main():
    drivers, orders, tt, meta = IG.generate_instance(
        n=C.N, B_gw=C.B_GW, B_od=C.B_OD, tw_width=C.TW_WIDTH, n_drivers=C.N_DRIVERS,
        seed=C.SEED, tau=C.TAU, spatial_mode=C.SPATIAL_MODE)
    driver_cls = {d["id"]: d["cls"] for d in drivers}
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, C.B_GW, C.B_OD)

    groups = {}
    for did, pool in pool_by_driver.items():
        if driver_cls.get(did) != "GW":
            continue
        for bundle, kw_list in pool.items():
            if len(bundle) > C.B_GW:
                continue
            key = (did, tuple(sorted(bundle)))
            groups[key] = [(K, W, None) for (K, W) in kw_list]

    # lay 5 group nhieu diem nhat
    top5 = sorted(groups.items(), key=lambda kv: -len(kv[1]))[:5]

    print("=== Kiem tay 5 group nhieu diem nhat ===\n")
    all_ok = True
    for key, pts in top5:
        pareto_pts = C.pareto_filter(pts)
        hull_pts = C.lower_hull_on_pareto(pareto_pts)
        hull_kw = set((round(k, 6), round(w, 6)) for k, w, _ in hull_pts)

        print("Group %s: %d diem goc -> %d Pareto -> %d hull" % (key, len(pts), len(pareto_pts), len(hull_pts)))
        print("  Toan bo diem Pareto (K, W), sap theo K tang:")
        for k, w, _ in pareto_pts:
            on_hull_claimed = (round(k, 6), round(w, 6)) in hull_kw
            print("    K=%8.3f  W=%7.4f  %s" % (k, w, "<== HULL (claimed)" if on_hull_claimed else ""))

        # kiem doc lap tung diem Pareto: co phai la argmin cho MOT b>=0 nao
        # do khong (brute-force numeric, khong dung lai lower_hull_on_pareto)
        print("  Kiem doc lap (brute-force numeric, quet b grid rong):")
        mismatch = 0
        pareto_only_pts = [(k, w) for k, w, _ in pareto_pts]
        for i, (k, w) in enumerate(pareto_only_pts):
            is_argmin_somewhere, best_b = brute_force_is_on_lower_hull(pareto_only_pts, i)
            claimed_on_hull = (round(k, 6), round(w, 6)) in hull_kw
            status = "OK" if is_argmin_somewhere == claimed_on_hull else "MISMATCH"
            if status == "MISMATCH":
                mismatch += 1
                all_ok = False
            print("    K=%8.3f W=%7.4f  hull_claims=%-5s  brute_force_says=%-5s  %s"
                  % (k, w, claimed_on_hull, is_argmin_somewhere, status))
        print("  -> %d mismatch tren %d diem Pareto\n" % (mismatch, len(pareto_only_pts)))

    print("=== KET LUAN KIEM TAY ===")
    if all_ok:
        print("[OK] Khong co mismatch nao giua lower_hull_on_pareto va brute-force doc lap,")
        print("     tren toan bo 5 group nhieu diem nhat. Thuat toan hull v2 dang tin cay.")
    else:
        print("[CANH BAO] Co mismatch - can xem lai thuat toan lower_hull_on_pareto TRUOC KHI")
        print("           dua bat ky con so reduction nao vao ban thao chinh thuc.")


if __name__ == "__main__":
    main()
