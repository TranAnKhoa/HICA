"""Rq1.md Sec1.1-1.3 - sinh theta_i (private VOT, GW+OD) va q_o (public FD cost),
cung don vi voi KAPPA=1.0 cost-unit/km da dung trong Algorithm A (t4_profile.py,
t6_dp.py). Day la input con THIEU chan toan bo pipeline WDP that (khong rieng
RQ1) - khoa MOT LAN, dung chung cho moi thuc nghiem ve sau (Rq1.md dong 28-29).

KHONG doi KAPPA=1.0 da khoa o t4_profile.py - chi ADD them theta/q_o cung he
don vi do (cost-unit = km, vi kappa=1.0 cost-unit/km => 1 cost-unit = 1 km
quy doi).

Neo gia tri theta: Uniform[18,25] USD/gio (Amazon Flex, Li & Zhang benchmark)
-> quy doi ve cost-unit/gio bang 1 UNIT_PER_USD duy nhat, khoa cung voi kappa.
"""

import math
import random

# ---------------------------------------------------------------------------
# [LOCK] Sec 1.1 - theta_i (value of time), CUNG mot ho phan phoi cho GW/OD
# ---------------------------------------------------------------------------

THETA_MIN_USD_PER_HOUR = 18.0
THETA_MAX_USD_PER_HOUR = 25.0

# [LOCK] Quy doi USD -> cost-unit. kappa=1.0 cost-unit/km da khoa o t4_profile.py
# (xem KAPPA trong t4_profile.py / t6_dp.py). Khong co benchmark rieng cho
# "1 cost-unit = X USD" trong du an - chon UNIT_PER_USD=1.0 (1 cost-unit = 1
# USD) la lua chon TRUNG LAP DUY NHAT khong dua them gia dinh moi: kappa=1.0
# cost-unit/km tuong duong 1.0 USD/km, mot muc phi hop ly cho quang duong xe
# may/xe con o do thi (tham khao thuc te: phi giao hang last-mile ~0.5-1.5
# USD/km). Cong khai lua chon nay - neu co benchmark tot hon cho rate USD/km
# cua GW/OD, thay doi O DAY (mot noi duy nhat), khong o rieng theta hay q_o.
UNIT_PER_USD = 1.0

THETA_MIN = THETA_MIN_USD_PER_HOUR * UNIT_PER_USD   # cost-unit / gio
THETA_MAX = THETA_MAX_USD_PER_HOUR * UNIT_PER_USD


def sample_theta(rng, n_drivers):
    """Tra {driver_id_index: theta} se duoc gan cho driver ben ngoai - ham nay
    chi sinh list gia tri, khong biet driver id (goi tu instance-building code).
    theta ~ Uniform[THETA_MIN, THETA_MAX], CUNG mot phan phoi cho GW va OD
    (Rq1.md Sec1.1 - khong tach rieng tru khi co nguon cu the)."""
    return [rng.uniform(THETA_MIN, THETA_MAX) for _ in range(n_drivers)]


def assign_theta(rng, drivers):
    """drivers: list dict co 'id' (tu instance_gen.generate_instance). Tra
    {driver_id: theta}, KHONG sua drivers list (giu instance_gen.py nguyen
    ven theo rang buoc 'khong sua t2_core/t6_dp' da khoa truoc)."""
    vals = sample_theta(rng, len(drivers))
    return {dv["id"]: v for dv, v in zip(drivers, vals)}


# ---------------------------------------------------------------------------
# [LOCK] Sec 1.2 - q_o (public FD cost per order)
# ---------------------------------------------------------------------------
# Cong thuc khoa: q_o = base_fee + rate_per_km * max(0, dist - free_radius)
# Gia tri DA KHOA qua calibration pass (Sec1.4, xem rq1_calibration.py +
# results/rq1_locked_params.json) - bo tham so DAU TIEN dat ca 2 tieu chi
# (fd_rate in [0.10,0.50], khong supply-cell nao GW/OD thang 0 tuyet doi):
# fd_rate=0.483, gw_wins=32, od_wins=24, 0 cell thang trang. KHONG sua lai
# 3 hang so nay sau khi da khoa (Rq1.md quy tac chong bia ket qua #4).

