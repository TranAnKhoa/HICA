"""C5h = C5 + an exact dead-end filter (feasibility look-ahead), and C4h (same, post-hoc frontier).

Observation (2026-10-07): in C5, occasional drivers account for 50-62% of all extension attempts on the
label instances, while their frontier holds 6-7 routes. The reason is in experiments/T2BFS/t6_dp.py: the
detour budget of an occasional driver is checked only when the home leg is added (_try_home); pickups and
deliveries never ask whether home can still be reached in time, so prefixes that can no longer be
completed are extended to the end.

Dead-end filter, applied to every new label L = (v, IV, C, t, K, W) right after _try_pickup/_try_delivery:
  (a) every order j on board must still be deliverable:  t + tau(v, d_j) <= l(d_j)
  (b) occasional driver: home must still be reachable by its deadline l(home):
        LB = max( t + tau(v, home),  max_{j in IV} [ max(t + tau(v, d_j), e(d_j)) + s(d_j) + tau(d_j, home) ] )
        LB <= l(home)
Both are lower bounds on what any completion needs (triangle inequality, nonnegative waiting and service),
so a label that fails has no feasible completion. If a failing label dominates another label of the same key
(same v and IV, no later clock), that label fails too, so removing failing labels never changes which live
labels survive Layer 1: R and K* are unchanged exactly. A margin of 1e-6 minutes is added to every test so
that floating-point rounding can never remove a feasible label.
"""
import paths  # noqa: F401
from collections import defaultdict

from variants import D, C, INF, LO, HI, new_cnt, _bundle_front, _kstar_filter_bundle
import variants as V

MARGIN = 1e-6


def make_dead(tt, pd, home):
    deliveries = {j: pd[j][1] for j in pd}
    if home is None:
        def dead(nl):
            t, v = nl.t, nl.v
            for j in nl.IV:
                d = deliveries[j]
                if t + tt(v, d.id) > d.l + MARGIN:
                    return True
            return False
        return dead
    hid, hl = home.id, home.l

    def dead(nl):
        t, v = nl.t, nl.v
        lb = t + tt(v, hid)
        for j in nl.IV:
            d = deliveries[j]
            a = t + tt(v, d.id)
            if a > d.l + MARGIN:
                return True
            x = (a if a > d.e else d.e) + d.s + tt(d.id, hid)
            if x > lb:
                lb = x
        return lb > hl + MARGIN
    return dead


def run_tier_h(tt, driver, orders, B, q=None, lo=LO, hi=HI, inloop=True, rule_tables=None, dead_log=None):
    """rule_tables=(TT, KK): also apply Layer 3 (fastrule implementation) to Layer-1 survivors (variant C8h).
    dead_log: list; every label removed by the dead-end filter is appended (audit)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_cnt()
    cnt["killed_dead"] = 0
    dead0 = make_dead(tt, pd, home)
    if dead_log is None:
        dead = dead0
    else:
        def dead(nl):
            if dead0(nl):
                dead_log.append(nl)
                return True
            return False
    rule = rule_tables is not None
    if rule:
        import fastrule as FR
        TT, KK = rule_tables
        max_e = max([p.e for p, _d in pd.values()] +
                    [d.e for _p, d in pd.values() if d.e > -INF] + [-INF])
        lab0 = FR.F.LabelA(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
        lab0.sc = {}

        def rule_pass(survivors):
            out = []
            for l in survivors:
                if l.action is None:
                    out.append(l)
                    continue
                kind, oid = l.action
                pt = pd[oid][0] if kind == "pickup" else pd[oid][1]
                nsc = FR.next_sc_fast(l.parent, kind, oid, pt, TT, KK)
                if FR.rule_fires_fast(l, nsc, TT, pd, q, lo, B, max_e, cnt, KK):
                    cnt["killed_rule"] += 1
                    continue
                w = FR.F.LabelA(l.v, l.IV, l.Cd, l.t, l.K, l.W, parent=l.parent, action=l.action)
                w.sc = nsc
                out.append(w)
            return out
    else:
        lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete = defaultdict(list)
    pool = {}
    kstar_by_bundle = {}
    cur = [lab0]
    m = 0
    while cur:
        by_key = defaultdict(list)
        for l in cur:
            by_key[l.key()].append(l)
        alive = []
        for k, labs in by_key.items():
            kept = D._filter_dominated_labels(labs)
            cnt["killed_layer1"] += len(labs) - len(kept)
            alive.extend(kept)
        if rule:
            alive = rule_pass(alive)
        if not has_home:
            for l in alive:
                if not l.IV and len(l.Cd) >= 1:
                    complete[l.Cd].append(l)
                    cnt["complete_labels"] += 1
        nxt = []
        for lab in alive:
            for j in sorted(lab.IV):
                cnt["ext_attempts"] += 1
                nl = D._try_delivery(tt, driver, pd, lab, j)
                if nl is None:
                    continue
                if (nl.IV or has_home) and dead(nl):   # a GW label with nothing on board is complete
                    cnt["killed_dead"] += 1
                    continue
                cnt["labels_created"] += 1
                nxt.append(nl)
            if has_home and not lab.IV and len(lab.Cd) >= 1:
                cnt["ext_attempts"] += 1
                nl = D._try_home(tt, driver, home, lab)
                if nl is not None:
                    cnt["labels_created"] += 1
                    complete[nl.Cd].append(nl)
                    cnt["complete_labels"] += 1
            if len(lab.IV) + len(lab.Cd) < B:
                for j in order_ids:
                    cnt["ext_attempts"] += 1
                    nl = D._try_pickup(tt, driver, pd, lab, j, B)
                    if nl is None:
                        continue
                    if dead(nl):
                        cnt["killed_dead"] += 1
                        continue
                    cnt["labels_created"] += 1
                    nxt.append(nl)
        if m % 2 == 0 and m >= 2:
            k = m // 2
            for S in [S for S in complete if len(S) == k]:
                front = _bundle_front(driver, complete.pop(S))
                if not front:
                    continue
                if inloop:
                    kk = _kstar_filter_bundle(S, front, kstar_by_bundle, q, lo, hi)
                    if kk:
                        kstar_by_bundle[S] = kk
                        pool[S] = kk
                else:
                    pool[S] = front
        cur = nxt
        m += 1
    cnt["routes_kept"] = sum(len(v) for v in pool.values())
    return pool, cnt


def run_c5h(tt, driver, orders, B, q=None, **kw):
    return run_tier_h(tt, driver, orders, B, q=q, inloop=True)


def run_c4h(tt, driver, orders, B, q=None, **kw):
    return run_tier_h(tt, driver, orders, B, q=q, inloop=False)


def build_all_c8h(tt, drivers, orders, q, B, tables):
    """C8h = C5h + Layer 3 (fast implementation), frontier in the loop."""
    pool, per = {}, {}
    for dr in drivers:
        p, c = run_tier_h(tt, dr, orders, B, q=q, inloop=True, rule_tables=tables)
        pool[dr["id"]] = p
        per[dr["id"]] = (dr["cls"], c)
    return pool, per


V.VARIANTS.update(C5h=run_c5h, C4h=run_c4h)
V.INLOOP.update({"C5h"})
build_all = V.build_all
