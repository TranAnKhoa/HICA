"""C8 = C5 + Layer 3 (the FD-completion label rule), and the C5 copy used to check it.

Question (author, 2026-10-07): C5 (event-count tiers + Layer 1 + per-bundle Layer 2 +
in-loop frontier) was the fastest variant in EXPERIMENT_REPORT.md, but it does not use
Layer 3. Does adding Layer 3 to C5 make Algorithm A faster still, with the same K*?

C8 is run_tier of audit_fd_rule2/variants.py (fd_dom=False, inloop=True), with ONE
addition: after the Layer-1 filter of each tier, every survivor goes through RuleFires,
the same function and the same lazy shortcut-triple update that C3 uses
(fdrule_dp._next_sc / _rule_fires, singleton T = {j}). A label that fires is dropped
with all its extensions. Everything else (feasibility, Layer 1, Layer 2, in-loop
frontier, counters) is the unchanged code of variants.py.

With rule=False this function must reproduce C5 exactly (checked in gate_c8.py).
"""
import paths  # noqa: F401  (repository paths, Dataset stub)
from collections import defaultdict

import variants as V
from variants import D, C, F, INF, LO, HI, new_cnt, _bundle_front, _kstar_filter_bundle


def _witness(l, nsc, tt, pd, q, lo, B, max_e):
    """The singleton T = {j} for which RuleFires fires (audit only)."""
    dummy = new_cnt()
    for j in sorted(nsc):
        if F._rule_fires(l, {j: nsc[j]}, tt, pd, q, lo, B, max_e, dummy):
            return j
    return None


def run_tier_rule(tt, driver, orders, B, q=None, lo=LO, hi=HI, rule=True, inloop=True,
                  fire_log=None):
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = new_cnt()
    if rule:
        assert q is not None
        max_e = max([p.e for p, _d in pd.values()] +
                    [d.e for _p, d in pd.values() if d.e > -INF] + [-INF])
        lab0 = F.LabelA(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
        lab0.sc = {}
    else:
        max_e = None
        lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)

    def rule_pass(survivors):
        """Layer 3 on Layer-1 survivors (as C3): triples are computed now from the parent's
        triples; the parent is a survivor that was expanded, so it carries its triples."""
        out = []
        for l in survivors:
            if l.action is None:                      # the start label
                out.append(l)
                continue
            kind, oid = l.action
            pt = pd[oid][0] if kind == "pickup" else pd[oid][1]
            nsc = F._next_sc(l.parent, l, kind, oid, pt, tt)
            if F._rule_fires(l, nsc, tt, pd, q, lo, B, max_e, cnt):
                cnt["killed_rule"] += 1
                if fire_log is not None:
                    fire_log.append((l, _witness(l, nsc, tt, pd, q, lo, B, max_e)))
                continue
            w = F.LabelA(l.v, l.IV, l.Cd, l.t, l.K, l.W, parent=l.parent, action=l.action)
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
        alive = rule_pass(surv) if rule else surv
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


def run_c8(tt, driver, orders, B, q=None, **kw):
    """C5 + Layer 3 (rule on survivors), in-loop frontier: outputs K* directly."""
    return run_tier_rule(tt, driver, orders, B, q=q, rule=True, inloop=True)


def run_c9(tt, driver, orders, B, q=None, **kw):
    """C4 + Layer 3, post-hoc frontier (isolates the effect of the rule on R)."""
    return run_tier_rule(tt, driver, orders, B, q=q, rule=True, inloop=False)


def run_c5copy(tt, driver, orders, B, q=None, **kw):
    """This file's code path with the rule switched off: must equal C5."""
    return run_tier_rule(tt, driver, orders, B, q=q, rule=False, inloop=True)


V.VARIANTS.update(C8=run_c8, C9=run_c9, C5copy=run_c5copy)
V.INLOOP.update({"C8", "C5copy"})
VARIANTS, INLOOP, build_all = V.VARIANTS, V.INLOOP, V.build_all
