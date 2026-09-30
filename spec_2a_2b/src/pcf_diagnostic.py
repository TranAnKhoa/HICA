"""new03.md Viec 2.0 - chan doan re TRUOC KHI cai Gate T4-B / PCF day du.

Do pair_infeasibility_rate = ty le cap order (i,j) KHONG the di cung nhau
duoi BAT KY thu tu nao trong 6 thu tu hop le (xem new03.md Sec2.1), rieng
theo driver_class (GW / OD). Dung DUNG feasibility check da co (khong viet
cong thuc thu 2):
  - GW: chi xet time window + travel (khong tau/home) - dung logic giong
    instance_gen._pair_has_feasible_order (da viet cho compat_graph chung).
  - OD: PHAI xet ca home + direct_time + tau (deadline_home = t0 + direct_time
    + tau) - day la diem khac biet quan trong voi GW, vi OD bi rang buoc chat
    hon nhieu (cung ly do OD-corridor-bias patch truoc da phai sua).

KHONG chay nhieu lan voi tham so khac nhau de "tim so dep" - luoi da khoa
duoi day, doc ket qua 1 lan theo dung nguong new03.md Sec2.0.
"""

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

EPS = 1e-9

# Luoi khoa (new03.md Sec2.0): uu tien vung da biet bung no (tw in {120,240},
# n in {30,50}), them 1-2 o tw hep de doi chung.
N_GRID = (30, 50)
TW_GRID = (60, 120, 240)
DRIVER_CLASSES = ("GW", "OD")
SEEDS = range(3)
TAU_FIXED = 45.0   # gia tri giua luoi tau da khoa {30,45,60} - dai dien, khong quet


def _feasible_seq(travel_time, t0, seq):
    """seq: list (node_id, e, l, s), diem dau tien la 'goc' voi t co san t0."""
    cur_node, cur_t = seq[0][0], t0
    for (nid, e, l, s) in seq:
        tt = travel_time(cur_node, nid)
        A = cur_t + tt
        Bt = A if A > e else e
        if Bt > l + EPS:
            return False, None
        cur_t = Bt + s
        cur_node = nid
    return True, cur_t


def _order_pd(oid, o):
    p = (o["pickup_node"], o["ready_time_p"], o["deadline_p"], o["service_time"])
    d = (o["delivery_node"], o["ready_time_d"], o["deadline_d"], o["service_time"])
    return p, d


def _six_orderings(Pi, Di, Pj, Dj):
    return [
        [Pi, Di, Pj, Dj], [Pj, Dj, Pi, Di],
        [Pi, Pj, Di, Dj], [Pi, Pj, Dj, Di],
        [Pj, Pi, Di, Dj], [Pj, Pi, Dj, Di],
    ]


def pair_feasible_gw(travel_time, oi, oj):
    """GW: khong home/tau - chi start gia dinh = pickup som nhat, khong deadline
    ve nha. Dung diem xuat phat tai node cua pickup som hon, t0 = ready_time_p
    tuong ung (giong instance_gen._pair_has_feasible_order)."""
    Pi, Di = _order_pd(*oi)
    Pj, Dj = _order_pd(*oj)
    t0_guess = min(Pi[1], Pj[1])
    start_node = Pi[0] if Pi[1] <= Pj[1] else Pj[0]
    for seq in _six_orderings(Pi, Di, Pj, Dj):
        ok, _ = _feasible_seq(travel_time, t0_guess, [(start_node, t0_guess, t0_guess, 0.0)] + seq)
        if ok:
            return True
    return False


