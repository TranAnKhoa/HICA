"""Test3.md Viec 1 - chay lai TOAN BO Test2 (gate + Q2 + Q3), CHI OD, sau patch
neo ready_time theo tau (t2_gen.py da sua). Doi chieu feasibility_rate_k1 moi
voi bang cu (Test2_report.md Sec4: 0.8/5.1/27.4% theo tau=15/30/60).

Dung lai chinh xac logic cua t2_run.py (khong doi B_GRID/TW_WIDTH_GRID/v.v.,
chi loc DRIVER_CLASS=('OD',)) + them log feasibility_rate_k1 moi cell.
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t2_run as R
import t3_check_k1 as K1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test3")


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    gate_log = []
    small_rows = []
    k1_rows = []
    t_all = time.time()
    print("=== GATE (OD only, sau patch) ===")
    cell_id = 0
    for n in G.N_ORDERS_SMALL:
        for B in G.B_GRID:
            if B > n:
                continue
            cls = "OD"
            for tw in G.TW_WIDTH_GRID:
                for tau in G.TAU_GRID:
                    n_pass_complete = n_pass_valid = n_pass_filter = 0
                    n_mono_viol_total = 0
                    n_seeds_run = 0
                    k1_rates = []
                    for sd in range(G.SEEDS_PER_CELL):
                        rng = random.Random(R.seed_from(n, B, cls, tw, tau, sd, 20260907, "t3patch"))
                        try:
                            driver, orders, tt, meta = G.build_instance(rng, R.SESSION, n, cls, tw, tau, B)
                        except SystemExit as e:
                            print("  [skip] %s" % e)
                            continue
                        rate, ok = K1.check_and_warn(driver, orders, tt,
                            label="n=%d B=%d tw=%d tau=%s seed=%d" % (n, B, tw, tau, sd))
                        k1_rates.append(rate)
                        k1_rows.append(dict(n=n, B=B, tw_width=tw, tau=tau, seed=sd, feasibility_rate_k1=rate))
                        if not ok:
                            continue   # bo qua cell nay khoi gate/Q2 (spec: "khong chay tiep cell do")

                        bf, bf_stats = C.brute_force(tt, driver, orders, B)
                        seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(
                            tt, driver, orders, B, use_filter=True)

                        n_seeds_run += 1
                        completeness_ok = True
                        for S in bf:
                            bf_set = set(x[0] for x in bf[S])
                            bfs_set = set(x[0] for x in seq.get(S, []))
                            if bf_set != bfs_set:
                                completeness_ok = False
                                break
                        validator_ok = True
                        for S, entries in seq.items():
                            for canon, slack, walk in entries:
                                ok2, errs = C.validate(tt, driver, walk)
                                if not ok2:
                                    validator_ok = False
                        filter_no_wrong_prune = all(len(bf[S]) == 0 for S in pruned)
                        mono_violations = []
                        keys = list(bf.keys())
                        for S in keys:
                            for Sp in keys:
                                if S != Sp and S.issubset(Sp):
                                    ss_S = max((x[1] for x in bf[S]), default=float("-inf"))
                                    ss_Sp = max((x[1] for x in bf[Sp]), default=float("-inf"))
                                    if ss_Sp > ss_S + 1e-9:
                                        mono_violations.append((sorted(S), sorted(Sp)))

                        n_pass_complete += int(completeness_ok)
                        n_pass_valid += int(validator_ok)
                        n_pass_filter += int(filter_no_wrong_prune)
                        n_mono_viol_total += len(mono_violations)

                        for S in bf:
                            k = len(S)
                            small_rows.append(dict(
                                instance_id="t3_n%d_B%d_OD_tw%d_tau%s_seed%d" % (n, B, tw, tau, sd),
                                seed=sd, n_orders=n, B=B, driver_class="OD", tw_width=tw, tau=tau,
                                subset_id="|".join(sorted(S)), k=k,
                                n_feasible_sequences=len(seq.get(S, [])),
                                n_insertion_attempts=ins_by_S.get(S, 0),
                                n_permutations_bruteforce=bf_stats[S],
                                was_pruned_by_filter=(S in pruned),
                                slack_star=sstar.get(S),
                                walltime_bfs_ms=None, walltime_bruteforce_ms=None,
                            ))
                        if not completeness_ok:
                            print("  COMPLETENESS FAIL n=%d B=%d tw=%d tau=%s seed=%d" % (n, B, tw, tau, sd))
                        if mono_violations:
                            print("  MONOTONICITY COUNTEREXAMPLE n=%d B=%d tw=%d tau=%s seed=%d :: %s"
                                  % (n, B, tw, tau, sd, mono_violations[:2]))

                    gate_log.append(dict(
                        n=n, B=B, cls=cls, tw=tw, tau=tau, n_seeds=n_seeds_run,
                        n_seeds_skipped_low_k1=G.SEEDS_PER_CELL - len(k1_rates) if False else (len(k1_rates) - n_seeds_run),
                        completeness_pass=n_pass_complete, validator_pass=n_pass_valid,
                        filter_pass=n_pass_filter, mono_violations=n_mono_viol_total,
                        mean_feasibility_rate_k1=(sum(k1_rates) / len(k1_rates)) if k1_rates else None))
                    cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs)" % (n, cell_id, time.time() - t_all))

    with open(os.path.join(OUT, "od_patched_gate_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gate_log[0].keys()))
        w.writeheader()
        w.writerows(gate_log)
    with open(os.path.join(OUT, "od_patched_small_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=R.FIELDS)
        w.writeheader()
        w.writerows(small_rows)
    with open(os.path.join(OUT, "od_patched_k1_rates.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "tau", "seed", "feasibility_rate_k1"])
        w.writeheader()
        w.writerows(k1_rows)

    total_fail = sum(1 for g in gate_log if g["completeness_pass"] < g["n_seeds"])
    total_mono = sum(g["mono_violations"] for g in gate_log)
    total_filter_fail = sum(1 for g in gate_log if g["filter_pass"] < g["n_seeds"])
    total_valid_fail = sum(1 for g in gate_log if g["validator_pass"] < g["n_seeds"])
    print("\nGATE SUMMARY (OD, patched): cells=%d  completeness_fail_cells=%d  validator_fail_cells=%d  "
          "filter_wrongprune_cells=%d  monotonicity_counterexamples=%d"
          % (len(gate_log), total_fail, total_valid_fail, total_filter_fail, total_mono))

    if total_fail > 0:
        print("\n*** DUNG: completeness gate FAIL sau patch. Khong chay tiep Q2/Q3. ***")
        return 1

    print("\n=== Q2/Q3 (OD only, big grid, patched) ===")
    big_rows = []
    t_big0 = time.time()
    n_cells_big = 0
    k1_big_rows = []
    for n in G.N_ORDERS_BIG:
        for B in G.B_GRID:
            cls = "OD"
            for tw in G.TW_WIDTH_GRID:
                for tau in G.TAU_GRID:
                    for sd in range(G.SEEDS_PER_CELL):
                        rng = random.Random(R.seed_from(n, B, cls, tw, tau, sd, 20260907, "big", "t3patch"))
                        try:
                            driver, orders, tt, meta = G.build_instance(rng, R.SESSION, n, cls, tw, tau, B)
                        except SystemExit as e:
                            print("  [skip] %s" % e)
                            continue
                        rate, ok = K1.check_and_warn(driver, orders, tt,
                            label="[big] n=%d B=%d tw=%d tau=%s seed=%d" % (n, B, tw, tau, sd))
                        k1_big_rows.append(dict(n=n, B=B, tw_width=tw, tau=tau, seed=sd, feasibility_rate_k1=rate))
                        if not ok:
                            continue

                        seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(
                            tt, driver, orders, B, use_filter=True)
                        for S, entries in seq.items():
                            k = len(S)
                            n_perm_bf = 1
                            for i in range(2 * k, 0, -1):
                                n_perm_bf *= i
                            big_rows.append(dict(
                                instance_id="t3_n%d_B%d_OD_tw%d_tau%s_seed%d" % (n, B, tw, tau, sd),
                                seed=sd, n_orders=n, B=B, driver_class="OD", tw_width=tw, tau=tau,
                                subset_id="|".join(sorted(S)), k=k,
                                n_feasible_sequences=len(entries),
                                n_insertion_attempts=ins_by_S.get(S, 0),
                                n_permutations_bruteforce=n_perm_bf,
                                was_pruned_by_filter=(S in pruned),
                                slack_star=sstar.get(S),
                                walltime_bfs_ms=None, walltime_bruteforce_ms=None,
                            ))
                    n_cells_big += 1
        print("  n_orders=%d done (%d cells, %.1fs)" % (n, n_cells_big, time.time() - t_big0))

    with open(os.path.join(OUT, "od_patched_big_raw.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=R.FIELDS)
        w.writeheader()
        w.writerows(big_rows)
    with open(os.path.join(OUT, "od_patched_k1_rates_big.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "tau", "seed", "feasibility_rate_k1"])
        w.writeheader()
        w.writerows(k1_big_rows)

    print("\nTONG (OD patched): %d gate rows, %d Q2 rows, %.1fs"
          % (len(small_rows), len(big_rows), time.time() - t_all))
    return 0


if __name__ == "__main__":
    sys.exit(main())
