"""Test4.md Viec 4 - kiem gia thuyet d>=2 (Front_X tai k=2 co du de BFS tiep
2 level toi k=4 ma khong mat bundle nao so voi brute force).

Chi chay tren grid nho (n<=6, B=4 co dinh, GW - trong tam theo spec Sec6),
dung ground truth brute force cua t2_core.

DUNG: Output/Test4/depth2.csv
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

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test4")
SESSION = 3

N_ORDERS_SMALL = G.N_ORDERS_SMALL   # (4,5,6) - can n>=4 vi B=4 co dinh, chi n=4,5,6 dung duoc
TW_WIDTH_GRID = G.TW_WIDTH_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL
B_FIXED = 4


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def _insert_positions_walk(walk, has_home):
    upper = len(walk) - 1 if has_home else len(walk)
    return range(1, upper + 1)


def bfs_from_front(travel_time, driver, pd, front_entries, S, order_ids, target_k):
    """BFS level-wise, bat dau tu front_entries (list walk) cua tap S, sinh
    tiep TOI target_k (chi chen 1 order/level, LUON dung TOAN BO ket qua
    level truoc lam nguon cho level sau - giong bfs_generate goc, nhung
    XUAT PHAT tu front thay vi Seq day du).　Chi ho tro sinh THEO 1 THU TU
    CO DINH cac order duoc them (khong phai moi thu tu co the - specify ro
    trong ham goi: se thu MOI thu tu them order con lai, hop voi dinh nghia
    downward-closed cua BFS goc).

    Tra dict {S': [walk,...]} cho MOI S' voi S subset S' subset (S hop
    target_k - |S| order duoc them dan), sinh tu front CUA S ban dau."""
    remaining = [o for o in order_ids if o not in S]
    result = {S: front_entries}
    frontier = {S: front_entries}

    cur_size = len(S)
    while cur_size < target_k:
        next_frontier = {}
        for Sp, entries in frontier.items():
            rem_p = [o for o in order_ids if o not in Sp]
            for j in rem_p:
                p, d = pd[j]
                Snew = frozenset(set(Sp) | {j})
                out = []
                seen = set()
                for walk in entries:
                    has_home = walk[-1].kind == "home"
                    for a in _insert_positions_walk(walk, has_home):
                        R1 = walk[:a] + [p] + walk[a:]
                        for b in _insert_positions_walk(R1, has_home):
                            if b <= a:
                                continue
                            R2 = R1[:b] + [d] + R1[b:]
                            ok, slack, sched = C.is_feasible(travel_time, driver, R2)
                            if ok:
                                c = C.canonical(R2)
                                if c not in seen:
                                    seen.add(c)
                                    out.append(R2)
                if Snew in next_frontier:
                    # gop (co the sinh tu nhieu Sp khac nhau neu |S|<target_k-1
                    # va co nhieu duong toi Snew - giu UNION, dedupe theo canonical)
                    existed = next_frontier[Snew]
                    seen2 = set(C.canonical(w) for w in existed)
                    for w in out:
                        c = C.canonical(w)
                        if c not in seen2:
                            seen2.add(c)
                            existed.append(w)
                else:
                    next_frontier[Snew] = out
                result[Snew] = next_frontier[Snew]
        frontier = next_frontier
        cur_size += 1

    return result


def run_cell(rng, n, tw, seed_idx):
    B = B_FIXED
    cls = "GW"
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, None, B)
    order_ids = sorted(orders.keys())
    start, pd, home = C.build_walk_nodes(driver, orders)

    # ground truth brute force TOI k=4 (chi can subset |S|=2 lam goc, |S|=4 la dich)
    bf, bf_stats = C.brute_force(tt, driver, orders, B)
    seq, prune_cnt, ins_att, sstar, pruned, ins_by_S = C.bfs_generate(tt, driver, orders, B, use_filter=True)
    reach_ids = set(P.reachable_orders(driver, tt, pd, order_ids))

    rows = []
    for S_tuple in itertools.combinations(order_ids, 2):
        S = frozenset(S_tuple)
        entries = seq.get(S, [])
        if not entries:
            continue
        rem = [o for o in order_ids if o not in S and o in reach_ids]
        if not rem:
            continue

        entries_with_gamma = []
        for canon, slack, walk in entries:
            _, _, sched_full = C.is_feasible(tt, driver, walk)
            gamma = P.compute_gamma(driver, tt, walk, sched_full, pd, rem)
            entries_with_gamma.append((canon, walk, sched_full, gamma))

        for variant in ("D2", "D3"):
            front = P.filter_dominated(entries_with_gamma, rem, variant)
            front_walks = [w for (c, w, s, g) in front]

            gen = bfs_from_front(tt, driver, pd, front_walks, S, order_ids, 4)

            # so voi brute force o k=4: MOI S4 (|S4|=4, S subset S4) khoi
            # tao tu S nay (theo bat ky duong nao qua rem)
            violation = False
            lost_bundles = []
            for S4 in itertools.combinations(order_ids, 4):
                S4f = frozenset(S4)
                if not S.issubset(S4f):
                    continue
                bf_s4 = set(x[0] for x in bf.get(S4f, []))
                if not bf_s4:
                    continue
                gen_s4 = set(C.canonical(w) for w in gen.get(S4f, []))
                missing = bf_s4 - gen_s4
                if missing:
                    violation = True
                    lost_bundles.append(sorted(S4f))

            rows.append(dict(
                n=n, B=B, cls=cls, tw_width=tw, tau=None, seed=seed_idx,
                subset_id="|".join(sorted(S)), variant=variant,
                violation=violation, lost_bundles=str(lost_bundles) if lost_bundles else "",
            ))
    return rows


FIELDS = ["n", "B", "class", "tw_width", "tau", "seed", "subset_id",
          "violation_D2", "violation_D3", "lost_bundles",
          "ub_lb_activation_pairs", "ub_lb_total_pairs", "activation_rate"]


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_raw = []
    t0 = time.time()
    for n in N_ORDERS_SMALL:
        if n < B_FIXED:
            continue
        for tw in TW_WIDTH_GRID:
            for sd in range(SEEDS_PER_CELL):
                rng = random.Random(seed_from(n, B_FIXED, "GW", tw, None, sd, "t4viec4"))
                try:
                    rows = run_cell(rng, n, tw, sd)
                except SystemExit as e:
                    print("  [skip] %s" % e)
                    continue
                all_raw.extend(rows)
        print("  n=%d done, %.1fs, rows=%d" % (n, time.time() - t0, len(all_raw)))

    # pivot: 1 dong / subset_id, gop D2/D3 violation vao 2 cot
    by_key = {}
    for r in all_raw:
        key = (r["n"], r["B"], r["cls"], r["tw_width"], r["seed"], r["subset_id"])
        if key not in by_key:
            by_key[key] = dict(n=r["n"], B=r["B"], cls=r["cls"], tw_width=r["tw_width"],
                                tau=None, seed=r["seed"], subset_id=r["subset_id"],
                                violation_D2=False, violation_D3=False, lost_bundles="")
        by_key[key]["violation_%s" % r["variant"]] = r["violation"]
        if r["violation"] and r["lost_bundles"]:
            by_key[key]["lost_bundles"] += ("|" if by_key[key]["lost_bundles"] else "") + \
                ("%s:%s" % (r["variant"], r["lost_bundles"]))

    final_rows = []
    for key, d in by_key.items():
        d2 = dict(d)
        d2["class"] = d2.pop("cls")
        d2["ub_lb_activation_pairs"] = None
        d2["ub_lb_total_pairs"] = None
        d2["activation_rate"] = None
        final_rows.append(d2)

    with open(os.path.join(OUT, "depth2.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(final_rows)

    n_total = len(final_rows)
    n_viol_d2 = sum(1 for r in final_rows if r["violation_D2"])
    n_viol_d3 = sum(1 for r in final_rows if r["violation_D3"])
    print("\n=== VIEC 4 SUMMARY ===")
    print("total subsets (k=2, GW, B=4) checked: %d" % n_total)
    print("D2 violation: %d (%.4f%%)" % (n_viol_d2, 100.0 * n_viol_d2 / n_total if n_total else 0))
    print("D3 violation: %d (%.4f%%)" % (n_viol_d3, 100.0 * n_viol_d3 / n_total if n_total else 0))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
