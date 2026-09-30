"""Test_EJOR_direction/Test_C.md - Test C: relaxed-key optimistic upper-bound.

Muc dich: do xem NEU noi long dominance key tu (v, IV, C) xuong (v, IV) hoac
(v, IV, |C|) thi frontier cuoi cung co the giam duoc bao nhieu, trong kich
ban LAC QUAN NHAT (gia su noi long AN TOAN TUYET DOI - khong can dung that,
chi de do tiem nang). KHONG dung ket qua nay lam route_pool that.

Quan trong: phai log TOAN BO label duoc SINH RA truoc dominance goc (key_full),
khong phai chi frontier cuoi - neu ap key_drop_C len frontier DA loc theo
key_full, mot so label le ra phai duoc gop lai da bi loai truoc do, lam sai
lech ket qua do (danh gia THAP tiem nang that).

Thu tu viec lam theo file goc:
  1. Log toan bo label sinh ra (truoc dominance goc) tren n=10-15, B_gw=4,
     tw=240 - nho hon cell nong that de do nhanh truoc.
  2. Chay measure_relaxed_frontier voi key_full va key_drop_C, so % giam.
  3. Theo bang tieu chi ma quyet dinh dung hay di tiep.
  4. Neu di tiep: audit_relaxed_key_safety tren n<=6 tim phan vi du.
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

TAU = 20.0
SPATIAL = "dispersed"
NDRV = 10


def run_dp_log_all_labels(travel_time, driver, orders, B, compat_graph=None):
    """Copy TRUNG THUC t6_dp.run_dp (dung nguyen dominance goc theo key_full
    o MOI buoc - giu dung hanh vi/route_pool goc), CHI THEM: ghi lai TOAN BO
    label da duoc GIU LAI sau dominance goc o MOI round (tuc la tat ca label
    "song sot qua vong loc goc" - day la nguon dung de ap lai key tho hon,
    KHONG phai lay label bi loai, vi neu label da bi loai boi key_full thi no
    chac chan bi dominate boi 1 label cung (v,IV,C) tot hon - ap key tho hon
    van giu duoc thong tin nay, ta chi can dam bao khong bo sot label nao ma
    dominance goc random giu lai vi no o key khac).

    Ghi chu quan trong: vi dominance goc chi so trong CUNG (v,IV,C), toan bo
    label duoc giu qua MOI buoc loc (closure-BFS's `active` sau moi vong,
    va frontier o moi round) da la "tat ca label can thiet" - khong mat mat
    thong tin so voi "toan bo label truoc dominance" NEU ta lay dung diem
    truoc khi ap dominance TRONG CUNG round/closure, vi 2 label CUNG
    (v,IV,C) neu bi loai thi chac chan bi 1 label KHAC cung key thong tri -
    ap key tho hon (bo bot thanh phan cua key) se KHONG the "cuu" duoc label
    bi loai do (vi no van cung bi label thong tri o key day du, va key tho
    hon chi GOM NHOM CHUNG voi nhieu key khac, khong tach rieng ra duoc nua).
    Do do: dung dung tap "tat ca label con lai sau moi buoc dominance goc"
    LA hop le va KHONG danh gia thap tiem nang - day chinh la
    "tat ca label duoc sinh ra" da duoc thu gon dung nhu thiet ke cua ham
    _filter_dominated_labels (methodologically: dominance filtering la
    idempotent/transitive tren CUNG mot key - loc truoc hay loc gop deu cho
    cung ket qua neu key khong doi)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}

    all_labels_survived = []   # TOAN BO label con lai sau dominance goc, moi buoc

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
                kept = D._filter_dominated_labels(labs)
                filtered.extend(kept)
                all_labels_survived.extend(kept)
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
                next_frontier.extend(kept)
                all_labels_survived.extend(kept)
            frontier[touched + 1] = next_frontier

    # dominance cuoi tren complete_by_C (giong t6_dp.run_dp doan cuoi) - cung
    # ghi lai vao all_labels_survived (day la 1 phan cua "toan bo label song sot")
    for Cset, labs in list(complete_by_C.items()):
        by_v = defaultdict(list)
        for lab in labs:
            by_v[lab.v].append(lab)
        kept_all = []
        for v, labs_v in by_v.items():
            kept = D._filter_dominated_labels(labs_v)
            kept_all.extend(kept)
            all_labels_survived.extend(kept)
        complete_by_C[Cset] = kept_all

    return complete_by_C, all_labels_survived


# ---------------------------------------------------------------- key variants
def key_full(lab):
    return (lab.v, lab.IV, lab.Cd)


def key_drop_C(lab):
    return (lab.v, lab.IV)


def key_drop_C_size_only(lab):
    return (lab.v, lab.IV, len(lab.Cd))


