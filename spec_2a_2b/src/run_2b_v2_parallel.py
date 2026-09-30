"""Ban song song cua run_2b_v2.py - CHI danh cho phan con lai (Bgw/Bod combos
chua chay xong trong 2b_v2_summary.csv). Logic sinh du lieu/tinh toan giu
NGUYEN VEN tu run_2b_v2.py (goi lai run_one qua import) - chi doi cach dispatch
tu tuan tu sang ProcessPoolExecutor.

Moi (n,Bgw,Bod,tau,mode,supply,seed) la mot don vi cong viec DOC LAP hoan toan
(khong CPLEX, khong shared state) - an toan chay song song. Ghi CSV van xay ra
TUAN TU o process chinh (khong co race) - script resume-safe giong ban goc,
dua tren cung file summary/raw.

Chay: python -u run_2b_v2_parallel.py [n_workers]
"""

import csv
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_2b_v2 import (RAW, SUMMARY, N_GRID, TAU_GRID, SPATIAL_GRID, SUPPLY_GRID,
                        SEEDS, BGW_BOD_COMBOS, FIELDS, run_one, _load_done)


def _task(args):
    n, B_gw, B_od, tau, spatial_mode, supply_ratio, sd = args
    rec = run_one(n, B_gw, B_od, tau, spatial_mode, supply_ratio, sd)
    return args, rec


def main():
    n_workers = int(sys.argv[1]) if len(sys.argv) > 1 else max(1, os.cpu_count() - 1)
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    total = (len(BGW_BOD_COMBOS) * len(N_GRID) * len(TAU_GRID)
             * len(SPATIAL_GRID) * len(SUPPLY_GRID) * len(SEEDS))
    already = _load_done()
    print("RESUME: %d rows already in summary, skipping those. workers=%d" % (len(already), n_workers))

    pending = []
    for B_gw, B_od in BGW_BOD_COMBOS:
        for n in N_GRID:
            for spatial_mode in SPATIAL_GRID:
                for supply_ratio in SUPPLY_GRID:
                    for tau in TAU_GRID:
                        for sd in SEEDS:
                            key = (n, B_gw, B_od, float(tau), spatial_mode, float(supply_ratio), sd)
                            if key in already:
                                continue
                            pending.append((n, B_gw, B_od, tau, spatial_mode, supply_ratio, sd))

    done = len(already)
    if not pending:
        print("\n=== 2b v2 DONE (nothing pending) ===  runs=%d  elapsed=%.1fs" % (done, time.time() - t_start))
        return

    mode = "a" if already else "w"
    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()

        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futs = {ex.submit(_task, args): args for args in pending}
            for fut in as_completed(futs):
                args, rec = fut.result()
                row = {k: rec[k] for k in FIELDS}
                row["component_sizes"] = "|".join(str(x) for x in rec["component_sizes"])
                w.writerow(row)
                f.flush()
                done += 1
                n, B_gw, B_od, tau, spatial_mode, supply_ratio, sd = args
                print("  [%d/%d] Bgw=%d Bod=%d n=%d %s sr=%.1f tau=%d seed=%d  comps=%d  "
                      "largest_frac=%.3f  elapsed=%.1fs"
                      % (done, total, B_gw, B_od, n, spatial_mode, supply_ratio, tau, sd,
                         rec["n_components"], rec["largest_component_fraction"],
                         time.time() - t_start))

    print("\n=== 2b v2 DONE ===  runs=%d  elapsed=%.1fs" % (done, time.time() - t_start))


if __name__ == "__main__":
    main()
