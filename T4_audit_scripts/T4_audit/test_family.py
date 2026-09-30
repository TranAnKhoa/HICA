"""Price-of-locality family: |K*_i| = Theta(n^B) while only n routes are ever optimal
over the WHOLE bid space Theta^m. Fully geometric (Euclidean, real OD competitors)."""
import sys
from math import comb
from hica_core import *
from test_realizable import competitor_od
LO, HI = 18.0, 25.0

def family(n, seed=0, B=3):
    rng = random.Random(seed)
    orders = {}
    for k in range(n):
        p = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
        d = (6 + rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
        q = 8.0 + 3.0 * max(0.0, dist(p, d) - 2.0)      # same FD tariff shape as RQ1
        orders[f"o{k}"] = Order(f"o{k}", p, d, 0.0, 500.0, 1000.0, q)
    gw = Driver("gw0", 'GW', (-2.0, 0.0), 0.0, 1000.0, B, 0.5)
    return orders, gw

def run(n, B=3, n_bids=200):
    orders, gw = family(n, B=B)
    Pi = enumerate_pool(gw, orders, B)
    K = kstar(Pi, orders, LO, HI)
    comps = [enumerate_pool(competitor_od(o), orders, B)[0] for o in orders.values()]
    allR = Pi + comps
    rng = random.Random(7); ever = set()
    for _ in range(n_bids):
        bids = {"gw0": rng.uniform(LO, HI)}; bids.update({c.driver: rng.uniform(LO, HI) for c in comps})
        _, ch = solve_wdp(allR, orders, bids); ever |= {r.rid for r in ch}
    # certificate that gw0 is NEVER optimal for ANY bid profile (not only sampled ones):
    worst_comp = max(c.cost(HI) for c in comps)
    cheapest_gw = min(r.cost(LO) / len(r.bundle) for r in Pi)
    gw_ever = [r for r in Pi if r.rid in ever]
    print(f"n={n:2d}  |pool gw0|={len(Pi):4d}  sum_k C(n,k)={sum(comb(n,k) for k in range(1,B+1)):4d}  "
          f"|K*(gw0)|={len(K):4d}  routes ever optimal={len(ever):3d} (gw0: {len(gw_ever)})  "
          f"certificate: min_r c_r(lo)/|S|={cheapest_gw:.2f} > max competitor cost={worst_comp:.2f}: {cheapest_gw > worst_comp}")
    sys.stdout.flush()

if __name__ == "__main__":
    for n in (4, 6, 8, 10, 12): run(n)
