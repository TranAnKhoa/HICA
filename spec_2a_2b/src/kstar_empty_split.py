"""Final_run_checkilist.md Viec A (Hica_S_Master_Writeup.md Sec18.1) - tach
"K* rong" thanh hai loai:
  feasible_empty : R_i rong (khong co route nao kha thi - su that hinh hoc,
                    khong lien quan Theorem 4)
  fd_dominated    : R_i khac rong NHUNG K*_i rong (moi route bi FD-completion
                    vuot troi tren toan Theta - day moi la he qua That 4)
Dung dung 1500 instance RQ1 main grid + 180 instance RQ5 V0/V5/V6 nhu
kstar_empty_rate.py da chay - khong sinh instance moi, khong giai lai WDP.
"""
import csv
import glob
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)

import rq_common as C
import kstar_rule as KR
from kstar_empty_rate import driver_pool_to_routes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")


def kstar_split_for_instance(pool_by_driver, q):
    """Tra list per-driver dict {feasible_empty, kstar_empty, fd_dominated}."""
    out = []
    for did, pool in pool_by_driver.items():
        routes = driver_pool_to_routes(pool)
        feasible_empty = (len(routes) == 0)
        if feasible_empty:
            kstar_empty = True   # R_i rong => K*_i rong theo dinh nghia (khong co gi de giu)
        else:
            kept, _ = KR.local_frontier(routes, q, C.THETA_LO, C.THETA_HI)
            kstar_empty = (len(kept) == 0)
        fd_dominated = kstar_empty and not feasible_empty
        out.append(dict(driver_id=did, feasible_empty=feasible_empty,
                        kstar_empty=kstar_empty, fd_dominated=fd_dominated))
    return out


def part_i_rq1_main_grid():
    print("=" * 90)
    print("Viec A phan (i) - RQ1 main grid, 1500 instance, tach feasible_empty/fd_dominated")
    print("=" * 90)
    jobs = [(a, n, ng, no, rep) for a in [0.10, 0.30, 0.50, 0.70, 0.90]
            for n in [10, 15, 20] for (ng, no) in [(2, 2), (3, 2), (2, 3), (3, 3)]
            for rep in range(25)]
    assert len(jobs) == 1500

    driver_rows = []
    inst_rows = []
    t0 = time.time()
    for i, (a, n, ng, no, rep) in enumerate(jobs):
        d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
        pool, _ = C.build_pool(tt, d, o, 3)
        per_driver = kstar_split_for_instance(pool, q)
        for pd in per_driver:
            driver_rows.append(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, **pd))

        nd = len(per_driver)
        n_feas_empty = sum(1 for r in per_driver if r["feasible_empty"])
        n_kstar_empty = sum(1 for r in per_driver if r["kstar_empty"])
        n_fd_dom = sum(1 for r in per_driver if r["fd_dominated"])
        nonempty = [r for r in per_driver if not r["feasible_empty"]]
        inst_rows.append(dict(
            alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, n_drivers=nd,
            n_feasible_empty=n_feas_empty, n_kstar_empty=n_kstar_empty, n_fd_dominated=n_fd_dom,
            all_feasible_empty=(n_feas_empty == nd),
            all_kstar_empty=(n_kstar_empty == nd),
            all_nonempty_fd_dominated=(len(nonempty) > 0 and all(r["fd_dominated"] for r in nonempty)),
            n_nonempty=len(nonempty),
        ))
        if (i + 1) % 150 == 0:
            print("  [%d/%d] %.1f min" % (i + 1, len(jobs), (time.time() - t0) / 60.0))
            sys.stdout.flush()

    out_d = os.path.join(D, "kstar_empty_split_by_alignment.csv")
    with open(out_d, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(driver_rows[0].keys()))
        w.writeheader(); w.writerows(driver_rows)
    print("-> %s (%d dong per-driver)" % (out_d, len(driver_rows)))

    out_i = os.path.join(D, "kstar_empty_split_by_alignment_instance.csv")
    with open(out_i, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(inst_rows[0].keys()))
        w.writeheader(); w.writerows(inst_rows)
    print("-> %s (%d dong per-instance)" % (out_i, len(inst_rows)))

    print("\nBang per-driver (mean tren toan bo driver, %):")
    print("| alignment | %% feasible_empty | %% fd_dominated (moi driver) | %% fd_dominated | R_i != empty |")
    print("|---:|---:|---:|---:|")
    by_a = {}
    for r in driver_rows:
        by_a.setdefault(r["alignment"], []).append(r)
    for a in sorted(by_a):
        rs = by_a[a]
        pf = statistics.mean(1.0 if r["feasible_empty"] else 0.0 for r in rs)
        pfd = statistics.mean(1.0 if r["fd_dominated"] else 0.0 for r in rs)
        nonempty = [r for r in rs if not r["feasible_empty"]]
        pfd_cond = (statistics.mean(1.0 if r["fd_dominated"] else 0.0 for r in nonempty)
                   if nonempty else float("nan"))
        print("| %.2f | %.1f%% | %.1f%% | %.1f%% |" % (a, 100 * pf, 100 * pfd, 100 * pfd_cond))

    print("\nBang per-instance (%):")
    print("| alignment | %% instance moi driver feasible_empty | %% instance moi driver kstar_empty | %% instance moi driver (R_i!=empty) deu fd_dominated |")
    print("|---:|---:|---:|---:|")
    by_a2 = {}
    for r in inst_rows:
        by_a2.setdefault(r["alignment"], []).append(r)
    for a in sorted(by_a2):
        rs = by_a2[a]
        pf = statistics.mean(1.0 if r["all_feasible_empty"] else 0.0 for r in rs)
        pk = statistics.mean(1.0 if r["all_kstar_empty"] else 0.0 for r in rs)
        pfd = statistics.mean(1.0 if r["all_nonempty_fd_dominated"] else 0.0 for r in rs)
        print("| %.2f | %.1f%% | %.1f%% | %.1f%% |" % (a, 100 * pf, 100 * pk, 100 * pfd))

    # check bat buoc: feasible_empty KHONG doi theo FD (kiem sau, o phan (ii))
    return driver_rows, inst_rows


