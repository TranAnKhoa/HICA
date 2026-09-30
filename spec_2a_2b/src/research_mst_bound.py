"""Nghien cuu doc lap (KHONG dung trong pipeline 2a/2b/Gate) - so sanh do
manh cua PCF (Pairwise Compatibility Filter, new03.md) voi mot can duoi hinh
hoc kieu MST/1-tree cho GW (khong co tau, khong co "diem neo" nhu OD).

Y tuong: voi tap S order ma mot driver GW co the nhan, thoi gian route toi
thieu de tham HET cac diem pickup+delivery cua S (bo qua rang buoc precedence
va time-window, chi hinh hoc/khoang cach) duoc can duoi boi trong luong cay
khung nho nhat (MST) tren tap {diem xuat phat} U {pickup,delivery cua S}.

Neu MST_weight(S) + thoi diem bat dau som nhat > deadline muon nhat trong S,
S chac chan infeasible (VI: bat ky thu tu tham nao cung phai di ít nhat bang
trong luong MST - cay khung la can duoi chuan cho bai toan TSP-path tren do
thi metric). Day la dieu kien CAN, khong DU - giong tinh chat cua PCF.

Muc tieu do: voi CUNG mot tap instance (GW, B_gw, tw quet), tinh ty le % tap
S bi loai boi (a) PCF rieng, (b) MST-bound rieng, (c) ca hai, (d) hop cua ca
hai - de xem MST co "bind" (cat duoc nhieu hon) PCF khong, dac biet o vung
tw rong (da xac nhan PCF yeu nhat o do qua run_pcf_benefit.py).

KHONG sua t6_dp.py/dp_labeling.py/instance_gen.py - script nay tu doc lai
instance qua instance_gen.generate_instance() (read-only) va tu cai dat MST
rieng (Prim, tham khao experiments/T4/t4_core.py::_mst_weight ve thuat toan,
nhung viet lai doc lap vi khong gian bai toan khac - o day co pickup/delivery
tach biet, khong phai driver_node don).
"""

import csv
import itertools
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "research_mst_bound.csv")

N_GRID = (20, 30, 50, 75)
BGW_GRID = (3, 4, 5)
TW_GRID = (30, 60, 120, 240)
SEEDS = range(3)
NDRV = 10
TAU = 20.0
SPATIAL = "dispersed"
MAX_K_ENUM = 4   # subset kich thuoc <= 4 (du de thay xu huong, tranh no to hop khi liet ke S)


def _mst_weight(node_ids, travel_time):
    """Prim tren tap node_ids (list id node, KHONG trung). Tra tong trong so MST."""
    m = len(node_ids)
    if m <= 1:
        return 0.0
    INF = float("inf")
    in_tree = [False] * m
    dist = [INF] * m
    dist[0] = 0.0
    total = 0.0
    for _ in range(m):
        u = -1
        best = INF
        for i in range(m):
            if not in_tree[i] and dist[i] < best:
                best = dist[i]
                u = i
        in_tree[u] = True
        total += best
        for i in range(m):
            if not in_tree[i]:
                w = travel_time(node_ids[u], node_ids[i])
                if w < dist[i]:
                    dist[i] = w
    return total


def mst_infeasible(travel_time, driver, orders, S):
    """[NGHIEN CUU] Can duoi MST cho tap S (GW, khong tau): nut = {start} U
    {pickup,delivery moi don trong S}. earliest = start_e cua driver (t0).
    latest = deadline MUON NHAT trong S (max, dung logic nhu budget() cua
    experiments/T4 va LB_detour da sua - "neu diem xa/muon nhat khong kip
    thi ca tap khong kip", KHONG phai min).
    Tra True neu S CHAC CHAN infeasible theo can nay (dieu kien CAN, khong DU)."""
    node_ids = [driver["start_node"]]
    latest_deadline = float("-inf")
    for oid in S:
        o = orders[oid]
        node_ids.append(o["pickup_node"])
        node_ids.append(o["delivery_node"])
        latest_deadline = max(latest_deadline, o["deadline_p"], o["deadline_d"])
    mst_w = _mst_weight(node_ids, travel_time)
    earliest_start = driver["t0"]
    return (earliest_start + mst_w) > latest_deadline + 1e-9


