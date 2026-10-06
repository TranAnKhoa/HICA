"""EXPERIMENT_TRIAL variants of Algorithm A (branch exp-tiers-fd-dominance).

Fairness (Experiment_trial.md section 1, rule 3): every variant re-uses, unchanged,
  t6_dp._try_pickup / _try_delivery / _try_home, t6_dp._filter_dominated_labels (Layer 1),
  t6_dp.finalize_KW, dp_labeling._pareto_front (Layer 2), the same counters, the same Label class.
Two engines:
  run_round : production structure (rounds on |IV|+|C|, closure of deliveries)  -> C1, C3
  run_tier  : tiers on events m = |IV| + 2|C|, one Layer-1 batch per tier        -> C4, C5, C6, C7

  id  engine  rule                              Layer 2          Frontier
  C1  round   off                               after loop       post-hoc (harness)
  C3  round   RuleFires on FilterDominated      after loop       post-hoc
              survivors only (lazy triples)
  C4  tier    off                               per bundle       post-hoc
  C5  tier    off                               per bundle       IN LOOP (only K* kept)
  C6  tier    FD-dominance between real labels  per bundle       post-hoc
  C7  tier    FD-dominance between real labels  per bundle       IN LOOP

Every run_* returns (pool, cnt): pool = {bundle: [(K, W)]} = R (C1,C3,C4,C6) or K* (C5,C7).
NOT PROVEN: FD-dominance (Idea 3) and the in-loop frontier hypothesis; they are validated only by the gates.
"""
import os
import sys
import itertools
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "audit_fd_rule"))
from common import *            # noqa: E402,F401,F403  IG RC DL KR F label_instance LABEL_INSTANCES sig kstar_pool LO HI
import t6_dp as D               # noqa: E402
import t2_core as C             # noqa: E402

INF = float("inf")
KAPPA = D.KAPPA
TOL = 1e-9
EPS = D.EPS


def new_cnt():
    return dict(ext_attempts=0, labels_created=0, killed_layer1=0, killed_rule=0,
                complete_labels=0, a_evals=0, routes_kept=0, fd_lookups=0, fd_tests=0)


# ----------------------------------------------------------------- Layer 2 (per bundle)
def _bundle_front(driver, labs):
    """Final per-(C,v) Layer-1 filter + finalize_KW + Layer-2 Pareto: exactly what
    dp_labeling.run_pool does for one bundle."""
    by_v = defaultdict(list)
    for l in labs:
        by_v[l.v].append(l)
    kept = []
    for v, lv in by_v.items():
        kept.extend(D._filter_dominated_labels(lv))
    kw = [D.finalize_KW(driver, l) for l in kept]
    return DL._pareto_front(kw)


# ----------------------------------------------------------------- engine 1: production rounds
def run_round(tt, driver, orders, B, q=None, lo=LO, lazy_rule=False):
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_cnt()
    max_e = None
    if lazy_rule:
        assert q is not None
        max_e = max([p.e for p, _d in pd.values()] +
                    [d.e for _p, d in pd.values() if d.e > -INF] + [-INF])
        lab0 = F.LabelA(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
        lab0.sc = {}
    else:
        lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)

    def rule_pass(survivors):
        """C3: RuleFires only on labels that survived FilterDominated; triples computed now
        from the parent's triples (the parent is a survivor that was expanded)."""
        out = []
        for l in survivors:
            kind, oid = l.action
            pt = pd[oid][0] if kind == "pickup" else pd[oid][1]
            nsc = F._next_sc(l.parent, l, kind, oid, pt, tt)
            if F._rule_fires(l, nsc, tt, pd, q, lo, B, max_e, cnt):
                cnt["killed_rule"] += 1
                continue
            w = F.LabelA(l.v, l.IV, l.Cd, l.t, l.K, l.W, parent=l.parent, action=l.action)
            w.sc = nsc
            out.append(w)
        return out

    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}
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
                    nl = D._try_delivery(tt, driver, pd, lab, j)
                    if nl is None:
                        continue
                    cnt["labels_created"] += 1
                    next_active.append(nl)
                    if not lazy_rule and not nl.IV and len(nl.Cd) >= 1 and not has_home:
                        complete_by_C[nl.Cd].append(nl)
                        cnt["complete_labels"] += 1
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    cnt["ext_attempts"] += 1
                    nl = D._try_home(tt, driver, home, lab)
                    if nl is not None:
                        cnt["labels_created"] += 1
                        complete_by_C[nl.Cd].append(nl)
                        cnt["complete_labels"] += 1
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            next_active = []
            for k, labs in by_key.items():
                kept = D._filter_dominated_labels(labs)
                cnt["killed_layer1"] += len(labs) - len(kept)
                next_active.extend(kept)
            if lazy_rule:
                next_active = rule_pass(next_active)
                if not has_home:
                    for nl in next_active:
                        if not nl.IV and len(nl.Cd) >= 1:
                            complete_by_C[nl.Cd].append(nl)
                            cnt["complete_labels"] += 1
            active = next_active
        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    cnt["ext_attempts"] += 1
                    nl = D._try_pickup(tt, driver, pd, lab, j, B)
                    if nl is None:
                        continue
                    cnt["labels_created"] += 1
                    new_by_key[nl.key()].append(nl)
            nf = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                cnt["killed_layer1"] += len(labs) - len(kept)
                nf.extend(kept)
            if lazy_rule:
                nf = rule_pass(nf)
            frontier[touched + 1] = nf
    pool = {}
    for Cset, labs in complete_by_C.items():
        if not Cset:
            continue
        front = _bundle_front(driver, labs)
        if front:
            pool[Cset] = front
    cnt["routes_kept"] = sum(len(v) for v in pool.values())
    return pool, cnt


