"""Test2.md - chay toan bo grid, log CSV (Sec6), gate (Sec4).

    python -m experiments.T2BFS.t2_run
"""

import csv
import hashlib
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test2")
SESSION = 3   # 1 session that dai dien - xem ghi chu Deviations trong report


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def run_small_gate_cell(rng, n, B, cls, tw, tau, seed_idx):
    """Mot instance nho: chay brute force + BFS, tra ket qua gate."""
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    t0 = time.perf_counter()
    bf, bf_stats = C.brute_force(tt, driver, orders, B)
    t_bf = time.perf_counter() - t0

    t0 = time.perf_counter()
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(
        tt, driver, orders, B, use_filter=True)
    t_bfs = time.perf_counter() - t0

    completeness_ok = True
    mismatch_detail = None
    for S in bf:
        bf_set = set(x[0] for x in bf[S])
        bfs_set = set(x[0] for x in seq.get(S, []))
        if bf_set != bfs_set:
            completeness_ok = False
            mismatch_detail = (sorted(S), sorted(bf_set - bfs_set), sorted(bfs_set - bf_set))
            break

    validator_ok = True
    for S, entries in seq.items():
        for canon, slack, walk in entries:
            ok, errs = C.validate(tt, driver, walk)
            if not ok:
                validator_ok = False

    filter_no_wrong_prune = all(len(bf[S]) == 0 for S in pruned)

    # gate 4.3: phan chung monotonicity, tren GROUND TRUTH brute force (khong
    # phu thuoc BFS/filter co dung hay khong)
    mono_violations = []
    keys = list(bf.keys())
    for S in keys:
        for Sp in keys:
            if S != Sp and S.issubset(Sp):
                ss_S = max((x[1] for x in bf[S]), default=float("-inf"))
                ss_Sp = max((x[1] for x in bf[Sp]), default=float("-inf"))
                if ss_Sp > ss_S + 1e-9:
                    mono_violations.append((sorted(S), sorted(Sp), ss_S, ss_Sp))

    rows = []
    for S in bf:
        k = len(S)
        n_perm_bf = bf_stats[S]
        rows.append(dict(
            instance_id="s%d_n%d_B%d_%s_tw%d_tau%s_seed%d" % (SESSION, n, B, cls, tw, tau, seed_idx),
            seed=seed_idx, n_orders=n, B=B, driver_class=cls, tw_width=tw, tau=tau,
            subset_id="|".join(sorted(S)), k=k,
            n_feasible_sequences=len(seq.get(S, [])),
            n_insertion_attempts=ins_by_S.get(S, 0),
            n_permutations_bruteforce=n_perm_bf,
            was_pruned_by_filter=(S in pruned),
            slack_star=sstar.get(S),
            walltime_bfs_ms=None, walltime_bruteforce_ms=None,
        ))
    return dict(rows=rows, completeness_ok=completeness_ok, mismatch=mismatch_detail,
               validator_ok=validator_ok, filter_ok=filter_no_wrong_prune,
               mono_violations=mono_violations, t_bf=t_bf, t_bfs=t_bfs,
               prune_cnt=prune_cnt, ins_att=ins_att, n_subsets=len(bf))


def run_big_cell(rng, n, B, cls, tw, tau, seed_idx):
    """Instance lon: CHI BFS (khong brute force), do Q2."""
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    t0 = time.perf_counter()
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(
        tt, driver, orders, B, use_filter=True)
    t_bfs = time.perf_counter() - t0

    rows = []
    for S, entries in seq.items():
        k = len(S)
        n_perm_bf = 1
        for i in range(2 * k, 0, -1):
            n_perm_bf *= i
        rows.append(dict(
            instance_id="s%d_n%d_B%d_%s_tw%d_tau%s_seed%d" % (SESSION, n, B, cls, tw, tau, seed_idx),
            seed=seed_idx, n_orders=n, B=B, driver_class=cls, tw_width=tw, tau=tau,
            subset_id="|".join(sorted(S)), k=k,
            n_feasible_sequences=len(entries),
            n_insertion_attempts=ins_by_S.get(S, 0),
            n_permutations_bruteforce=n_perm_bf,
            was_pruned_by_filter=(S in pruned),
            slack_star=sstar.get(S),
            walltime_bfs_ms=t_bfs * 1000.0, walltime_bruteforce_ms=None,
        ))
    return rows, t_bfs, prune_cnt, ins_att, len(seq)