def pcf_infeasible(compat_graph, S):
    """[Doi chieu] PCF thuc: S bi loai neu TON TAI it nhat 1 cap (i,j) trong S
    khong tuong thich (theo dung dinh nghia new03.md - PCF that ap dung o
    MOI buoc pickup, nhung dieu kien 'ton tai cap khong tuong thich trong S'
    la dieu kien tuong duong de S khong bao gio duoc sinh day du qua DP).
    compat_graph: dict {frozenset({i,j}): bool}, dung dung API cua
    instance_gen.build_compat_graph (mac dinh True neu khong co trong dict,
    giong _compat_lookup trong t6_dp.py)."""
    for i, j in itertools.combinations(sorted(S), 2):
        if not compat_graph.get(frozenset((i, j)), True):
            return True
    return False


def run_one(n, B_gw, tw, seed):
    gen_seed = IG.stable_seed(n, B_gw, 2, tw, NDRV, seed, "research_mst")
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    compat_graph = IG.build_compat_graph(tt, orders)

    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    order_ids = sorted(orders.keys())

    n_total = n_pcf = n_mst = n_both = n_either = 0
    t0 = time.time()
    for drv in gw_drivers:
        for k in range(2, MAX_K_ENUM + 1):
            if k > B_gw:
                break
            for S in itertools.combinations(order_ids, k):
                n_total += 1
                is_pcf = pcf_infeasible(compat_graph, S)
                is_mst = mst_infeasible(tt, drv, orders, S)
                if is_pcf:
                    n_pcf += 1
                if is_mst:
                    n_mst += 1
                if is_pcf and is_mst:
                    n_both += 1
                if is_pcf or is_mst:
                    n_either += 1
    elapsed = time.time() - t0

    return dict(
        n=n, B_gw=B_gw, tw_width=tw, seed=seed, n_gw_drivers=len(gw_drivers),
        n_subsets_checked=n_total,
        pcf_cut_rate=round(n_pcf / n_total, 6) if n_total else 0.0,
        mst_cut_rate=round(n_mst / n_total, 6) if n_total else 0.0,
        both_cut_rate=round(n_both / n_total, 6) if n_total else 0.0,
        either_cut_rate=round(n_either / n_total, 6) if n_total else 0.0,
        mst_extra_over_pcf=round((n_mst - n_both) / n_total, 6) if n_total else 0.0,
        elapsed_s=round(elapsed, 3),
    )


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


FIELDS = ["n", "B_gw", "tw_width", "seed", "n_gw_drivers", "n_subsets_checked",
          "pcf_cut_rate", "mst_cut_rate", "both_cut_rate", "either_cut_rate",
          "mst_extra_over_pcf", "elapsed_s"]


def main():
    t_start = time.time()
    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already done." % len(already))

    total = len(N_GRID) * len(BGW_GRID) * len(TW_GRID) * len(SEEDS)
    done = 0
    with open(OUT, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for n in N_GRID:
            for B_gw in BGW_GRID:
                for tw in TW_GRID:
                    for sd in SEEDS:
                        if (n, B_gw, tw, sd) in already:
                            done += 1
                            continue
                        rec = run_one(n, B_gw, tw, sd)
                        w.writerow(rec)
                        f.flush()
                        done += 1
                    print("  [%d/%d] n=%d Bgw=%d tw=%d  pcf=%.1f%% mst=%.1f%% "
                          "mst_extra=%.1f%%  elapsed=%.1fs"
                          % (done, total, n, B_gw, tw,
                             rec["pcf_cut_rate"] * 100, rec["mst_cut_rate"] * 100,
                             rec["mst_extra_over_pcf"] * 100, time.time() - t_start))
    print("\n=== RESEARCH MST BOUND DONE ===  elapsed=%.1fs" % (time.time() - t_start))


if __name__ == "__main__":
    main()
