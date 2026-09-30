"""Test_EJOR_direction/Test_C.md - buoc 4: audit_relaxed_key_safety.

Sau khi do upper-bound optimistic (test_C_relaxed_key.py): trung binh 87.1%
giam frontier o n=10-15, B_gw=4, tw=240 - VUOT XA nguong >50%, theo bang
tieu chi phai chuyen sang buoc nay: chay THAT DP voi key noi long thay key
goc, so route_pool cuoi voi brute-force tren n<=6 de tim phan vi du.

QUAN TRONG: day la buoc kiem tra AN TOAN, KHONG phai buoc do toc do. Neu
GATE FAIL (co phan vi du), dung lai bao cao phan vi du cu the - KHONG
chuyen sang bien the chat hon ma khong bao cao that bai truoc.
"""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import brute_force as BF

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp as D
import t2_core as C

TAU = 20.0
SPATIAL = "dispersed"
EPS = 1e-9


def _filter_dominated_by_KW(labels):
    """Loc Pareto thuan tren (K, W) - dung cho dominance da NOI LONG key
    (khong con phan biet theo C nua trong cung bucket)."""
    pareto = []
    for lb in sorted(labels, key=lambda x: x.K):
        dominated = False
        for p in pareto:
            if p.K <= lb.K + EPS and p.W <= lb.W + EPS:
                dominated = True
                break
        if not dominated:
            pareto = [p for p in pareto if not (lb.K <= p.K + EPS and lb.W <= p.W + EPS)]
            pareto.append(lb)
    return pareto


def key_full(lab):
    return (lab.v, lab.IV, lab.Cd)


def key_drop_C(lab):
    return (lab.v, lab.IV)


def key_drop_C_size_only(lab):
    return (lab.v, lab.IV, len(lab.Cd))


def run_dp_relaxed_key(travel_time, driver, orders, B, key_fn, compat_graph=None):
    """Copy TRUNG THUC logic t6_dp.run_dp, CHI THAY key dung de nhom
    dominance (ca trong closure-BFS lan trong buoc pickup) tu key_full sang
    key_fn (tho hon). MOI logic khac (thu tu round, _try_pickup/_try_delivery/
    _try_home, dieu kien capacity |IV|+|C|<=B) giu NGUYEN - nen neu key_fn
    lam mat capacity-tracking dung, no se the hien qua sai lech route_pool
    khi so voi brute-force (capacity van duoc kiem trong _try_pickup qua
    lab.IV/lab.Cd that, KHONG bi anh huong boi key dung de nhom dominance -
    chi anh huong o CHO 2 label CO the bi coi la 'giong nhau du C khac nhau'
    va 1 trong 2 bi loai nham)."""
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
                by_key[key_fn(lab)].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(_filter_dominated_by_KW(labs))
            active = filtered

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B,
                                            compat_graph=compat_graph)
                    if new_lab is None:
                        continue
                    new_by_key[key_fn(new_lab)].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                next_frontier.extend(_filter_dominated_by_KW(labs))
            frontier[touched + 1] = next_frontier

    # dominance cuoi: y het t6_dp.py (loc theo v, KHONG phan biet C - vi C
    # da la khac nhau giua cac bundle roi, day la buoc GOM theo v cho toan bo
    # (K,W) - giu nguyen y nghia canonical pool nhu cac test truoc)
    for Cset, labs in list(complete_by_C.items()):
        by_v = defaultdict(list)
        for lab in labs:
            by_v[lab.v].append(lab)
        kept = []
        for v, labs_v in by_v.items():
            kept.extend(_filter_dominated_by_KW(labs_v))
        complete_by_C[Cset] = kept

    return complete_by_C


def _canonical_pool(complete_by_C, driver):
    """Giong het cac test truoc: Pareto front TREN TOAN BO (K,W) khong phan
    biet v, de so cong bang voi brute_force.py."""
    import dp_labeling as DL
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


def gate_check_n6(key_fn, key_name):
    print("=== GATE audit_relaxed_key_safety: n<=6, key=%s vs brute-force ===" % key_name)
    n_checked = 0
    n_mismatch = 0
    mismatch_examples = []
    for n in (3, 4, 5, 6):
        for B_gw in (2, 3, 4):
            for tw in (60, 120, 240):
                for sd in range(5):
                    gen_seed = IG.stable_seed(n, B_gw, 2, tw, 4, sd, "testC_gate_%s" % key_name)
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=4,
                        seed=gen_seed, tau=TAU, spatial_mode=SPATIAL)
                    for drv in drivers:
                        B_eff = B_gw if drv["cls"] == "GW" else 2

                        res_relaxed = run_dp_relaxed_key(tt, drv, orders, B_eff, key_fn)
                        pool_relaxed = _canonical_pool(res_relaxed, drv)

                        pool_brute_raw = BF.brute_pool_for_driver(tt, drv, orders, B_gw, 2)
                        pool_brute = {S: sorted(set((round(K, 6), round(W, 6)) for K, W in front))
                                       for S, front in pool_brute_raw.items()}

                        n_checked += 1
                        if pool_relaxed != pool_brute:
                            n_mismatch += 1
                            if len(mismatch_examples) < 5:
                                mismatch_examples.append({
                                    "n": n, "B_gw": B_gw, "tw": tw, "seed": sd,
                                    "driver": drv["id"], "cls": drv["cls"],
                                    "pool_relaxed": pool_relaxed, "pool_brute": pool_brute,
                                })
    print("Instances checked: %d   Mismatches: %d" % (n_checked, n_mismatch))
    if n_mismatch > 0:
        print("*** KEY '%s' KHONG AN TOAN - vi du phan vi du dau tien: ***" % key_name)
        for ex in mismatch_examples:
            print("  n=%(n)d B_gw=%(B_gw)d tw=%(tw)d seed=%(seed)d driver=%(driver)s cls=%(cls)s" % ex)
            missing = {}
            for S in set(ex["pool_brute"].keys()) | set(ex["pool_relaxed"].keys()):
                b = set(ex["pool_brute"].get(S, []))
                r = set(ex["pool_relaxed"].get(S, []))
                if b != r:
                    missing[S] = {"brute_only": sorted(b - r), "relaxed_only": sorted(r - b)}
            for S, diff in list(missing.items())[:3]:
                print("    bundle=%s  brute_only(bi mat)=%s  relaxed_only(du thua/sai)=%s"
                      % (sorted(S), diff["brute_only"], diff["relaxed_only"]))
    return n_checked, n_mismatch


def main():
    for key_fn, key_name in [(key_drop_C, "key_drop_C"), (key_drop_C_size_only, "key_drop_C_size_only")]:
        n_checked, n_mismatch = gate_check_n6(key_fn, key_name)
        if n_mismatch == 0:
            print("*** GATE PASS cho %s - AN TOAN tren n<=6 (%d instance) ***" % (key_name, n_checked))
        print()


if __name__ == "__main__":
    main()
