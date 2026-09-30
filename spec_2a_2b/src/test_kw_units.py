"""new_02.md - Gate K/W. Test 1a/1b/1c + Viec 2 (waiting time), Viec 3 (nguon
K/W duy nhat), dung TRUC TIEP t6_dp.run_dp/finalize_KW - KHONG viet lai
cong thuc, chi dung tay tinh doc lap roi so sanh.

DON VI CHUAN (xac nhan tu code, Viec 0):
  travel_time(a,b) -> PHUT
  SPEED_KMH = 20.0 (t2_gen.py) hoac 20.0 (instance_gen.py) - CHUNG mot hang so
  SERVICE_MIN = per-node "s" field (WNode.s), tinh vao thoi gian (t/W) nhung
                KHONG tinh vao khoang cach (K) - Test 1c kiem dung diem nay.
  K (cost)   = kappa * distance_km, kappa=1.0 (t4_profile.KAPPA / t6_dp.KAPPA)
  W (billable time) = active_time_min / 60.0 (GW); (detour_time_min)/60.0 (OD)
    active_time_min/detour_time_min TICH LUY tu (Bt - t0) qua tung buoc, va
    Bt = max(A, ready_time) -> BAO GOM thoi gian cho (xem Viec 2 duoi).
"""

import os
import sys

