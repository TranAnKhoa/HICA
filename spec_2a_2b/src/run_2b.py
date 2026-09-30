"""Spec 2b - phan phoi kich thuoc component tren route pool THAT do DP sinh.

Luoi da khoa: config/grid_2b.yaml (locked_at 2026-09-10T12:59:28Z).
720 lan chay = lat cat 2a {n in {30,50}, B=3, tw=120}  x  tau(6)  x
spatial_mode(2)  x  supply_ratio(3)  x  seed(10).

n_drivers = round(supply_ratio * n)   (KHAC 2a - 2a n_drivers co dinh {5,10};
khac biet co chu dich, ghi ro trong report).

Moi lan chay:
  1. sinh instance (spatial_mode, tau bien thien)
  2. DP route pool cho TUNG driver (t6_dp qua dp_labeling)
  3. build conflict graph tren TOAN BO pool (dinh nghia T5 Sec2.2)
  4. connected components -> n_components, sizes, largest_fraction, singletons

Chi giu instance co route pool day du (DP hoan tat - o day khong dat timeout
vi B=3/n<=50 da biet chay < ~10s tu probe 2a).

Ghi:
  results/2b_raw/<key>.json     1 file / lan chay
  results/2b_summary.csv        1 dong / lan chay
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
RAW = os.path.join(ROOT, "results", "2b_raw")
SUMMARY = os.path.join(ROOT, "results", "2b_summary.csv")

N_GRID = (30, 50)
B_FIXED = 3
TW_FIXED = 120
TAU_GRID = (30, 45, 60)   # [PATCH new_01] bo tau in {10,15,20}: feasibility_gate.py
#   xac nhan bat kha thi hinh hoc co he thong (feasibility_rate_k1 <25% du da
#   ap dung corridor bias + AREA_KM=8.0) - xem results/feasibility_gate_k1_by_tau.csv
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
    print("\n=== 2b DONE ===  runs=%d  elapsed=%.1fs" % (len(rows), time.time() - t_start))


if __name__ == "__main__":
    main()
