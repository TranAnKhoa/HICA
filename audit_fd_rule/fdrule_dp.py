"""AUDIT (Audit.md, branch audit-fd-rule): Algorithm A with switchable Layer 1 / Layer 3.

Copy of experiments/T2BFS/t6_dp.run_dp (the production Algorithm A). The tracked production
files are NOT modified. Re-used unchanged from t6_dp: Label, _try_pickup/_try_delivery/_try_home
(feasibility), _filter_dominated_labels (Layer 1), finalize_KW. Added:

  * use_layer1  : Layer 1 dominance on key (v, IV, C), compare (t,K,W)   [production = True]
  * use_rule    : Layer 3 FD-completion label rule, singleton T={j}       [production = no such call]
  * counters    : ext_attempts, labels_created, killed_layer1, killed_layer3, complete_labels

With use_layer1=True, use_rule=False the output must equal t6_dp.run_dp (regression test,
audit_fd_rule/test_regression.py).

Rule (port of New_t4/files/dp_fast.py:52-105 in its FIXED mode, LEGACY flags = False), applied to
every label produced by a pickup/delivery extension, BEFORE it enters the batch / Layer 1:
  shortcut state of order j  = (K_j, v_j, r_j): same path with j's two stops removed.
  dK = K - K_j - kappa*d(v_j, v)            (junction term)
  dW = max(0, (t - r_j - tau(v_j, v)) - A)/60 (absorption A = waiting the shortcut would absorb)
  fire  <=>  dK + lo * dW >= q_j            (lo = 18 = lower end of the report domain)
Reads only public data (q_j, time windows); never a bid.
"""
import os
import sys
from collections import defaultdict

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)

import t6_dp as D          # noqa: E402  production Algorithm A (read-only use)
import t2_core as C        # noqa: E402

INF = float("inf")
KAPPA = D.KAPPA
TOL = 1e-9


class LabelA(D.Label):
    __slots__ = ("sc",)


def _km(tt_min):
    return D._tt_to_km(tt_min)


def new_counters():
    return dict(ext_attempts=0, labels_created=0, killed_layer1=0, killed_layer3=0,
                complete_labels=0, a_evals=0)


def _wrap(nl, sc):
    out = LabelA(nl.v, nl.IV, nl.Cd, nl.t, nl.K, nl.W, parent=nl.parent, action=nl.action)
    out.sc = sc
    return out


def _next_sc(lab, nl, kind, oid, pt_node, travel_time):
    """Incremental shortcut states (dp_fast.py:52-64): j's own stop leaves its shortcut alone,
    every other stop is visited by the shortcut too (waiting for the opening time)."""
    nsc = {}
    for j, (Kj, vj, rj) in lab.sc.items():
        if j == oid:
            nsc[j] = (Kj, vj, rj)
        else:
            tt = travel_time(vj, pt_node.id)
            nsc[j] = (Kj + KAPPA * _km(tt), pt_node.id,
                      max(rj + tt, pt_node.e) + pt_node.s)
    if kind == "pickup":
        nsc[oid] = (lab.K, lab.v, lab.t)      # shortcut without oid = parent path
    return nsc


def _rule_fires(nl, nsc, travel_time, pd, q, lo, B, max_e, cnt):
    """True iff some singleton T={j} satisfies dK + lo*dW >= q_j (dp_fast.py:66-104)."""
    picked = nl.IV | nl.Cd
    for j, (Kj, vj, rj) in nsc.items():
        qj = q[j]
        jt = travel_time(vj, nl.v)
        dK = nl.K - Kj - KAPPA * _km(jt)
        delta0 = nl.t - rj - jt
        if dK + lo * max(0.0, delta0) / 60.0 < qj + TOL:
            continue                                   # cannot fire even with A = 0
        A = 0.0
        # deliveries still to be made by every order on board at the end of L, INCLUDING j
        for w in nl.IV:
            e_d = pd[w][1].e
            if e_d > -INF:
                A = max(A, e_d - (rj + travel_time(vj, pd[w][1].id)))
        if len(picked) < B and rj < max_e:
            cnt["a_evals"] += 1
            for w, (wp, wd) in pd.items():
                if w in picked:
                    continue
                if nl.t + travel_time(nl.v, wp.id) <= wp.l + 1e-9:
                    A = max(A, wp.e - (rj + travel_time(vj, wp.id)))
                if wd.e > -INF and nl.t + travel_time(nl.v, wd.id) <= wd.l + 1e-9:
                    A = max(A, wd.e - (rj + travel_time(vj, wd.id)))
        dW = max(0.0, delta0 - A) / 60.0
        if dK + lo * dW >= qj + TOL:
            return True
    return False


