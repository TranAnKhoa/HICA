"""Test_case2_followup.md - Test B: bucket/index hoa dominance (engineering
thuan tuy, KHONG duoc phep doi ket qua).

Muc dich: do xem bucket hoa theo v + sort theo K co giam wall-clock khong,
so voi _filter_dominated_labels goc (quet O(F) tren toan bo list cung key
moi lan can loc). Day KHONG phai thu de giam frontier_lastround (van ~4.5M
nhu cu, dung du doan) - chi do tong wall-clock co giam nho moi lan so sanh
re hon khong.

Gate bat buoc: route_pool cuoi cung phai GIONG HET ban goc (canonical
signature), n<=6 khop brute-force - kiem truoc khi tin ket qua toc do.
"""

import bisect
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import brute_force as BF

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp as D
import t2_core as C

N, B_GW, TW, SEED, NDRV = 20, 4, 240, 0, 10
TAU = 20.0
SPATIAL = "dispersed"
EPS = 1e-9


# ---------------------------------------------------------------- Test B: bucket hoa
class DominanceBucket:
    """1 bucket ung voi 1 key day du (v, IV, C) - giu frontier Pareto (K,W)
    da sort theo K de cat som bang bisect. Dung DUNG dinh nghia dominance
    cua t6_dp.py (minimize K,W, >=1 strict) - khong noi long."""
    __slots__ = ("K_sorted", "labels")

    def __init__(self):
        self.K_sorted = []
        self.labels = []

    def try_insert(self, new_label):
        K2, W2 = new_label.K, new_label.W
        # kiem xem new_label co bi label da co dominate khong (K<=K2, W<=W2, >=1 strict)
        for i in range(len(self.K_sorted)):
            Ki, lab_i = self.K_sorted[i], self.labels[i]
            if Ki <= K2 + EPS and lab_i.W <= W2 + EPS and (Ki < K2 - EPS or lab_i.W < W2 - EPS):
                return False   # bi dominate, loai ngay
        # xoa cac label bi new_label dominate
        keep = []
        for i in range(len(self.K_sorted)):
            Ki, lab_i = self.K_sorted[i], self.labels[i]
            if K2 <= Ki + EPS and W2 <= lab_i.W + EPS and (K2 < Ki - EPS or W2 < lab_i.W - EPS):
                continue   # label cu bi new_label dominate -> loai
            keep.append(i)
        self.K_sorted = [self.K_sorted[i] for i in keep]
        self.labels = [self.labels[i] for i in keep]
        pos = bisect.bisect_left(self.K_sorted, K2)
        self.K_sorted.insert(pos, K2)
        self.labels.insert(pos, new_label)
        return True


def _filter_dominated_labels_bucketed(labels):
    """Ham thay the _filter_dominated_labels goc, dung DominanceBucket -
    labels dau vao CUNG 1 key (nhu ham goc), tra list khong bi dominate."""
    bucket = DominanceBucket()
    for lab in labels:
        bucket.try_insert(lab)
    return list(bucket.labels)


