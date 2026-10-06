"""Table C: wasted_share of C1 (Phase 1.3) vs the same measurement on the tiered engine (C4, rule off)."""
import sys, json, time
from phase1_ceiling import *     # LabelI, ceiling, label_instance, LABEL_INSTANCES, D, C, DL, sig, defaultdict
from phase1_ceiling import _wrap


def run_tier_instr(tt, driver, orders, B):
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys()); has_home = home is not None
    cnt = dict(ext_attempts=0, labels_created=0); ctr = [0]; log = []
    lab0 = _wrap(D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0), ("S",), ctr)
    log.append(lab0)
    complete = defaultdict(list)
    cur = [lab0]; m = 0
    while cur:
        by_key = defaultdict(list)
        for l in cur: by_key[l.key()].append(l)
        alive = []
        for k, labs in by_key.items(): alive.extend(D._filter_dominated_labels(labs))
        if not has_home:
            for l in alive:
                if not l.IV and l.Cd: complete[l.Cd].append(l)
        nxt = []
        for lab in alive:
            lab.expanded = True
            for j in sorted(lab.IV):
                cnt["ext_attempts"] += 1; lab.natt += 1
                nl = D._try_delivery(tt, driver, pd, lab, j)
                if nl is None: continue
                cnt["labels_created"] += 1; lab.nch += 1
                w = _wrap(nl, ("T", m + 1), ctr); log.append(w); nxt.append(w)
            if has_home and not lab.IV and lab.Cd:
                cnt["ext_attempts"] += 1; lab.natt += 1
                nl = D._try_home(tt, driver, home, lab)
                if nl is not None:
                    cnt["labels_created"] += 1; lab.nch += 1
                    w = _wrap(nl, ("H",), ctr); log.append(w); complete[w.Cd].append(w)
            if len(lab.IV) + len(lab.Cd) < B:
                for j in order_ids:
                    cnt["ext_attempts"] += 1; lab.natt += 1
                    nl = D._try_pickup(tt, driver, pd, lab, j, B)
                    if nl is None: continue
                    cnt["labels_created"] += 1; lab.nch += 1
                    w = _wrap(nl, ("T", m + 1), ctr); log.append(w); nxt.append(w)
        cur = nxt; m += 1
    return dict(counters=cnt, log=log, complete=complete)

rows = []
for B in (3, 4):
    for (n, nd, seed) in LABEL_INSTANCES:
        drivers, orders, tt, q = label_instance(n, nd, seed, B)
        a = defaultdict(int)
        for dr in drivers:
            r = run_tier_instr(tt, dr, orders, B)
            c = ceiling(r["log"]); c["ext_attempts"] = r["counters"]["ext_attempts"]
            for k, v in c.items(): a[k] += v
        rows.append(dict(B=B, inst="n%d_s%d" % (n, seed), ext=a["ext_attempts"], wasted_labels=a["wasted_labels"],
                         wasted_children=a["wasted_children"], cross_batch_pairs=a["cross_batch_pairs"],
                         dup_expanded=a["dup_expanded"], wasted_share=a["wasted_children"] / a["ext_attempts"]))
        print(rows[-1]); sys.stdout.flush()
json.dump(rows, open("../audit_logs2/phase1_after_tier.json", "w"), indent=1)
