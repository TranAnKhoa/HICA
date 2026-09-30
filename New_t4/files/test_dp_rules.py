"""Audit of the FD-completion LABEL rules (FW / LB) against brute force."""
import sys, time, random
from hica_core import *
from dp_rules import enumerate_dp, path_cost

LO, HI = 18.0, 25.0

def to_routes(dr, triples, pareto_filter=True):
    by = {}
    for seq, K, W in triples:
        by.setdefault(frozenset(o for o, _ in seq), []).append((K, W, seq))
    pool = []
    for S, pts in by.items():
        if pareto_filter: pts = pareto(pts)
        for K, W, s in pts: pool.append(Route(dr.id, S, K, W, s))
    for j, r in enumerate(pool): r.rid = f"{dr.id}_r{j}"
    return pool

def sig(r):
    return (r.bundle, round(r.K, 9), round(r.W, 9))

def audit_driver(dr, orders, B, rules, check_bounds=True):
    q = {o: orders[o].q for o in orders}
    full, st0 = enumerate_dp(dr, orders, B, q, LO, rules=())
    # (0) DP without rules == brute force enumeration of all feasible sequences
    brute = {s for k in range(1, B+1) for S in itertools.combinations(sorted(orders), k)
             for s in sequences(S) if simulate(dr, orders, s) is not None}
    assert {s for s, _, _ in full} == brute, "DP enumerator differs from brute force"
    log = []
    red, st = enumerate_dp(dr, orders, B, q, LO, rules=rules, log=log)
    fullseq = {s: (K, W) for s, K, W in full}
    # (1) bound validity at EVERY firing, over EVERY feasible completion in the subtree
    viol = 0; checked = 0
    if check_bounds:
        index = {}
        for s in fullseq:
            for k in range(1, len(s) + 1): index.setdefault(s[:k], []).append(s)
        for rec in log:
            kind, L, T, dK_lb, dW_lb, qT = rec
            if kind == "FW":
                prefix = L + ((T, 'P'),); Tset = {T}
            else:
                prefix = L; Tset = set(T)
            for s in index.get(prefix, []):
                K1, W1 = path_cost(dr, orders, s)
                K2, W2 = path_cost(dr, orders, tuple(x for x in s if x[0] not in Tset))
                checked += 1
                if K1 - K2 < dK_lb - 1e-9 or W1 - W2 < dW_lb - 1e-9: viol += 1
    # (2) K* preservation
    R = to_routes(dr, full); Rp = to_routes(dr, red)
    Kfull = {sig(r) for r in kstar(R, orders, LO, HI)}
    Kred = {sig(r) for r in kstar(Rp, orders, LO, HI)}
    return dict(full_routes=len(full), red_routes=len(red), pareto_full=len(R), pareto_red=len(Rp),
                ext0=st0["ext"], ext=st["ext"], fw=st["fw"], lb=st["lb"],
                firings=len(log), completions_checked=checked, bound_viol=viol,
                kstar_equal=(Kfull == Kred), kstar=len(Kfull)), (R, Rp)

def run(seed, n=8, B=3, rules=('FW', 'LB'), n_bids=40, wdp=True, **kw):
    orders, drivers = random_instance(n, 2, 2, seed, B=B, **kw)
    tot = {}; pools_full, pools_red = [], []
    for d in drivers:
        rep, (R, Rp) = audit_driver(d, orders, B, rules)
        for k, v in rep.items():
            if isinstance(v, bool): tot[k] = tot.get(k, True) and v
            else: tot[k] = tot.get(k, 0) + v
        pools_full += R; pools_red += [r for r in Rp if sig(r) in {sig(x) for x in kstar(Rp, orders, LO, HI)}]
    if wdp:
        rng = random.Random(seed + 77); gap = 0.0
        for _ in range(n_bids):
            bids = {d.id: rng.uniform(LO, HI) for d in drivers}
            Zf, _ = solve_wdp(pools_full, orders, bids); Zr, _ = solve_wdp(pools_red, orders, bids)
            gap = max(gap, abs(Zf - Zr))
        tot["wdp_gap"] = gap
    return tot

if __name__ == "__main__":
    for s in range(int(sys.argv[1]) if len(sys.argv) > 1 else 3):
        t = time.time(); r = run(s); r["sec"] = round(time.time() - t, 1); print(s, r); sys.stdout.flush()
