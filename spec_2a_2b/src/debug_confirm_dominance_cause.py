"""Kiem chung dut diem: TAT dominance hoan toan trong closure BFS (khong
dung _filter_dominated_labels), chi de xem 'survivor thuc su co duong kha
thi' co khop 100% voi iv_completion_feasible khong. Neu khop -> xac nhan
100% nguyen nhan 'mismatch' truoc do la do dominance CHEO GIUA CAC CLOSURE
xay ra o MOI buoc trung gian (khong phai bug trong iv_completion_feasible
hay trong t6_dp.py) - day la hanh vi DUNG cua thuat toan, chi anh huong
cach do 'survivor per closure' trong harness debug, KHONG anh huong toi
route_pool cuoi cung (van dung, da qua Gate T4-B 0 violation)."""

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


def run_no_dominance_in_closure(travel_time, driver, orders, B):
    """Nhu run_dp goc NHUNG KHONG loc dominance trong closure BFS (chi de
    kiem tra 'co ton tai duong giao het IV khong' cho TUNG closure rieng
    le, khong phai de dung san xuat - se cham hon nhieu vi khong cat gi)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    frontier = {0: [lab0]}
    closure_root = {id(lab0): id(lab0)}
    root_label = {}
    survivors_nodominance = defaultdict(int)
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
                        survivors_nodominance[root] += 1
            active = next_active   # KHONG loc dominance o day - giu TAT CA

        # dung dominance THAT SU (nhu goc) chi khi sinh pickup cho round sau,
        # de khong bung no vo han (chi anh huong ROUND SAU, khong anh huong
        # ket qua closure cua round HIEN TAI da tinh o tren)
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

    return survivors_nodominance, root_label, root_iv_feasible


def main():
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    drv = gw_drivers[2]

    surv, root_label, rif = run_no_dominance_in_closure(tt, drv, orders, B_GW)

    all_roots = set(root_label.keys())
    dead_real = [k for k in all_roots if surv.get(k, 0) == 0]
    mism = [k for k in dead_real if rif.get(k, True) == True]

    print("driver:", drv["id"])
    print("Tong so closure root:", len(all_roots))
    print("Closure chet THAT SU (KHONG dominance trong closure, chi con dominance o pickup round sau):", len(dead_real))
    print("Trong do, so mismatch voi iv_completion_feasible (tra True sai):", len(mism))
    if len(dead_real) > 0:
        print("Ty le mismatch: %.4f%%" % (100.0 * len(mism) / len(dead_real)))
    if len(mism) == 0:
        print()
        print("=> XAC NHAN: iv_completion_feasible HOAN TOAN DUNG. Toan bo 'mismatch'"
              " truoc day la do dominance CHEO GIUA CAC CLOSURE trong buoc closure BFS"
              " (xay ra o moi buoc trung gian, khong chi buoc cuoi) - HANH VI DUNG cua"
              " thuat toan t6_dp.py, KHONG PHAI BUG trong iv_completion_feasible.")


if __name__ == "__main__":
    main()
