"""Test3.md Viec 1 - check bat buoc sau khi sinh instance: % order song o k=1.

feasibility_rate_k1(driver, orders, travel_time) = ty le order ma mot minh
no (khong ket hop voi don nao khac) van kha thi (brute force tren subset don,
dung is_feasible dung 1 lan - Test2.md yeu cau).

assert >= 0.5; neu duoi 0.5, canh bao va KHONG dua cell do vao Q2/Q3.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C


def feasibility_rate_k1(driver, orders, travel_time):
    start, pd, home = C.build_walk_nodes(driver, orders)
    has_home = home is not None
    n = len(orders)
    if n == 0:
        return 1.0
    n_ok = 0
    for oid, (p, d) in pd.items():
        walk = [start, p, d] + ([home] if has_home else [])
        ok, slack, sched = C.is_feasible(travel_time, driver, walk)
        if ok:
            n_ok += 1
    return n_ok / n


def check_and_warn(driver, orders, travel_time, label="", threshold=0.5):
    """Tra (rate, ok). In canh bao neu ok=False. KHONG raise - de caller quyet
    dinh co bo qua cell hay khong (Test3.md: 'in canh bao, khong chay tiep
    cell do')."""
    rate = feasibility_rate_k1(driver, orders, travel_time)
    ok = rate >= threshold
    if not ok:
        print("  [CANH BAO feasibility_rate_k1] %s: rate=%.4f < %.2f - bo qua cell nay"
              % (label, rate, threshold))
    return rate, ok
