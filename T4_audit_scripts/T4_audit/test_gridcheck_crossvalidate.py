"""Add_test.md Sec1 -- independent re-implementation check: so kstar_rule.py
(kink-based, affine dominator lines + envelope) voi kstar_gridcheck.py (grid
brute-force, KHONG dung cau truc affine/kink, tu viet lai E_r/c_r tu dau).

Chay tren CA HAI nguon instance:
  (A) 5 seed tong hop cua test_theorem.py (hica_core.random_instance, cung
      seed 0-4 da dung trong AUDIT_REPORT.md Sec2) -- moi seed nhieu driver,
      moi driver 1 pool rieng.
  (B) 5 instance RQ1 THAT da dung trong kstar_rq1_crosscheck.py (cung n,
      n_drivers, seed voi log activation-rate cu) -- phu them moi truong
      thesis that (dp_labeling.build_route_pool), khong chi instance tong hop.

Gate (Add_test.md Sec1.3): hai tap kept phai khop TUYET DOI tren MOI driver
cua MOI instance. Neu lech, tang n_grid truoc khi ket luan la bug that.

Chay bang Python 3.13 (anaconda) cho phan (A) -- hica_core can scipy.
Phan (B) can Python 3.7.7 + CPLEX (dung lai instance_gen/dp_labeling/rq1_cost_gen
cua spec_2a_2b) -- TACH RIENG thanh ham run_part_B(), goi tu file khac trong
moi truong dung neu can (xem huong dan cuoi file).
"""
import sys
import time

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")

from hica_core import random_instance, enumerate_pool
import kstar_rule as KR
import kstar_gridcheck as GC

LO, HI = 18.0, 25.0
N_GRID = 5000


def routes_as_tuples(pool):
    """hica_core.Route list -> [(rid, bundle, K, W), ...] (dinh dang chung
    ca kstar_rule.local_frontier va kstar_gridcheck.kstar_gridcheck can)."""
    return [(r.rid, r.bundle, r.K, r.W) for r in pool]


def qdict(orders):
    return {oid: o.q for oid, o in orders.items()}


def run_part_A(seeds=range(5), n=8, n_gw=2, n_od=2, B=3, n_grid=N_GRID):
    """5 seed tong hop (giong test_theorem.py) -- moi truong Python 3.13 + scipy
    (chi can hica_core cho random_instance/enumerate_pool, KHONG can solve_wdp
    o day vi chi so sanh K*, khong giai WDP)."""
    rows = []
    for seed in seeds:
        t0 = time.time()
        orders, drivers = random_instance(n, n_gw, n_od, seed, B=B)
        q = qdict(orders)
        for d in drivers:
            pool = enumerate_pool(d, orders, B)
            if not pool:
                continue
            routes = routes_as_tuples(pool)
            kept_kink, _ = KR.local_frontier(routes, q, LO, HI)
            kept_grid, _ = GC.kstar_gridcheck(routes, q, LO, HI, n_grid=n_grid)
            match = set(kept_kink) == set(kept_grid)
            rows.append(dict(source="A-synthetic", seed=seed, driver=d.id,
                             pool=len(pool), kept_kink=len(kept_kink),
                             kept_grid=len(kept_grid), match=match,
                             only_kink=sorted(set(kept_kink) - set(kept_grid)),
                             only_grid=sorted(set(kept_grid) - set(kept_kink))))
        print("  [A] seed=%d done (%.1fs)" % (seed, time.time() - t0))
        sys.stdout.flush()
    return rows


def print_report(rows):
    print("\n%-14s %6s %8s %6s %10s %10s %6s" %
         ("source", "seed", "driver", "pool", "kept_kink", "kept_grid", "match"))
    n_fail = 0
    for r in rows:
        ok = "OK" if r["match"] else "MISMATCH"
        if not r["match"]:
            n_fail += 1
        print("%-14s %6s %8s %6d %10d %10d %6s" %
             (r["source"], r["seed"], r["driver"], r["pool"],
              r["kept_kink"], r["kept_grid"], ok))
        if not r["match"]:
            print("      only_kink:", r["only_kink"])
            print("      only_grid:", r["only_grid"])
    print("\n[Gate Add_test.md Sec1.3] %d/%d driver-pool khop tuyet doi -> %s"
         % (len(rows) - n_fail, len(rows), "PASS" if n_fail == 0 else "FAIL"))
    return n_fail


if __name__ == "__main__":
    print("=" * 100)
    print("Independent re-implementation check: kstar_rule (kink-based) vs kstar_gridcheck (grid brute-force)")
    print("Phan (A): 5 seed tong hop (hica_core.random_instance), n_grid=%d" % N_GRID)
    print("=" * 100)
    rows_A = run_part_A()
    n_fail = print_report(rows_A)

    print("\nPhan (B) instance RQ1 THAT (Python 3.7.7 + CPLEX) can chay rieng --")
    print("xem test_gridcheck_crossvalidate_rq1.py (moi truong khac, khong the goi")
    print("chung file nay vi hica_core/scipy chi co o Python 3.13, dp_labeling/CPLEX")
    print("chi co o Python 3.7.7).")

    sys.exit(1 if n_fail else 0)
