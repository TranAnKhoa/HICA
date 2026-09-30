"""Trace 1 closure mismatch cu the: tim label vua pickup (root) co attempts=3,
IV nho, ma toan bo cac lan _try_delivery/_try_pickup tiep theo deu chet, nhung
iv_completion_feasible(root) tra True. In het chi tiet IV, t, v cua root VA
so sanh tung buoc voi _try_delivery that."""

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


def iv_completion_feasible_verbose(travel_time, pd, lab):
    iv_list = list(lab.IV)
    print("    iv_completion_feasible called: v=%s IV=%s t=%.3f" % (lab.v, sorted(iv_list), lab.t))
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
            print("      perm=%s oid=%s v=%s->d=%s tt=%.3f A=%.3f e=%.3f l=%.3f Bt=%.3f feasible=%s"
                  % (perm, oid, v, d.id, tt, A, d.e, d.l, Bt, Bt <= d.l + 1e-9))
            if Bt > d.l + 1e-9:
                ok = False
                break
            t = Bt + d.s
            v = d.id
        if ok:
            return True
    return False


def main():
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    drv = [d for d in gw_drivers if d["id"] == "gw2"][0]

    start, pd, home = C.build_walk_nodes(drv, orders)
    order_ids = sorted(orders.keys())

    lab0 = D.Label(start.id, frozenset(), frozenset(), drv["t0"], 0.0, 0.0)
    closure_root = {id(lab0): id(lab0)}
    frontier = {0: [lab0]}

    target_root_attempts = None
    B = B_GW
    found = []

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
                    new_lab = D._try_delivery(tt, drv, pd, lab, j)
                    if new_lab is None:
                        continue
                    closure_root[id(new_lab)] = root
                    next_active.append(new_lab)
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(D._filter_dominated_labels(labs))
            active = filtered

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(tt, drv, pd, lab, j, B)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                for lb in kept:
                    rid = id(lb)
                    closure_root[rid] = rid
                    if len(found) < 500:
                        found.append(lb)
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    print("So label vua pickup tim duoc (mau):", len(found))

    def iv_completion_feasible_silent(travel_time, pd, lab):
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
                tvl = travel_time(v, d.id)
                A = t + tvl
                Bt = A if A > d.e else d.e
                if Bt > d.l + 1e-9:
                    ok = False
                    break
                t = Bt + d.s
                v = d.id
            if ok:
                return True
        return False

    def try_all(cur_lab, remaining):
        if not remaining:
            return True
        for oid in sorted(remaining):
            nl = D._try_delivery(tt, drv, pd, cur_lab, oid)
            if nl is not None and try_all(nl, remaining - {oid}):
                return True
        return False

    n_mismatch = 0
    for lb in found:
        feas = iv_completion_feasible_silent(tt, pd, lb)
        real_feasible = try_all(lb, lb.IV)
        if feas != real_feasible:
            n_mismatch += 1
            print("MISMATCH: v=%s IV=%s t=%.3f  iv_completion_feasible=%s  real=%s"
                  % (lb.v, sorted(lb.IV), lb.t, feas, real_feasible))
    print("Tong mismatch (predict vs real _try_delivery-only feasibility): %d / %d" % (n_mismatch, len(found)))


if __name__ == "__main__":
    main()
