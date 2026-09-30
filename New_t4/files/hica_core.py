"""
hica_core.py -- brute-force reference implementation used ONLY to verify the
Local Pruning Frontier theorem (T4). Independent of the thesis code base:
exhaustive route enumeration, (K,W) per class, Pareto filter, K* rule, exact WDP.
"""
import itertools, math, random

MIN_PER_KM = 3.0      # 20 km/h
SERVICE = 2.0         # minutes per stop (pickup and delivery)
TOL = 1e-7

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def tt(a, b):
    return dist(a, b) * MIN_PER_KM

class Order:
    def __init__(self, oid, p, d, e_p, l_p, l_d, q, e_d=None):
        self.id, self.p, self.d = oid, p, d
        self.e_p, self.l_p, self.l_d, self.q = e_p, l_p, l_d, q
        # [RQ1 crosscheck 2026-09-23] instance_gen.py that CO ready_time_d
        # (driver phai cho neu den delivery som - xem t6_dp.py._try_delivery
        # dong 155: Bt = A if A > d.e else d.e). e_d=None (mac dinh) => -inf,
        # GIU NGUYEN hanh vi cu cho instance tong hop (khong co delivery
        # window) - chi doi khi instance THAT truyen e_d vao.
        self.e_d = e_d if e_d is not None else float("-inf")

class Driver:
    def __init__(self, did, cls, start, t0, t1, cap, kappa, dest=None, tau=None):
        self.id, self.cls, self.start = did, cls, start
        self.t0, self.t1, self.cap, self.kappa = t0, t1, cap, kappa
        self.dest, self.tau = dest, tau

class Route:
    __slots__ = ("driver", "bundle", "K", "W", "seq", "rid")
    def __init__(self, driver, bundle, K, W, seq, rid=None):
        self.driver, self.bundle, self.K, self.W, self.seq, self.rid = driver, bundle, K, W, seq, rid
    def cost(self, b):
        return self.K + b * self.W

# ---------------------------------------------------------------- routing
def simulate(dr, orders, seq):
    """seq: tuple of (order_id, 'P'|'D'). Returns (K, W) or None if infeasible."""
    pos, t, load, dsum = dr.start, dr.t0, 0, 0.0
    for oid, kind in seq:
        o = orders[oid]
        nxt = o.p if kind == 'P' else o.d
        dsum += dist(pos, nxt); t += tt(pos, nxt); pos = nxt
        if kind == 'P':
            t = max(t, o.e_p)
            if t > o.l_p + 1e-9: return None
            load += 1
            if load > dr.cap: return None
        else:
            t = max(t, o.e_d)
            if t > o.l_d + 1e-9: return None
            load -= 1
        t += SERVICE
    if dr.cls == 'GW':
        if t > dr.t1 + 1e-9: return None
        return dr.kappa * dsum, (t - dr.t0) / 60.0
    # OD: continue to personal destination
    dsum += dist(pos, dr.dest); t += tt(pos, dr.dest)
    if t > dr.t1 + 1e-9: return None
    direct_d = dist(dr.start, dr.dest); direct_t = tt(dr.start, dr.dest)
    det_d, det_t = dsum - direct_d, (t - dr.t0) - direct_t
    if det_t > dr.tau + 1e-9: return None
    return dr.kappa * max(0.0, det_d), max(0.0, det_t) / 60.0

def sequences(bundle):
    """all precedence-feasible pickup/delivery sequences of a bundle"""
    bundle = list(bundle)
    out = []
    def rec(prefix, picked, dropped):
        if len(dropped) == len(bundle):
            out.append(tuple(prefix)); return
        for o in bundle:
            if o not in picked:
                rec(prefix + [(o, 'P')], picked | {o}, dropped)
            elif o not in dropped:
                rec(prefix + [(o, 'D')], picked, dropped | {o})
    rec([], frozenset(), frozenset())
    return out

def pareto(points):
    """points: list of (K,W,seq). keep componentwise non-dominated, dedupe exact ties."""
    pts = sorted(points, key=lambda z: (z[0], z[1]))
    keep, bestW = [], math.inf
    for K, W, s in pts:
        if W < bestW - 1e-12:
            keep.append((K, W, s)); bestW = W
    return keep

def enumerate_pool(dr, orders, B, pareto_filter=True):
    oids = sorted(orders)
    pool = []
    for k in range(1, B + 1):
        for bundle in itertools.combinations(oids, k):
            if k > dr.cap and False: pass
            pts = []
            for s in sequences(bundle):
                kw = simulate(dr, orders, s)
                if kw is not None: pts.append((kw[0], kw[1], s))
            if not pts: continue
            if pareto_filter: pts = pareto(pts)
            for K, W, s in pts:
                pool.append(Route(dr.id, frozenset(bundle), K, W, s))
    for j, r in enumerate(pool): r.rid = f"{dr.id}_r{j}"
    return pool