def part_ii_rq5_fd_price():
    print("\n" + "=" * 90)
    print("Viec A phan (ii) - RQ5 V0/V5/V6, tach theo gia FD, alignment=0.50 co dinh")
    print("=" * 90)
    variants = [("V5_fd075", 0.75), ("V0_baseline", 1.00), ("V6_fd125", 1.25)]
    driver_rows = []
    for vname, mult in variants:
        for (ng, no) in C.RQ5_SUPPLY_BASE:
            for rep in range(15):
                d, o, tt, meta, th, q, tw = C.make_rq5_instance(vname, ng, no, rep, B=3)
                pool, _ = C.build_pool(tt, d, o, 3)
                per_driver = kstar_split_for_instance(pool, q)
                for pd in per_driver:
                    driver_rows.append(dict(variant=vname, fd_multiplier=mult, n_gw=ng, n_od=no,
                                            rep=rep, **pd))

    out = os.path.join(D, "kstar_empty_split_by_fd_price.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(driver_rows[0].keys()))
        w.writeheader(); w.writerows(driver_rows)
    print("-> %s (%d dong)" % (out, len(driver_rows)))

    print("\n| FD multiplier | %% feasible_empty | %% fd_dominated (moi driver) | %% fd_dominated | R_i != empty |")
    print("|---:|---:|---:|---:|")
    by_v = {}
    for r in driver_rows:
        by_v.setdefault(r["fd_multiplier"], []).append(r)
    prev_pf, prev_pfd = None, None
    feas_ok, fd_mono_ok = True, True
    for mult in sorted(by_v):
        rs = by_v[mult]
        pf = statistics.mean(1.0 if r["feasible_empty"] else 0.0 for r in rs)
        pfd = statistics.mean(1.0 if r["fd_dominated"] else 0.0 for r in rs)
        nonempty = [r for r in rs if not r["feasible_empty"]]
        pfd_cond = (statistics.mean(1.0 if r["fd_dominated"] else 0.0 for r in nonempty)
                   if nonempty else float("nan"))
        print("| x%.2f | %.1f%% | %.1f%% | %.1f%% |" % (mult, 100 * pf, 100 * pfd, 100 * pfd_cond))
        if prev_pf is not None and abs(pf - prev_pf) > 1e-9:
            feas_ok = False
        if prev_pfd is not None and pfd > prev_pfd + 1e-9:
            fd_mono_ok = False
        prev_pf, prev_pfd = pf, pfd

    print("\n[CHECK] feasible_empty KHONG doi theo gia FD (bat buoc)? -> %s"
          % ("CO" if feas_ok else "KHONG - CO BUG trong cach gan co"))
    print("[CHECK] fd_dominated GIAM don dieu khi FD dat hon (bat buoc)? -> %s"
          % ("CO" if fd_mono_ok else "KHONG - dung lai, kiem tra local_frontier/gan gia"))
    return driver_rows, feas_ok, fd_mono_ok


if __name__ == "__main__":
    part_i_rq1_main_grid()
    _, feas_ok, fd_mono_ok = part_ii_rq5_fd_price()
    print("\n" + "=" * 90)
    print("TONG KET Viec A: feasible_empty bat bien theo FD=%s  fd_dominated don dieu=%s -> %s"
          % (feas_ok, fd_mono_ok, "CO THE BAO CAO" if (feas_ok and fd_mono_ok) else "CAN DIEU TRA"))
