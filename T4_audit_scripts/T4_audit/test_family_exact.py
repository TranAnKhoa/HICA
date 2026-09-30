"""Exact (co-located) construction used in the proof of the price-of-locality theorem."""
from math import comb
import random
from hica_core import *
LO, HI, S_STOP = 18.0, 25.0, SERVICE
def build(n, B=3, dAP=2.0, dPD=6.0, kappa=0.5):
    P, D = (0.0, 0.0), (dPD, 0.0)
    q0 = 8.0 + 3.0 * max(0.0, dPD - 2.0)
    orders = {f"o{k}": Order(f"o{k}", P, D, 0.0, 1e6, 1e6, q0) for k in range(n)}
    gw = Driver("gw", 'GW', (-dAP, 0.0), 0.0, 1e6, B, kappa)
    ods = [Driver(f"od{k}", 'OD', P, 0.0, 1e6, B, kappa, dest=D, tau=2*S_STOP) for k in range(n)]
    return orders, gw, ods, q0
for n in (3, 5, 7, 9):
    B = 3
    orders, gw, ods, q0 = build(n, B)
    Pg = enumerate_pool(gw, orders, B)
    Kg = kstar(Pg, orders, LO, HI)
    Pods = [enumerate_pool(o, orders, B) for o in ods]
    assert all(len(P) == n and all(len(r.bundle) == 1 and r.K == 0 for r in P) for P in Pods)
    allR = Pg + [r for P in Pods for r in P]
    rng = random.Random(3); gw_used = 0
    for _ in range(150):
        bids = {"gw": rng.uniform(LO, HI)}; bids.update({o.id: rng.uniform(LO, HI) for o in ods})
        _, ch = solve_wdp(allR, orders, bids); gw_used += any(r.driver == "gw" for r in ch)
    # analytic certificate of (ii): kappa*(dAP+dPD) > B*(HI-LO)*2s/60
    cert = 0.5 * 8.0 > B * (HI - LO) * 2 * S_STOP / 60
    print(f"n={n}: |pool gw|={len(Pg)} = sum C(n,k)={sum(comb(n,k) for k in range(1,B+1))}; |K*(gw)|={len(Kg)}; "
          f"q0={q0}; gw optimal in {gw_used}/150 sampled profiles; analytic certificate: {cert}")
