"""Final_t4_Speedup.md Sec1 -- repeated timing of dp_fast.py with/without the label rule on the
5 real RQ1 instances; reports median + IQR of the per-instance speedup.

Per repetition, the with-rule and no-rule runs of each driver alternate order (rep even: off
then on; rep odd: on then off) so that slow drift (thermal, background load) does not bias one
side. GC is collected before and disabled during each measured call.

Usage: python repeat_timing.py [B] [N_REPEATS]
"""
import gc, json, statistics, sys, time
import dp_fast_rq1 as X
import dp_fast as DF

LO = 18.0
INSTANCES = [(12, 5, 42), (10, 4, 1), (15, 5, 7), (12, 6, 123), (10, 4, 999)]


def timed(dr, orders, B, use_rule):
    gc.collect(); gc.disable()
    t0 = time.perf_counter()
    out, st = DF.enumerate_fast(dr, orders, B, LO, use_rule=use_rule)
    t = time.perf_counter() - t0
    gc.enable()
    return t, st["ext"], len(out)


def quartiles(xs):
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return q[0], q[2]


def main():
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    only = {int(x) for x in sys.argv[3].split(",")} if len(sys.argv) > 3 else None
    global INSTANCES
    if only:
        INSTANCES = [t for t in INSTANCES if t[2] in only]
    DF.MUT.clear()
    DF.LEGACY["exclude_own_delivery"] = False
    DF.LEGACY["shortcut_ignores_e_d"] = False
    results = {}
    all_off, all_on = [0.0] * N, [0.0] * N
    for n, nd, seed in INSTANCES:
        drivers, orders = X.build_hica_instance(n, nd, seed, B=B)
        gws = [d for d in drivers if d.cls == "GW"]
        off, on = [0.0] * N, [0.0] * N
        ext_off = ext_on = 0
        for rep in range(N):
            for dr in drivers:
                order = (False, True) if rep % 2 == 0 else (True, False)
                for use_rule in order:
                    t, ext, _ = timed(dr, orders, B, use_rule)
                    if use_rule:
                        on[rep] += t
                        if rep == 0: ext_on += ext
                    else:
                        off[rep] += t
                        if rep == 0: ext_off += ext
        sp = [a / b for a, b in zip(off, on)]
        med = statistics.median(sp)
        q1, q3 = quartiles(sp)
        sd = statistics.stdev(sp)
        key = "n%d_seed%d" % (n, seed)
        results[key] = dict(B=B, n_repeats=N, n_gw=len(gws),
                            median_no_rule_s=statistics.median(off),
                            median_with_rule_s=statistics.median(on),
                            median_speedup=med, q1_speedup=q1, q3_speedup=q3,
                            min_speedup=min(sp), max_speedup=max(sp),
                            stdev_over_median=sd / med,
                            ext_no_rule=ext_off, ext_with_rule=ext_on,
                            ext_saved=1 - ext_on / ext_off, ext_ratio=ext_off / ext_on)
        for r in range(N):
            all_off[r] += off[r]; all_on[r] += on[r]
        print("%s B=%d: speedup median %.2fx [IQR %.2f-%.2f] min %.2f max %.2f  sd/med=%.3f  "
              "| ext %d->%d (saved %.1f%%, ratio %.2fx)"
              % (key, B, med, q1, q3, min(sp), max(sp), sd / med, ext_off, ext_on,
                 100 * (1 - ext_on / ext_off), ext_off / ext_on))
        sys.stdout.flush()
    tot = [a / b for a, b in zip(all_off, all_on)]
    q1, q3 = quartiles(tot)
    results["ALL"] = dict(median_speedup=statistics.median(tot), q1_speedup=q1, q3_speedup=q3,
                          stdev_over_median=statistics.stdev(tot) / statistics.median(tot))
    print("ALL B=%d: speedup median %.2fx [IQR %.2f-%.2f] sd/med=%.3f"
          % (B, statistics.median(tot), q1, q3, results["ALL"]["stdev_over_median"]))
    suffix = ("_seeds" + "-".join(str(t[2]) for t in INSTANCES)) if only else ""
    with open("timing_medians_B%d%s.json" % (B, suffix), "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
