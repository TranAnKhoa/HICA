"""Tim VA in chi tiet 1 vi du closure 'chet that su' (khong sinh duoc IV-rong
o buoc nao, KHONG phai do dominance) nhung iv_completion_feasible tra True -
de debug tay xem sai o dau."""

import itertools
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp as D
import t2_core as C

N, B_GW, TW, SEED, NDRV = 20, 4, 240, 0, 10
TAU = 20.0
SPATIAL = "dispersed"


def iv_completion_feasible(travel_time, pd, lab):
    iv_list = list(lab.IV)
    if not iv_list:
        return True
    if len(iv_list) > 7:
        return True
    for perm in itertools.permutations(iv_list):
        t = lab.t
        v = lab.v
        ok = True
        for oid in perm:
            _, d = pd[oid]
            tt = travel_time(v, d.id)
            A = t + tt
            Bt = A if A > d.e else d.e
            if Bt > d.l + 1e-9:
                ok = False
                break
            t = Bt + d.s
            v = d.id
        if ok:
            return True
    return False


def run_and_find(travel_time, driver, orders, B):
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    frontier = {0: [lab0]}
    closure_root = {id(lab0): id(lab0)}
    root_label = {}   # closure_root_id -> the actual root Label object

    survivors_pre = defaultdict(int)
    survivors_post = defaultdict(int)
    root_iv_feasible = {}

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
                root = closure_root.get(id(lab), id(lab))
                for j in sorted(lab.IV):
                    new_lab = D._try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        continue
                    closure_root[id(new_lab)] = root
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1:
                        survivors_pre[root] += 1

            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(D._filter_dominated_labels(labs))
            active = filtered
            for lab in filtered:
                if not lab.IV and len(lab.Cd) >= 1:
                    root = closure_root.get(id(lab), id(lab))
                    survivors_post[root] += 1

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                for lb in kept:
                    rid = id(lb)
                    closure_root[rid] = rid
                    root_label[rid] = lb
                    root_iv_feasible[rid] = iv_completion_feasible(travel_time, pd, lb)
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    all_roots = set(root_label.keys())
    dead_real = [k for k in all_roots if survivors_pre.get(k, 0) == 0]
    mism = [k for k in dead_real if root_iv_feasible.get(k, True) == True]
    return mism, root_label, pd


def main():
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    drv = gw_drivers[2]

    mism, root_label, pd = run_and_find(tt, drv, orders, B_GW)
    print("So mismatch that su (khong phai dominance):", len(mism))

    for rid in mism[:5]:
        lab = root_label[rid]
        print("\n=== Label: v=%s IV=%s Cd=%s t=%.6f ===" % (lab.v, sorted(lab.IV), sorted(lab.Cd), lab.t))
        for oid in sorted(lab.IV):
            p, d = pd[oid]
            tt_ = tt(lab.v, d.id)
            A = lab.t + tt_
            Bt = A if A > d.e else d.e
            print("   order %s: delivery node=%s e=%.6f l=%.6f s=%.6f  tt(v,d)=%.6f  A=%.6f Bt=%.6f  Bt<=l? %s"
                  % (oid, d.id, d.e, d.l, d.s, tt_, A, Bt, Bt <= d.l + 1e-9))
        feas = iv_completion_feasible(tt, pd, lab)
        print("   iv_completion_feasible =", feas)

        def try_all_chain(cur, remaining, path):
            if not remaining:
                print("     THANH CONG chuoi day du:", path)
                return True
            any_ok = False
            for oid in sorted(remaining):
                nl = D._try_delivery(tt, drv, pd, cur, oid)
                if nl is None:
                    print("     that bai tai buoc:", path + [oid], " (tu v=%s t=%.6f)" % (cur.v, cur.t))
                else:
                    ok = try_all_chain(nl, remaining - {oid}, path + [oid])
                    any_ok = any_ok or ok
            return any_ok

        real = try_all_chain(lab, lab.IV, [])
        print("   => real chain feasible =", real)


if __name__ == "__main__":
    main()
