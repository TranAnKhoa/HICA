"""Test_case2_followup.md - Test A: attempts_per_closure.

Muc dich: dong dut diem cau hoi (a) vs (b) - moi label CHA (vua duoc pickup,
chuan bi buoc vao closure delivery/home lien tiep trong CUNG round) bi thu
bao nhieu thu tu giao truoc khi TAT CA chet hoac co cai song.

(a) mean_attempts ~ 1.0-1.5  -> khong co gi de toi uu, dong han y tuong
    IV-completion check (Test A2).
(b) mean_attempts cao ro ret (>3-4), dac biet trong nhom closure TOAN-CHET
    -> dang thu patch nho o Test A2.

KHONG sua t6_dp.py - REIMPLEMENT logic run_dp TRUNG THUC (dua tren
research_case1_vs_case2.py da doi chieu khop 100% voi ban goc qua smoke
test truoc do), CHI THEM dem attempts/deaths/survivors theo closure_root
(= id() cua label VUA duoc pickup, diem bat dau closure rieng cua no).
"""

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

# cell nong nhat da xac nhan qua run_2a_stepB.py + nghien cuu Case 1 vs Case 2
N, B_GW, TW, SEED, NDRV = 20, 4, 240, 0, 10
TAU = 20.0
SPATIAL = "dispersed"


def run_dp_with_closure_tracking(travel_time, driver, orders, B, compat_graph=None):
    """Copy TRUNG THUC logic t6_dp.run_dp. Them dem closure_attempts/
    closure_deaths/closure_survivors theo closure_root_id = id(label VUA
    duoc pickup, tuc la label nguon cua 1 lan chay closure delivery/home)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}

    # closure_root[id(label)] = id() cua label GOC cua closure hien tai ma
    # label nay dang tham gia (moi label trong 1 chuoi delivery lien tiep
    # deu ke thua closure_root tu label cha truc tiep cua no trong closure).
    closure_root = {id(lab0): id(lab0)}

    closure_attempts = defaultdict(int)
    closure_deaths = defaultdict(int)
    closure_survivors = defaultdict(int)

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
                        closure_deaths[root] += 1
                        continue
                    closure_root[id(new_lab)] = root
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1 and not has_home:
                        complete_by_C[new_lab.Cd].append(new_lab)
                        closure_survivors[root] += 1
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    closure_attempts[root] += 1
                    new_lab = D._try_home(travel_time, driver, home, lab)
                    if new_lab is None:
                        closure_deaths[root] += 1
                    else:
                        complete_by_C[new_lab.Cd].append(new_lab)
                        closure_survivors[root] += 1
                elif not lab.IV and touched == 0 and len(lab.Cd) == 0:
                    pass   # label goc rong, khong tinh la closure

            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(D._filter_dominated_labels(labs))
            active = filtered

        # --- pickup: sinh sang touched+1, MOI label sinh ra o day la mot
        # closure_root MOI (diem bat dau closure cua rieng no) ---
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
                    closure_root[id(lb)] = id(lb)   # goc closure moi cua rieng no
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    return closure_attempts, closure_deaths, closure_survivors, complete_by_C


def main():
    t0 = time.time()
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    print("Cell: n=%d B_gw=%d tw=%d seed=%d  n_gw_drivers=%d" % (N, B_GW, TW, SEED, len(gw_drivers)))

    agg_attempts = defaultdict(int)
    agg_deaths = defaultdict(int)
    agg_survivors = defaultdict(int)
    for i, drv in enumerate(gw_drivers):
        t_drv = time.time()
        ca, cd, cs, _ = run_dp_with_closure_tracking(tt, drv, orders, B_GW)
        for k, v in ca.items():
            agg_attempts[k] += v
        for k, v in cd.items():
            agg_deaths[k] += v
        for k, v in cs.items():
            agg_survivors[k] += v
        print("  driver %d/%d done  elapsed_driver=%.1fs  total_elapsed=%.1fs"
              % (i + 1, len(gw_drivers), time.time() - t_drv, time.time() - t0))

    n_closures = len(agg_attempts)
    if n_closures == 0:
        print("Khong co closure nao duoc ghi nhan.")
        return

    mean_attempts = sum(agg_attempts.values()) / n_closures
    max_attempts = max(agg_attempts.values())
    all_dead = [k for k in agg_attempts if agg_survivors.get(k, 0) == 0]
    n_all_dead = len(all_dead)
    mean_attempts_all_dead = (sum(agg_attempts[k] for k in all_dead) / n_all_dead
                               if n_all_dead else 0.0)

    print()
    print("=== TEST A: attempts_per_closure ===")
    print("So closure quan sat:                 %d" % n_closures)
    print("Trung binh attempts/closure:          %.3f" % mean_attempts)
    print("Max attempts trong 1 closure:         %d" % max_attempts)
    print("So closure toan-bo-chet (0 survivor): %d (%.1f%%)"
          % (n_all_dead, 100 * n_all_dead / n_closures))
    print("Attempts trung binh CHI trong closure toan-chet: %.3f" % mean_attempts_all_dead)
    print()
    if mean_attempts < 1.5:
        print("KET LUAN: mean_attempts ~1.0-1.5 -> kich ban (a), DONG HAN y tuong IV-completion.")
    else:
        print("KET LUAN: mean_attempts cao (%.2f) -> kich ban (b) co that, dang thu Test A2." % mean_attempts)
    print("elapsed_total=%.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main()
