"""Do thu instance cang lon cang tot (tang n, B) tren 1 driver GW, ca hai che do
(co/khong rule), de tim gioi han thuc te truoc khi thoi gian bung no. Dung lai
dung dp_fast_rq1.build_hica_instance() (khong doi logic sinh instance), chi
tang dan n va dat timeout mem/thoi gian de dung som neu qua cham.

Chay: python find_max_instance.py
"""
import sys, time
import dp_fast_rq1 as X
import dp_fast as DF

LO = 18.0
TIME_LIMIT_S = 60.0   # cat 1 phep do neu vuot qua nguong nay (danh dau la "qua cham")

DF.MUT.clear()
DF.LEGACY["exclude_own_delivery"] = False
DF.LEGACY["shortcut_ignores_e_d"] = False


def try_one(n, n_drivers, seed, B):
    drivers, orders = X.build_hica_instance(n, n_drivers, seed, B=B)
    gw = [d for d in drivers if d.cls == "GW"][0]
    t0 = time.perf_counter()
    out_on, st_on = DF.enumerate_fast(gw, orders, B, LO, use_rule=True)
    t_on = time.perf_counter() - t0
    if t_on > TIME_LIMIT_S:
        return dict(n=n, B=B, t_on=t_on, t_off=None, routes=len(out_on),
                    ext_on=st_on["ext"], skipped_off=True)
    t0 = time.perf_counter()
    out_off, st_off = DF.enumerate_fast(gw, orders, B, LO, use_rule=False)
    t_off = time.perf_counter() - t0
    return dict(n=n, B=B, t_on=t_on, t_off=t_off, routes=len(out_on),
                ext_on=st_on["ext"], ext_off=st_off["ext"], skipped_off=False)


def main():
    B = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    n_drivers = 4
    print("B=%d seed=%d (1 driver GW timed, orders shared across all n_drivers=%d)" % (B, seed, n_drivers))
    for n in [10, 15, 20, 25, 30, 35, 40, 50, 60, 80, 100]:
        try:
            r = try_one(n, n_drivers, seed, B)
        except MemoryError:
            print("n=%3d  OUT OF MEMORY -- stopping" % n)
            break
        if r["skipped_off"]:
            print("n=%3d  t_on=%8.2fs (rule)  routes=%6d  ext_on=%9d   [off run SKIPPED, on already > %.0fs]"
                  % (n, r["t_on"], r["routes"], r["ext_on"], TIME_LIMIT_S))
            if r["t_on"] > 10 * TIME_LIMIT_S:
                print("  -> stopping, far past practical limit")
                break
            continue
        speedup = r["t_off"] / r["t_on"] if r["t_on"] > 0 else float("nan")
        print("n=%3d  t_off=%8.2fs  t_on=%8.2fs  speedup=%5.2fx  routes=%6d  ext %d->%d"
              % (n, r["t_off"], r["t_on"], speedup, r["routes"], r["ext_off"], r["ext_on"]))
        sys.stdout.flush()
        if r["t_off"] > 5 * TIME_LIMIT_S:
            print("  -> t_off far past practical limit, stopping")
            break


if __name__ == "__main__":
    main()
