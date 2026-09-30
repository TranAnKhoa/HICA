"""Testb_hull_final.md Sec2/4 - Test B chinh: do peak_frontier va runtime
TRUOC/SAU hull filter tai DP intermediate state, tren hot cell da khoa (n=20,
B_gw=4, tw=240, n_drivers=5), CUNG 8 seed da dung o Test A de doi chieu duoc.

Gate n<=6 (gate_hull_n6.py) da PASS 0/96 - duoc phep chay va tin ket qua nay.

Dung t6_dp_hull.run_dp() 2 lan tren CUNG instance: use_hull_filter=False
(tuong duong t6_dp.py goc) va use_hull_filter=True (hull moi), so peak
frontier + runtime.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp_hull as DH

N = 20
B_GW = 4
B_OD = 2
TW_WIDTH = 240
N_DRIVERS = 5
TAU = 30.0
SPATIAL_MODE = "dispersed"

SEEDS = [1, 12345, 8080, 999, 555, 777, 42, 2026]   # dung 8 seed Test A


def run_one_seed(seed):
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=B_OD, tw_width=TW_WIDTH, n_drivers=N_DRIVERS,
        seed=seed, tau=TAU, spatial_mode=SPATIAL_MODE)

    results = {}
    for label, use_hull in [("no_hull", False), ("with_hull", True)]:
        t0 = time.time()
        peak = 0
        total_survived = 0
        total_created = 0
        for drv in drivers:
            B = B_GW if drv["cls"] == "GW" else B_OD
            res = DH.run_dp(tt, drv, orders, B, use_dominance=True,
                            use_hull_filter=use_hull)
            fs = res.get("frontier_sizes", [])
            drv_peak = max((cnt for _lvl, cnt in fs), default=0)
            peak = max(peak, drv_peak)
            total_survived += res["n_labels_survived"]
            total_created += res["n_labels_created"]
        rt = time.time() - t0
        results[label] = dict(runtime_s=rt, peak_frontier=peak,
                              total_survived=total_survived, total_created=total_created)

    return results


def main():
    print("=== Test B - hot cell n=%d B_gw=%d tw=%d n_drivers=%d, %d seed ==="
          % (N, B_GW, TW_WIDTH, N_DRIVERS, len(SEEDS)))
    print()

    rows = []
    for seed in SEEDS:
        t_seed0 = time.time()
        r = run_one_seed(seed)
        no_h = r["no_hull"]
        with_h = r["with_hull"]

        peak_reduction = (100.0 * (no_h["peak_frontier"] - with_h["peak_frontier"])
                          / no_h["peak_frontier"] if no_h["peak_frontier"] else 0.0)
        speedup = (no_h["runtime_s"] / with_h["runtime_s"]
                  if with_h["runtime_s"] > 0 else float("nan"))

        print("seed=%-6d  no_hull: peak=%9d rt=%6.2fs  |  with_hull: peak=%9d rt=%6.2fs  "
              "peak_reduction=%.1f%%  speedup=%.2fx  (%.1fs)"
              % (seed, no_h["peak_frontier"], no_h["runtime_s"],
                 with_h["peak_frontier"], with_h["runtime_s"],
                 peak_reduction, speedup, time.time() - t_seed0))

        rows.append(dict(seed=seed, no_hull_peak=no_h["peak_frontier"],
                         no_hull_rt=no_h["runtime_s"], with_hull_peak=with_h["peak_frontier"],
                         with_hull_rt=with_h["runtime_s"], peak_reduction_pct=peak_reduction,
                         speedup=speedup))

    print("\n=== TONG HOP ===")
    import statistics
    reds = [r["peak_reduction_pct"] for r in rows]
    speeds = [r["speedup"] for r in rows]
    print("peak_frontier reduction: mean=%.1f%% median=%.1f%% min=%.1f%% max=%.1f%%"
          % (statistics.mean(reds), statistics.median(reds), min(reds), max(reds)))
    print("runtime speedup:         mean=%.2fx median=%.2fx min=%.2fx max=%.2fx"
          % (statistics.mean(speeds), statistics.median(speeds), min(speeds), max(speeds)))

    print("\n=== Interpretation (Testb_hull_final.md Sec5) ===")
    mean_red = statistics.mean(reds)
    if mean_red >= 30.0:
        print(">= 30%% peak reduction trung binh: Implement chinh thuc vao dp_labeling.py")
    else:
        print("< 30%% peak reduction trung binh: giu Proposition Sec0 (dung, doc lap thuc "
              "nghiem) nhung dong gop T4 chu yeu dua vao Proposition + lower-bound, "
              "khong phai speedup thuc te")

    return rows


if __name__ == "__main__":
    main()