def run_c1(tt, driver, orders, B, q=None, **kw):
    return run_round(tt, driver, orders, B, q=q, lazy_rule=False)


def run_c3(tt, driver, orders, B, q=None, **kw):
    return run_round(tt, driver, orders, B, q=q, lazy_rule=True)


# ----------------------------------------------------------------- in-loop frontier test
def _kstar_filter_bundle(S, front, kstar_by_bundle, q, lo, hi, tol=1e-9):
    """Same math as kstar_rule.local_frontier, restricted to the lines available in the loop:
    empty route, K* routes of proper sub-bundles, the other Pareto routes of the same bundle."""
    Sl = sorted(S)
    qS = sum(q[o] for o in S)
    base = [(qS, 0.0)]
    for r in range(1, len(Sl)):
        for T in itertools.combinations(Sl, r):
            T = frozenset(T)
            ks = kstar_by_bundle.get(T)
            if ks:
                qrest = qS - sum(q[o] for o in T)
                for (K2, W2) in ks:
                    base.append((K2 + qrest, W2))
    out = []
    for i, (K, W) in enumerate(front):
        lines = base + [front[j] for j in range(len(front)) if j != i]
        pts = [lo, hi]
        for (a1, w1), (a2, w2) in itertools.combinations(lines, 2):
            if abs(w1 - w2) > 1e-12:
                x = (a2 - a1) / (w1 - w2)
                if lo < x < hi:
                    pts.append(x)
        m = max(min(a + b * w for a, w in lines) - (K + b * W) for b in pts)
        if m > tol:
            out.append((K, W))
    return out



def _absorption_A(tt, pd, L2, L1, B):
    """A = max(0, max_{w in F(L2)} (e_w - t1 - tau(v, w))); F(L2) = deliveries of orders on board,
    pickups still reachable from L2, deliveries of the orders of those pickups."""
    v = L2.v
    A = 0.0
    for w in L2.IV:
        de = pd[w][1].e
        if de > -INF:
            A = max(A, de - L1.t - tt(v, pd[w][1].id))
    if len(L2.IV) + len(L2.Cd) < B:
        for w, (wp, wd) in pd.items():
            if w in L2.IV or w in L2.Cd:
                continue
            if L2.t + tt(v, wp.id) <= wp.l + 1e-9:
                A = max(A, wp.e - L1.t - tt(v, wp.id))
                if wd.e > -INF:
                    A = max(A, wd.e - L1.t - tt(v, wd.id))
    return A

