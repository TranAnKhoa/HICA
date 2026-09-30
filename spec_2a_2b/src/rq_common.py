"""RQ_Master.md - helpers dung chung cho RQ2-RQ5 (Guideline_Total/RQ_Master.md).

Dung lai NGUYEN ha tang RQ1: instance_gen (cung seed formula), rq1_cost_gen
(theta, q_o), dp_labeling.build_route_pool (Algorithm A), t8_cplex.solve_wdp
(Algorithm B). Chi THEM: loc pool theo |S|<=B, heuristic bundle (HEUR),
solver WDP voi ham cost tuy bien (dung chung cho true cost / pay-as-bid / posted
price), VCG naive, posted price, pay-as-bid best response.

Moi truong: Python 3.7.7 + CPLEX 12.10.
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RQ1_LOCKED = os.path.join(ROOT, "results", "rq1_locked_params.json")
OUT_DIR = os.path.join(ROOT, "results", "rq_all")
LOCKED_ALL = os.path.join(OUT_DIR, "rq_all_locked_params.json")

TW_WIDTH = 120        # [LOCK] ke thua RQ1
TAU = 30.0            # [LOCK] ke thua RQ1
THETA_LO, THETA_HI = RC.THETA_MIN, RC.THETA_MAX   # 18, 25 - mien bid Theta
EPS = 1e-6

_rq1 = None


def rq1_params():
    global _rq1
    if _rq1 is None:
        with open(RQ1_LOCKED, encoding="utf-8") as f:
            _rq1 = json.load(f)
    return _rq1


def corridor_for(align):
    t = rq1_params()["alignment"]["locked_targets"]["%.2f" % align]
    return t["corridor_share"], t["corridor_buffer_km"]


# ---------------------------------------------------------------------------
# Instance
# ---------------------------------------------------------------------------

def make_rq1_instance(align, n, n_gw, n_od, rep, B=3):
    """DUNG instance cua RQ1 main grid (cung gen_seed/theta_seed - B=3 trong
    cong thuc seed LUON co dinh, ke ca khi B menu khac). B chi dat capacity
    driver; generator KHONG dung B trong RNG => hinh hoc giong het giua cac B."""
    cs, cb = corridor_for(align)
    gen_seed = IG.stable_seed(n, 3, 3, align, n_gw, n_od, rep, "rq1_main_grid")
    theta_seed = IG.stable_seed(n, 3, 3, align, n_gw, n_od, rep, "rq1_main_grid_theta")
    nd = n_gw + n_od
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=TW_WIDTH, n_drivers=nd, seed=gen_seed, tau=TAU,
        spatial_mode="dispersed", corridor_share=cs, corridor_buffer_km=cb,
        gw_od_ratio=n_gw / float(nd))
    theta = RC.assign_theta(random.Random(theta_seed), drivers)
    q = RC.assign_q_o(orders, tt)
    return drivers, orders, tt, meta, theta, q


RQ5_VARIANTS = {
    "V0_baseline": {},
    "V1_tw60": {"tw": 60},
    "V2_tw240": {"tw": 240},
    "V3_tau20": {"tau": 20.0},
    "V4_tau45": {"tau": 45.0},
    "V5_fd075": {"fd_scale": 0.75},
    "V6_fd125": {"fd_scale": 1.25},
    "V7_clustered": {"spatial": "clustered"},
    "V8_theta15_30": {"theta_range": (15.0, 30.0)},
    "V9_n25": {"n": 25},
    "V10_n30": {"n": 30},
}
RQ5_SUPPLY_BASE = [(2, 2), (3, 2), (2, 3), (3, 3)]
RQ5_SUPPLY_SCALE = [(3, 3), (4, 3), (3, 4), (4, 4)]


def make_rq5_instance(variant, n_gw, n_od, rep, B=3):
    v = RQ5_VARIANTS[variant]
    n = v.get("n", 15)
    tw = v.get("tw", TW_WIDTH)
    tau = v.get("tau", TAU)
    spatial = v.get("spatial", "dispersed")
    cs, cb = corridor_for(0.50)
    nd = n_gw + n_od
    gen_seed = IG.stable_seed(n, n_gw, n_od, rep, "rq5")
    theta_seed = IG.stable_seed(n, n_gw, n_od, rep, "rq5_theta")
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=tw, n_drivers=nd, seed=gen_seed, tau=tau,
        spatial_mode=spatial, corridor_share=cs, corridor_buffer_km=cb,
        gw_od_ratio=n_gw / float(nd))
    lo, hi = v.get("theta_range", (THETA_LO, THETA_HI))
    trng = random.Random(theta_seed)
    theta = {d["id"]: trng.uniform(lo, hi) for d in drivers}
    q = RC.assign_q_o(orders, tt)
    s = v.get("fd_scale", 1.0)
    q = {o: s * c for o, c in q.items()}
    return drivers, orders, tt, meta, theta, q, tw


# ---------------------------------------------------------------------------
# Pool helpers
# ---------------------------------------------------------------------------

def build_pool(tt, drivers, orders, B):
    t0 = time.perf_counter()
    pool, agg = DL.build_route_pool(tt, drivers, orders, B, B)
    return pool, time.perf_counter() - t0


def filter_pool(pool_by_driver, maxB):
    return {d: {S: kw for S, kw in p.items() if 1 <= len(S) <= maxB}
            for d, p in pool_by_driver.items()}


def restrict_pool(pool_by_driver, driver_ids):
    ids = set(driver_ids)
    return {d: p for d, p in pool_by_driver.items() if d in ids}


def pool_size(pool_by_driver):
    return sum(len(kw) for p in pool_by_driver.values() for kw in p.values())


def heur_blocks(orders, tt, tw_width):
    """RQ_Master.md §3.2 - phan hoach heuristic co dinh, bid-independent."""
    ids = sorted(orders.keys(), key=lambda s: int(s[1:]))
    km = lambda a, b: tt(a, b) * RC.SPEED_KMH / 60.0
    d = {}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = orders[ids[i]], orders[ids[j]]
            d[(ids[i], ids[j])] = (km(a["pickup_node"], b["pickup_node"])
                                   + km(a["delivery_node"], b["delivery_node"]))
    if not d:
        return [frozenset([o]) for o in ids]
    vals = sorted(d.values())
    k = 0.25 * (len(vals) - 1)
    f = int(k)
    dmax = vals[f] + (vals[min(f + 1, len(vals) - 1)] - vals[f]) * (k - f)

    def ok_pair(x, y):
        key = (x, y) if (x, y) in d else (y, x)
        return (d[key] <= dmax + 1e-12
                and abs(orders[x]["ready_time_p"] - orders[y]["ready_time_p"]) <= tw_width)

    group = {o: frozenset([o]) for o in ids}
    for (x, y), _v in sorted(d.items(), key=lambda kv: (kv[1], kv[0])):
        gx, gy = group[x], group[y]
        if gx == gy:
            continue
        u = gx | gy
        if len(u) > 3:
            continue
        ul = sorted(u)
        if all(ok_pair(ul[i], ul[j]) for i in range(len(ul)) for j in range(i + 1, len(ul))):
            for o in u:
                group[o] = u
    return sorted(set(group.values()), key=lambda g: sorted(g))


def heur_pool(pool_b3, blocks):
    allowed = set(b for b in blocks if len(b) >= 2)
    return {d: {S: kw for S, kw in p.items() if len(S) == 1 or S in allowed}
            for d, p in pool_b3.items()}


# ---------------------------------------------------------------------------
# WDP voi ham cost tuy bien
# ---------------------------------------------------------------------------

def _san(s):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def solve(pool_by_driver, cost_fn, fd_cost, order_ids, excluded=None, restrict=None):
    """cost_fn(did, S, K, W) -> cost hoac None (route khong duoc dua vao).
    Tra dict z, status, assign {did: (S,K,W,cost)}, fd_orders, wall."""
    import t8_cplex as T8
    drivers, info = {}, {}
    for did, p in pool_by_driver.items():
        routes, ctr = [], 0
        for S, kwl in p.items():
            if not S:
                continue
            for (K, W) in kwl:
                c = cost_fn(did, S, K, W)
                if c is None:
                    continue
                rid = "%s_r%d" % (did, ctr)
                ctr += 1
                routes.append((rid, S, c))
                info["x_" + _san(rid)] = (did, S, K, W, c)
        drivers[did] = {"routes": routes}
    t0 = time.perf_counter()
    r = T8.solve_wdp(drivers, list(order_ids), fd_cost, excluded_driver=excluded,
                     restrict_orders=restrict)
    wall = time.perf_counter() - t0
    assign = {}
    for v in r["alloc_x"]:
        did, S, K, W, c = info[v]
        assign[did] = (S, K, W, c)
    target = set(order_ids) if restrict is None else set(restrict)
    covered = set().union(*[set(a[0]) for a in assign.values()]) if assign else set()
    return dict(z=r["z"], status=r["status"], assign=assign,
                fd_orders=sorted(target - covered), wall=wall)


def true_cost_fn(theta):
    return lambda did, S, K, W: K + theta[did] * W


def is_optimal(status):
    return status is not None and "optimal" in status and "infeasible" not in status


def alloc_stats(res, n_orders):
    a = res["assign"]
    n_crowd = sum(len(v[0]) for v in a.values())
    return dict(fd_rate=len(res["fd_orders"]) / float(n_orders),
                mean_bundle=(n_crowd / float(len(a))) if a else 0.0,
                n_routes=len(a))


# ---------------------------------------------------------------------------
# RQ3 mechanisms
# ---------------------------------------------------------------------------

def vcg(pool, theta, q, order_ids):
    """Naive Algorithm C. Tra Z*, payments, rents, true costs, timing."""
    cf = true_cost_fn(theta)
    t0 = time.perf_counter()
    full = solve(pool, cf, q, order_ids)
    statuses = [full["status"]]
    pay, rent, cost, zminus = {}, {}, {}, {}
    for did, (S, K, W, c) in full["assign"].items():
        rm = solve(pool, cf, q, order_ids, excluded=did)
        statuses.append(rm["status"])
        zminus[did] = rm["z"]
        cost[did] = c
        rent[did] = rm["z"] - full["z"]
        pay[did] = c + rent[did]
    wall = time.perf_counter() - t0
    payout = sum(pay.values()) + sum(q[o] for o in full["fd_orders"])
    return dict(Z=full["z"], full=full, pay=pay, rent=rent, cost=cost, zminus=zminus,
                payout=payout, wall=wall, statuses=statuses)


def posted(pool, theta, q, order_ids, lam):
    price = {o: lam * q[o] for o in q}

    def cf(did, S, K, W):
        p = sum(price[o] for o in S)
        return p if p >= K + theta[did] * W - 1e-9 else None

    r = solve(pool, cf, q, order_ids)
    true_c = sum(K + theta[d] * W for d, (S, K, W, c) in r["assign"].items()) \
        + sum(q[o] for o in r["fd_orders"])
    return dict(payout=r["z"], true_cost=true_c, res=r)


def bid_grid(theta_i, hi=THETA_HI, step=0.5):
    g, x = [], theta_i
    while x < hi - 1e-9:
        g.append(x)
        x += step
    if theta_i <= hi + 1e-12:
        g.append(hi)
    return g


def pab_br(pool, theta, q, order_ids, hi=THETA_HI, step=0.5, trace=False):
    """Pay-as-bid: best response don phuong cua moi driver (others truthful),
    roi ap dong thoi. Tra bids, payout, true_cost cua allocation, profit."""
    bids, tr = {}, {}
    for did in pool:
        best_b, best_pi = theta[did], 0.0
        tr[did] = []
        if theta[did] > hi:          # khong the bid that trong mien Theta
            bids[did] = theta[did]
            continue
        for b in bid_grid(theta[did], hi, step):
            th = dict(theta)
            th[did] = b
            r = solve(pool, true_cost_fn(th), q, order_ids)
            tr[did].append((b, r["z"]))
            if did not in r["assign"]:
                break                 # don dieu: bid cao hon cung khong thang
            S, K, W, c = r["assign"][did]
            pi = (b - theta[did]) * W
            if pi > best_pi + 1e-12:
                best_b, best_pi = b, pi
        bids[did] = best_b
    r = solve(pool, true_cost_fn(bids), q, order_ids)
    true_c = sum(K + theta[d] * W for d, (S, K, W, c) in r["assign"].items()) \
        + sum(q[o] for o in r["fd_orders"])
    rent = sum((bids[d] - theta[d]) * W for d, (S, K, W, c) in r["assign"].items())
    out = dict(bids=bids, payout=r["z"], true_cost=true_c, rent=rent, res=r)
    if trace:
        out["trace"] = tr
    return out
