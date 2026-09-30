"""Do that: instance n=30, n_drivers=5 (ty le GW/OD mac dinh nhu RQ1 that) --
Algorithm A tuan tu qua TAT CA driver (co/khong rule), cong voi so route pool
cuoi cung (sau K*) de uoc luong B+C tu du lieu da do o compare_bc_runtime.csv
(khong the goi CPLEX o day - Python 3.13, khong co binding CPLEX).
"""
import sys, time
import dp_fast_rq1 as X
import dp_fast as DF

LO = 18.0
DF.MUT.clear()
DF.LEGACY["exclude_own_delivery"] = False
DF.LEGACY["shortcut_ignores_e_d"] = False


def main():
    n, n_drivers, seed, B = 30, 5, 999, 3
    drivers, orders = X.build_hica_instance(n, n_drivers, seed, B=B)
    print("n=%d n_drivers=%d (GW=%d, OD=%d) B=%d"
          % (n, n_drivers, sum(1 for d in drivers if d.cls == "GW"),
             sum(1 for d in drivers if d.cls == "OD"), B))

    tot_off = tot_on = 0.0
    pool_full = pool_kstar = 0
    for dr in drivers:
        t0 = time.perf_counter()
        out_off, st_off = DF.enumerate_fast(dr, orders, B, LO, use_rule=False)
        t_off = time.perf_counter() - t0
        t0 = time.perf_counter()
        out_on, st_on = DF.enumerate_fast(dr, orders, B, LO, use_rule=True)
        t_on = time.perf_counter() - t0
        tot_off += t_off; tot_on += t_on
        # pool sau Pareto filter (chua K*) -- dung de tinh ty le nhu cac bao cao truoc
        from hica_core import pareto
        by = {}
        for seq, K, W in out_on:
            Skey = frozenset(o for o, _ in seq)
            by.setdefault(Skey, []).append((K, W, seq))
        pool_full += sum(len(pareto(v)) for v in by.values())
        print("  %-4s %-3s  t_off=%7.3fs  t_on=%7.3fs  routes(seq)=%7d"
              % (dr.id, dr.cls, t_off, t_on, len(out_on)))
        sys.stdout.flush()

    print("\nAlgorithm A tong (tuan tu qua %d driver): off=%.2fs  on=%.2fs  speedup=%.2fx"
          % (len(drivers), tot_off, tot_on, tot_off / tot_on if tot_on > 0 else float("nan")))
    print("Pool sau Pareto filter (truoc K*, tong ca instance) = %d route" % pool_full)


if __name__ == "__main__":
    main()