# ----------------------------------------------------------------- engine 2: event tiers
def run_tier(tt, driver, orders, B, q=None, lo=LO, hi=HI, fd_dom=False, inloop=False,
             mut=None, fire_log=None):
    """mut (only with fd_dom, used by the mutation test G6):
         'A0'    : ignore absorption (A = 0)            [invalid]
         'noK'   : drop the (K2-K1) term                [invalid]
         't5'    : relax t1 <= t2 to t1 <= t2 + 5       [invalid]
         'minus1': threshold q(T) - 1.0                 [invalid, extra]
         'plus1' : threshold q(T) + 1.0 (fires less)    [valid control]
       fire_log: list; every FD-dominance discard appends (L2, L1, T) (audit G5)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_cnt()
    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    surv_by_key = {}
    complete = defaultdict(list)
    pool = {}
    kstar_by_bundle = {}
    qo = q

    def fd_dominated(L2):
        cl = sorted(L2.Cd)
        nC = len(cl)
        qC2 = sum(qo[o] for o in cl)
        v = L2.v
        for r in range(0, nC):
            for comb in itertools.combinations(cl, r):
                C1 = frozenset(comb)
                cnt["fd_lookups"] += 1
                lst = surv_by_key.get((v, L2.IV, C1))
                if not lst:
                    continue
                T = L2.Cd - C1
                qT = qC2 - sum(qo[o] for o in comb)
                thr = qT + TOL
                if mut == "minus1":
                    thr = qT - 1.0
                elif mut == "plus1":
                    thr = qT + 1.0
                for L1 in lst:
                    cnt["fd_tests"] += 1
                    tslack = 5.0 if mut == "t5" else 0.0
                    if L1.t > L2.t + EPS + tslack:
                        continue
                    dK = 0.0 if mut == "noK" else (L2.K - L1.K)
                    dt = L2.t - L1.t
                    if dK + lo * max(0.0, dt) / 60.0 < thr:
                        continue                      # cannot pass even with A = 0
                    A = 0.0
                    if mut != "A0":
                        cnt["a_evals"] += 1
                        A = _absorption_A(tt, pd, L2, L1, B)
                    if dK + lo * max(0.0, dt - A) / 60.0 >= thr:
                        if fire_log is not None:
                            fire_log.append((L2, L1, T))
                        return True
        return False

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
        if fd_dom:
            alive = []
            for l in surv:
                if l.Cd and fd_dominated(l):
                    cnt["killed_rule"] += 1
                else:
                    alive.append(l)
            for l in surv:                          # every FilterDominated survivor can serve as L1
                surv_by_key.setdefault(l.key(), []).append(l)
        else:
            alive = surv
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
        if m % 2 == 0 and m >= 2:                    # all routes of bundle size k = m/2 are complete
            k = m // 2
            for S in [S for S in complete if len(S) == k]:
                front = _bundle_front(driver, complete.pop(S))
                if not front:
                    continue
                if inloop:
                    kk = _kstar_filter_bundle(S, front, kstar_by_bundle, qo, lo, hi)
                    if kk:
                        kstar_by_bundle[S] = kk
                        pool[S] = kk
                else:
                    pool[S] = front
        cur = nxt
        m += 1
    cnt["routes_kept"] = sum(len(v) for v in pool.values())
    return pool, cnt


def run_c4(tt, driver, orders, B, q=None, **kw):
    return run_tier(tt, driver, orders, B, q=q)


def run_c5(tt, driver, orders, B, q=None, **kw):
    return run_tier(tt, driver, orders, B, q=q, inloop=True)


def run_c6(tt, driver, orders, B, q=None, **kw):
    return run_tier(tt, driver, orders, B, q=q, fd_dom=True)


def run_c7(tt, driver, orders, B, q=None, **kw):
    return run_tier(tt, driver, orders, B, q=q, fd_dom=True, inloop=True)


VARIANTS = dict(C1=run_c1, C3=run_c3, C4=run_c4, C5=run_c5, C6=run_c6, C7=run_c7)
INLOOP = {"C5", "C7"}      # these output K* directly (t_F = 0)


def build_all(name, tt, drivers, orders, q, B, **kw):
    """Run one variant on every driver. Returns pool_by_driver, per-driver counters."""
    fn = VARIANTS[name]
    pool, per = {}, {}
    for dr in drivers:
        p, c = fn(tt, dr, orders, B, q=q, **kw)
        pool[dr["id"]] = p
        per[dr["id"]] = (dr["cls"], c)
    return pool, per
