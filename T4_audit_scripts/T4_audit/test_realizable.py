"""Geometric realisability of the adversary: competitors are genuine OD drivers
(origin = pickup of x, destination = delivery of x, detour budget = service time),
whose pools are produced by the SAME exhaustive enumerator as everyone else."""
import sys
from hica_core import *
from test_theorem import LO, HI, over_margin

def competitor_od(o, kappa=0.5):
    return Driver(f"cod_{o.id}", 'OD', o.p, o.e_p, 1e9, 1, kappa, dest=o.d, tau=2*SERVICE)

def realisable_margin(r, Pi, orders, b, lam):
    S = r.bundle
    m = envelope(dominator_lines(r, Pi, orders), b) - r.cost(b)
    for rp in Pi:
        if rp is r or rp.bundle <= S: continue
        cred = sum(min(lam[x], orders[x].q) for x in rp.bundle - S)
        m = min(m, rp.cost(b) + qsum(orders, S - rp.bundle) - r.cost(b) - cred)
    return m

def run(seed, n=8, B=3):
    orders, drivers = random_instance(n, 2, 2, seed, B=B)
    comp_pools = {}
    for x, o in orders.items():
        cd = competitor_od(o); P = enumerate_pool(cd, orders, B)
        assert len(P) == 1 and P[0].bundle == frozenset({x}) and P[0].K < 1e-9, (x, [(r.bundle, r.K, r.W) for r in P])
        comp_pools[x] = P
    lam = {x: LO * comp_pools[x][0].W for x in orders}      # competitor bids at theta_min
    stats = dict(kept=0, ess=0, pred_ess=0, pred_ok=0)
    for d in drivers:
        Pi = enumerate_pool(d, orders, B)
        for r in kstar(Pi, orders, LO, HI):
            stats["kept"] += 1
            grid = [LO + (HI-LO)*k/400 for k in range(401)]
            m, b = max((realisable_margin(r, Pi, orders, bb, lam), bb) for bb in grid)
            comps = [comp_pools[x][0] for x in orders if x not in r.bundle]
            bids = {d.id: b}; bids.update({c.driver: LO for c in comps})
            Z, ch = solve_wdp(Pi + comps, orders, bids)
            Zm, _ = solve_wdp(Pi + comps, orders, bids, exclude={r.rid})
            ess = (Zm - Z > 1e-6)
            stats["ess"] += ess; pred = m > 1e-7; stats["pred_ess"] += pred
            stats["pred_ok"] += (pred <= ess)          # prediction => essential must never fail
    print(seed, stats, "lambda(USD)=%.2f" % max(lam.values())); sys.stdout.flush()

if __name__ == "__main__":
    for s in range(int(sys.argv[1]) if len(sys.argv) > 1 else 4): run(s)
