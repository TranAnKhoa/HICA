"""Machine-drift anchor: re-time the OLD audit C1 (audit_fd_rule/fdrule_dp, rule off) on the five label instances
at B=3 and compare to AUDIT_REPORT.md Table B (t_A C1). >10% difference = drift."""
import sys, gc, time, statistics
from variants import *
ref = {"n12_s42": 0.536, "n10_s1": 0.485, "n15_s7": 1.704, "n12_s123": 1.004, "n10_s999": 0.315}
for (n, nd, seed) in LABEL_INSTANCES:
    drivers, orders, tt, q = label_instance(n, nd, seed, 3)
    ts = []
    for r in range(11):
        gc.collect(); gc.disable(); t0 = time.perf_counter()
        for dr in drivers:
            F.run_pool_audit(tt, dr, orders, 3, use_layer1=True, use_rule=False)
        ts.append(time.perf_counter() - t0); gc.enable()
    ts = ts[1:]
    k = "n%d_s%d" % (n, seed)
    m = statistics.median(ts)
    print("%s old-audit C1 t_A now %.3f s vs AUDIT_REPORT %.3f s  diff %+.1f%%" % (k, m, ref[k], 100 * (m / ref[k] - 1)))
