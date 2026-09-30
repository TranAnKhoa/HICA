"""Test4.md Viec 2 - do compression that: |Front_X(S)| / |Seq(S)|, tai MOI k
(khong chi k=B-1), tren CA grid nho (n<=6) LAN grid lon (n in {8,10,12,15}).

DUNG: Output/Test4/compression.csv

n_insertion_bfs GHI LAI = n_insertion_profile CHI KHI k=B-1 (d=1, spec Sec4:
"ve ly thuyet bang nhau" - cung cong thuc duyet R(+)j, khong do rieng de
tranh nhan doi chi phi cua chinh compute_gamma tren toan grid). t_bfs_next_ms
KHONG do o day (qua ton kem tren toan grid) - do rieng tren MAU nho o
t4_run_viec3.py, doi chieu voi t_profile_ms cua CHINH cac dong co k=B-1
trong file nay.

SAI LECH CONG KHAI (giong Test2/Test3): SEEDS_PER_CELL GIAM xuong
VIEC2_SEEDS_PER_CELL (< G.SEEDS_PER_CELL=8 dung cho Test2/Viec0/Viec1) - vi
compute_gamma + filter_dominated O(|Seq(S)|^2) qua ton kem de chay 8 seed
tren toan bo grid (uoc tinh > 10 gio o muc 8 seed, dua tren 1 cell nang
nhat ~160s). Van phu TOAN BO khong gian tham so (n,B,tw,tau,class), chi
giam so lan lap MOI o.
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
import t4_profile as P
import t3_check_k1 as K1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL
N_ORDERS_BIG = G.N_ORDERS_BIG
B_GRID = G.B_GRID
DRIVER_CLASS = G.DRIVER_CLASS
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
VIEC2_SEEDS_PER_CELL = 3   # xem ghi chu "SAI LECH CONG KHAI" o dau file


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def run_cell(rng, n, B, cls, tw, tau, seed_idx):
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

    rows = []
    for k in range(1, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            entries = seq.get(S, [])
            seq_count = len(entries)
            if seq_count == 0:
                continue
            rem = [o for o in order_ids if o not in S and o in reach_ids]
            m_rem = len(rem)

            if m_rem == 0:
                # khong co gi de tinh Gamma - compression khong xac dinh
                # (front = Seq_full nguyen ven, vi khong co gi de dominate
                # theo tieu chi phu thuoc Rem(S) - D1/D2/D3 deu ⪰ tam thuong
                # khi Rem rong, front = 1 phan tu bat ky ~ KHONG dung, bo qua
                # dong nay khoi thong ke compression, ghi rieng m_rem=0)
                rows.append(dict(
                    n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
                    subset_id="|".join(sorted(S)), k=k, m_rem=0,
                    seq_count=seq_count, front_D1=None, front_D2=None, front_D3=None,
                    compression_D1=None, compression_D2=None, compression_D3=None,
                    t_profile_ms=None, t_bfs_next_ms=None,
                    n_insertion_profile=None, n_insertion_bfs=None,
                ))
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

            fronts = {}
            for variant in ("D1", "D2", "D3"):
                fronts[variant] = P.filter_dominated(entries_with_gamma, rem, variant)

            # t_bfs_next/n_insertion_bfs: KHONG do o day (qua ton kem tren
            # toan bo grid - se lam Viec 2 khong the hoan tat). n_ins_bfs VE
            # LY THUYET = n_ins_profile khi k=B-1 (spec 4: "bang nhau" - cung
            # cong thuc duyet R(+)j). Do rieng tren MAU nho o t4_run_viec3.py.
            t_bfs = None
            n_ins_bfs = n_ins_profile if k == B - 1 else None

            rows.append(dict(
                n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
                subset_id="|".join(sorted(S)), k=k, m_rem=m_rem,
                seq_count=seq_count,
                front_D1=len(fronts["D1"]), front_D2=len(fronts["D2"]), front_D3=len(fronts["D3"]),
                compression_D1=len(fronts["D1"]) / seq_count,
                compression_D2=len(fronts["D2"]) / seq_count,
                compression_D3=len(fronts["D3"]) / seq_count,
                t_profile_ms=t_profile, t_bfs_next_ms=t_bfs,
                n_insertion_profile=n_ins_profile, n_insertion_bfs=n_ins_bfs,
            ))
    return rows


FIELDS = ["n", "B", "class", "tw_width", "tau", "seed", "subset_id", "k", "m_rem",
          "seq_count", "front_D1", "front_D2", "front_D3",
          "compression_D1", "compression_D2", "compression_D3",
          "t_profile_ms", "t_bfs_next_ms", "n_insertion_profile", "n_insertion_bfs"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    t0 = time.time()

    print("=== VIEC 2/3 - grid NHO (n<=6) ===")
    cell_id = 0
    for n in N_ORDERS_SMALL:
        for B in B_GRID:
            if B > n:
                continue
            for cls in DRIVER_CLASS:
                for tw in TW_WIDTH_GRID:
                    taus = TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(VIEC2_SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t4viec2"))
                            try:
                                rows = run_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            for r in rows:
                                r["class"] = r.pop("cls")
                            all_rows.extend(rows)
                        cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs, rows=%d)"
              % (n, cell_id, time.time() - t0, len(all_rows)))

    # ghi CSV grid nho NGAY, truoc khi chay grid lon (grid lon co the mat
    # nhieu gio - khong de mat ket qua grid nho neu can dung giua chung)
    with open(os.path.join(OUT, "compression_small.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print("  [da ghi compression_small.csv, %d rows, %.1fs]" % (len(all_rows), time.time() - t0))

    print("\n=== VIEC 2/3 - grid LON (n in {8,10,12,15}) ===")
    # GHI RIENG TUNG n NGAY SAU KHI XONG (incremental) - chay grid lon co the
    # mat vai gio, KHONG duoc de mat toan bo ket qua neu tien trinh bi dung
    # giua chung (da xay ra 1 lan: n=8,10 tinh xong nhung mat vi file cu chi
    # ghi SAU KHI CA VONG LAP LON hoan tat).
    t_big0 = time.time()
    big_rows_total = []
    for n in N_ORDERS_BIG:
        n_rows_this = []
        cell_id = 0
        for B in B_GRID:
            for cls in DRIVER_CLASS:
                for tw in TW_WIDTH_GRID:
                    taus = TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(VIEC2_SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t4viec2", "big"))
                            try:
                                rows = run_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            for r in rows:
                                r["class"] = r.pop("cls")
                            n_rows_this.extend(rows)
                        cell_id += 1
        big_rows_total.extend(n_rows_this)
        with open(os.path.join(OUT, "compression_big_n%d.csv" % n), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(n_rows_this)
        print("  n_orders=%d done (%d cells, %.1fs, rows=%d) [ghi compression_big_n%d.csv]"
              % (n, cell_id, time.time() - t_big0, len(n_rows_this), n))

    all_rows.extend(big_rows_total)
    with open(os.path.join(OUT, "compression.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    print("\nTONG: %d rows, %.1fs" % (len(all_rows), time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
