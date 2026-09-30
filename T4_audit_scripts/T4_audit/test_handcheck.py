# Hand-checkable twin example (numbers from the thesis worked example, driver g1)
from hica_core import *
orders = {"o1": Order("o1",(0,0),(0,0),0,0,0,15.0), "o2": Order("o2",(0,0),(0,0),0,0,0,45.0)}
g1 = [Route("g1", frozenset({"o1"}), 6.0, 0.6, None, "r_a"),
      Route("g1", frozenset({"o2"}), 8.0, 0.8, None, "r_b"),
      Route("g1", frozenset({"o1","o2"}), 11.0, 1.2, None, "r_c")]
lo, hi = 18.0, 25.0
for r in g1:
    m, b = strict_margin(r, g1, orders, lo, hi)
    print(f"{r.rid} bundle={sorted(r.bundle)} max_b(E_r - c_r)={m:+.3f} at b={b:.2f} ->", "KEEP (K*)" if m>1e-9 else "PRUNE")
# Twin instances, same local view of g1
# I0: only FD.   I1: add competitor for o1 with cost eps
eps = 0.5
bids = {"g1": 18.0, "c": 18.0}
Z0, ch0 = solve_wdp(g1, orders, bids); print("I0: Z* =", round(Z0,3), [r.rid for r in ch0])
comp = Route("c", frozenset({"o1"}), eps, 0.0, None, "comp_o1")
Z1, ch1 = solve_wdp(g1+[comp], orders, bids); print("I1: Z* =", round(Z1,3), [r.rid for r in ch1])
Z1m, _ = solve_wdp(g1+[comp], orders, bids, exclude={"r_b"}); print("I1 without r_b: Z* =", round(Z1m,3))
# is r_b ever optimal in I0 over the whole Theta?
act = set()
for k in range(701):
    b = lo + (hi-lo)*k/700
    _, ch = solve_wdp(g1, orders, {"g1": b}); act |= {r.rid for r in ch}
print("I0 routes ever optimal on Theta:", act)
# cross-bundle per-driver hull prunes r_b (Pareto dominated by r_a across bundles)
print("r_a Pareto-dominates r_b across bundles:", g1[0].K<=g1[1].K and g1[0].W<=g1[1].W)
