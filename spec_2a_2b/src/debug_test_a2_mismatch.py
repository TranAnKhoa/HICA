"""Debug: tai sao Test A do 22.4% closure toan-bo-chet nhung Test A2 patch
cat 0 label? Gia thuyet chinh: dinh nghia "chet" trong Test A bao gom ca
chet o buoc _try_home (het han tau/deadline ve nha), ma iv_completion_feasible
(Test A2) CHI kiem tra delivery cua IV hien tai, KHONG kiem tra home (theo
dung docstring da ghi trong test_case2_followup_A2.py). Neu dung, day la
scope mismatch da biet truoc (khong phai bug ngam), khong phai loi logic.

Script nay: chay lai closure tracking (nhu Test A) + parallel goi tay
iv_completion_feasible tren TUNG label vua pickup (closure root), phan loai
closure "chet" thanh 2 nhom: (1) chet vi khong hoan vi IV nao kha thi (patch
LE RA phai bat duoc) vs (2) chet CHI vi buoc home that bai (patch KHONG the
bat, ngoai pham vi thiet ke).
"""

import itertools
import os
import sys
import time
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
    """COPY Y HET tu test_case2_followup_A2.py - khong doi logic."""
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


def run_dp_with_full_tracking(travel_time, driver, orders, B, compat_graph=None):
    """Nhu Test A (closure_attempts/deaths/survivors theo closure_root) +
    THEM: ghi lai ket qua iv_completion_feasible tai THOI DIEM label vua
    duoc pickup (= closure root) - de doi chieu voi ket qua thuc te cua
    closure do (chet hoan toan hay khong, VA chet o dau: delivery hay home)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}

    closure_root = {id(lab0): id(lab0)}
    closure_attempts = defaultdict(int)
    closure_survivors = defaultdict(int)
    closure_home_death = defaultdict(int)   # so lan _try_home that bai trong closure nay
    closure_home_attempt = defaultdict(int)  # so lan _try_home duoc thu trong closure nay
    root_iv_feasible = {}   # closure_root_id -> iv_completion_feasible(label vua pickup)

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
                    closure_attempts[root] += 1
                    new_lab = D._try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        continue
                    closure_root[id(new_lab)] = root
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1 and not has_home:
                        complete_by_C[new_lab.Cd].append(new_lab)
                        closure_survivors[root] += 1
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    closure_attempts[root] += 1
                    closure_home_attempt[root] += 1
                    new_lab = D._try_home(travel_time, driver, home, lab)
                    if new_lab is None:
                        closure_home_death[root] += 1
                    else:
                        complete_by_C[new_lab.Cd].append(new_lab)
                        closure_survivors[root] += 1

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
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B,
                                            compat_graph=compat_graph)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                for lb in kept:
                    rid = id(lb)
                    closure_root[rid] = rid
                    root_iv_feasible[rid] = iv_completion_feasible(travel_time, pd, lb)
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    return (closure_attempts, closure_survivors, closure_home_death,
            closure_home_attempt, root_iv_feasible)


def main():
    t0 = time.time()
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    print("Cell: n=%d B_gw=%d tw=%d seed=%d  n_gw_drivers=%d (GW co has_home=False -> "
          "khong co buoc home, chi la sanity check)" % (N, B_GW, TW, SEED, len(gw_drivers)))

    # GW driver khong co home node (has_home=False trong build_walk_nodes cho GW),
    # nen closure_home_death se luon = 0 cho GW. Neu Test A do tren GW ma van co
    # mismatch, gia thuyet "home la nguyen nhan" SAI - phai tim nguyen nhan khac.
    agg_attempts = defaultdict(int)
    agg_survivors = defaultdict(int)
    agg_home_death = defaultdict(int)
    agg_home_attempt = defaultdict(int)
    agg_iv_feasible = {}

    for i, drv in enumerate(gw_drivers):
        ca, cs, chd, cha, rif = run_dp_with_full_tracking(tt, drv, orders, B_GW)
        for k, v in ca.items():
            agg_attempts[(drv["id"], k)] = v
        for k, v in cs.items():
            agg_survivors[(drv["id"], k)] = v
        for k, v in chd.items():
            agg_home_death[(drv["id"], k)] = v
        for k, v in cha.items():
            agg_home_attempt[(drv["id"], k)] = v
        for k, v in rif.items():
            agg_iv_feasible[(drv["id"], k)] = v
        print("  driver %s done  total_elapsed=%.1fs" % (drv["id"], time.time() - t0))

    all_roots = set(agg_attempts.keys())
    n_closures = len(all_roots)
    all_dead = [k for k in all_roots if agg_survivors.get(k, 0) == 0]
    n_all_dead = len(all_dead)

    # phan loai closure chet: co dung _try_home khong, va iv_feasible du doan gi
    dead_with_home_attempt = [k for k in all_dead if agg_home_attempt.get(k, 0) > 0]
    dead_no_home_attempt = [k for k in all_dead if agg_home_attempt.get(k, 0) == 0]
    dead_killed_purely_by_home = [k for k in dead_with_home_attempt
                                    if agg_home_death.get(k, 0) == agg_home_attempt.get(k, 0)
                                    and agg_home_attempt.get(k, 0) > 0]

    # Doi chieu: trong nhom "chet, KHONG dung home" (dead_no_home_attempt),
    # patch LE RA phai bat duoc (iv_feasible=False). Neu khong -> bug that.
    mismatch_no_home = [k for k in dead_no_home_attempt if agg_iv_feasible.get(k, True) == True]
    n_mismatch_no_home = len(mismatch_no_home)

    print()
    print("=== KET QUA PHAN LOAI ===")
    print("Tong so closure:                          %d" % n_closures)
    print("Closure chet hoan toan (0 survivor):       %d (%.1f%%)" % (n_all_dead, 100*n_all_dead/n_closures))
    print("  - trong do co dung buoc _try_home:       %d" % len(dead_with_home_attempt))
    print("  - trong do KHONG dung buoc home:         %d" % len(dead_no_home_attempt))
    print("  - chet nguyen nhan la home (moi lan thu home deu that bai): %d" % len(dead_killed_purely_by_home))
    print()
    print("Trong nhom 'chet, KHONG dung home' (patch LE RA phai bat duoc):")
    print("  So closure:                              %d" % len(dead_no_home_attempt))
    print("  So closure ma iv_completion_feasible tra SAI (True, tuc KHONG bat duoc): %d" % n_mismatch_no_home)
    if dead_no_home_attempt:
        print("  -> ty le mismatch trong nhom nay: %.2f%%" % (100*n_mismatch_no_home/len(dead_no_home_attempt)))
    print()
    if n_mismatch_no_home > 0:
        print("*** CO BUG THAT: iv_completion_feasible tra True sai cho closure da chet"
              " ma khong lien quan gi den home. Can debug ham nay. ***")
        print("Vi du 3 closure mismatch dau tien (driver_id, root_id):")
        for k in mismatch_no_home[:3]:
            print("   ", k, " attempts=", agg_attempts[k], " home_attempt=", agg_home_attempt.get(k,0))
    else:
        print("KHONG co mismatch ngoai pham vi home -> gia thuyet DUNG: toan bo 22.4%"
              " 'chet' trong Test A la do GW/OD khong co home (GW: has_home=False luon)"
              " hoac do buoc home that bai (OD), CA HAI deu NGOAI PHAM VI thiet ke cua"
              " patch A2 (chi kiem tra delivery IV, khong kiem tra home) - KHONG PHAI BUG.")

    print()
    print("elapsed_total=%.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
