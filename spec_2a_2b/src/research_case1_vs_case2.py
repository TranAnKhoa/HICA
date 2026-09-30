"""Nghien cuu doc lap (KHONG dung trong pipeline) - phan biet Case 1 (label
chet MUON - infeasibility phat hien tre, co the sua bang resource-extension
bound kieu Ropke & Cordeau 2009) voi Case 2 (frontier Pareto bung no vi cac
label khong the dominate lan nhau - gioi han cau truc, khong sua duoc bang
pruning, chi bang engineering toc do so sanh).

Do 3 loai theo TUNG ROUND (touched = 0..B), dung dinh nghia cua nguoi dung:
  killed_by_feasibility  : so lan _try_pickup/_try_delivery tra ve None
                            (vi pham time-window/capacity - CASE 1 candidate)
  killed_by_dominance    : so label bi loai boi _filter_dominated_labels
                            (bi thong tri - dominance hoat dong binh thuong,
                            KHONG phai Case 2)
  survived_to_next_round : so label con song sau dominance, di tiep sang
                            round sau - day la UNG VIEN Case 2 neu no TIEP
                            TUC ton tai song song va tang dan theo round.

Phan tich sau khi do xong (theo dung tieu chi nguoi dung dua ra):
  - Neu killed_by_feasibility gan bang 0 o round sau (hau nhu moi thu deu
    feasible) TRONG KHI survived tang nhanh -> Case 2 chiem uu the, khong
    sua duoc bang pruning.
  - Neu killed_by_feasibility van cao o round sau (nhieu nhanh van dang bi
    loai vi infeasible) NHUNG phai mo rong toi tan do moi phat hien -> Case 1
    chiem uu the, dang dau tu huong resource-extension-bound.

KHONG sua t6_dp.py (giu nguyen ban da PASS Gate T4-B/Gate 0) - script nay
REIMPLEMENT logic run_dp mot cach TRUNG THUC (cung thu tu, cung dieu kien,
copy tu t6_dp.py) chi THEM instrumentation (dem), khong doi hanh vi/logic.
"""

import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp as D
import t2_core as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "research_case1_vs_case2.csv")
OUT_BY_ROUND = os.path.join(ROOT, "results", "research_case1_vs_case2_by_round.csv")

# [Yeu cau nguoi dung] target dung vung "nong" da xac nhan qua 2a_stepB
# (runtime bung no that): n=20/30, B_gw=4-5, ho tro doi chieu voi tw=240
# (noi PCF that bai hoan toan va lan chay dau tien da lo dau hieu
# case2_dominant o B_gw=3/tw=240) - KHONG quet lai toan bo luoi rong nhu lan
# truoc (lang phi thoi gian o vung khong quan trong).
N_GRID = (20, 30)
BGW_GRID = (3, 4, 5)
TW_GRID = (60, 120, 240)   # bo tw=30 (da xac nhan case1_present ro rang o do, khong can lap lai)
SEEDS = range(3)
NDRV = 10
TAU = 20.0
SPATIAL = "dispersed"


