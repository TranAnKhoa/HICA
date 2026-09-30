"""Phase 3 §4.4/4.5: Tables A, B (and D data). Usage: python run_timing.py label|grid [reps]
C1 = Layer1 on / rule off ; C2 = Layer1 on / rule on. Alternating order, gc collected, single thread."""
import sys, json, gc, time, statistics, csv
from common import *
import rq_common as RQ

def run_cfg(tt, drivers, orders, q, B, rule):
    gc.collect(); gc.disable()
    pool, cls_cnt = {}, {}
    t0 = time.perf_counter()
    for dr in drivers:
        p, c = F.run_pool_audit(tt, dr, orders, B, use_layer1=True, use_rule=rule, q=q, lo=LO)
        pool[dr["id"]] = p; cls_cnt[dr["id"]] = (dr["cls"], c)
    tA = time.perf_counter() - t0
    t0 = time.perf_counter()
    kp = kstar_pool(pool, q)
    tF = time.perf_counter() - t0
    gc.enable()
    return pool, kp, cls_cnt, tA, tF

def _pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)

def q3(xs):
    """inclusive quartiles (== statistics.quantiles(method='inclusive'), unavailable in 3.7)."""
    return _pct(xs, 0.25), _pct(xs, 0.75)

def measure(tag, tt, drivers, orders, q, B, reps):
    T = {False: dict(A=[], F=[]), True: dict(A=[], F=[])}
    first = {}
    for r in range(reps):
        for rule in ((False, True) if r % 2 == 0 else (True, False)):
            pool, kp, cc, tA, tF = run_cfg(tt, drivers, orders, q, B, rule)
            T[rule]["A"].append(tA); T[rule]["F"].append(tF)
            if r == 0:
                first[rule] = (pool, kp, cc)
    (p1, k1, c1), (p2, k2, c2) = first[False], first[True]
    sum_ = lambda cc, k: sum(c[k] for _, c in cc.values())
    row = dict(tag=tag, B=B,
        ext_C1=sum_(c1, "ext_attempts"), ext_C2=sum_(c2, "ext_attempts"),
        created_C1=sum_(c1, "labels_created"), created_C2=sum_(c2, "labels_created"),
        killed_L1_C1=sum_(c1, "killed_layer1"), killed_L1_C2=sum_(c2, "killed_layer1"),
        killed_L3_C2=sum_(c2, "killed_layer3"),
        complete_C1=sum_(c1, "complete_labels"), complete_C2=sum_(c2, "complete_labels"),
        L2_C1=len(sig(p1)), L2_C2=len(sig(p2)), kstar_C1=len(sig(k1)), kstar_C2=len(sig(k2)),
        kstar_identical=(sig(k1) == sig(k2)),
        drivers_fired_GW=sum(1 for _, (cl, c) in c2.items() if cl == "GW" and c["killed_layer3"] > 0),
        n_GW=sum(1 for _, (cl, c) in c2.items() if cl == "GW"),
        drivers_fired_OD=sum(1 for _, (cl, c) in c2.items() if cl == "OD" and c["killed_layer3"] > 0),
        n_OD=sum(1 for _, (cl, c) in c2.items() if cl == "OD"))
    for rule, nm in ((False, "C1"), (True, "C2")):
        a, f = T[rule]["A"], T[rule]["F"]
        tot = [x + y for x, y in zip(a, f)]
        row["tA_" + nm] = statistics.median(a); row["tF_" + nm] = statistics.median(f)
        row["tTot_" + nm] = statistics.median(tot); row["tTot_%s_iqr" % nm] = "%.4f-%.4f" % q3(tot)
    sp = [(a1 + f1) / (a2 + f2) for a1, f1, a2, f2 in zip(T[False]["A"], T[False]["F"], T[True]["A"], T[True]["F"])]
    row["speedup_median"] = statistics.median(sp); row["speedup_iqr"] = "%.3f-%.3f" % q3(sp)
    row["_raw"] = dict(C1A=T[False]["A"], C1F=T[False]["F"], C2A=T[True]["A"], C2F=T[True]["F"])
    print("%s B=%d | ext %d->%d | L3 kills %d | L2 %d->%d | K* %d/%d id=%s | tA %.3f->%.3f tF %.4f->%.4f tot %.3f->%.3f | speedup %.2fx [%s]"
          % (tag, B, row["ext_C1"], row["ext_C2"], row["killed_L3_C2"], row["L2_C1"], row["L2_C2"],
             row["kstar_C1"], row["kstar_C2"], row["kstar_identical"], row["tA_C1"], row["tA_C2"],
             row["tF_C1"], row["tF_C2"], row["tTot_C1"], row["tTot_C2"], row["speedup_median"], row["speedup_iqr"]))
    sys.stdout.flush()
    return row

def main():
    which = sys.argv[1]; reps = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    rows = []
    if which == "label":
        for B in (3, 4):
            for (n, nd, seed) in LABEL_INSTANCES:
                drivers, orders, tt, q = label_instance(n, nd, seed, B)
                rows.append(measure("n%d_s%d" % (n, seed), tt, drivers, orders, q, B, reps))
    else:
        for align in (0.90, 0.50):
            for rep in range(10):
                d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
                r = measure("a%.2f_rep%d" % (align, rep), tt, d, o, q, 3, reps)
                r["alignment"] = align; rows.append(r)
    out = "../audit_logs/timing_%s.json" % which
    json.dump(rows, open(out, "w"), indent=1, default=str)
    print("saved", out)
main()