sys.path.insert(0, os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS"))
import t6_dp as D
import t2_core as C
import t2_gen as G

SPEED_KMH = G.SPEED_KMH   # =20.0
KAPPA = D.KAPPA           # =1.0


def make_travel_time(edges):
    """edges: {(a,b): minutes}. Symmetric. travel_time(a,a)=0."""
    def tt(a, b):
        if a == b:
            return 0.0
        if (a, b) in edges:
            return edges[(a, b)]
        if (b, a) in edges:
            return edges[(b, a)]
        raise KeyError("no edge %s-%s" % (a, b))
    return tt


def run_single_route_dp(driver, orders, travel_time, B=1):
    """Chay t6_dp that qua toan bo instance (1 driver, cac order da cho),
    tra (K,W) cua label hoan chinh DUY NHAT co C = tat ca order (bundle full)."""
    res = D.run_dp(travel_time, driver, orders, B, use_dominance=True)
    full_C = frozenset(orders.keys())
    labs = res["complete_by_C"].get(full_C, [])
    assert len(labs) >= 1, "khong tim thay label hoan chinh cho bundle day du: %s" % (res["complete_by_C"].keys(),)
    # neu nhieu label Pareto, lay label co K nho nhat (test khong co tradeoff)
    lab = min(labs, key=lambda l: (l.K, l.W))
    return D.finalize_KW(driver, lab)


# --------------------------------------------------------------------- 1a
def test_1a_single_order_gw():
    """GW, 1 order: start -> pickup -> delivery.
    travel(start,pickup)=10p, travel(pickup,delivery)=20p, service=5p/diem,
    SPEED_KMH=20 (dung hang so THAT trong code, khong tu bia 30 nhu spec vi
    du - spec chi minh hoa cong thuc, gia tri SPEED_KMH phai khop code that).
    kappa=1.0 (dung hang so THAT D.KAPPA, khong tu bia 0.5).
    """
    tt = make_travel_time({("s", "p"): 10.0, ("p", "d"): 20.0})
    driver = {"id": "gw0", "cls": "GW", "start_node": "s", "t0": 0.0,
              "capacity": 1.0, "availability_min": 600.0}
    orders = {"o1": {
        "pickup_node": "p", "delivery_node": "d", "demand": 1.0,
        "ready_time_p": 0.0, "deadline_p": 1000.0,
        "ready_time_d": 0.0, "deadline_d": 1000.0,
        "service_time": 5.0,
    }}
    K_code, W_code = run_single_route_dp(driver, orders, tt, B=1)

    # tinh tay, dung SPEED_KMH/KAPPA THAT cua code (khong bia so):
    total_travel_min = 10.0 + 20.0
    distance_km = total_travel_min * SPEED_KMH / 60.0
    K_tay = KAPPA * distance_km
    W_tay = (total_travel_min + 2 * 5.0) / 60.0   # travel + 2 service, KHONG cho

    assert abs(K_code - K_tay) < 1e-6, "K sai: code=%s tay=%s" % (K_code, K_tay)
    assert abs(W_code - W_tay) < 1e-4, "W sai: code=%s tay=%s" % (W_code, W_tay)
    print("test_1a PASS: K=%.6f W=%.6f (tay: K=%.6f W=%.6f)" % (K_code, W_code, K_tay, W_tay))


# --------------------------------------------------------------------- 1b
def test_1b_od_detour_positive():
    """OD, route: O1 -> pickup -> delivery -> Dest1 (home).
    Vi du DA SUA cho hop ly hinh hoc (detour>0 CA quang duong LAN thoi gian -
    ban dau chi sua duoc detour_time>0 nhung detour_distance van =0 vi
    route_dist(9.33km) < direct_dist(10km) - da phat hien va sua tiep):
    direct: O1->Dest1 truc tiep = 30p (dat thang, KHONG qua p/d) = 10km.
    route that: O1->pickup=4p, pickup->delivery=8p, delivery->Dest1=24p
      => tong travel = 36p (=12km) > direct 10km -> detour_distance=2km>0
      => tong thoi gian = 36p travel + 2*5p service = 46p
      => detour_time = 46 - 30 = 16p > 0
    """
    tt = make_travel_time({
        ("O1", "Dest1"): 30.0,
        ("O1", "p"): 4.0, ("p", "d"): 8.0, ("d", "Dest1"): 24.0,
    })
    driver = {"id": "od0", "cls": "OD", "start_node": "O1", "t0": 0.0,
              "capacity": 1.0, "home_node": "Dest1", "direct_time": 30.0, "tau": 60.0}
    orders = {"o1": {
        "pickup_node": "p", "delivery_node": "d", "demand": 1.0,
        "ready_time_p": 0.0, "deadline_p": 1000.0,
        "ready_time_d": 0.0, "deadline_d": 1000.0,
        "service_time": 5.0,
    }}
    K_code, W_code = run_single_route_dp(driver, orders, tt, B=1)

    route_total_time_min = 4.0 + 8.0 + 24.0 + 2 * 5.0   # =46
    route_total_distance_km = (4.0 + 8.0 + 24.0) * SPEED_KMH / 60.0  # CHI travel, khong service =12km
    direct_distance_km = 30.0 * SPEED_KMH / 60.0   # =10km
    detour_distance = max(0.0, route_total_distance_km - direct_distance_km)
    detour_time = max(0.0, route_total_time_min - 30.0)

    K_tay = KAPPA * detour_distance
    W_tay = detour_time / 60.0

    assert detour_distance > 0, "vi du chua sua dung: detour_distance=%s" % detour_distance
    assert detour_time > 0, "vi du chua sua dung hinh hoc: detour_time=%s" % detour_time
    assert abs(K_code - K_tay) < 1e-6, "K sai: code=%s tay=%s" % (K_code, K_tay)
    assert abs(W_code - W_tay) < 1e-4, "W sai: code=%s tay=%s" % (W_code, W_tay)
    print("test_1b PASS: K=%.6f W=%.6f (tay: K=%.6f W=%.6f, detour_dist=%.2fkm detour_time=%.2fp)"
          % (K_code, W_code, K_tay, W_tay, detour_distance, detour_time))


# --------------------------------------------------------------------- 1c
def test_1c_service_time_not_counted_as_distance():
    """Route GW voi travel=0 (start=pickup=delivery ve toa do, dung 1 node id
    lam ca 3 vi tri) - chi con service_time. K phai =0, W phai >0."""
    tt = make_travel_time({})   # khong co edge nao # a==b luon tra 0.0
    driver = {"id": "gw0", "cls": "GW", "start_node": "z", "t0": 0.0,
              "capacity": 1.0, "availability_min": 600.0}
    orders = {"o1": {
        "pickup_node": "z", "delivery_node": "z", "demand": 1.0,
        "ready_time_p": 0.0, "deadline_p": 1000.0,
        "ready_time_d": 0.0, "deadline_d": 1000.0,
        "service_time": 5.0,
    }}
    K_code, W_code = run_single_route_dp(driver, orders, tt, B=1)
    assert abs(K_code - 0.0) < 1e-6, "K phai =0 khi khong di chuyen, code tra %s" % K_code
    assert W_code > 0, "W phai >0 vi service_time van tinh, code tra %s" % W_code
    W_tay = (2 * 5.0) / 60.0
    assert abs(W_code - W_tay) < 1e-4, "W sai: code=%s tay=%s" % (W_code, W_tay)
    print("test_1c PASS: K=%.6f (=0 dung) W=%.6f (tay=%.6f)" % (K_code, W_code, W_tay))


# --------------------------------------------------------------------- Viec 2
def test_2_waiting_time_in_W():
    """Driver den SOM hon ready_time cua pickup, buoc phai cho.
    start->pickup travel=10p (den luc t=10), nhung ready_time_p=50p =>
    cho 40p truoc khi bat dau service. Sau pickup, delivery ngay canh
    (travel=0) de co the hoan tat bundle (B=1, khong can home - GW).
    Kiem W CO hay KHONG cong ca 40p cho nay."""
    tt = make_travel_time({("s", "p"): 10.0, ("p", "d"): 0.0})
    driver = {"id": "gw0", "cls": "GW", "start_node": "s", "t0": 0.0,
              "capacity": 1.0, "availability_min": 600.0}
    orders = {"o1": {
        "pickup_node": "p", "delivery_node": "d", "demand": 1.0,
        "ready_time_p": 50.0, "deadline_p": 1000.0,
        "ready_time_d": 0.0, "deadline_d": 1000.0,
        "service_time": 5.0,
    }}
    K_code, W_code = run_single_route_dp(driver, orders, tt, B=1)

    # duong di THAT (bao gom cho): arrival=10, wait->50, service->55 (pickup)
    #   travel(pickup,delivery)=0 -> arrival=55, ready_time_d=0 (khong cho) ->
    #   service -> 60 (delivery). t_final=60. W_neu_co_cho = 60/60 = 1.0
    # W_neu_KHONG_co_cho (chi travel+service, bo 40p cho) = (10+0+5+5)/60 = 20/60=0.3333
    W_with_wait = 60.0 / 60.0
    W_without_wait = (10.0 + 0.0 + 5.0 + 5.0) / 60.0

    print("test_2: W_code=%.6f | W_with_wait=%.6f | W_without_wait=%.6f"
          % (W_code, W_with_wait, W_without_wait))
    if abs(W_code - W_with_wait) < 1e-4:
        print("  => KET LUAN: W hien tai BAO GOM thoi gian cho (wait cong vao W).")
        return "includes_wait"
    elif abs(W_code - W_without_wait) < 1e-4:
        print("  => KET LUAN: W hien tai KHONG bao gom thoi gian cho.")
        return "excludes_wait"
    else:
        raise AssertionError("W_code=%s khop VOI CA HAI gia thuyet - kiem tra lai cong thuc" % W_code)


if __name__ == "__main__":
    test_1a_single_order_gw()
    test_1b_od_detour_positive()
    test_1c_service_time_not_counted_as_distance()
    verdict = test_2_waiting_time_in_W()
    print("\n=== ALL K/W UNIT GATE TESTS: PASS ===")
    print("Viec 2 verdict: %s" % verdict)
