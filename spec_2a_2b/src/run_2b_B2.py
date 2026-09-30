"""Spec2a,2b_addition_1.md - Viec 2: chay lai DUNG NGUYEN luoi 2b da khoa,
CHI doi B: 3 -> 2. Khong doi bat ky tham so nao khac (khong dung chung file
voi run_2b.py de khong lam nham lan / ghi de du lieu B=3 goc - tach RAW/
SUMMARY rieng, MOI THU KHAC (instance_gen, dp_labeling, conflict_graph,
cong thuc component_stats) dung y het run_2b.py).

Luoi: n in {30,50} x tau(6) x spatial_mode(2) x supply_ratio(3) x seed(10)
    = 720 lan chay. B=2 theo probe_scaling.csv chay duoi 1s/driver ngay ca
o n=100 -> chay DU 720, khong rut gon do phu nhu ban B=3 goc.
"""

import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import conflict_graph as CG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "2b_B2_raw")
SUMMARY = os.path.join(ROOT, "results", "2b_B2_summary.csv")

N_GRID = (30, 50)
B_FIXED = 2                # <-- DUY NHAT thay doi so voi run_2b.py
TW_FIXED = 120
TAU_GRID = (30, 45, 60)   # [PATCH new_01] dong bo voi run_2b.py - xem ly do o do
SPATIAL_GRID = ("dispersed", "clustered")
SUPPLY_GRID = (0.3, 0.6, 1.0)
SEEDS = range(10)

FIELDS = ["n", "B", "tw_width", "tau", "spatial_mode", "supply_ratio", "n_drivers",
          "seed", "n_edges", "n_components", "largest_component_fraction",
          "median_component_size", "n_singleton_components",
          "component_sizes", "dp_runtime_s", "total_bundles_in_pool", "status"]


def run_one(n, tau, spatial_mode, supply_ratio, seed):
    n_drivers = max(1, int(round(supply_ratio * n)))
    key = "n%d_tau%d_%s_sr%02d_s%d" % (n, tau, spatial_mode, int(supply_ratio * 10), seed)
    gen_seed = IG.stable_seed(n, tau, spatial_mode, supply_ratio, seed, "spec2b")
    # gen_seed CO Y giong het run_2b.py (cung tag "spec2b", KHONG doi) de
    # instance sinh ra CHI khac o B - moi thu khac (toa do, TW, driver) giu
    # nguyen giua ban B=2 va B=3, cho phep so sanh cong bang tung cap instance.

    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B=B_FIXED, tw_width=TW_FIXED, n_drivers=n_drivers, seed=gen_seed,
        tau=float(tau), spatial_mode=spatial_mode)

    t0 = time.time()
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_FIXED)
    dp_rt = time.time() - t0

    nodes, edges = CG.build_conflict_graph(pool_by_driver)
    stats = CG.component_stats(nodes, edges)

    rec = dict(
        n=n, B=B_FIXED, tw_width=TW_FIXED, tau=tau, spatial_mode=spatial_mode,
        supply_ratio=supply_ratio, n_drivers=n_drivers, seed=seed,
        n_edges=len(edges),
        n_components=stats["n_components"],
        largest_component_fraction=round(stats["largest_component_fraction"], 6),
        median_component_size=stats["median_component_size"],
        n_singleton_components=stats["n_singleton_components"],
        component_sizes=stats["component_sizes"],
        dp_runtime_s=round(dp_rt, 4),
        total_bundles_in_pool=agg["n_bundles_total"],
        status="completed",
    )
    with open(os.path.join(RAW, key + ".json"), "w", encoding="utf-8") as f:
        json.dump({"record": rec, "meta": meta,
                   "pool_sizes_by_driver": {d: len(p) for d, p in pool_by_driver.items()}},
                  f, indent=1)
    return rec


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    rows = []
    total = len(N_GRID) * len(TAU_GRID) * len(SPATIAL_GRID) * len(SUPPLY_GRID) * len(SEEDS)
    done = 0
    already = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    already.add((int(r["n"]), float(r["tau"]), r["spatial_mode"],
                                 float(r["supply_ratio"]), int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))

    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for n in N_GRID:
            for spatial_mode in SPATIAL_GRID:
                for supply_ratio in SUPPLY_GRID:
                    for tau in TAU_GRID:
                        rec = None
                        for sd in SEEDS:
                            if (n, float(tau), spatial_mode, float(supply_ratio), sd) in already:
                                done += 1
                                continue
                            rec = run_one(n, tau, spatial_mode, supply_ratio, sd)
                            row = {k: rec[k] for k in FIELDS}
                            row["component_sizes"] = "|".join(str(x) for x in rec["component_sizes"])
                            w.writerow(row)
                            f.flush()
                            rows.append(rec)
                            done += 1
                        if rec is None:
                            continue
                        print("  [%d/%d] n=%d %s sr=%.1f tau=%d  comps=%d  largest_frac=%.3f  sing3=%d  elapsed=%.1fs"
                              % (done, total, n, spatial_mode, supply_ratio, tau,
                                 rec["n_components"], rec["largest_component_fraction"],
                                 rec["n_singleton_components"], time.time() - t_start))
    print("\n=== 2b-B2 DONE ===  runs=%d  elapsed=%.1fs" % (len(rows), time.time() - t_start))


if __name__ == "__main__":
    main()