# ---------------------------------------------------------------- K* rule
def qsum(orders, S):
    return sum(orders[o].q for o in S)

def dominator_lines(r, pool_i, orders):
    """lines (a, w) with value a + b*w for every r' in D(r): r' != r, S' subset of S, plus empty route."""
    S = r.bundle
    lines = [(qsum(orders, S), 0.0)]                       # empty route + FD for all of S
    for rp in pool_i:
        if rp is r or not rp.bundle <= S: continue
        lines.append((rp.K + qsum(orders, S - rp.bundle), rp.W))
    return lines

def envelope(lines, b):
    return min(a + b * w for a, w in lines)

def candidate_points(lines, extra, lo, hi):
    pts = {lo, hi}
    allL = lines + extra
    for (a1, w1), (a2, w2) in itertools.combinations(allL, 2):
        if abs(w1 - w2) > 1e-12:
            x = (a2 - a1) / (w1 - w2)
            if lo < x < hi: pts.add(x)
    return sorted(pts)

def strict_margin(r, pool_i, orders, lo, hi):
    """max over b in Theta of E_r(b) - c_r(b)  (>0  <=>  r in K*). returns (margin, argmax b)."""
    lines = dominator_lines(r, pool_i, orders)
    pts = candidate_points(lines, [(r.K, r.W)], lo, hi)
    # c_r - E_r is convex -> E_r - c_r concave; max over candidates (endpoints + kinks) is exact
    best, bb = -math.inf, None
    for b in pts:
        m = envelope(lines, b) - r.cost(b)
        if m > best: best, bb = m, b
    return best, bb

def kstar(pool_i, orders, lo, hi, tol=1e-9):
    return [r for r in pool_i if strict_margin(r, pool_i, orders, lo, hi)[0] > tol]

# ---------------------------------------------------------------- exact WDP
def solve_wdp(routes, orders, bids, exclude=frozenset()):
    """routes: list[Route]; bids: dict driver->b. exact set-partitioning with FD. returns (Z, chosen routes)."""
    import numpy as np
    from scipy.optimize import milp, LinearConstraint, Bounds   # needs scipy>=1.9 (Python>=3.8)
    R = [r for r in routes if r.rid not in exclude]
    oids = sorted(orders)
    oidx = {o: k for k, o in enumerate(oids)}
    drivers = sorted({r.driver for r in R})
    didx = {d: k for k, d in enumerate(drivers)}
    nR, nO = len(R), len(oids)
    c = np.array([r.cost(bids[r.driver]) for r in R] + [orders[o].q for o in oids])
    Aeq = np.zeros((nO, nR + nO)); Aub = np.zeros((len(drivers), nR + nO))
    for j, r in enumerate(R):
        for o in r.bundle: Aeq[oidx[o], j] = 1
        Aub[didx[r.driver], j] = 1
    for k in range(nO): Aeq[k, nR + k] = 1
    cons = [LinearConstraint(Aeq, 1, 1)]
    if drivers: cons.append(LinearConstraint(Aub, -np.inf, 1))
    res = milp(c, constraints=cons, integrality=np.ones(nR + nO), bounds=Bounds(0, 1),
               options={"mip_rel_gap": 0.0, "presolve": True})
    assert res.status == 0, res.message
    chosen = [R[j] for j in range(nR) if res.x[j] > 0.5]
    return res.fun, chosen

# ---------------------------------------------------------------- instance generator
def random_instance(n, n_gw, n_od, seed, B=3, box=10.0, kappa=0.5,
                    base_fee=8.0, rate=3.0, free_radius=2.0, tw_width=(40, 120)):
    rng = random.Random(seed)
    orders = {}
    for k in range(n):
        p = (rng.uniform(0, box), rng.uniform(0, box))
        d = (rng.uniform(0, box), rng.uniform(0, box))
        e_p = rng.uniform(0, 60)
        l_p = e_p + rng.uniform(*tw_width)
        l_d = l_p + tt(p, d) + rng.uniform(20, 80)
        q = base_fee + rate * max(0.0, dist(p, d) - free_radius)
        orders[f"o{k}"] = Order(f"o{k}", p, d, e_p, l_p, l_d, q)
    drivers = []
    for g in range(n_gw):
        drivers.append(Driver(f"gw{g}", 'GW', (rng.uniform(0, box), rng.uniform(0, box)),
                              0.0, 400.0, 3, kappa))
    for c in range(n_od):
        o = (rng.uniform(0, box), rng.uniform(0, box)); de = (rng.uniform(0, box), rng.uniform(0, box))
        drivers.append(Driver(f"od{c}", 'OD', o, 0.0, 400.0, 3, kappa, dest=de,
                              tau=rng.uniform(25, 60)))
    return orders, drivers