def run_dp_instrumented(travel_time, driver, orders, B, compat_graph=None):
    """Copy TRUNG THUC logic t6_dp.run_dp (cung thu tu goi, cung dieu kien
    dung/sai) - THEM instrumentation:
      - dem killed_by_feasibility / killed_by_dominance / survived theo tung round
      - born_round[id(lab)]: round (touched) ma label do duoc SINH RA (dua vao
        frontier), dung de tinh "so round da song" khi 1 lan mo rong CU THE
        cua no bi tu choi vi feasibility - tra loi cau hoi nguoi dung: cong
        da dau tu (tinh bang so round) truoc khi phat hien nhanh nay chet o
        buoc tiep theo. Label goc (touched=0) co born_round=0.
    Khong doi bat ky nhanh re logic nao cua t6_dp.py."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}
    born_round = {id(lab0): 0}

    by_round = []   # list dict: touched, killed_feas, killed_dom, survived, attempted
    death_age_histogram = defaultdict(int)   # {age_in_rounds: count} - CHI cho killed_by_feasibility

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue

        killed_feas_this_round = 0
        killed_dom_this_round = 0
        attempted_this_round = 0

        # --- closure: delivery/home (khong doi touched - "tuoi" cua label
        # cha van la touched hien tai, delivery/home khong tang touched) ---
        active = list(labs_here)
        closure_all = []
        while active:
            next_active = []
            for lab in active:
                closure_all.append(lab)
                parent_age = touched - born_round.get(id(lab), touched)
                for j in sorted(lab.IV):
                    attempted_this_round += 1
                    new_lab = D._try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        killed_feas_this_round += 1
                        death_age_histogram[parent_age] += 1
                        continue
                    born_round[id(new_lab)] = born_round.get(id(lab), touched)
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1 and not has_home:
                        complete_by_C[new_lab.Cd].append(new_lab)
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    attempted_this_round += 1
                    new_lab = D._try_home(travel_time, driver, home, lab)
                    if new_lab is None:
                        killed_feas_this_round += 1
                        death_age_histogram[parent_age] += 1
                    else:
                        complete_by_C[new_lab.Cd].append(new_lab)

            # dominance tren closure (delivery/home khong doi touched)
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                before = len(labs)
                kept = D._filter_dominated_labels(labs)
                killed_dom_this_round += (before - len(kept))
                filtered.extend(kept)
            active = filtered

        survived_here = len(closure_all)

        # --- pickup: sinh sang touched+1 (day la buoc TANG touched, label
        # moi sinh ra o day co born_round = touched+1) ---
        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                parent_age = touched - born_round.get(id(lab), touched)
                for j in order_ids:
                    attempted_this_round += 1
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B,
                                            compat_graph=compat_graph)
                    if new_lab is None:
                        killed_feas_this_round += 1
                        death_age_histogram[parent_age] += 1
                        continue
                    new_by_key[new_lab.key()].append(new_lab)

            next_frontier = []
            for k, labs in new_by_key.items():
                before = len(labs)
                kept = D._filter_dominated_labels(labs)
                killed_dom_this_round += (before - len(kept))
                for lab in kept:
                    born_round[id(lab)] = touched + 1
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier
            survived_to_next = len(next_frontier)
        else:
            survived_to_next = 0

        by_round.append(dict(
            touched=touched,
            attempted=attempted_this_round,
            killed_by_feasibility=killed_feas_this_round,
            killed_by_dominance=killed_dom_this_round,
            frontier_at_this_round=survived_here,
            survived_to_next_round=survived_to_next,
        ))

    return by_round, complete_by_C, death_age_histogram


def run_one(n, B_gw, tw, seed):
    gen_seed = IG.stable_seed(n, B_gw, 2, tw, NDRV, seed, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]

    agg_by_round = defaultdict(lambda: dict(attempted=0, killed_by_feasibility=0,
                                             killed_by_dominance=0,
                                             frontier_at_this_round=0,
                                             survived_to_next_round=0))
    agg_death_age = defaultdict(int)
    t0 = time.time()
    for drv in gw_drivers:
        by_round, _, death_age = run_dp_instrumented(tt, drv, orders, B_gw)
        for rec in by_round:
            a = agg_by_round[rec["touched"]]
            a["attempted"] += rec["attempted"]
            a["killed_by_feasibility"] += rec["killed_by_feasibility"]
            a["killed_by_dominance"] += rec["killed_by_dominance"]
            a["frontier_at_this_round"] += rec["frontier_at_this_round"]
            a["survived_to_next_round"] += rec["survived_to_next_round"]
        for age, cnt in death_age.items():
            agg_death_age[age] += cnt
    elapsed = time.time() - t0

    rows_by_round = []
    for touched in sorted(agg_by_round):
        a = agg_by_round[touched]
        feas_rate = (a["killed_by_feasibility"] / a["attempted"]) if a["attempted"] else 0.0
        rows_by_round.append(dict(
            n=n, B_gw=B_gw, tw_width=tw, seed=seed, touched=touched,
            attempted=a["attempted"],
            killed_by_feasibility=a["killed_by_feasibility"],
            killed_by_dominance=a["killed_by_dominance"],
            frontier_at_this_round=a["frontier_at_this_round"],
            survived_to_next_round=a["survived_to_next_round"],
            feasibility_kill_rate=round(feas_rate, 6),
        ))

    # verdict don gian: so sanh feas_kill_rate o round DAU (touched=0/1) vs
    # round CUOI (touched=B-1, ngay truoc pickup cuoi) - neu giam manh ve
    # gan 0 trong khi frontier van tang -> Case 2 chiem uu the.
    if len(rows_by_round) >= 2:
        first = rows_by_round[0]
        last = rows_by_round[-1]
        verdict = "case2_dominant" if (last["feasibility_kill_rate"] < 0.05
                                        and last["frontier_at_this_round"] >
                                        first["frontier_at_this_round"]) else "case1_present"
    else:
        verdict = "insufficient_rounds"

    # death-age histogram: age=0 nghia la "chet ngay o lan mo rong dau tien
    # sau khi sinh ra" (khong co gi de look-ahead cat som hon - da toi uu).
    # age lon nghia la label song qua nhieu round roi moi chet - "cong lang
    # phi" that su, dang de look-ahead/resource-extension-bound cat som.
    total_deaths = sum(agg_death_age.values())
    mean_death_age = (sum(age * cnt for age, cnt in agg_death_age.items()) / total_deaths
                       if total_deaths else 0.0)
    age0_frac = (agg_death_age.get(0, 0) / total_deaths) if total_deaths else 0.0
    hist_str = "|".join("%d:%d" % (age, cnt) for age, cnt in sorted(agg_death_age.items()))

    summary = dict(
        n=n, B_gw=B_gw, tw_width=tw, seed=seed,
        elapsed_s=round(elapsed, 3),
        feas_kill_rate_round0=rows_by_round[0]["feasibility_kill_rate"] if rows_by_round else None,
        feas_kill_rate_lastround=rows_by_round[-1]["feasibility_kill_rate"] if rows_by_round else None,
        frontier_round0=rows_by_round[0]["frontier_at_this_round"] if rows_by_round else None,
        frontier_lastround=rows_by_round[-1]["frontier_at_this_round"] if rows_by_round else None,
        verdict=verdict,
        total_feasibility_deaths=total_deaths,
        mean_death_age_rounds=round(mean_death_age, 4),
        death_age0_fraction=round(age0_frac, 6),
        death_age_histogram=hist_str,
    )
    return summary, rows_by_round


FIELDS_SUMMARY = ["n", "B_gw", "tw_width", "seed", "elapsed_s",
                   "feas_kill_rate_round0", "feas_kill_rate_lastround",
                   "frontier_round0", "frontier_lastround", "verdict",
                   "total_feasibility_deaths", "mean_death_age_rounds",
                   "death_age0_fraction", "death_age_histogram"]
FIELDS_BY_ROUND = ["n", "B_gw", "tw_width", "seed", "touched", "attempted",
                    "killed_by_feasibility", "killed_by_dominance",
                    "frontier_at_this_round", "survived_to_next_round",
                    "feasibility_kill_rate"]


def _load_done():
    seen = set()
    if os.path.isfile(OUT):
        with open(OUT, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B_gw"]), int(r["tw_width"]), int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    t_start = time.time()
    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already done." % len(already))

    total = len(N_GRID) * len(BGW_GRID) * len(TW_GRID) * len(SEEDS)
    done = 0
    with open(OUT, mode, newline="", encoding="utf-8") as f, \
         open(OUT_BY_ROUND, mode, newline="", encoding="utf-8") as fbr:
        w = csv.DictWriter(f, fieldnames=FIELDS_SUMMARY)
        wbr = csv.DictWriter(fbr, fieldnames=FIELDS_BY_ROUND)
        if not already:
            w.writeheader()
            wbr.writeheader()
        for n in N_GRID:
            for B_gw in BGW_GRID:
                for tw in TW_GRID:
                    for sd in SEEDS:
                        if (n, B_gw, tw, sd) in already:
                            done += 1
                            continue
                        summary, rows_by_round = run_one(n, B_gw, tw, sd)
                        w.writerow(summary)
                        f.flush()
                        for r in rows_by_round:
                            wbr.writerow(r)
                        fbr.flush()
                        done += 1
                    print("  [%d/%d] n=%d Bgw=%d tw=%d  verdict(last_seed)=%s  "
                          "feas_kill_r0=%.1f%%->lastround=%.1f%%  elapsed=%.1fs"
                          % (done, total, n, B_gw, tw, summary["verdict"],
                             (summary["feas_kill_rate_round0"] or 0) * 100,
                             (summary["feas_kill_rate_lastround"] or 0) * 100,
                             time.time() - t_start))
    print("\n=== CASE1 vs CASE2 RESEARCH DONE ===  elapsed=%.1fs" % (time.time() - t_start))


if __name__ == "__main__":
    main()
