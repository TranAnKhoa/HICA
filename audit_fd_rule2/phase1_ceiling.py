"""EXPERIMENT Phase 1.3: ceiling of Layer-1 ordering for C1 (production Algorithm A).

Instrumented copy of experiments/T2BFS/t6_dp.run_dp (same _try_* / _filter_dominated_labels, rule OFF,
Layer 1 ON). Behaviour is unchanged; every created label is logged with a batch id.

Batch = the group over which Layer 1 is applied in the production loop:
  ("P", level)      : pickup-created labels of level `level` (new_by_key in t6_dp.py:282-287)
  ("D", level, s)   : delivery-created labels of closure iteration s of level `level` (t6_dp.py:258-265)
  ("H",)            : home-created (terminal, never expanded)
"""
import sys, os, time, json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "audit_fd_rule"))
from common import *            # noqa: E402,F401  (IG, RC, DL, KR, label_instance, LABEL_INSTANCES, sig)
import t6_dp as D               # noqa: E402
import t2_core as C             # noqa: E402


class LabelI(D.Label):
    __slots__ = ("lid", "batch", "natt", "nch", "expanded")


def _wrap(nl, batch, counter):
    o = LabelI(nl.v, nl.IV, nl.Cd, nl.t, nl.K, nl.W, parent=nl.parent, action=nl.action)
    o.lid = counter[0]; counter[0] += 1
    o.batch = batch; o.natt = 0; o.nch = 0; o.expanded = False
    return o


def run_dp_instr(travel_time, driver, orders, B):
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    cnt = dict(ext_attempts=0, labels_created=0)
    ctr = [0]
    log = []
    lab0 = _wrap(D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0), ("S",), ctr)
    log.append(lab0); lab0.expanded = True
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue
        active = list(labs_here)
        closure_all = []
        s = 0
        while active:
            s += 1
            next_active = []
            for lab in active:
                closure_all.append(lab); lab.expanded = True
                for j in sorted(lab.IV):
                    cnt["ext_attempts"] += 1; lab.natt += 1
                    nl = D._try_delivery(travel_time, driver, pd, lab, j)
                    if nl is None:
                        continue
                    cnt["labels_created"] += 1; lab.nch += 1
                    w = _wrap(nl, ("D", touched, s), ctr); log.append(w)
                    next_active.append(w)
                    if not w.IV and len(w.Cd) >= 1 and not has_home:
                        complete_by_C[w.Cd].append(w)
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    cnt["ext_attempts"] += 1; lab.natt += 1
                    nl = D._try_home(travel_time, driver, home, lab)
                    if nl is not None:
                        cnt["labels_created"] += 1; lab.nch += 1
                        w = _wrap(nl, ("H",), ctr); log.append(w)
                        complete_by_C[w.Cd].append(w)
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            next_active = []
            for k, labs in by_key.items():
                next_active.extend(D._filter_dominated_labels(labs))
            active = next_active
        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    cnt["ext_attempts"] += 1; lab.natt += 1
                    nl = D._try_pickup(travel_time, driver, pd, lab, j, B)
                    if nl is None:
                        continue
                    cnt["labels_created"] += 1; lab.nch += 1
                    w = _wrap(nl, ("P", touched + 1), ctr); log.append(w)
                    new_by_key[w.key()].append(w)
            nf = []
            for k, labs in new_by_key.items():
                nf.extend(D._filter_dominated_labels(labs))
            frontier[touched + 1] = nf
    for Cset, labs in list(complete_by_C.items()):
        by_v = defaultdict(list)
        for lab in labs:
            by_v[lab.v].append(lab)
        kept = []
        for v, lv in by_v.items():
            kept.extend(D._filter_dominated_labels(lv))
        complete_by_C[Cset] = kept
    return dict(complete_by_C=dict(complete_by_C), counters=cnt, log=log)


