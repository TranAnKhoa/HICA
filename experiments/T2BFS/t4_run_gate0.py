"""Test4.md Viec 0 - chay Gate 0.1 (F tuong duong recompute) + Gate 0.2 (so
muc chat voi min-slack), tren grid nho (n<=6) dung Test2.md Sec5 (giu nguyen
grid, dung generator DA PATCH cua Test3 cho OD).

DUNG: Output/Test4/f_slack_check.csv
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
import t4_fwdslack as FS
import t4_gate0 as G0
import t3_check_k1 as K1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL
B_GRID = G.B_GRID
DRIVER_CLASS = G.DRIVER_CLASS
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def run_cell(rng, n, B, cls, tw, tau, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)

    if cls == "OD":
        rate, ok = K1.check_and_warn(driver, orders, tt,
            label="n=%d B=%d %s tw=%d tau=%s seed=%d" % (n, B, cls, tw, tau, seed_idx))
        if not ok:
            return [], 0, 0, 0

    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())

    rows = []
    n_mismatch = 0
    n_checked = 0
    n_pruned_by_minslack_but_F_keep = 0

    for k in range(1, B):     # k = 1..B-1 (can co it nhat 1 order con lai)
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            entries = seq.get(S, [])
            if not entries:
                continue
            rem = [o for o in order_ids if o not in S]
            if not rem:
                continue

            cap = driver["capacity"]
            for canon, slack, walk in entries:
                F_data = FS.forward_slack(tt, driver, walk)
                ok0, schedule, F, Fp = F_data
                if not ok0:
                    continue    # khong the xay ra (walk trong Seq da feasible) - an toan bo qua

                for j in rem:
                    p, d = pd[j]
                    has_home = walk[-1].kind == "home"
                    # QUAN TRONG: a chay tren WALK GOC (upper_a = len(walk),
                    # tru 1 neu co home), nhung b chay tren WALK DA CHEN P
                    # (dai hon 1 phan tu) - dung cong thuc CUNG voi
                    # t2_core._insert_positions goc (R1 = walk sau khi chen
                    # P, upper_b = len(R1) = len(walk)+1, tru 1 neu co home).
                    upper_a = len(walk) - 1 if has_home else len(walk)
                    upper_b = len(walk) if has_home else len(walk) + 1
                    for a in range(1, upper_a + 1):
                        for b in range(a + 1, upper_b + 1):
                            res = G0.feasible_by_F_two_insert(tt, walk, schedule, Fp, p, d, a, b)
                            ok_by_F_tw = res[0]

                            walk2 = walk[:a] + [p] + walk[a:]
                            walk2 = walk2[:b] + [d] + walk2[b:]
                            ok_recompute, slack2, sched2 = C.is_feasible(tt, driver, walk2)

                            # capacity: F/Fp chi bao TW, khong bao capacity.
                            # Kiem capacity DAY DU bang cach duyet load doc
                            # toan doan [a,b] cua walk MOI (khong chi tai P) -
                            # can dung tuyet doi cho Gate 0.1 (yeu cau khop
                            # 100%), du capacity=B duoc thiet ke de khong bao
                            # gio la nut that trong Test2 Sec5.
                            cap_ok = True
                            load = schedule[a - 1][3]
                            load += p.demand
                            if load > cap + FS.EPS:
                                cap_ok = False
                            else:
                                for idx in range(a, b - 1):
                                    load += walk[idx].demand
                                    if load > cap + FS.EPS or load < -FS.EPS:
                                        cap_ok = False
                                        break
                                if cap_ok:
                                    load += d.demand
                                    if load < -FS.EPS:
                                        cap_ok = False

                            ok_by_F = bool(ok_by_F_tw) and cap_ok
                            mismatch = (ok_by_F != ok_recompute)
                            n_checked += 1
                            if mismatch:
                                n_mismatch += 1

                            # Gate 0.2: so voi min-slack (slack(R) dung nhu
                            # arc-capacity CHUNG cho moi vi tri) - hoi "co
                            # PRUNE nham khong": pruned_by_minslack = True
                            # neu push (tai vi tri chen dau tien, a) > slack(R)
                            # (slack toan tuyen) NHUNG F cho KEEP (that su
                            # kha thi theo recompute).
                            pruned_by_minslack = (slack is not None) and (
                                _min_slack_would_prune(tt, walk, schedule, slack, p, d, a, b))
                            if pruned_by_minslack and ok_recompute:
                                n_pruned_by_minslack_but_F_keep += 1

                            rows.append(dict(
                                n=n, B=B, cls=cls, tw_width=tw, tau=tau, seed=seed_idx,
                                k=k, subset_id="|".join(sorted(S)), route_id=canon,
                                j=j, pos_a=a, pos_b=b,
                                feasible_by_F=ok_by_F, feasible_by_recompute=ok_recompute,
                                mismatch=mismatch, pruned_by_minslack=pruned_by_minslack,
                            ))

    return rows, n_mismatch, n_checked, n_pruned_by_minslack_but_F_keep


def _min_slack_would_prune(travel_time, walk, schedule, slack_R, p, d, a, b):
    """Uoc luong tho: neu push tai vi tri chen dau tien (a) > slack_R (slack
    toan tuyen, dung nhu 1 'arc capacity' CHUNG duy nhat cho moi vi tri, cach
    lam CU truoc khi co F), thi cach cu se PRUNE (tu choi chen) - bat ke phan
    duoi co du kha nang hap thu hay khong (day chinh la diem F sua: F[a-1]
    RIENG cho tung vi tri, khong dung 1 con so chung cho ca route)."""
    if a >= len(walk):
        return False
    prev = walk[a - 1]
    D_prev = schedule[a - 1][2]
    A_p = D_prev + travel_time(prev.id, p.id)
    B_p = A_p if A_p > p.e else p.e
    if B_p > p.l + FS.EPS:
        return False   # da infeasible ngay tai p, khong phai do "prune qua chat"
    D_p = B_p + p.s
    nxt = walk[a]
    A_nxt_old = D_prev + travel_time(prev.id, nxt.id)
    push = D_p - A_nxt_old
    return push > slack_R + FS.EPS


FIELDS = ["n", "B", "class", "tw_width", "tau", "seed", "k", "subset_id", "route_id",
          "j", "pos_a", "pos_b", "feasible_by_F", "feasible_by_recompute", "mismatch",
          "pruned_by_minslack"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_rows = []
    total_mismatch = 0
    total_checked = 0
    total_pruned_minslack_but_ok = 0
    t0 = time.time()
    cell_id = 0
    for n in N_ORDERS_SMALL:
        for B in B_GRID:
            if B > n:
                continue
            for cls in DRIVER_CLASS:
                for tw in TW_WIDTH_GRID:
                    taus = TAU_GRID if cls == "OD" else (None,)
                    for tau in taus:
                        for sd in range(SEEDS_PER_CELL):
                            rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t4gate0"))
                            try:
                                rows, n_mm, n_chk, n_pm = run_cell(rng, n, B, cls, tw, tau, sd)
                            except SystemExit as e:
                                print("  [skip] %s" % e)
                                continue
                            all_rows.extend(rows)
                            total_mismatch += n_mm
                            total_checked += n_chk
                            total_pruned_minslack_but_ok += n_pm
                            if n_mm > 0:
                                print("  MISMATCH n=%d B=%d %s tw=%d tau=%s seed=%d : %d/%d"
                                      % (n, B, cls, tw, tau, sd, n_mm, n_chk))
                        cell_id += 1
        print("  n_orders=%d done (%d cells so far, %.1fs, checked=%d, mismatch=%d)"
              % (n, cell_id, time.time() - t0, total_checked, total_mismatch))

    with open(os.path.join(OUT, "f_slack_check.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "n", "B", "cls", "tw_width", "tau", "seed", "k", "subset_id", "route_id",
            "j", "pos_a", "pos_b", "feasible_by_F", "feasible_by_recompute", "mismatch",
            "pruned_by_minslack"])
        w.writeheader()
        w.writerows(all_rows)

    print("\n=== GATE 0.1 SUMMARY ===")
    print("total_checked=%d  total_mismatch=%d  mismatch_rate=%.6f%%"
          % (total_checked, total_mismatch, 100.0 * total_mismatch / total_checked if total_checked else 0))

    print("\n=== GATE 0.2 (min-slack loai nham so voi F) ===")
    print("pruned_by_minslack_but_actually_feasible = %d / %d (%.4f%%)"
          % (total_pruned_minslack_but_ok, total_checked,
             100.0 * total_pruned_minslack_but_ok / total_checked if total_checked else 0))

    print("\nelapsed=%.1fs  rows=%d" % (time.time() - t0, len(all_rows)))

    if total_mismatch > 0:
        print("\n*** GATE 0.1 FAIL: mismatch > 0. DUNG, sua bug F_i truoc khi lam Viec 1. ***")
        return 1
    print("\nGATE 0.1: PASS (0 mismatch)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
