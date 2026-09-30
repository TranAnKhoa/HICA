"""T4 diagnostic experiment - runner (spec Guideline/Test1.md, muc 3).

Voi moi instance, moi driver:
  1. loc size-1, 2. sinh size-2 tu survivors, size-3 tu size-2 da pass,
  3. ghi lai bound / prune / ground truth / thoi gian cho moi subset k>=2.
LUON chay DFS ke ca khi da bi can cat (can ground truth de do).
Soundness gate: assert NOT (prune AND feasible) -> fail la DUNG NGAY.
"""

import csv
import itertools
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_core as C

OUT_DIR = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "T4")
RAW_CSV = os.path.join(OUT_DIR, "T4_raw.csv")
META_JSON = os.path.join(OUT_DIR, "T4_meta.json")
INSTANCE_TIME_LIMIT = 60.0      # spec 7: instance > 60s -> log va bo qua

FIELDS = ["n_orders", "tw", "seed", "driver", "k", "orders",
          "mst_bound", "one_tree_bound", "budget",
          "prune_mst", "prune_1tree", "feasible",
          "dfs_time_s", "mst_time_s", "one_tree_time_s"]


def run():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    violations = []          # soundness gate
    skipped = []             # instance vuot 60s
    t_start = time.time()
    n_rows = 0

    fh = open(RAW_CSV, "w", newline="", encoding="utf-8")
    w = csv.writer(fh)
    w.writerow(FIELDS)

    for n in C.N_ORDERS_GRID:
        for tw in ("TIGHT", "MEDIUM", "LOOSE"):
            cell_t0 = time.time()
            cell_rows = 0
            for seed in range(C.N_SEEDS):
                inst = C.Instance(n, tw, seed)
                inst_t0 = time.perf_counter()
                timed_out = False
                buf = []

                for d in range(inst.m):
                    if time.perf_counter() - inst_t0 > INSTANCE_TIME_LIMIT:
                        timed_out = True
                        break

                    # --- buoc 0: loc size-1 -------------------------------
                    survivors = [o for o in range(inst.n) if C.is_feasible(inst, d, [o])]

                    # --- size 2 -------------------------------------------
                    feasible_pairs = []
                    for S in itertools.combinations(survivors, 2):
                        S = list(S)
                        row, feas = measure(inst, d, S, violations)
                        buf.append(row)
                        if feas:
                            feasible_pairs.append(S)

                    # --- size 3: chi mo rong tu size-2 da pass ------------
                    seen3 = set()
                    for S2 in feasible_pairs:
                        for o in survivors:
                            if o in S2:
                                continue
                            S3 = tuple(sorted(S2 + [o]))
                            if S3 in seen3:
                                continue
                            seen3.add(S3)
                            row, _ = measure(inst, d, list(S3), violations)
                            buf.append(row)

                    if violations:
                        fh.close()
                        report_violation(violations)
                        return 1

                if timed_out:
                    skipped.append({"n_orders": n, "tw": tw, "seed": seed,
                                    "elapsed_s": time.perf_counter() - inst_t0})
                    continue

                w.writerows(buf)
                n_rows += len(buf)
                cell_rows += len(buf)

            print("  n=%-3d %-7s  rows=%-8d  %.1fs" %
                  (n, tw, cell_rows, time.time() - cell_t0))
            sys.stdout.flush()

    fh.close()

    meta = {
        "spec": "Guideline/Test1.md",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_orders_grid": C.N_ORDERS_GRID,
        "tw_grid": C.TW_GRID,
        "n_seeds": C.N_SEEDS,
        "bundle_cap": C.BUNDLE_CAP,
        "driver_capacity": C.DRIVER_CAPACITY,
        "available_until": C.AVAILABLE_UNTIL,
        "map_km": C.MAP_KM,
        "speed_kmh": C.SPEED_KMH,
        "n_instances": len(C.N_ORDERS_GRID) * 3 * C.N_SEEDS,
        "n_subset_rows": n_rows,
        "soundness_violations": len(violations),
        "instances_skipped_timeout": skipped,
        "instance_time_limit_s": INSTANCE_TIME_LIMIT,
        "wall_clock_s": time.time() - t_start,
        "seeding": "geometry+release RNG = f(n, seed); slack RNG = f(n, seed) "
                   "-> 3 cau hinh TW dung chung ban do (paired comparison)",
    }
    with open(META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("\nTONG: %d subset rows, %.1fs, soundness violations = %d, skipped = %d"
          % (n_rows, meta["wall_clock_s"], len(violations), len(skipped)))
    return 0


def measure(inst, d, S, violations):
    t0 = time.perf_counter()
    mb = C.mst_bound(inst, d, S)
    t1 = time.perf_counter()
    ob = C.one_tree_bound(inst, d, S)
    t2 = time.perf_counter()
    bud = C.budget(inst, S)
    p_mst = mb > bud
    p_1t = ob > bud
    t3 = time.perf_counter()
    feas = C.is_feasible(inst, d, S)
    t4 = time.perf_counter()

    # ---- 2.5 SOUNDNESS GATE ----
    if feas and (p_mst or p_1t):
        violations.append({"n": inst.n, "tw": inst.tw, "seed": inst.seed,
                           "driver": d, "S": S, "mst": mb, "one_tree": ob,
                           "budget": bud, "prune_mst": p_mst, "prune_1tree": p_1t})

    row = [inst.n, inst.tw, inst.seed, d, len(S), "|".join(str(o) for o in S),
           "%.6f" % mb, "%.6f" % ob, "%.6f" % bud,
           int(p_mst), int(p_1t), int(feas),
           "%.9f" % (t4 - t3), "%.9f" % (t1 - t0), "%.9f" % (t2 - t1)]
    return row, feas


def report_violation(violations):
    print("\n" + "!" * 70)
    print("SOUNDNESS GATE FAIL - can KHONG sound. DUNG NGAY (spec 2.5).")
    for v in violations[:10]:
        print(json.dumps(v))
    print("!" * 70)


if __name__ == "__main__":
    sys.exit(run())
