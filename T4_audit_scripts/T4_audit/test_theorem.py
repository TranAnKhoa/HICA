"""Numerical audit of the Local Pruning Frontier theorem on random Euclidean PDPTW instances."""
import sys, time
from hica_core import *

LO, HI = 18.0, 25.0

def check_DC(pool_i, bgrid):
    """Property (DC): for r' in pool, T subset of S', b: exists route with bundle T, cost<=c_r'(b)."""
    by = {}
    for r in pool_i: by.setdefault(r.bundle, []).append(r)
    viol = 0
    for rp in pool_i:
        S = rp.bundle
        for k in range(1, len(S)):
            for T in itertools.combinations(sorted(S), k):
                T = frozenset(T)
                for b in bgrid:
                    best = min((r.cost(b) for r in by.get(T, [])), default=math.inf)
                    if best > rp.cost(b) + 1e-9: viol += 1
    return viol

def over_margin(r, pool_i, orders, b):
    """min over r' with S' not subset of S of [c_r'(b)+q(S\\S')-c_r(b)]"""
    S = r.bundle; m = math.inf
    for rp in pool_i:
        if rp is r or rp.bundle <= S: continue
        m = min(m, rp.cost(b) + qsum(orders, S - rp.bundle) - r.cost(b))
    return m

def best_b(r, pool_i, orders, n_grid=801):
    """b in Theta maximising delta(b)=min(E_r-c_r, over_margin)."""
    lines = dominator_lines(r, pool_i, orders)
    best, bb = -math.inf, None
    for k in range(n_grid):
        b = LO + (HI - LO) * k / (n_grid - 1)
        d = min(envelope(lines, b) - r.cost(b), over_margin(r, pool_i, orders, b))
        if d > best: best, bb = d, b
    return best, bb

def run(seed, n=8, n_gw=2, n_od=2, B=3, n_bids=150, verbose=True):
    orders, drivers = random_instance(n, n_gw, n_od, seed, B=B)
    pools = {d.id: enumerate_pool(d, orders, B) for d in drivers}
    allR = [r for d in drivers for r in pools[d.id]]
    rep = {"seed": seed, "pool": len(allR)}
    # ---- (DC) property of every own pool
    bgrid = [LO, (LO+HI)/2, HI]
    rep["DC_viol"] = sum(check_DC(pools[d.id], bgrid) for d in drivers)
    # ---- K* per driver
    K = {d.id: kstar(pools[d.id], orders, LO, HI) for d in drivers}
    kept = [r for d in drivers for r in K[d.id]]
    rep["kept"] = len(kept)
    # ---- (a) SAFETY: full vs pruned, base value and every removal value
    rng = random.Random(1000 + seed)
    ids = [d.id for d in drivers]
    maxgap, pay_gap, n_pay = 0.0, 0.0, 0
    for _ in range(n_bids):
        bids = {i: rng.uniform(LO, HI) for i in ids}
        Zf, chf = solve_wdp(allR, orders, bids)
        Zp, chp = solve_wdp(kept, orders, bids)
        maxgap = max(maxgap, abs(Zf - Zp))
        for i in ids:                                    # removal solves (VCG)
            ex_f = {r.rid for r in allR if r.driver == i}
            zf, _ = solve_wdp(allR, orders, bids, exclude=ex_f)
            zp, _ = solve_wdp(kept, orders, bids, exclude=ex_f)
            maxgap = max(maxgap, abs(zf - zp))
            # payment of i (Clarke pivot) if winner in both
            wf = [r for r in chf if r.driver == i]; wp = [r for r in chp if r.driver == i]
            if wf and wp:
                pf = wf[0].cost(bids[i]) + zf - Zf; pp = wp[0].cost(bids[i]) + zp - Zp
                pay_gap = max(pay_gap, abs(pf - pp)); n_pay += 1
    rep["safety_max_value_gap"] = maxgap; rep["payment_max_gap"] = pay_gap; rep["n_payments"] = n_pay
    # ---- (b) TIGHTNESS: abstract adversary for EVERY r in K*
    ok, fail, min_incr = 0, 0, math.inf
    for d in drivers:
        Pi = pools[d.id]
        for r in K[d.id]:
            delta, b = best_b(r, Pi, orders)
            if delta <= 1e-7:            # non-generic (superset tie) -> report separately
                fail += 1; continue
            eps = delta / (2 * B)
            comps = [Route(f"c_{x}", frozenset({x}), eps, 0.0, None, f"c_{x}_r")
                     for x in orders if x not in r.bundle]
            bids = {d.id: b}; bids.update({c.driver: LO for c in comps})
            Z, ch = solve_wdp(Pi + comps, orders, bids)
            Zm, _ = solve_wdp(Pi + comps, orders, bids, exclude={r.rid})
            if r in ch and Zm - Z > 1e-6: ok += 1; min_incr = min(min_incr, Zm - Z)
            else: fail += 1
    rep["tight_ok"], rep["tight_fail"], rep["tight_min_increase"] = ok, fail, min_incr
    # ---- routes pruned by K* : were any ever optimal in the real instance? (must be 0 by (a))
    # ---- comparison with per-driver cross-bundle hull (unsafe rule from report §5)
    hull_pruned_but_essential = 0
    for d in drivers:
        Pi = pools[d.id]
        if not Pi: continue
        onhull = set()
        pts = candidate_points([(r.K, r.W) for r in Pi], [], LO, HI)
        mids = pts + [(a+c)/2 for a, c in zip(pts, pts[1:])]
        for b in mids:
            m = min(r.cost(b) for r in Pi)
            onhull |= {r.rid for r in Pi if r.cost(b) <= m + 1e-9}
        hull_pruned_but_essential += sum(1 for r in K[d.id] if r.rid not in onhull)
    rep["hull_prunes_essential"] = hull_pruned_but_essential
    rep["by_class"] = {cls: (sum(len(pools[d.id]) for d in drivers if d.cls == cls),
                             sum(len(K[d.id]) for d in drivers if d.cls == cls)) for cls in ("GW", "OD")}
    if verbose: print(rep); sys.stdout.flush()
    return rep

if __name__ == "__main__":
    t = time.time()
    reps = [run(s) for s in range(int(sys.argv[1]) if len(sys.argv) > 1 else 5)]
    print("elapsed", round(time.time() - t, 1), "s")