def run_dp_bucketed(travel_time, driver, orders, B, compat_graph=None):
    """Copy TRUNG THUC t6_dp.run_dp, CHI thay _filter_dominated_labels goc
    bang _filter_dominated_labels_bucketed. Moi logic khac giu nguyen."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue
        active = list(labs_here)
        closure_all = []
        while active:
            next_active = []
            for lab in active:
                closure_all.append(lab)
                for j in sorted(lab.IV):
                    new_lab = D._try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        continue
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1 and not has_home:
                        complete_by_C[new_lab.Cd].append(new_lab)
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    new_lab = D._try_home(travel_time, driver, home, lab)
                    if new_lab is not None:
                        complete_by_C[new_lab.Cd].append(new_lab)
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(_filter_dominated_labels_bucketed(labs))
            active = filtered

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B,
                                            compat_graph=compat_graph)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                next_frontier.extend(_filter_dominated_labels_bucketed(labs))
            frontier[touched + 1] = next_frontier

    # dominance cuoi tren complete_by_C (giong t6_dp.run_dp doan cuoi)
    for Cset, labs in list(complete_by_C.items()):
        by_v = defaultdict(list)
        for lab in labs:
            by_v[lab.v].append(lab)
        kept = []
        for v, labs_v in by_v.items():
            kept.extend(_filter_dominated_labels_bucketed(labs_v))
        complete_by_C[Cset] = kept

    return complete_by_C


def _canonical_pool(complete_by_C, driver):
    """[FIX] complete_by_C's dominance CUOI trong run_dp CHI loc trong CUNG
    v (dung thiet ke Sec1.2 - xem comment t6_dp.py dong 298-300), nen 1
    bundle C co the con nhieu diem tu cac v (diem giao cuoi) KHAC nhau. Phai
    loc lai Pareto front TREN TOAN BO (K,W) khong phan biet v - GIONG HET
    dp_labeling.py::run_pool goi _pareto_front - moi so sanh cong bang duoc
    voi brute_force.py (brute_pool_for_driver cung Pareto tren toan bo,
    khong phan biet v)."""
    pool = {}
    for Cset, labs in complete_by_C.items():
        if not Cset:
            continue
        kw = []
        for lab in labs:
            K, W = D.finalize_KW(driver, lab)
            kw.append((K, W))
        front = DL._pareto_front(kw)
        pool[Cset] = sorted(set((round(K, 6), round(W, 6)) for K, W in front))
    return pool


def gate_check_n6():
    """Gate bat buoc: n<=6, so sanh route_pool ban bucket vs ban goc vs
    brute-force - PHAI khop 100% truoc khi tin ket qua toc do Test B."""
    print("=== GATE: n<=6, bucket vs goc vs brute-force ===")
    n_checked = 0
    n_mismatch = 0
    for n in (3, 4, 5, 6):
        for B_gw in (2, 3, 4):
            for tw in (60, 120):
                for sd in range(3):
                    gen_seed = IG.stable_seed(n, B_gw, 2, tw, 4, sd, "testB_gate")
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=4,
                        seed=gen_seed, tau=TAU, spatial_mode=SPATIAL)
                    for drv in drivers:
                        B_eff = B_gw if drv["cls"] == "GW" else 2
                        res_orig = D.run_dp(tt, drv, orders, B_eff, use_dominance=True)
                        pool_orig = _canonical_pool(res_orig["complete_by_C"], drv)

                        complete_bucketed = run_dp_bucketed(tt, drv, orders, B_eff)
                        pool_bucket = _canonical_pool(complete_bucketed, drv)

                        pool_brute_raw = BF.brute_pool_for_driver(tt, drv, orders, B_gw, 2)
                        pool_brute = {S: sorted(set((round(K, 6), round(W, 6)) for K, W in front))
                                       for S, front in pool_brute_raw.items()}

                        n_checked += 1
                        if pool_orig != pool_bucket or pool_orig != pool_brute:
                            n_mismatch += 1
                            print("  !! MISMATCH n=%d B_gw=%d tw=%d seed=%d driver=%s"
                                  % (n, B_gw, tw, sd, drv["id"]))
    print("Instances checked: %d   Mismatches: %d" % (n_checked, n_mismatch))
    return n_mismatch == 0


def speed_compare():
    print("\n=== TEST B: so sanh wall-clock (goc vs bucket) tren cell nong ===")
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    print("Cell: n=%d B_gw=%d tw=%d seed=%d  n_gw_drivers=%d" % (N, B_GW, TW, SEED, len(gw_drivers)))

    t0 = time.time()
    for drv in gw_drivers:
        D.run_dp(tt, drv, orders, B_GW, use_dominance=True)
    t_orig = time.time() - t0
    print("Ban GOC   : %.2fs" % t_orig)

    t0 = time.time()
    for drv in gw_drivers:
        run_dp_bucketed(tt, drv, orders, B_GW)
    t_bucket = time.time() - t0
    print("Ban BUCKET: %.2fs" % t_bucket)

    speedup = t_orig / t_bucket if t_bucket > 0 else float("inf")
    print("Speedup (goc/bucket): %.3fx" % speedup)


def main():
    ok = gate_check_n6()
    if not ok:
        print("\n*** GATE FAILED - Test B UNSAFE, KHONG bao cao speedup ***")
        return 1
    print("\nGATE PASS - route_pool khop 100% (goc == bucket == brute-force).")
    speed_compare()
    return 0


if __name__ == "__main__":
    sys.exit(main())
