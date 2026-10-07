"""A faster implementation of the SAME Layer-3 rule (fdrule_dp._next_sc / _rule_fires).

Only the implementation changes; every decision is identical:
  * travel times are read from a table TT[a][b] = travel_time(a, b), built once per instance;
  * the distance term KAPPA * _km(travel_time(a, b)) is read from KK[a][b], computed with the
    same float expression, so every shortcut triple and every test value is bit-identical;
  * the loops, the order of the tests and the cheap A = 0 pre-test are unchanged.
gate_c8.py checks that C8f produces exactly the same counters (labels killed by the rule,
extensions, routes) and the same K* as C8 on every instance.

Fairness: the travel-time table is also handed to every other variant (C1, C4, C5, ...) in the
"matrix" timing setting (timing_c8.py), so that no variant profits alone from the table.
"""
import paths  # noqa: F401
from variants import D, F, INF, new_cnt, _bundle_front, _kstar_filter_bundle, LO, HI, C
from collections import defaultdict

KAPPA = D.KAPPA
TOL = F.TOL


def node_ids(drivers, orders):
    ids = set()
    for d in drivers:
        ids.add(d["start_node"])
        if d.get("home_node") is not None:
            ids.add(d["home_node"])
    for o in orders.values():
        ids.add(o["pickup_node"])
        ids.add(o["delivery_node"])
    return sorted(ids)


def make_tables(tt, ids):
    TT = {a: {b: tt(a, b) for b in ids} for a in ids}
    KK = {a: {b: KAPPA * D._tt_to_km(TT[a][b]) for b in ids} for a in ids}
    return TT, KK


def matrix_tt(TT):
    """A travel-time function that reads the table (same values as the original function)."""
    def tt(a, b):
        return TT[a][b]
    return tt


def next_sc_fast(parent, kind, oid, pt, TT, KK):
    nsc = {}
    uid, ue, us = pt.id, pt.e, pt.s
    for j, (Kj, vj, rj) in parent.sc.items():
        if j == oid:
            nsc[j] = (Kj, vj, rj)
        else:
            a = rj + TT[vj][uid]
            nsc[j] = (Kj + KK[vj][uid], uid, (a if a >= ue else ue) + us)
    if kind == "pickup":
        nsc[oid] = (parent.K, parent.v, parent.t)
    return nsc


def rule_fires_fast(nl, nsc, TT, pd, q, lo, B, max_e, cnt, KK):
    picked = nl.IV | nl.Cd
    v, K, t = nl.v, nl.K, nl.t
    for j, (Kj, vj, rj) in nsc.items():
        qj = q[j]
        TTj = TT[vj]
        jt = TTj[v]
        dK = K - Kj - KK[vj][v]
        delta0 = t - rj - jt
        if dK + lo * (delta0 if delta0 > 0.0 else 0.0) / 60.0 < qj + TOL:
            continue                                   # cannot fire even with A = 0
        A = 0.0
        for w in nl.IV:
            e_d = pd[w][1].e
            if e_d > -INF:
                x = e_d - (rj + TTj[pd[w][1].id])
                if x > A:
                    A = x
        if len(picked) < B and rj < max_e:
            cnt["a_evals"] += 1
            TTv = TT[v]
            for w, (wp, wd) in pd.items():
                if w in picked:
                    continue
                if t + TTv[wp.id] <= wp.l + 1e-9:
                    x = wp.e - (rj + TTj[wp.id])
                    if x > A:
                        A = x
                if wd.e > -INF and t + TTv[wd.id] <= wd.l + 1e-9:
                    x = wd.e - (rj + TTj[wd.id])
                    if x > A:
                        A = x
        d = delta0 - A
        dW = (d if d > 0.0 else 0.0) / 60.0
        if dK + lo * dW >= qj + TOL:
            return True
    return False


def run_tier_rule_fast(tt, driver, orders, B, q=None, lo=LO, hi=HI, inloop=True, tables=None):
    """C8f: identical to variants3.run_tier_rule(rule=True), with the fast rule implementation."""
    TT, KK = tables
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_cnt()
    max_e = max([p.e for p, _d in pd.values()] +
                [d.e for _p, d in pd.values() if d.e > -INF] + [-INF])
    lab0 = F.LabelA(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    lab0.sc = {}
    LabelA = F.LabelA

    def rule_pass(survivors):
        out = []
        for l in survivors:
            if l.action is None:
                out.append(l)
                continue
            kind, oid = l.action
            pt = pd[oid][0] if kind == "pickup" else pd[oid][1]
            nsc = next_sc_fast(l.parent, kind, oid, pt, TT, KK)
            if rule_fires_fast(l, nsc, TT, pd, q, lo, B, max_e, cnt, KK):
                cnt["killed_rule"] += 1
                continue
            w = LabelA(l.v, l.IV, l.Cd, l.t, l.K, l.W, parent=l.parent, action=l.action)
            w.sc = nsc
            out.append(w)
        return out

    complete = defaultdict(list)
    pool = {}
    kstar_by_bundle = {}
    cur = [lab0]
    m = 0
    while cur:
        by_key = defaultdict(list)
        for l in cur:
            by_key[l.key()].append(l)
        surv = []
        for k, labs in by_key.items():
            kept = D._filter_dominated_labels(labs)
            cnt["killed_layer1"] += len(labs) - len(kept)
            surv.extend(kept)
        alive = rule_pass(surv)
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


def build_all_fast(tt, drivers, orders, q, B, tables, inloop=True):
    pool, per = {}, {}
    for dr in drivers:
        p, c = run_tier_rule_fast(tt, dr, orders, B, q=q, inloop=inloop, tables=tables)
        pool[dr["id"]] = p
        per[dr["id"]] = (dr["cls"], c)
    return pool, per
