"""new03.md Viec 3.1 Buoc A - xac nhan B_od KHONG tao bung no (re, lam truoc
Buoc B). B_gw CO DINH = 2 (baseline re nhat). Neu runtime OD-side phang nhu
B=2 cu, khong co gi bat ngo - xac nhan gia thuyet Viec 1.1 bang du lieu.

Luoi: n in {10,30,50,75,100} x B_od in {1,2} x tw in {30,60,120,240} x
seed in {0..4}. B_gw = 2 co dinh, n_drivers = 10 co dinh (khong quet ndrv o
buoc nay - chi de kiem B_od, khong phai scaling day du).
"""

import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "2a_stepA_raw")
SUMMARY = os.path.join(ROOT, "results", "2a_stepA_summary.csv")

N_GRID = (10, 30, 50, 75, 100)
BOD_GRID = (1, 2)
BGW_FIXED = 2
TW_GRID = (30, 60, 120, 240)
NDRV_FIXED = 10
SEEDS = range(5)
TAU = 20.0
SPATIAL = "dispersed"
TIMEOUT_S = 300.0

FIELDS = ["n", "B_gw", "B_od", "tw_width", "n_drivers", "seed",
          "runtime_seconds", "peak_frontier_size", "total_states_generated",
          "total_states_surviving", "n_complete_bundles_found", "status"]


def run_one(n, B_od, tw, seed):
    key = "n%d_Bod%d_tw%d_s%d" % (n, B_od, tw, seed)
    gen_seed = IG.stable_seed(n, BGW_FIXED, B_od, tw, NDRV_FIXED, seed, "spec2a_stepA")

    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=BGW_FIXED, B_od=B_od, tw_width=tw, n_drivers=NDRV_FIXED,
        seed=gen_seed, tau=TAU, spatial_mode=SPATIAL)

    t0 = time.time()
    n_generated = n_surviving = peak_frontier = n_bundles_total = 0
    status = "completed"
    od_drivers = [d for d in drivers if d["cls"] == "OD"]
    for drv in od_drivers:
        if time.time() - t0 > TIMEOUT_S:
            status = "timeout"
            break
        r = DL.run_pool(tt, drv, orders, BGW_FIXED, B_od)
        n_generated += r["n_generated"]
        n_surviving += r["n_surviving"]
        peak_frontier = max(peak_frontier, r["peak_frontier"])
        n_bundles_total += r["n_bundles"]

    runtime = time.time() - t0
    rec = dict(
        n=n, B_gw=BGW_FIXED, B_od=B_od, tw_width=tw, n_drivers=NDRV_FIXED, seed=seed,
        runtime_seconds=round(runtime, 4),
        peak_frontier_size=peak_frontier,
        total_states_generated=n_generated,
        total_states_surviving=n_surviving,
        n_complete_bundles_found=n_bundles_total,
        status=status,
    )
    with open(os.path.join(RAW, key + ".json"), "w", encoding="utf-8") as f:
        json.dump({"record": rec}, f, indent=1)
    return rec


def _load_done():
    seen = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B_od"]), int(r["tw_width"]), int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    total = len(N_GRID) * len(BOD_GRID) * len(TW_GRID) * len(SEEDS)
    done = 0

    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))

    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for n in N_GRID:
            for B_od in BOD_GRID:
                for tw in TW_GRID:
                    for sd in SEEDS:
                        if (n, B_od, tw, sd) in already:
                            done += 1
                            continue
                        rec = run_one(n, B_od, tw, sd)
                        w.writerow(rec)
                        f.flush()
                        done += 1
                    print("  [%d/%d] n=%d B_od=%d tw=%d  elapsed=%.1fs"
                          % (done, total, n, B_od, tw, time.time() - t_start))
    print("\n=== 2a STEP A DONE ===  elapsed=%.1fs" % (time.time() - t_start))


if __name__ == "__main__":
    main()