FD_BASE_FEE = 8.0          # cost-unit - [LOCK] 2026-09-15
FD_RATE_PER_KM = 3.0       # cost-unit/km - [LOCK] 2026-09-15
FD_FREE_RADIUS_KM = 1.0    # km - [LOCK] 2026-09-15 (khong doi tu placeholder)


def compute_q_o(pickup_xy, delivery_xy, base_fee=FD_BASE_FEE,
                rate_per_km=FD_RATE_PER_KM, free_radius=FD_FREE_RADIUS_KM):
    dist = math.hypot(pickup_xy[0] - delivery_xy[0], pickup_xy[1] - delivery_xy[1])
    return base_fee + rate_per_km * max(0.0, dist - free_radius)


SPEED_KMH = 20.0   # PHAI khop instance_gen.SPEED_KMH - dung de suy khoang
                    # cach tu travel_time (generate_instance khong tra node_xy
                    # truc tiep, chi tra travel_time closure - xem t4_profile.py
                    # dist_km = travel_time*SPEED_KMH/60, dung lai dung quy uoc)


def compute_q_o_from_traveltime(travel_time, pickup_node, delivery_node,
                                base_fee=FD_BASE_FEE, rate_per_km=FD_RATE_PER_KM,
                                free_radius=FD_FREE_RADIUS_KM):
    dist_km = travel_time(pickup_node, delivery_node) * SPEED_KMH / 60.0
    return base_fee + rate_per_km * max(0.0, dist_km - free_radius)


def assign_q_o(orders, travel_time, base_fee=FD_BASE_FEE, rate_per_km=FD_RATE_PER_KM,
               free_radius=FD_FREE_RADIUS_KM):
    """orders: dict tu instance_gen.generate_instance (co 'pickup_node',
    'delivery_node'). travel_time: closure tra ve boi generate_instance
    (PHUT) - dung suy khoang cach km qua SPEED_KMH, KHONG can node_xy rieng."""
    out = {}
    for oid, o in orders.items():
        out[oid] = compute_q_o_from_traveltime(
            travel_time, o["pickup_node"], o["delivery_node"],
            base_fee, rate_per_km, free_radius)
    return out


# ---------------------------------------------------------------------------
# [CHECK] Sec 1.3 - unit-check kappa*distance vs theta*time_hours
# ---------------------------------------------------------------------------

def unit_check(median_distance_km, median_speed_kmh, theta_values, kappa=1.0):
    """Tra dict {kappa_term, theta_term_mean, ratio} - ratio phai trong [0.2, 5]
    (2-5 lan) theo dung nguong Rq1.md Sec1.3. Neu ratio ngoai khoang nay,
    KHONG duoc tiep tuc - phai dieu chinh UNIT_PER_USD hoac free_radius/rate
    truoc khi khoa params."""
    median_time_hours = median_distance_km / median_speed_kmh
    kappa_term = kappa * median_distance_km
    theta_mean = sum(theta_values) / len(theta_values)
    theta_term = theta_mean * median_time_hours
    ratio = kappa_term / theta_term if theta_term > 0 else float("inf")
    ok = 0.2 <= ratio <= 5.0
    return {
        "median_distance_km": median_distance_km,
        "median_speed_kmh": median_speed_kmh,
        "median_time_hours": median_time_hours,
        "kappa_term": kappa_term,
        "theta_mean": theta_mean,
        "theta_term": theta_term,
        "ratio_kappa_over_theta": ratio,
        "ok": ok,
    }


if __name__ == "__main__":
    rng = random.Random(42)
    thetas = sample_theta(rng, 1000)
    print("theta sample: min=%.3f max=%.3f mean=%.3f (n=1000, cost-unit/gio)"
          % (min(thetas), max(thetas), sum(thetas) / len(thetas)))

    # sanity: AREA_KM=8.0, SPEED_KMH=20.0 (instance_gen.py) -> khoang cach
    # trung binh 2 diem ngau nhien trong hop 8x8km ~ 0.5214*8 ~ 4.17km
    median_dist = 4.17
    r = unit_check(median_dist, 20.0, thetas, kappa=1.0)
    print("\nunit_check (median_distance=%.2fkm, speed=20km/h):" % median_dist)
    for k, v in r.items():
        print("  %s = %s" % (k, v))
    print("\n[CHECK] ratio trong [0.2, 5.0]? -> %s" % r["ok"])