def _filter(labels, cnt, use_layer1):
    if not use_layer1:
        return labels
    kept = D._filter_dominated_labels(labels)
    cnt["killed_layer1"] += len(labels) - len(kept)
    return kept


def run_dp_audit(travel_time, driver, orders, B, use_layer1=True, use_rule=False,
                 q=None, lo=18.0, log=None):
    """Same contract as t6_dp.run_dp plus `counters` (and `rule_log` if log is a list)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_counters()
    if use_rule:
        assert q is not None
        max_e = max([p.e for p, _d in pd.values()] +
                    [d.e for _p, d in pd.values() if d.e > -INF] + [-INF])

    lab0 = LabelA(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    lab0.sc = {}
    complete_by_C = defaultdict(list)
    frontier_sizes = []
    frontier = {0: [lab0]}

    def accept(nl, lab, kind, oid, pt_node):
        """Count, run the rule; return the wrapped label or None if the rule killed it."""
        cnt["labels_created"] += 1
        if not use_rule:
            return _wrap(nl, None)
        nsc = _next_sc(lab, nl, kind, oid, pt_node, travel_time)
        if _rule_fires(nl, nsc, travel_time, pd, q, lo, B, max_e, cnt):
            cnt["killed_layer3"] += 1
            return None
        return _wrap(nl, nsc)

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue
        active = list(labs_here)
        closure_all = []
        while active:
            next_active = []
            for lab in active:
                closure_all.append(lab)
                for j in sorted(lab.IV):
                    cnt["ext_attempts"] += 1
                    nl = D._try_delivery(travel_time, driver, pd, lab, j)
                    if nl is None:
                        continue
                    nl = accept(nl, lab, "delivery", j, pd[j][1])
                    if nl is None:
                        continue
                    next_active.append(nl)
                    if not nl.IV and len(nl.Cd) >= 1 and not has_home:
                        complete_by_C[nl.Cd].append(nl)
                        cnt["complete_labels"] += 1
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    cnt["ext_attempts"] += 1
                    nl = D._try_home(travel_time, driver, home, lab)
                    if nl is not None:
                        cnt["labels_created"] += 1
                        complete_by_C[nl.Cd].append(nl)
                        cnt["complete_labels"] += 1
            if use_layer1:
                by_key = defaultdict(list)
                for lab in next_active:
                    by_key[lab.key()].append(lab)
                next_active = []
                for k, labs in by_key.items():
                    next_active.extend(_filter(labs, cnt, True))
            active = next_active

        frontier_sizes.append((touched, len(closure_all)))

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    cnt["ext_attempts"] += 1
                    nl = D._try_pickup(travel_time, driver, pd, lab, j, B)
                    if nl is None:
                        continue
                    nl = accept(nl, lab, "pickup", j, pd[j][0])
                    if nl is None:
                        continue
                    new_by_key[nl.key()].append(nl)
            next_frontier = []
            for k, labs in new_by_key.items():
                next_frontier.extend(_filter(labs, cnt, use_layer1))
            frontier[touched + 1] = next_frontier

    if use_layer1:
        for Cset, labs in list(complete_by_C.items()):
            by_v = defaultdict(list)
            for lab in labs:
                by_v[lab.v].append(lab)
            kept = []
            for v, labs_v in by_v.items():
                kept.extend(_filter(labs_v, cnt, True))
            complete_by_C[Cset] = kept

    return dict(complete_by_C=dict(complete_by_C), counters=cnt,
                frontier_sizes=frontier_sizes)


def pareto_front(kw_list, eps=1e-6):
    """Layer 2 - identical to dp_labeling._pareto_front (imported to avoid drift)."""
    import dp_labeling as DL
    return DL._pareto_front(kw_list)


def run_pool_audit(travel_time, driver, orders, B, **kw):
    """Layer 2 per bundle, as dp_labeling.run_pool. Returns pool, counters."""
    res = run_dp_audit(travel_time, driver, orders, B, **kw)
    pool = {}
    for Cset, labs in res["complete_by_C"].items():
        if not Cset:
            continue
        kwl = [D.finalize_KW(driver, lab) for lab in labs]
        front = pareto_front(kwl)
        if front:
            pool[Cset] = front
    cnt = res["counters"]
    cnt["routes_layer2"] = sum(len(v) for v in pool.values())
    return pool, cnt
