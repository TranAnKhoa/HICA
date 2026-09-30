"""Test6.md Viec 2 - CHI chay neu Viec1 (Gate1.A/B/C + Sec2.3) pass tuyet doi.
Do state space that: n_states_visited (created) vs n_states_survived (sau
dominance) vs n_feasible_sequences (Test2's blowup, ~2520 o k=4/tw=240).

3 o trong tam giong Test4/Test5: GW, B=4, k=3-4 (o day do CA INSTANCE, khong
tach theo k - DP sinh dong thoi moi |C| tu 1..B trong 1 lan chay), tw in
{120,240}.

DUNG: Output/Test6/viec2_state_space.csv
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t6_dp as D
import t6_run_gate1 as G1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")

B_FIXED = 4
TW_TARGET = (120, 240)
N_ORDERS_SMALL = (4, 5, 6)   # can n>=B=4
SEEDS_PER_CELL = G.SEEDS_PER_CELL


def run_cell(rng, n, tw, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, G1.SESSION, n, "GW", tw, None, B_FIXED)

    t0 = time.perf_counter()
    dp_result = D.run_dp(tt, driver, orders, B_FIXED, use_dominance=True)
    t_dp = time.perf_counter() - t0

    # so sanh voi Test2's Seq(S) full (n_feasible_sequences tong qua moi S)
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B_FIXED, use_filter=True)
    n_feasible_seq_total = sum(len(v) for v in seq.values())

    return dict(
        n=n, B=B_FIXED, tw_width=tw, seed=seed_idx,
        n_states_created=dp_result["n_labels_created"],
        n_states_survived=dp_result["n_labels_survived"],
        n_complete_bundles=sum(len(v) for v in dp_result["complete_by_C"].values()),
        n_feasible_seq_total=n_feasible_seq_total,
        t_dp_s=t_dp,
    )


FIELDS = ["n", "B", "tw_width", "seed", "n_states_created", "n_states_survived",
          "n_complete_bundles", "n_feasible_seq_total", "t_dp_s"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    t0 = time.time()
    for tw in TW_TARGET:
        for n in N_ORDERS_SMALL:
            for sd in range(SEEDS_PER_CELL):
                rng = random.Random(G1.seed_from(n, B_FIXED, "GW", tw, None, sd, "t6viec2"))
                try:
                    row = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                rows.append(row)
        print("  tw=%d done, %.1fs, rows=%d" % (tw, time.time() - t0, len(rows)))

    with open(os.path.join(OUT, "viec2_state_space.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print("\n=== VIEC2 SUMMARY (n=6, tw=240, worst) ===")
    worst = [r for r in rows if r["n"] == 6 and r["tw_width"] == 240]
    if worst:
        avg_created = sum(r["n_states_created"] for r in worst) / len(worst)
        avg_survived = sum(r["n_states_survived"] for r in worst) / len(worst)
        avg_seq = sum(r["n_feasible_seq_total"] for r in worst) / len(worst)
        print("avg n_states_created=%.1f, n_states_survived=%.1f, n_feasible_seq_total=%.1f"
              % (avg_created, avg_survived, avg_seq))
        print("compression (survived/seq_total): %.4f" % (avg_survived / avg_seq if avg_seq else 0))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
