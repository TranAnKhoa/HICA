"""RQ_following_check.md Viec (b) - component decomposition (T5) tren pool
da cat K*, dung dung 600 instance cua RQ3+RQ4 (cung seed, cung B=3). Dung lai
NGUYEN rq_common (instance/pool) + prune_pool_by_kstar (da dung o RQ4) +
t8_cplex.build_conflict_graph/connected_components (khong viet lai logic).
"""
import csv
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)

import rq_common as C
import rq1_wdp as RW
import t8_cplex as T8
from kstar_zstar_payment_check import prune_pool_by_kstar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")
OUT = os.path.join(D, "component_distribution_kstar.csv")


def component_stats(pool_by_driver, theta):
    """pool_by_driver -> wdp_drivers format (build_conflict_graph can) -> comps."""
    wdp = RW.build_wdp_drivers(pool_by_driver, theta)
    g = T8.build_conflict_graph(wdp)
    comps = T8.connected_components(g)
    n_drivers = len(pool_by_driver)
    if n_drivers == 0:
        return 0, 0.0, 0
    largest = max((len(c) for c in comps), default=0)
    n_isolated = sum(1 for c in comps if len(c) == 1)
    return len(comps), largest / float(n_drivers), n_isolated


def run_step4(pool_kstar, theta, q, oids, comps):
    """Voi instance co >=2 component: t_component_wise (removal-solve tung
    component rieng, cong lai) vs t_monolithic (removal-solve tren toan pool
    K* khong tach). 'removal-solve' = 1 full-solve + 1 removal-solve/driver
    trong component do (dung logic C.vcg nhung gioi han vao subset driver)."""
    def removal_block(pool_sub, driver_ids):
        sub = {d: pool_sub[d] for d in driver_ids if d in pool_sub}
        if not sub:
            return 0.0
        t0 = time.perf_counter()
        full = C.solve(sub, C.true_cost_fn(theta), q, oids)
        for did in sub:
            C.solve(sub, C.true_cost_fn(theta), q, oids, excluded=did)
        return time.perf_counter() - t0

    t0 = time.perf_counter()
    t_component_wise = sum(removal_block(pool_kstar, list(comp)) for comp in comps)
    t_monolithic = removal_block(pool_kstar, list(pool_kstar.keys()))
    return t_monolithic, t_component_wise


def main():
    r34 = []
    import glob
    for fn in sorted(glob.glob(os.path.join(D, "rq34_shard*.csv"))):
        with open(fn, encoding="utf-8") as f:
            r34.extend(csv.DictReader(f))
    jobs = [(float(r["alignment"]), int(r["n"]), int(r["n_gw"]), int(r["n_od"]), int(r["rep"]))
            for r in r34]
    assert len(jobs) == 600, "khong du 600 instance RQ3/RQ4 (%d)" % len(jobs)

    rows = []
    t_start = time.time()
    for i, (a, n, ng, no, rep) in enumerate(jobs):
        d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
        oids = list(o)
        pool_full, _ = C.build_pool(tt, d, o, 3)
        pool_k = prune_pool_by_kstar(pool_full, q, C.THETA_LO, C.THETA_HI)

        n_full, frac_full, iso_full = component_stats(pool_full, th)
        n_k, frac_k, iso_k = component_stats(pool_k, th)
        n_drivers = len(pool_full)

        rows.append(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, n_drivers=n_drivers,
                         n_components_full=n_full, largest_component_full_frac=frac_full,
                         n_components_kstar=n_k, largest_component_kstar_frac=frac_k,
                         n_isolated_kstar=iso_k, pct_isolated_kstar=iso_k / float(n_drivers)))
        if (i + 1) % 100 == 0:
            print("[%d/%d] %.1f min" % (i + 1, len(jobs), (time.time() - t_start) / 60.0))
            sys.stdout.flush()

    os.makedirs(D, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("-> %s" % OUT)

    print("\n| alignment | largest/n_drivers pool day du (median) | largest/n_drivers pool K* (median) | %% driver co lap (K*) |")
    print("|---:|---:|---:|---:|")
    by_a = {}
    for r in rows:
        by_a.setdefault(r["alignment"], []).append(r)
    do_step4 = []
    for a in sorted(by_a):
        rs = by_a[a]
        mf = statistics.median(r["largest_component_full_frac"] for r in rs)
        mk = statistics.median(r["largest_component_kstar_frac"] for r in rs)
        iso = statistics.mean(r["pct_isolated_kstar"] for r in rs)
        print("| %.2f | %.3f | %.3f | %.1f%% |" % (a, mf, mk, 100 * iso))
        if abs(a - 0.90) < 1e-9:
            do_step4 = rs

    print("\nSo instance (alignment=0.90) co >=2 component o pool K*: %d / %d"
          % (sum(1 for r in do_step4 if r["n_components_kstar"] >= 2), len(do_step4)))

    if do_step4 and statistics.median(r["largest_component_kstar_frac"] for r in do_step4) < 0.85:
        print("\n=== Buoc 4 - do speedup component-wise vs monolithic (alignment=0.90, >=2 component) ===")
        step4_rows = []
        multi = [(r["alignment"], r["n"], r["n_gw"], r["n_od"], r["rep"]) for r in do_step4
                if r["n_components_kstar"] >= 2]
        for (a, n, ng, no, rep) in multi:
            d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
            oids = list(o)
            pool_full, _ = C.build_pool(tt, d, o, 3)
            pool_k = prune_pool_by_kstar(pool_full, q, C.THETA_LO, C.THETA_HI)
            wdp = RW.build_wdp_drivers(pool_k, th)
            g = T8.build_conflict_graph(wdp)
            comps = T8.connected_components(g)
            t_mono, t_comp = run_step4(pool_k, th, q, oids, comps)
            sp = t_mono / t_comp if t_comp > 0 else float("nan")
            step4_rows.append(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep,
                                   n_components=len(comps), t_monolithic=t_mono,
                                   t_component_wise=t_comp, speedup=sp))
        with open(os.path.join(D, "component_speedup_kstar_step4.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(step4_rows[0].keys()))
            w.writeheader(); w.writerows(step4_rows)
        sp_vals = [r["speedup"] for r in step4_rows if r["speedup"] == r["speedup"]]
        print("N=%d instance co >=2 component. Speedup median=%.2fx mean=%.2fx"
              % (len(step4_rows), statistics.median(sp_vals), statistics.mean(sp_vals)))
    else:
        print("\nlargest_component_kstar_frac o alignment=0.90 van >= 0.85 (gan bang pool day du)")
        print("-> T5 tren K* KHONG cai thien dang ke o che do canh tranh. Bo qua Buoc 4 (dung theo tieu chi da khoa).")


if __name__ == "__main__":
    main()
