"""Spec 2a - Gate 0: brute-force route enumeration, DOC LAP voi dp_labeling.py.

KHONG import t6_dp, KHONG import t2_core, KHONG import t4_profile. Viet lai
tu dau:
  - feasibility check (vong lap tho, precedence + time window + capacity)
  - cong thuc K/W (Test4 Sec0.1 / t4_profile._K_W_from_dist_time - viet lai):
      GW: K = kappa * total_dist_km ; W = active_time_min / 60
      OD: K = kappa * (total_dist_km - direct_dist_km)
          W = (active_time_min - direct_time_min) / 60      (>= 0, clamp)
    kappa = 1.0 (bat bien voi moi so sanh Pareto - xem t4_profile ghi chu).

Duyet MOI hoan vi cua 2k su kien pickup/delivery cho moi S, |S| <= B, loc
precedence, kiem feasibility, lay Pareto front (K,W). Dung lam ORACLE cho DP.
"""

import itertools
import math

KAPPA = 1.0
EPS = 1e-6
SPEED_KMH = 20.0   # khop instance_gen (travel_time PHUT -> km qua SPEED_KMH/60)


def _tt_km(tt_min):
    return tt_min * SPEED_KMH / 60.0


def _walk_feasible_and_cost(travel_time, driver, seq_nodes):
    """seq_nodes: list (node_id, e, l, s, demand, kind, order_id) - KHONG gom
    start; start lay tu driver. Voi OD: them 'home' o cuoi (deadline = t0 +
    direct_time + tau).

    Tra (ok, total_dist_km, active_time_min) hoac (False, None, None).
    """
    t = driver["t0"]
    cur = driver["start_node"]
    load = 0.0
    cap = driver["capacity"]
    picked = set()
    total_dist_km = 0.0

    nodes = list(seq_nodes)
    if driver["cls"] == "OD":
        deadline_home = driver["t0"] + driver["direct_time"] + driver["tau"]
        nodes = nodes + [(driver["home_node"], 0.0, deadline_home, 0.0, 0.0, "home", None)]

    for (nid, e, l, s, dem, kind, oid) in nodes:
        tt = travel_time(cur, nid)
        total_dist_km += _tt_km(tt)
        A = t + tt
        Bt = A if A > e else e
        if Bt > l + EPS:
            return False, None, None
        if kind == "pickup":
            load += dem
            if load > cap + EPS:
                return False, None, None
            picked.add(oid)
        elif kind == "delivery":
            if oid not in picked:
                return False, None, None
            load -= dem
            if load < -EPS:
                return False, None, None
        t = Bt + s
        cur = nid

    active_time_min = t - driver["t0"]
    return True, total_dist_km, active_time_min


def _KW(driver, total_dist_km, active_time_min):
    if driver["cls"] == "OD":
        direct_dist = driver["direct_time"] * SPEED_KMH / 60.0
        K = KAPPA * max(0.0, total_dist_km - direct_dist)
        W = max(0.0, (active_time_min - driver["direct_time"]) / 60.0)
    else:
        K = KAPPA * total_dist_km
        W = active_time_min / 60.0
    return K, W


def _pareto(kw_list):
    n = len(kw_list)
    dom = [False] * n
    for i in range(n):
        Ki, Wi = kw_list[i]
        for j in range(n):
            if i == j:
                continue
            Kj, Wj = kw_list[j]
            if Kj <= Ki + EPS and Wj <= Wi + EPS and (Kj < Ki - EPS or Wj < Wi - EPS):
                dom[i] = True
                break
    out, seen = [], set()
    for i in range(n):
        if dom[i]:
            continue
        key = (round(kw_list[i][0], 6), round(kw_list[i][1], 6))
        if key not in seen:
            seen.add(key)
            out.append(kw_list[i])
    return out


def brute_pool_for_driver(travel_time, driver, orders, B_gw, B_od):
    """[PATCH new_03] B tach lop: chon B hieu luc theo driver["cls"] (dung y
    het dp_labeling.run_pool - xem new03.md Viec 1). Tra
    {frozenset(order_ids): [(K,W), ...]}  (Pareto front tung bundle)."""
    B = B_gw if driver["cls"] == "GW" else B_od
    oids = sorted(orders.keys())
    node_of = {}
    for oid, o in orders.items():
        node_of[(oid, "pickup")] = (o["pickup_node"], o["ready_time_p"], o["deadline_p"],
                                    o["service_time"], o["demand"], "pickup", oid)
        node_of[(oid, "delivery")] = (o["delivery_node"], o["ready_time_d"], o["deadline_d"],
                                      o["service_time"], o["demand"], "delivery", oid)
    pool = {}
    for k in range(1, B + 1):
        for S in itertools.combinations(oids, k):
            events = []
            for oid in S:
                events.append(node_of[(oid, "pickup")])
                events.append(node_of[(oid, "delivery")])
            kw_list = []
            for perm in itertools.permutations(events):
                seen_p = set()
                ok_prec = True
                for (nid, e, l, s, dem, kind, oid) in perm:
                    if kind == "pickup":
                        seen_p.add(oid)
                    else:
                        if oid not in seen_p:
                            ok_prec = False
                            break
                if not ok_prec:
                    continue
                ok, dist_km, act_min = _walk_feasible_and_cost(travel_time, driver, perm)
                if ok:
                    kw_list.append(_KW(driver, dist_km, act_min))
            if kw_list:
                pool[frozenset(S)] = _pareto(kw_list)
    return pool
