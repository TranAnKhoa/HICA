"""Test_case2_followup.md - Test A2: patch thu IV-completion feasibility
check (chi chay vi Test A cho tin hieu (b): mean_attempts=8.36, 22.4% closure
toan-bo-chet, attempts trung binh 3.69 truoc khi phat hien chet hoan toan).

Y tuong: ngay sau khi 1 label vua pickup xong (truoc khi buoc vao closure
delivery/home), kiem tra THUAN SO HOC (khong sinh label con) - co ton tai it
nhat 1 hoan vi cua IV hien tai ma tat ca deu dung deadline delivery khong.
Neu KHONG hoan vi nao kha thi -> bo qua toan bo closure cho label nay, khong
sinh bat ky label con nao (tiet kiem chinh xac phan "attempts thua" da do
o Test A).

QUAN TRONG - pham vi patch: chi xet DELIVERY cua IV hien tai (chua tinh
home cho OD) - vi day la kiem tra ve "co giao het IV hien tai duoc khong",
KHONG phai "co ve nha kip khong" (home la buoc rieng, da co check tai
_try_home). Voi GW: khi IV rong la hoan chinh - kiem tra nay dung cho ca
GW/OD nhu nhau (chi xet delivery).

Gate bat buoc: so sanh route_pool (canonical signature) ban co patch vs ban
goc tren n<=6, moi B, >=30 instance - PHAI khop 100% truoc khi tin bat ky
so lieu toc do nao.
"""

import itertools
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


def iv_completion_feasible(travel_time, pd, lab):
    """[NGHIEN CUU] Kiem thuan so hoc (KHONG sinh label con): co ton tai
    hoan vi nao cua lab.IV sao cho giao het deu dung deadline_d, xuat phat
    tu (v=lab.v, t=lab.t)? Tra True neu CO IT NHAT 1 hoan vi kha thi (khong
    can biet hoan vi nao - DP goc se tu tim lai khi thuc su mo rong).
    Dung DUNG (p.l, p.e, p.s) tu pd (WNode) - khop dinh nghia _try_delivery."""
    iv_list = list(lab.IV)
    if not iv_list:
        return True
    if len(iv_list) > 7:
        return True   # qua nhieu hoan vi (>5040) - bo qua kiem tra, an toan (khong loai nham)
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


def run_dp_with_iv_patch(travel_time, driver, orders, B, compat_graph=None):
    """Copy TRUNG THUC t6_dp.run_dp. THEM 1 diem chen DUY NHAT: ngay sau
    _try_pickup thanh cong (truoc khi day vao closure/frontier), kiem
    iv_completion_feasible - neu False, bo qua (khong dua vao new_by_key,
    tuong duong 'khong sinh label con', dung nhu thiet ke trong file)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}
    n_pruned_by_iv_patch = 0

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
                    # --- DIEM CHEN Test A2: kiem IV-completion truoc khi giu ---
                    if not iv_completion_feasible(travel_time, pd, new_lab):
                        n_pruned_by_iv_patch += 1
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                next_frontier.extend(D._filter_dominated_labels(labs))
            frontier[touched + 1] = next_frontier

    return complete_by_C, n_pruned_by_iv_patch


def _canonical_pool(complete_by_C, driver):
    """[FIX] xem chu thich cung ten trong test_case2_followup_B.py - dominance
    cuoi trong run_dp CHI loc trong CUNG v, phai loc lai Pareto tren toan bo
    (K,W) khong phan biet v (giong dp_labeling.py::run_pool) moi so sanh
    cong bang duoc voi brute_force.py."""
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
    print("=== GATE Test A2: n<=6, patch vs goc vs brute-force ===")
    n_checked = 0
    n_mismatch = 0
    for n in (3, 4, 5, 6):
        for B_gw in (2, 3, 4):
            for tw in (60, 120):
                for sd in range(3):
                    gen_seed = IG.stable_seed(n, B_gw, 2, tw, 4, sd, "testA2_gate")
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=4,
                        seed=gen_seed, tau=TAU, spatial_mode=SPATIAL)
                    for drv in drivers:
                        B_eff = B_gw if drv["cls"] == "GW" else 2
                        res_orig = D.run_dp(tt, drv, orders, B_eff, use_dominance=True)
                        pool_orig = _canonical_pool(res_orig["complete_by_C"], drv)

                        complete_patch, _ = run_dp_with_iv_patch(tt, drv, orders, B_eff)
                        pool_patch = _canonical_pool(complete_patch, drv)

                        pool_brute_raw = BF.brute_pool_for_driver(tt, drv, orders, B_gw, 2)
                        pool_brute = {S: sorted(set((round(K, 6), round(W, 6)) for K, W in front))
                                       for S, front in pool_brute_raw.items()}

                        n_checked += 1
                        if pool_orig != pool_patch or pool_orig != pool_brute:
                            n_mismatch += 1
                            print("  !! MISMATCH n=%d B_gw=%d tw=%d seed=%d driver=%s"
                                  % (n, B_gw, tw, sd, drv["id"]))
                            print("     orig !=patch:", pool_orig != pool_patch,
                                  " orig!=brute:", pool_orig != pool_brute)
    print("Instances checked: %d   Mismatches: %d" % (n_checked, n_mismatch))
    return n_mismatch == 0


def speed_compare():
    print("\n=== TEST A2: so sanh wall-clock (goc vs patch IV-completion) tren cell nong ===")
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
    print("Ban GOC : %.2fs" % t_orig)

    t0 = time.time()
    total_pruned = 0
    for drv in gw_drivers:
        _, n_pruned = run_dp_with_iv_patch(tt, drv, orders, B_GW)
        total_pruned += n_pruned
    t_patch = time.time() - t0
    print("Ban PATCH: %.2fs  (so label bi cat boi IV-completion: %d)" % (t_patch, total_pruned))

    speedup = t_orig / t_patch if t_patch > 0 else float("inf")
    print("Speedup (goc/patch): %.3fx" % speedup)


def main():
    ok = gate_check_n6()
    if not ok:
        print("\n*** GATE FAILED - Test A2 patch UNSAFE, KHONG bao cao speedup ***")
        return 1
    print("\nGATE PASS - route_pool khop 100% (goc == patch == brute-force).")
    speed_compare()
    return 0


if __name__ == "__main__":
    sys.exit(main())