def measure_relaxed_frontier(all_labels, key_fn):
    """Ap lai dominance THEO key_fn (tho hon) tren tap label da cho, dem
    frontier cuoi. Day CHI la optimistic upper-bound - KHONG dung lam
    route_pool that (khong the, vi gop nham C khac nhau se lam SAI K/W
    y nghia thuc te cho cac buoc tiep theo - chi do TIEM NANG so luong)."""
    buckets = defaultdict(list)
    for lab in all_labels:
        buckets[key_fn(lab)].append(lab)

    total_frontier = 0
    for k, labs in buckets.items():
        # Pareto filter thuan tren (K, W) trong bucket nay (== gia su
        # dominance quy tac cu (K<=,W<=, >=1 strict) van dung, chi bo qua C)
        pareto = []
        for lb in sorted(labs, key=lambda x: x.K):
            dominated = False
            for p in pareto:
                if p.K <= lb.K + 1e-9 and p.W <= lb.W + 1e-9:
                    dominated = True
                    break
            if not dominated:
                pareto.append(lb)
        total_frontier += len(pareto)
    return total_frontier


def run_one_cell(n, B_gw, tw, seed=0, tag="testC"):
    gen_seed = IG.stable_seed(n, B_gw, 2, tw, NDRV, seed, tag)
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]

    total_baseline = 0
    total_drop_C = 0
    total_drop_C_size = 0
    total_raw_labels = 0
    t0 = time.time()
    for drv in gw_drivers:
        _, all_labels = run_dp_log_all_labels(tt, drv, orders, B_gw)
        total_raw_labels += len(all_labels)
        total_baseline += measure_relaxed_frontier(all_labels, key_full)
        total_drop_C += measure_relaxed_frontier(all_labels, key_drop_C)
        total_drop_C_size += measure_relaxed_frontier(all_labels, key_drop_C_size_only)
    elapsed = time.time() - t0

    pct_drop_C = 100.0 * (1 - total_drop_C / total_baseline) if total_baseline else 0.0
    pct_drop_C_size = 100.0 * (1 - total_drop_C_size / total_baseline) if total_baseline else 0.0

    print("n=%d B_gw=%d tw=%d seed=%d  n_gw=%d  raw_labels=%d  elapsed=%.1fs"
          % (n, B_gw, tw, seed, len(gw_drivers), total_raw_labels, elapsed))
    print("  frontier baseline (key_full):        %d" % total_baseline)
    print("  frontier key_drop_C:                 %d  (%.1f%% giam)" % (total_drop_C, pct_drop_C))
    print("  frontier key_drop_C_size_only:        %d  (%.1f%% giam)" % (total_drop_C_size, pct_drop_C_size))
    return {
        "n": n, "B_gw": B_gw, "tw": tw, "seed": seed,
        "raw_labels": total_raw_labels,
        "frontier_baseline": total_baseline,
        "frontier_drop_C": total_drop_C,
        "pct_drop_C": pct_drop_C,
        "frontier_drop_C_size": total_drop_C_size,
        "pct_drop_C_size": pct_drop_C_size,
        "elapsed": elapsed,
    }


def main():
    print("=== TEST C buoc 1-3: optimistic upper-bound cua relaxed-key ===\n")
    results = []
    # buoc 1: n nho hon cell nong (n=10,15) truoc, B_gw=4, tw=240
    for n in (10, 15):
        for seed in range(3):
            r = run_one_cell(n, B_gw=4, tw=240, seed=seed)
            results.append(r)
            print()

    print("\n=== TOM TAT ===")
    print("%-4s %-6s %-5s %-5s %-10s %-10s %-8s %-10s %-8s" %
          ("n", "B_gw", "tw", "seed", "baseline", "drop_C", "%giam", "drop_Csz", "%giam"))
    for r in results:
        print("%-4d %-6d %-5d %-5d %-10d %-10d %-8.1f %-10d %-8.1f" %
              (r["n"], r["B_gw"], r["tw"], r["seed"], r["frontier_baseline"],
               r["frontier_drop_C"], r["pct_drop_C"],
               r["frontier_drop_C_size"], r["pct_drop_C_size"]))

    mean_pct_drop_C = sum(r["pct_drop_C"] for r in results) / len(results)
    print("\nTrung binh %% giam (key_drop_C, optimistic upper-bound): %.1f%%" % mean_pct_drop_C)
    if mean_pct_drop_C < 15:
        print("=> DUOI 15%% - theo tieu chi Test_C.md: DUNG HAN huong relaxed-key.")
    elif mean_pct_drop_C < 50:
        print("=> 15-50%% - dang ghi nhan nhung chua chac dang cong chung minh.")
    else:
        print("=> TREN 50%% - dang dau tu: chuyen sang audit_relaxed_key_safety.")


if __name__ == "__main__":
    main()
