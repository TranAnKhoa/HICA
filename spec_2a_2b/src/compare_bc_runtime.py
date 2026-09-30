"""Final_t4_Speedup.md Sec4 -- runtime of Algorithm B + C (WDP full-solve + every removal-solve
for VCG, CPLEX 12.10) on the full route pool vs the K*-pruned pool, on the 5 real RQ1 instances.

Per bid profile: t_full = full-solve + one removal-solve per driver on the full pool;
t_kstar = the same on the K*-pruned pool. Order of the two alternates across profiles. The one-off
cost of computing K* is reported separately. Z* and every Z*_{-i} are asserted equal (1e-6).

Environment: Python 3.7.7 + CPLEX.
"""
import csv, os, random, statistics, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL
import rq1_cost_gen as RC
import rq1_wdp as RW
from kstar_zstar_payment_check import prune_pool_by_kstar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(ROOT, "results", "compare_bc_runtime.csv")
LO, HI = RC.THETA_MIN, RC.THETA_MAX
N_PROFILES = 20
INSTANCES = [(12, 5, 42), (10, 4, 1), (15, 5, 7), (12, 6, 123), (10, 4, 999)]


def solve_all(pool, orders, theta, q, driver_ids):
    t0 = time.perf_counter()
    r = RW.solve_wdp_for_instance(pool, orders, theta, q)
    zs = [r["z"]]
    for did in driver_ids:
        zs.append(RW.solve_wdp_for_instance(pool, orders, theta, q, excluded_driver=did)["z"])
    return time.perf_counter() - t0, zs


def pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k)
    return xs[f] + (xs[min(f + 1, len(xs) - 1)] - xs[f]) * (k - f)


def main():
    rows = []
    all_full, all_k = [], []
    for n, nd, seed in INSTANCES:
        drivers, orders, tt, meta = IG.generate_instance(
            n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=nd, seed=seed,
            tau=30.0, spatial_mode="dispersed")
        pool_full, _ = DL.build_route_pool(tt, drivers, orders, B_gw=3, B_od=3)
        q = RC.assign_q_o(orders, tt)
        t0 = time.perf_counter()
        pool_k = prune_pool_by_kstar(pool_full, q, LO, HI)
        t_kstar_build = time.perf_counter() - t0
        size_f = sum(len(v) for p in pool_full.values() for v in p.values())
        size_k = sum(len(v) for p in pool_k.values() for v in p.values())
        ids = [d["id"] for d in drivers]
        rng = random.Random(31337 + seed)
        tf, tk, worst = [], [], 0.0
        for bp in range(N_PROFILES):
            theta = {d: rng.uniform(LO, HI) for d in ids}
            if bp % 2 == 0:
                a, za = solve_all(pool_full, orders, theta, q, ids)
                b, zb = solve_all(pool_k, orders, theta, q, ids)
            else:
                b, zb = solve_all(pool_k, orders, theta, q, ids)
                a, za = solve_all(pool_full, orders, theta, q, ids)
            for x, y in zip(za, zb):
                if x is not None and y is not None:
                    worst = max(worst, abs(x - y))
            assert worst < 1e-6, "Z mismatch full vs K* (%g)" % worst
            tf.append(a); tk.append(b)
        sp = [a / b for a, b in zip(tf, tk)]
        all_full.append(sum(tf)); all_k.append(sum(tk))
        row = dict(n=n, n_drivers=nd, seed=seed, pool_full=size_f, pool_kstar=size_k,
                   cut=1 - size_k / float(size_f), kstar_build_s=t_kstar_build,
                   median_t_full_s=statistics.median(tf), median_t_kstar_s=statistics.median(tk),
                   median_speedup=statistics.median(sp), q1_speedup=pct(sp, .25),
                   q3_speedup=pct(sp, .75), max_abs_z_gap=worst,
                   solves_per_profile=1 + len(ids))
        rows.append(row)
        print("n=%2d seed=%-4d pool %5d->%4d (cut %.2f%%)  B+C per profile: full %.3fs  K* %.3fs  "
              "speedup median %.2fx [IQR %.2f-%.2f]  K* build %.3fs  max|dZ|=%.1e"
              % (n, seed, size_f, size_k, 100 * row["cut"], row["median_t_full_s"],
                 row["median_t_kstar_s"], row["median_speedup"], row["q1_speedup"],
                 row["q3_speedup"], t_kstar_build, worst))
        sys.stdout.flush()
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("-> %s" % OUT_CSV)
    print("ALL: total B+C time full %.2fs vs K* %.2fs -> %.2fx"
          % (sum(all_full), sum(all_k), sum(all_full) / sum(all_k)))


if __name__ == "__main__":
    main()