FIELDS = ["instance_id", "seed", "n_orders", "B", "driver_class", "tw_width", "tau",
          "subset_id", "k", "n_feasible_sequences", "n_insertion_attempts",
          "n_permutations_bruteforce", "was_pruned_by_filter", "slack_star",
          "walltime_bfs_ms", "walltime_bruteforce_ms"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    gate_log = []
    small_rows = []
    t_all = time.time()
    print("=== GATE (n_orders_small, brute force + BFS) ===")
    cell_id = 0
    for n in G.N_ORDERS_SMALL:
        for B in G.B_GRID:
            if B > n:
                continue
            for cls in G.DRIVER_CLASS:
                for tw in G.TW_WIDTH_GRID:
                    taus = G.TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        n_pass_complete = n_pass_valid = n_pass_filter = 0
                        n_mono_viol_total = 0
                        n_seeds_run = 0
                        for sd in range(G.SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, 20260907))
                            try:
                                res = run_small_gate_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            n_seeds_run += 1
                            small_rows.extend(res["rows"])
                            n_pass_complete += int(res["completeness_ok"])
                            n_pass_valid += int(res["validator_ok"])
                            n_pass_filter += int(res["filter_ok"])
                            n_mono_viol_total += len(res["mono_violations"])
                            if not res["completeness_ok"]:
                                print("  COMPLETENESS FAIL n=%d B=%d %s tw=%d tau=%s seed=%d :: %s"
                                     % (n, B, cls, tw, tau, sd, res["mismatch"]))
                            if res["mono_violations"]:
                                print("  MONOTONICITY COUNTEREXAMPLE n=%d B=%d %s tw=%d tau=%s seed=%d :: %s"
                                     % (n, B, cls, tw, tau, sd, res["mono_violations"][:2]))
                        gate_log.append(dict(
                            n=n, B=B, cls=cls, tw=tw, tau=tau, n_seeds=n_seeds_run,
                            completeness_pass=n_pass_complete, validator_pass=n_pass_valid,
                            filter_pass=n_pass_filter, mono_violations=n_mono_viol_total))
                        cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs)" % (n, cell_id, time.time() - t_all))

    with open(os.path.join(OUT, "gate_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gate_log[0].keys()))
        w.writeheader()
        w.writerows(gate_log)

    with open(os.path.join(OUT, "small_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(small_rows)

    total_fail = sum(1 for g in gate_log if g["completeness_pass"] < g["n_seeds"])
    total_mono = sum(g["mono_violations"] for g in gate_log)
    total_filter_fail = sum(1 for g in gate_log if g["filter_pass"] < g["n_seeds"])
    total_valid_fail = sum(1 for g in gate_log if g["validator_pass"] < g["n_seeds"])
    print("\nGATE SUMMARY: cells=%d  completeness_fail_cells=%d  validator_fail_cells=%d  "
         "filter_wrongprune_cells=%d  monotonicity_counterexamples=%d"
         % (len(gate_log), total_fail, total_valid_fail, total_filter_fail, total_mono))

    if total_fail > 0:
        print("\n*** DUNG: completeness gate FAIL. Xem chi tiet o tren, khong chay tiep Q2/Q3. ***")
        return 1

    print("\n=== Q2/Q3 (n_orders_big, chi BFS) ===")
    big_rows = []
    t_big0 = time.time()
    n_cells_big = 0
    for n in G.N_ORDERS_BIG:
        for B in G.B_GRID:
            for cls in G.DRIVER_CLASS:
                for tw in G.TW_WIDTH_GRID:
                    taus = G.TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(G.SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, 20260907, "big"))
                            try:
                                rows, t_bfs, prune_cnt, ins_att, n_sub = run_big_cell(
                                    rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            big_rows.extend(rows)
                        n_cells_big += 1
        print("  n_orders=%d done (%d cells, %.1fs)" % (n, n_cells_big, time.time() - t_big0))

    with open(os.path.join(OUT, "big_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(big_rows)

    print("\nTONG: %d gate rows, %d Q2 rows, %.1fs" % (len(small_rows), len(big_rows), time.time() - t_all))
    return 0


if __name__ == "__main__":
    sys.exit(main())
