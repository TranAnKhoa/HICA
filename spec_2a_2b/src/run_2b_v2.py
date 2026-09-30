"""new03.md Viec 3.2 - lai 2b cho B_gw/B_od tach roi. KHONG nhan cheo toan bo
B_gw x B_od voi luoi tau x mode x supply (qua lon) - chon 3 to hop dai dien:
  (B_gw=3, B_od=1)   baseline nho nhat ca 2 lop
  (B_gw=3, B_od=2)   B_od tang, xem component OD co doi khong
  (B_gw=5, B_od=2)   B_gw toi da moi, kiem gia thuyet "GW cang lon cang de gop cum"

Moi to hop chay day du luoi tau(3) x spatial_mode(2) x supply_ratio(3) x
seed(10) = 180 lan/to hop x 3 = 540 lan - nho hon luoi B=3 cu (720).

Su dung compat_graph=None (PCF TAT) cho lan chay component-structure nay -
Viec 3.2 khong yeu cau do PCF, chi do cau truc component voi B tach lop MOI.
Neu can so sanh PCF-on component sau nay, chay rieng (khong lam luoi nay).
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
RAW = os.path.join(ROOT, "results", "2b_v2_raw")
SUMMARY = os.path.join(ROOT, "results", "2b_v2_summary.csv")

N_GRID = (30, 50)
TW_FIXED = 120
TAU_GRID = (30, 45, 60)
SPATIAL_GRID = ("dispersed", "clustered")
SUPPLY_GRID = (0.3, 0.6, 1.0)
SEEDS = range(10)

BGW_BOD_COMBOS = (
    (3, 1),
    (3, 2),
    (5, 2),
)

FIELDS = ["n", "B_gw", "B_od", "tw_width", "tau", "spatial_mode", "supply_ratio", "n_drivers",
          "seed", "n_edges", "n_components", "largest_component_fraction",
          "median_component_size", "n_singleton_components",
          "component_sizes", "dp_runtime_s", "total_bundles_in_pool", "status"]


def run_one(n, B_gw, B_od, tau, spatial_mode, supply_ratio, seed):
    n_drivers = max(1, int(round(supply_ratio * n)))
    key = "n%d_Bgw%d_Bod%d_tau%d_%s_sr%02d_s%d" % (
        n, B_gw, B_od, tau, spatial_mode, int(supply_ratio * 10), seed)
    gen_seed = IG.stable_seed(n, B_gw, B_od, tau, spatial_mode, supply_ratio, seed, "spec2b_v2")

    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=TW_FIXED, n_drivers=n_drivers, seed=gen_seed,
        tau=float(tau), spatial_mode=spatial_mode)

    t0 = time.time()
    pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
    dp_rt = time.time() - t0

    nodes, edges = CG.build_conflict_graph(pool_by_driver)
    stats = CG.component_stats(nodes, edges)

    rec = dict(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=TW_FIXED, tau=tau, spatial_mode=spatial_mode,
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


def _load_done():
    seen = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B_gw"]), int(r["B_od"]), float(r["tau"]),
                              r["spatial_mode"], float(r["supply_ratio"]), int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    rows = []
    total = (len(BGW_BOD_COMBOS) * len(N_GRID) * len(TAU_GRID)
             * len(SPATIAL_GRID) * len(SUPPLY_GRID) * len(SEEDS))
    done = 0
    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))

    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for B_gw, B_od in BGW_BOD_COMBOS:
            for n in N_GRID:
                for spatial_mode in SPATIAL_GRID:
                    for supply_ratio in SUPPLY_GRID:
                        for tau in TAU_GRID:
                            rec = None
                            for sd in SEEDS:
                                if (n, B_gw, B_od, float(tau), spatial_mode,
                                        float(supply_ratio), sd) in already:
                                    done += 1
                                    continue
                                rec = run_one(n, B_gw, B_od, tau, spatial_mode, supply_ratio, sd)
                                row = {k: rec[k] for k in FIELDS}
                                row["component_sizes"] = "|".join(str(x) for x in rec["component_sizes"])
                                w.writerow(row)
                                f.flush()
                                rows.append(rec)
                                done += 1
                            if rec is None:
                                continue
                            print("  [%d/%d] Bgw=%d Bod=%d n=%d %s sr=%.1f tau=%d  comps=%d  "
                                  "largest_frac=%.3f  elapsed=%.1fs"
                                  % (done, total, B_gw, B_od, n, spatial_mode, supply_ratio, tau,
                                     rec["n_components"], rec["largest_component_fraction"],
                                     time.time() - t_start))
    print("\n=== 2b v2 DONE ===  runs=%d  elapsed=%.1fs" % (len(rows), time.time() - t_start))


if __name__ == "__main__":
    main()
