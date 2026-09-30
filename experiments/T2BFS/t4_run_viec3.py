"""Test4.md Viec 3 - do t_bfs_next that su (bang cach BFS chuan tu Seq(S),
KHONG dung F/Fp), doi chieu voi t_profile (da co trong compression.csv o
cac dong k=B-1). Chi chay tren MOT MAU nho dai dien (khong toan bo grid -
qua ton kem, xem ghi chu trong t4_run_viec2.py).

DUNG: them cot t_bfs_next_ms_viec3 vao 1 file rieng Output/Test4/viec3_sample.csv
(khong ghi de compression.csv).
"""

import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t3_check_k1 as K1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

# Mau dai dien: bao trum ca 3 o trong tam cua Viec 2 (Sec3) + vai o nhe hon
# de doi chung, ca GW lan OD, seed co dinh (deterministic, khong doc bid).
SAMPLE_CELLS = [
    # (n, B, cls, tw, tau)  - trong tam Sec3
    (6, 4, "GW", 120, None),
    (6, 4, "GW", 240, None),
    (6, 3, "GW", 240, None),
    # doi chung nhe hon
    (6, 2, "GW", 240, None),
    (6, 4, "GW", 30, None),
    (6, 4, "OD", 240, 60),
]
N_SEEDS_VIEC3 = 2


def seed_from(*parts):
    import hashlib
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def run_cell_viec3(rng, n, B, cls, tw, tau, seed_idx):
    """Giong t4_run_viec2.run_cell nhung CHI o k=B-1 (d=1), CO do ca
    t_profile va t_bfs_next that su (so sanh truc tiep, cung 1 lan chay)."""
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    if cls == "OD":
        rate, ok = K1.check_and_warn(driver, orders, tt,
            label="n=%d B=%d %s tw=%d tau=%s seed=%d" % (n, B, cls, tw, tau, seed_idx))
        if not ok:
            return []

    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    import itertools
    k = B - 1
    rows = []
    for S_tuple in itertools.combinations(order_ids, k):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        seq_count = len(entries)
        if seq_count == 0:
            continue
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        m_rem = len(rem)
        if m_rem == 0:
            continue

        t0 = time.perf_counter()
        entries_with_gamma = []
        n_ins_profile = 0
        for canon, slack, walk in entries:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            entries_with_gamma.append((canon, walk, sched_full, gamma))
            has_home = walk[-1].kind == "home"
            upper_a = len(walk) - 1 if has_home else len(walk)
            upper_b = len(walk) if has_home else len(walk) + 1
            n_positions = sum(1 for a in range(1, upper_a + 1) for b in range(a + 1, upper_b + 1))
            n_ins_profile += n_positions * m_rem
        t_profile = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        n_ins_bfs = 0
        for j in rem:
            p, d = pd[j]
            for canon, walk, sched_full, gamma in entries_with_gamma:
                has_home = walk[-1].kind == "home"
                upper_a = len(walk) - 1 if has_home else len(walk)
                upper_b = len(walk) if has_home else len(walk) + 1
                for a in range(1, upper_a + 1):
                    R1 = walk[:a] + [p] + walk[a:]
                    for b in range(a + 1, upper_b + 1):
                        R2 = R1[:b] + [d] + R1[b:]
                        n_ins_bfs += 1
                        C.is_feasible(tt, driver, R2)
        t_bfs = (time.perf_counter() - t1) * 1000.0

        rows.append(dict(
            n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
            subset_id="|".join(sorted(S)), k=k, m_rem=m_rem, seq_count=seq_count,
            t_profile_ms=t_profile, t_bfs_next_ms=t_bfs,
            n_insertion_profile=n_ins_profile, n_insertion_bfs=n_ins_bfs,
            ratio_profile_over_bfs=(t_profile / t_bfs) if t_bfs > 0 else None,
        ))
    return rows


FIELDS = ["n", "B", "class", "tw_width", "tau", "seed", "subset_id", "k", "m_rem",
          "seq_count", "t_profile_ms", "t_bfs_next_ms",
          "n_insertion_profile", "n_insertion_bfs", "ratio_profile_over_bfs"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    t0 = time.time()
    for (n, B, cls, tw, tau) in SAMPLE_CELLS:
        for sd in range(N_SEEDS_VIEC3):
            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t4viec3"))
            try:
                rows = run_cell_viec3(rng, n, B, cls, tw, tau, sd)
            except SystemExit as e:
                print("  [skip] %s" % e)
                continue
            for r in rows:
                r["class"] = r.pop("cls")
            all_rows.extend(rows)
            print("  n=%d B=%d %s tw=%s tau=%s seed=%d -> %d rows (%.1fs elapsed)"
                  % (n, B, cls, tw, tau, sd, len(rows), time.time() - t0))

    with open(os.path.join(OUT, "viec3_sample.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    print("\nTONG: %d rows, %.1fs" % (len(all_rows), time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
