"""
kstar_rule.py -- local pruning frontier K* (Theorem 1 of T4_Local_Pruning_Frontier.tex).
Pure Python (>=3.6, no third-party packages) so it can run next to the thesis code (Py 3.7 + CPLEX).

Input for ONE driver:
    routes : list of (route_id, bundle, K, W), bundle = frozenset of order ids (nonempty, |bundle|<=B)
    q      : dict order_id -> FD price
    lo, hi : bid range Theta = [lo, hi], lo < hi
Output:
    kept   : list of route_ids in K*_i      (keep these; delete the rest -- safe by Thm 1(a))
    margin : dict route_id -> max_{b in Theta} mu_r(b)   (>0 <=> kept)

The rule reads no bid, so it is bid-independent (allocation_range_hash stays fixed).
Apply it per driver AFTER Algorithm A and BEFORE Algorithms B/C; do not feed it a pool that
was already pruned by an unproven rule.
"""
import itertools, math

def _subsets(S):
    S = sorted(S)
    for k in range(len(S) + 1):
        for T in itertools.combinations(S, k):
            yield frozenset(T)

def local_frontier(routes, q, lo, hi, tol=1e-9):
    assert lo < hi
    by_bundle = {}
    for rid, S, K, W in routes:
        by_bundle.setdefault(frozenset(S), []).append((rid, K, W))
    kept, margin = [], {}
    for rid, S, K, W in routes:
        S = frozenset(S)
        qS = sum(q[o] for o in S)
        lines = [(qS, 0.0)]                                  # empty route: all of S to FD
        for T in _subsets(S):
            if not T: continue
            qrest = qS - sum(q[o] for o in T)
            for rid2, K2, W2 in by_bundle.get(T, []):
                if rid2 == rid: continue
                lines.append((K2 + qrest, W2))
        # mu_r = min(lines) - (K + bW) is concave: its max over [lo,hi] is at an endpoint or a kink
        pts = [lo, hi]
        for (a1, w1), (a2, w2) in itertools.combinations(lines, 2):
            if abs(w1 - w2) > 1e-12:
                x = (a2 - a1) / (w1 - w2)
                if lo < x < hi: pts.append(x)
        m = max(min(a + b * w for a, w in lines) - (K + b * W) for b in pts)
        margin[rid] = m
        if m > tol: kept.append(rid)
    return kept, margin