def pair_feasible_od(travel_time, oi, oj, od_driver):
    """OD: PHAI ket thuc ve home truoc deadline_home = t0 + direct_time + tau.
    Start = od_driver start_node, t0 = od_driver t0 (KHONG doan pickup som
    nhat - day la khac biet co chu dich voi GW, vi OD co diem xuat phat that
    su co dinh, khong "gia dinh")."""
    Pi, Di = _order_pd(*oi)
    Pj, Dj = _order_pd(*oj)
    home = od_driver["home_node"]
    deadline_home = od_driver["t0"] + od_driver["direct_time"] + od_driver["tau"]
    home_leg = (home, 0.0, deadline_home, 0.0)
    for seq in _six_orderings(Pi, Di, Pj, Dj):
        full = [(od_driver["start_node"], od_driver["t0"], od_driver["t0"], 0.0)] + seq + [home_leg]
        ok, _ = _feasible_seq(travel_time, od_driver["t0"], full)
        if ok:
            return True
    return False


def pair_infeasibility_rate(travel_time, orders, driver_class, od_driver=None):
    oids = sorted(orders.keys())
    total = 0
    infeasible = 0
    for a, b in itertools.combinations(range(len(oids)), 2):
        i, j = oids[a], oids[b]
        oi = (i, orders[i])
        oj = (j, orders[j])
        total += 1
        if driver_class == "GW":
            ok = pair_feasible_gw(travel_time, oi, oj)
        else:
            ok = pair_feasible_od(travel_time, oi, oj, od_driver)
        if not ok:
            infeasible += 1
    return (infeasible / total) if total else 0.0, infeasible, total


def main():
    print("%-6s %-6s %-8s %10s  %s" % ("n", "tw", "class", "rate", "detail"))
    by_tw_class = {}
    for n in N_GRID:
        for tw in TW_GRID:
            for cls in DRIVER_CLASSES:
                tot_inf = tot_pairs = 0
                for sd in SEEDS:
                    seed = IG.stable_seed(n, tw, cls, sd, "pcf_diag")
                    n_drivers = 4
                    drivers, orders, tt, meta = IG.generate_instance(
                        n=n, B_gw=99, B_od=99, tw_width=tw, n_drivers=n_drivers,
                        seed=seed, tau=TAU_FIXED, spatial_mode="dispersed")
                    if cls == "OD":
                        od_drivers = [d for d in drivers if d["cls"] == "OD"]
                        od_driver = od_drivers[0]
                        rate, inf, tot = pair_infeasibility_rate(tt, orders, "OD", od_driver=od_driver)
                    else:
                        rate, inf, tot = pair_infeasibility_rate(tt, orders, "GW")
                    tot_inf += inf
                    tot_pairs += tot
                overall = (tot_inf / tot_pairs) if tot_pairs else 0.0
                by_tw_class[(n, tw, cls)] = overall
                print("%-6d %-6d %-8s %9.2f%%  (%d/%d cap qua %d seed)"
                      % (n, tw, cls, overall * 100, tot_inf, tot_pairs, len(SEEDS)))

    print("\n=== DOC KET QUA THEO NGUONG new03.md Sec2.0 (vung tw in {120,240}) ===")
    focus = [v for (n, tw, cls), v in by_tw_class.items() if tw in (120, 240)]
    avg_focus = sum(focus) / len(focus) if focus else 0.0
    print("pair_infeasibility_rate trung binh (tw=120,240, ca 2 lop, ca 2 n): %.2f%%" % (avg_focus * 100))
    if avg_focus < 0.10:
        verdict = "KHONG cai Gate T4-B / PCF - gan nhu chac chan khong cuu duoc vung bung no (lap lai Test5)."
    elif avg_focus < 0.25:
        verdict = "VUNG XAM - cai Gate T4-B nhung ha ky vong o Viec 2.4."
    else:
        verdict = "PCF co co so that - tien hanh Gate T4-B + Viec 2.4 day du."
    print("KET LUAN: %s" % verdict)

    import csv
    outdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
    with open(os.path.join(outdir, "pcf_diagnostic.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "tw", "driver_class", "pair_infeasibility_rate"])
        for (n, tw, cls), v in sorted(by_tw_class.items()):
            w.writerow([n, tw, cls, round(v, 6)])

    return 0


if __name__ == "__main__":
    sys.exit(main())