def ceiling(log):
    """Per-key analysis over all non-terminal created labels."""
    groups = defaultdict(list)
    for l in log:
        if l.batch[0] != "H":
            groups[l.key()].append(l)
    wasted = wasted_children = wasted_att = 0
    wasted_by_earlier = wasted_only_later = dup = 0
    xb_pairs = 0
    multi_batch_keys = 0
    for k, g in groups.items():
        if len(set(x.batch for x in g)) > 1:
            multi_batch_keys += 1
        for b in g:
            dom_earlier = dom_later = False
            for a in g:
                if a is b:
                    continue
                if D._dominates_label(a, b):
                    if a.batch != b.batch:
                        xb_pairs += 1
                    if b.expanded:
                        if a.lid < b.lid:
                            dom_earlier = True
                        else:
                            dom_later = True
            if b.expanded and (dom_earlier or dom_later):
                wasted += 1; wasted_children += b.nch; wasted_att += b.natt
                if dom_earlier:
                    wasted_by_earlier += 1
                else:
                    wasted_only_later += 1
        # exact duplicates (equal t,K,W) in the same key and both expanded
        seen = {}
        for b in g:
            if not b.expanded:
                continue
            sg = (round(b.t, 9), round(b.K, 9), round(b.W, 9))
            if sg in seen:
                dup += 1
            seen[sg] = 1
    return dict(wasted_labels=wasted, wasted_children=wasted_children, wasted_attempts=wasted_att,
                wasted_by_earlier=wasted_by_earlier, wasted_only_later=wasted_only_later,
                cross_batch_pairs=xb_pairs, multi_batch_keys=multi_batch_keys, n_keys=len(groups),
                dup_expanded=dup)


def main():
    rows = []
    allok = True
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            agg = defaultdict(int); aggc = {"GW": defaultdict(int), "OD": defaultdict(int)}
            t0 = time.perf_counter()
            for dr in drivers:
                ref = DL.run_pool(tt, dr, orders, B, B)["pool"]
                res = run_dp_instr(tt, dr, orders, B)
                # regression: same complete labels -> same pool
                pool = {}
                for Cset, labs in res["complete_by_C"].items():
                    if not Cset:
                        continue
                    kw = [D.finalize_KW(dr, l) for l in labs]
                    fr = DL._pareto_front(kw)
                    if fr:
                        pool[Cset] = fr
                same = sig({dr["id"]: ref}) == sig({dr["id"]: pool})
                allok &= same
                c = ceiling(res["log"])
                c["ext_attempts"] = res["counters"]["ext_attempts"]
                c["labels_created"] = res["counters"]["labels_created"]
                c["expanded"] = sum(1 for l in res["log"] if l.expanded)
                for k_, v_ in c.items():
                    agg[k_] += v_; aggc[dr["cls"]][k_] += v_
                print("B=%d n=%d s=%d %s %s ext=%d expanded=%d wasted=%d (earlier %d / later-only %d) "
                      "wasted_children=%d xb_pairs=%d dup=%d"
                      % (B, n, seed, dr["id"], "SAME" if same else "DIFF", c["ext_attempts"],
                         c["expanded"], c["wasted_labels"], c["wasted_by_earlier"],
                         c["wasted_only_later"], c["wasted_children"], c["cross_batch_pairs"],
                         c["dup_expanded"]))
                sys.stdout.flush()
            row = dict(B=B, inst="n%d_s%d" % (n, seed), seconds=round(time.perf_counter() - t0, 1),
                       **dict(agg))
            row["wasted_share"] = agg["wasted_children"] / agg["ext_attempts"]
            row["wasted_attempt_share"] = agg["wasted_attempts"] / agg["ext_attempts"]
            for cls in ("GW", "OD"):
                a = aggc[cls]
                row["wasted_share_" + cls] = (a["wasted_children"] / a["ext_attempts"]) if a["ext_attempts"] else None
            rows.append(row)
    print("REGRESSION(instrumented C1 == production pool)", "PASS" if allok else "FAIL")
    with open(os.path.join(ROOT, "audit_logs2", "phase1_ceiling.json"), "w") as f:
        json.dump(rows, f, indent=1)
    print("\n| B | instance | ext_attempts | expanded | wasted_labels | wasted_children | wasted_share | "
          "wasted_attempt_share | cross_batch_pairs | dup_expanded | share GW | share OD |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print("| %d | %s | %d | %d | %d | %d | %.2f%% | %.2f%% | %d | %d | %s | %s |" % (
            r["B"], r["inst"], r["ext_attempts"], r["expanded"], r["wasted_labels"],
            r["wasted_children"], 100 * r["wasted_share"], 100 * r["wasted_attempt_share"],
            r["cross_batch_pairs"], r["dup_expanded"],
            "%.2f%%" % (100 * r["wasted_share_GW"]) if r["wasted_share_GW"] is not None else "-",
            "%.2f%%" % (100 * r["wasted_share_OD"]) if r["wasted_share_OD"] is not None else "-"))


if __name__ == "__main__":
    main()
