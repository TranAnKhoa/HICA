"""Cau noi: chay dp_fast.py (LB2 incremental, New_t4) TREN INSTANCE RQ1 THAT
(instance_gen.py/dp_labeling.py cua spec_2a_2b) - do wall-clock that co/khong
co rule, thay vi tiep tuc suy doan tu ti le gia FD tren instance tong hop.

Cac diem da xac nhan can sua truoc khi chay (khong sua se cho ket qua SAI so
voi RQ1, khong phai chi la "xap xi"):

  1. SERVICE: hica_core.py/dp_rules.py/dp_fast.py hard-code SERVICE=2.0 (phut/
     stop). RQ1 that dung SERVICE_MIN=5.0 (instance_gen.py dong 38). Patch
     thuoc tinh SERVICE cua CA BA module SAU KHI import (vi dp_rules.py/
     dp_fast.py da "from hica_core import SERVICE" - copy gia tri vao
     namespace rieng luc import, patch hica_core.SERVICE sau do KHONG anh
     huong 2 module kia).

  2. ready_time_d: instance_gen.py (dong 228: ready_d = ready_p) CO dat opening
     time cho delivery - driver phai CHO neu den delivery som. Ban goc cua
     hica_core.Order/dp_rules.py/dp_fast.py GIA DINH delivery khong co opening
     time (dung cho instance tong hop cu). Da SUA ca 3 file (hica_core.py:
     Order.e_d + simulate(); dp_rules.py: stop_e()/future_stops()/absorption()
     goi dung F(L) mo rong dung Remark 'Delivery time windows with an opening
     time' cua T4_Label_Rule.tex; dp_fast.py: cho tai delivery + A tinh ca
     onboard-delivery lan future-delivery) - GIU NGUYEN core logic/chung minh,
     chi mo rong dung pham vi da duoc .tex xac nhan an toan.

  3. kappa=1.0, FD base_fee=8.0/rate=3.0/free_radius=2.0: DA KHOP san giua
     hica_core.random_instance() va RQ1 (t4_profile.KAPPA=1.0,
     rq1_cost_gen.FD_BASE_FEE/RATE) - khong can sua, chi can DUNG DUNG q_o
     that tu rq1_cost_gen.assign_q_o() thay vi cong thuc rieng cua
     hica_core.random_instance().

  4. SPEED_KMH=20 ca hai ben (hica_core.MIN_PER_KM=3.0 <=> 20km/h,
     instance_gen.SPEED_KMH=20.0) - khop san, khong can sua.

Instance dung: CUNG 5 instance RQ1 that da dung trong kstar_rq1_crosscheck.py/
kstar_gridcheck_rq1.py (khop log activation-rate cu) - de so sanh xuyen suot
cac report.

CHAY BANG PYTHON 3.13 (anaconda) - dp_fast.py/dp_rules.py/hica_core.py
KHONG can CPLEX, chi can doc route pool RQ1 THAT qua instance_gen/dp_labeling
(pure Python, khong phu thuoc CPLEX) - khong can Python 3.7.
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_SPEC = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "spec_2a_2b", "src")
if _SPEC not in sys.path:
    sys.path.insert(0, _SPEC)

import instance_gen as IG
import rq1_cost_gen as RC

import hica_core as HC
import dp_rules as DR
import dp_fast as DF

# --- patch SERVICE = SERVICE_MIN (5.0) tren CA BA module (xem ghi chu #1) ---
import instance_gen as _IGcheck
assert _IGcheck.SERVICE_MIN == 5.0, "instance_gen.SERVICE_MIN doi gia tri - kiem lai patch"
HC.SERVICE = _IGcheck.SERVICE_MIN
DR.SERVICE = _IGcheck.SERVICE_MIN
DF.SERVICE = _IGcheck.SERVICE_MIN

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_fast_rq1_results.csv")

LO, HI = 18.0, 25.0

INSTANCES = [
    dict(n=12, n_drivers=5, seed=42),
    dict(n=10, n_drivers=4, seed=1),
    dict(n=15, n_drivers=5, seed=7),
    dict(n=12, n_drivers=6, seed=123),
    dict(n=10, n_drivers=4, seed=999),
]


def build_hica_instance(n, n_drivers, seed, B=3):
    """Sinh instance qua instance_gen.py THAT, chuyen sang hica_core.Order/
    Driver (toa do (x,y) truc tiep can cho dist()/tt() cua hica_core - lay tu
    instance_gen's internal node_xy qua travel_time()/mot lop tra nguoc toa
    do bang cach doc lai node_xy tra ve trong meta neu co, hoac tai tao qua
    duong tim toa do)."""
    drivers_raw, orders_raw, tt_fn, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=120, n_drivers=n_drivers, seed=seed,
        tau=30.0, spatial_mode="dispersed")
    q_o_by_order = RC.assign_q_o(orders_raw, tt_fn)

    # instance_gen.py khong xuat node_xy truc tiep - nhung KHONG can toa do
    # that: hica_core.dist()/tt() chi can BAT KY he toa do nao thoa Euclid +
    # tam giac, VA travel_time cua instance_gen.py DA la Euclid chuan (dong
    # 147-150: _euclid_km/SPEED_KMH*60). Dung MDS 1 chieu don gian KHONG on -
    # thay vao do: goi truc tiep tt_fn(a,b) CHO MOI cap node can, KHONG di qua
    # dist()/tt() cua hica_core (von gia dinh co toa do (x,y)) - PATCH ca hai
    # ham nay thanh wrapper goi tt_fn that, giu dung khoang cach RQ1.
    def dist_rq1(a, b):
        # hica_core dung dist() rieng cho K (kappa*km) - can km, khong phai
        # phut. tt_fn tra PHUT; suy km qua SPEED_KMH co dinh (khop ca hai ben,
        # xem ghi chu #4).
        return tt_fn(a, b) * IG.SPEED_KMH / 60.0

    def tt_rq1(a, b):
        return tt_fn(a, b)

    HC.dist = dist_rq1
    HC.tt = tt_rq1
    DR.dist = dist_rq1
    DR.tt = tt_rq1
    DF.dist = dist_rq1
    DF.tt = tt_rq1

    orders = {}
    for oid, o in orders_raw.items():
        orders[oid] = HC.Order(oid, o["pickup_node"], o["delivery_node"],
                               o["ready_time_p"], o["deadline_p"], o["deadline_d"],
                               q_o_by_order[oid], e_d=o["ready_time_d"])

    driver_list = drivers_raw if isinstance(drivers_raw, list) else list(drivers_raw.values())
    hica_drivers = []
    for d in driver_list:
        if d["cls"] == "GW":
            # [SUA 2026-09-23] availability_min CHI la metadata "ghi nhan,
            # KHONG ep thanh rang buoc feasibility rieng" (t2_gen.py dong
            # 185-186) - t6_dp.py THAT (Algorithm A goc) khong doc driver["t1"]
            # o dau ca: GW la open-route, khong co deadline cung (xem
            # Algorithm_A_Description.md Sec2.3 "GW... Khong can quay ve dau
            # ca"). Dat t1=+inf (khop dung RQ1 that), KHONG dung
            # t0+availability_min (do la GIA DINH SAI ban dau).
            dr = HC.Driver(d["id"], "GW", d["start_node"], d["t0"], float("inf"),
                           d["capacity"], 1.0)
        else:
            # OD cung khong co t1 rieng trong RQ1 that (khong xuat hien trong
            # instance_gen.py/t2_gen.py) - feasibility cua OD hoan toan qua
            # tau (detour budget, da enforce trong simulate()/dp_rules.py qua
            # dr.tau, xem hica_core.simulate() dong 61) - dat t1=+inf.
            dr = HC.Driver(d["id"], "OD", d["start_node"], d["t0"], float("inf"),
                           d["capacity"], 1.0, dest=d["home_node"], tau=d["tau"])
        hica_drivers.append(dr)

    return hica_drivers, orders


def run_one(n, n_drivers, seed):
    drivers, orders = build_hica_instance(n, n_drivers, seed)
    rows = []
    for dr in drivers:
        B = int(dr.cap)
        t0 = time.perf_counter()
        out_off, st_off = DF.enumerate_fast(dr, orders, B, LO, use_rule=False)
        t_off = time.perf_counter() - t0

        t0 = time.perf_counter()
        out_on, st_on = DF.enumerate_fast(dr, orders, B, LO, use_rule=True)
        t_on = time.perf_counter() - t0

        rows.append(dict(
            n=n, n_drivers=n_drivers, seed=seed, driver=dr.id, cls=dr.cls, B=B,
            routes_off=len(out_off), routes_on=len(out_on),
            ext_off=st_off["ext"], ext_on=st_on["ext"],
            fired=st_on["fired"], A_evals=st_on["A_evals"],
            wall_off_s=t_off, wall_on_s=t_on,
        ))
    return rows


def main():
    all_rows = []
    print("=" * 100)
    print("dp_fast.py (LB2 incremental, co ready_time_d + SERVICE=5.0 khop RQ1) tren instance RQ1 that")
    print("=" * 100)
    for spec in INSTANCES:
        rows = run_one(**spec)
        all_rows.extend(rows)
        for r in rows:
            ext_saved = 100.0 * (1 - r["ext_on"] / r["ext_off"]) if r["ext_off"] else 0.0
            speedup = r["wall_off_s"] / r["wall_on_s"] if r["wall_on_s"] > 0 else float("nan")
            print("n=%2d n_drivers=%d seed=%-4d driver=%-6s B=%d  "
                  "ext_off=%7d ext_on=%7d (saved %5.1f%%)  "
                  "wall_off=%7.2fs wall_on=%7.2fs (speedup %.2fx)  fired=%d"
                 % (r["n"], r["n_drivers"], r["seed"], r["driver"], r["B"],
                    r["ext_off"], r["ext_on"], ext_saved,
                    r["wall_off_s"], r["wall_on_s"], speedup, r["fired"]))
            sys.stdout.flush()

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    print("\n-> %s" % OUT_CSV)

    tot_off = sum(r["wall_off_s"] for r in all_rows)
    tot_on = sum(r["wall_on_s"] for r in all_rows)
    tot_ext_off = sum(r["ext_off"] for r in all_rows)
    tot_ext_on = sum(r["ext_on"] for r in all_rows)
    print("\n[TONG] wall_off=%.2fs wall_on=%.2fs speedup=%.2fx | ext saved=%.1f%%"
         % (tot_off, tot_on, tot_off / tot_on if tot_on > 0 else float("nan"),
            100.0 * (1 - tot_ext_on / tot_ext_off) if tot_ext_off else 0.0))


if __name__ == "__main__":
    main()
