"""Test4.1 - doi chung Sec5.4 tai n=10 (thay vi chi n<=6 nhu bao cao Test4
goc). Cau hoi: activation_rate co con >=10% khi m=|Rem(S)| lon hon that (gan
voi quy mo n=10-50 du kien cua main experiment) hay khong - hay no chi cao
vi pool nho (n<=6) it order de "phan biet"?

Dung LAI logic cua t4_run_viec54.py (run_cell, LB_greedy, UB_of) - CHI doi
N_ORDERS = (10,) thay vi (4,5,6), va CHI 1 gia tri n (khong phai ca 4 gia
tri {8,10,12,15} nhu Viec 2 spec goc - qua ton kem, xem Test4_report.md
Sec0.2). GW, B=4, k=2, tw_width in {120,240}, 8 seed - dung grid.

DUNG: Output/Test4/activation_rate_n10.csv
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_run_viec54 as R54

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")

N_TARGET = 10
TW_TARGET = (120, 240)
SEEDS_PER_CELL = R54.SEEDS_PER_CELL
B_FIXED = R54.B_FIXED


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    rows = []
    t0 = time.time()
    total_pairs = 0
    total_activated = 0
    for tw in TW_TARGET:
        for sd in range(SEEDS_PER_CELL):
            rng = random.Random(R54.seed_from(N_TARGET, B_FIXED, "GW", tw, None, sd, "t4viec54_n10"))
            try:
                n_total, n_act = R54.run_cell(rng, N_TARGET, tw, sd)
            except SystemExit as e:
                print("  [skip] %s" % e)
                continue
            total_pairs += n_total
            total_activated += n_act
            rows.append(dict(n=N_TARGET, B=B_FIXED, tw_width=tw, seed=sd,
                              pairs_total=n_total, pairs_activated=n_act,
                              activation_rate=(n_act / n_total) if n_total else None))
            print("  tw=%d seed=%d done, %.1fs, pairs=%d activated=%d"
                  % (tw, sd, time.time() - t0, total_pairs, total_activated))

    with open(os.path.join(OUT, "activation_rate_n10.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["n", "B", "tw_width", "seed", "pairs_total",
                                           "pairs_activated", "activation_rate"])
        w.writeheader()
        w.writerows(rows)

    rate = total_activated / total_pairs if total_pairs else 0.0
    print("\n=== SEC5.4 @ n=10 SUMMARY ===")
    print("total pairs (Ra,Rb): %d, activated: %d, activation_rate=%.4f%%"
          % (total_pairs, total_activated, rate * 100))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
