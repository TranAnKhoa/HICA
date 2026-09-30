"""Spec 2a - Gate 0: DP route pool == brute-force route pool, n in {3..7}.

Vi instance_gen.py la code MOI, Gate 0 chay lai (khong skip). brute_force.py
doc lap hoan toan voi dp_labeling.py / t6_dp.py (khong import chung).

[PATCH new_03] B tach B_gw/B_od - Gate 0 kiem DP THUAN (compat_graph=None,
PCF tat) tren luoi B_gw x B_od moi. PCF correctness co gate rieng (Gate T4-B,
xem run_gate_t4b.py) - CHI cai neu chan doan Viec 2.0 cho thay dang lam.

PASS = 0 vi pham completeness: voi MOI driver, MOI bundle S, Pareto front
(K,W) cua DP KHOP Pareto front cua brute-force (so 2 chieu):
  - moi diem brute-force co diem DP <= (ca K lan W)   [completeness]
  - moi diem DP co diem brute-force <= (ca K lan W)    [soundness]
va tap bundle S ton tai phai trung nhau (bundle-existence).
"""

import os
import sys
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import brute_force as BF

EPS = 1e-4

N_GRID = (3, 4, 5, 6, 7)
BGW_GRID = (2, 3, 4)
BOD_GRID = (1, 2)     # [PATCH new_03] B tach lop - Gate 0 van kiem DP thuan (PCF tat)
TW_GRID = (60, 120)
SEEDS = range(3)
N_DRIVERS = 4          # 2 GW + 2 OD - du de kiem GW lan OD, nho de brute-force nhanh
TAU = 20.0

# brute-force (2k)! bung no o n lon + B lon. Gioi han: chi chay to-hop
# co the brute trong thoi gian hop ly. n=7,B=4 -> C(7,4)*8! ~ 1.4M perm/driver,
# van chay duoc nhung cham; giu vi day la GATE (dung tuyet doi). Bo n=7,B=4
# va n=6,B=4 (2k=8, C nhieu) chi khi tong thoi gian > ~15 phut - xem report.
def _skip_cell(n, B):
    return False


def _match_front(front_a, front_b):
    """moi diem trong front_a co diem trong front_b <= ca 2 chieu."""
    for (Ka, Wa) in front_a:
        ok = any(Kb <= Ka + EPS and Wb <= Wa + EPS for (Kb, Wb) in front_b)
        if not ok:
            return False, (Ka, Wa)
    return True, None


def check_instance(travel_time, drivers, orders, B_gw, B_od, ctx):
    viol = []
    for drv in drivers:
        dp = DL.run_pool(travel_time, drv, orders, B_gw, B_od)["pool"]
        bt = BF.brute_pool_for_driver(travel_time, drv, orders, B_gw, B_od)

        keys = set(dp.keys()) | set(bt.keys())
        for S in keys:
            in_dp, in_bt = S in dp, S in bt
            if in_dp != in_bt:
                viol.append(dict(ctx=ctx, drv=drv["id"], S=sorted(S),
                                 kind="bundle-existence",
                                 detail="DP=%s BRUTE=%s" % (in_dp, in_bt)))
                continue
            if not in_dp:
                continue
            ok1, bad1 = _match_front(bt[S], dp[S])   # completeness
            if not ok1:
                viol.append(dict(ctx=ctx, drv=drv["id"], S=sorted(S),
                                 kind="completeness",
                                 detail="brute point %s khong co DP <=; DP_front=%s"
                                        % (bad1, [(round(k, 4), round(w, 4)) for k, w in dp[S]])))
            ok2, bad2 = _match_front(dp[S], bt[S])   # soundness
            if not ok2:
                viol.append(dict(ctx=ctx, drv=drv["id"], S=sorted(S),
                                 kind="soundness",
                                 detail="DP point %s khong co brute <=; brute_front=%s"
                                        % (bad2, [(round(k, 4), round(w, 4)) for k, w in bt[S]])))
    return viol


def main():
    t0 = time.time()
    all_viol = []
    n_checked = 0
    for n in N_GRID:
        for B_gw in BGW_GRID:
            for B_od in BOD_GRID:
                if n < 1:
                    continue
                for tw in TW_GRID:
                    for sd in SEEDS:
                        for mode in ("dispersed", "clustered"):
                            seed = IG.stable_seed(n, B_gw, B_od, tw, sd, mode, "gate0")
                            drivers, orders, tt, meta = IG.generate_instance(
                                n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=N_DRIVERS,
                                seed=seed, tau=TAU, spatial_mode=mode)
                            ctx = "n=%d B_gw=%d B_od=%d tw=%d seed=%d mode=%s" % (
                                n, B_gw, B_od, tw, sd, mode)
                            v = check_instance(tt, drivers, orders, B_gw, B_od, ctx)
                            n_checked += 1
                            if v:
                                all_viol.extend(v)
                                print("!!! VIOLATION at %s" % ctx)
                                for x in v[:5]:
                                    print("   ", x)
                                print("\n*** GATE 0 FAILED - DUNG NGAY ***")
                                _write(all_viol)
                                print("elapsed=%.1fs, instances=%d" % (time.time() - t0, n_checked))
                                return 1
        print("  n=%d done  (%.1fs, instances=%d, violations=%d)"
              % (n, time.time() - t0, n_checked, len(all_viol)))

    _write(all_viol)
    print("\n=== GATE 0 SUMMARY ===")
    print("instances checked: %d" % n_checked)
    print("violations: %d" % len(all_viol))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


def _write(viol):
    import csv
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    with open(os.path.join(outdir, "gate0_violations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ctx", "drv", "S", "kind", "detail"])
        w.writeheader()
        w.writerows(viol)


if __name__ == "__main__":
    sys.exit(main())
