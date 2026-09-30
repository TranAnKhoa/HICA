"""new03.md Viec 2.3 - Gate T4-B: PCF correctness, dung khung Gate 0.

So sanh 3 nguon tren CUNG mot instance:
  1. route_pool (PCF BAT)  - dp_labeling.run_pool(..., compat_graph=graph)
  2. route_pool (PCF TAT)  - dp_labeling.run_pool(..., compat_graph=None) = DP goc
  3. brute_force (oracle)  - brute_force.brute_pool_for_driver

PASS = ca 3 nguon cho CUNG route_pool (Pareto-front K,W tung bundle), 0 vi pham.
Neu PCF lam MAT bundle hop le nao (PCF-bat thieu so voi 2 nguon kia) -> PCF SAI,
KHONG duoc noi long gate de "cho qua" (xem new03.md "Viec KHONG duoc lam").
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import brute_force as BF

EPS = 1e-4

# n=3,4,5 da chay xong truoc (0 vi pham, xem results/gate_t4b_stdout.txt) -
# chi con n=6,7 (voi skip-guard ben duoi cho cac cell bat kha thi).
N_GRID = (6, 7)
BGW_GRID = (2, 3, 4, 5)
BOD_GRID = (1, 2)
TW_GRID = (60, 120)
SEEDS = range(3)
N_DRIVERS = 4
TAU = 20.0

# Brute-force oracle la (2k)! / 2^k hoan vi moi bundle kich thuoc k - no thuc
# nghiem xac nhan truc tiep: n=7,B_gw=5,B_od=2 mot driver DA timeout sau 60s+.
# Gate T4-B goi brute-force cho MOI driver (N_DRIVERS=4) x 2 spatial_mode x
# len(SEEDS) x len(TW_GRID) instance/cell - hoan toan bat kha thi o vung nay.
# Bo qua (n,B_gw) qua lon THEO BANG CHUNG THUC NGHIEM (khong phai doan), giu
# nguyen B_od (khong lien quan brute-force blowup, do la truc GW/anchor).
# Nguong: k = n (so don hang toi da 1 bundle co the chua), can (2k)!/2^k nho.
_SKIP_N_BGW = frozenset([
    (6, 4), (6, 5),
    (7, 3), (7, 4), (7, 5),
])


def _skip_cell(n, B_gw):
    return (n, B_gw) in _SKIP_N_BGW


def _match_front(front_a, front_b):
    for (Ka, Wa) in front_a:
        ok = any(Kb <= Ka + EPS and Wb <= Wa + EPS for (Kb, Wb) in front_b)
        if not ok:
            return False, (Ka, Wa)
    return True, None


def _compare_pools(pool_a, pool_b, label_a, label_b, ctx, drv_id, viol):
    keys = set(pool_a.keys()) | set(pool_b.keys())
    for S in keys:
        in_a, in_b = S in pool_a, S in pool_b
        if in_a != in_b:
            viol.append(dict(ctx=ctx, drv=drv_id, S=sorted(S),
                             kind="bundle-existence(%s vs %s)" % (label_a, label_b),
                             detail="%s=%s %s=%s" % (label_a, in_a, label_b, in_b)))
            continue
        if not in_a:
            continue
        ok1, bad1 = _match_front(pool_b[S], pool_a[S])
        if not ok1:
            viol.append(dict(ctx=ctx, drv=drv_id, S=sorted(S),
                             kind="completeness(%s missing vs %s)" % (label_a, label_b),
                             detail="%s point %s khong co %s <=" % (label_b, bad1, label_a)))
        ok2, bad2 = _match_front(pool_a[S], pool_b[S])
        if not ok2:
            viol.append(dict(ctx=ctx, drv=drv_id, S=sorted(S),
                             kind="soundness(%s vs %s)" % (label_a, label_b),
                             detail="%s point %s khong co %s <=" % (label_a, bad2, label_b)))


def check_instance(travel_time, drivers, orders, B_gw, B_od, compat_graph, ctx):
    viol = []
    for drv in drivers:
        pool_pcf_on = DL.run_pool(travel_time, drv, orders, B_gw, B_od,
                                  compat_graph=compat_graph)["pool"]
        pool_pcf_off = DL.run_pool(travel_time, drv, orders, B_gw, B_od,
                                   compat_graph=None)["pool"]
        pool_brute = BF.brute_pool_for_driver(travel_time, drv, orders, B_gw, B_od)

        _compare_pools(pool_pcf_on, pool_pcf_off, "PCF-on", "PCF-off", ctx, drv["id"], viol)
        _compare_pools(pool_pcf_on, pool_brute, "PCF-on", "brute", ctx, drv["id"], viol)
        _compare_pools(pool_pcf_off, pool_brute, "PCF-off", "brute", ctx, drv["id"], viol)
    return viol


def main():
    t0 = time.time()
    all_viol = []
    n_checked = 0
    n_skipped = 0
    for n in N_GRID:
        for B_gw in BGW_GRID:
            if _skip_cell(n, B_gw):
                n_skipped += 1
                continue
            for B_od in BOD_GRID:
                for tw in TW_GRID:
                    for sd in SEEDS:
                        for mode in ("dispersed", "clustered"):
                            seed = IG.stable_seed(n, B_gw, B_od, tw, sd, mode, "gate_t4b")
                            drivers, orders, tt, meta = IG.generate_instance(
                                n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=N_DRIVERS,
                                seed=seed, tau=TAU, spatial_mode=mode)
                            compat_graph = IG.build_compat_graph(tt, orders)
                            ctx = "n=%d B_gw=%d B_od=%d tw=%d seed=%d mode=%s" % (
                                n, B_gw, B_od, tw, sd, mode)
                            v = check_instance(tt, drivers, orders, B_gw, B_od, compat_graph, ctx)
                            n_checked += 1
                            if v:
                                all_viol.extend(v)
                                print("!!! VIOLATION at %s" % ctx)
                                for x in v[:5]:
                                    print("   ", x)
                                print("\n*** GATE T4-B FAILED - DUNG NGAY ***")
                                _write(all_viol)
                                print("elapsed=%.1fs, instances=%d" % (time.time() - t0, n_checked))
                                return 1
        print("  n=%d done  (%.1fs, instances=%d, violations=%d)"
              % (n, time.time() - t0, n_checked, len(all_viol)))

    _write(all_viol)
    print("\n=== GATE T4-B SUMMARY ===")
    print("instances checked: %d" % n_checked)
    print("(n,B_gw) cells skipped (brute-force khong kha thi, xem _SKIP_N_BGW): %d" % n_skipped)
    print("violations: %d" % len(all_viol))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


def _write(viol):
    import csv
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    with open(os.path.join(outdir, "gate_t4b_violations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ctx", "drv", "S", "kind", "detail"])
        w.writeheader()
        w.writerows(viol)


if __name__ == "__main__":
    sys.exit(main())
