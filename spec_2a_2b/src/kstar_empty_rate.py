"""RQ_following_check.md Viec (c) - tan suat K* rong, per-driver va per-instance.

(i) RQ1 main grid, TOAN BO 1500 instance (5 alignment x 3 n x 4 supply x 25 rep),
    dung dung seed cua RQ1 (rq_common.make_rq1_instance, B=3).
(ii) RQ5 V0/V5/V6 (FD x1.00/x0.75/x1.25), alignment=0.50 co dinh, dung dung seed
    cua RQ5 (rq_common.make_rq5_instance).

Dung lai NGUYEN kstar_rule.local_frontier (khong viet lai). Doi voi dinh nghia
K*_i rong: local_frontier tren pool CUA RIENG driver i (dinh dang list
(rid,S,K,W)) tra ve rong.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")


def driver_pool_to_routes(pool):
    routes, ctr = [], 0
    for S, kwl in pool.items():
        if not S:
            continue
        for (K, W) in kwl:
            routes.append(("r%d" % ctr, S, K, W))
            ctr += 1
    return routes


def kstar_empty_for_instance(pool_by_driver, q):
    """Tra (n_drivers, n_empty, per_driver_empty:list[bool])."""
    n_empty = 0
    flags = []
    for did, pool in pool_by_driver.items():
        routes = driver_pool_to_routes(pool)
        if not routes:
            # driver khong co route nao (khong the phuc vu bat ky order nao trong
            # gioi han B/tau) - tinh la "K* rong" theo dung dinh nghia Buoc 1:
            # khong co route nao dang dung o bat ky bid nao, vi khong co route.
            n_empty += 1
            flags.append(True)
            continue
        kept, _ = KR.local_frontier(routes, q, C.THETA_LO, C.THETA_HI)
        empty = len(kept) == 0
        n_empty += int(empty)
        flags.append(empty)
    return len(pool_by_driver), n_empty, flags


def part_i_rq1_main_grid():
    print("=" * 90)
    print("(i) RQ1 main grid - TOAN BO 1500 instance, K* rong theo alignment")
    print("=" * 90)
    jobs = [(a, n, ng, no, rep) for a in [0.10, 0.30, 0.50, 0.70, 0.90]
            for n in [10, 15, 20] for (ng, no) in [(2, 2), (3, 2), (2, 3), (3, 3)]
            for rep in range(25)]
    assert len(jobs) == 1500

    rows = []
    t0 = time.time()
    for i, (a, n, ng, no, rep) in enumerate(jobs):
        d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
        pool, _ = C.build_pool(tt, d, o, 3)
        nd, nempty, _ = kstar_empty_for_instance(pool, q)
        rows.append(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, n_drivers=nd,
                         n_driver_kstar_empty=nempty, driver_empty_rate=nempty / float(nd),
                         instance_fully_fd=(nempty == nd)))
        if (i + 1) % 150 == 0:
            print("  [%d/%d] %.1f min" % (i + 1, len(jobs), (time.time() - t0) / 60.0))
            sys.stdout.flush()

    out = os.path.join(D, "kstar_empty_by_alignment.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("-> %s" % out)

    print("\n| alignment | %% driver K* rong (mean) | %% instance TOAN BO driver K* rong |")
    print("|---:|---:|---:|")
    by_a = {}
    for r in rows:
        by_a.setdefault(r["alignment"], []).append(r)
    prev_mean = None
    monotone_ok = True
    for a in sorted(by_a):
        rs = by_a[a]
        m = statistics.mean(r["driver_empty_rate"] for r in rs)
        fi = statistics.mean(1.0 if r["instance_fully_fd"] else 0.0 for r in rs)
        print("| %.2f | %.1f%% | %.1f%% |" % (a, 100 * m, 100 * fi))
        if prev_mean is not None and m > prev_mean + 1e-9:
            monotone_ok = False
        prev_mean = m
    print("\nDon dieu giam theo alignment (bat buoc)? -> %s" % ("CO" if monotone_ok else "KHONG - DUNG LAI, kiem tra loi"))

    # doi chieu K* cut ratio da co o RQ4 (rq34_shard*.csv, pool_full/pool_kstar)
    r34 = []
    for fn in sorted(glob.glob(os.path.join(D, "rq34_shard*.csv"))):
        with open(fn, encoding="utf-8") as f:
            r34.extend(csv.DictReader(f))
    if r34:
        print("\nDoi chieu voi K* cut ratio (RQ4, pool-level, 600 instance alignment 0.50/0.90):")
        for a in [0.50, 0.90]:
            rs = [r for r in r34 if abs(float(r["alignment"]) - a) < 1e-9]
            cut = statistics.median(1 - float(r["pool_kstar"]) / float(r["pool_full"]) for r in rs)
            de = statistics.mean(r["driver_empty_rate"] for r in by_a[a])
            print("  alignment=%.2f: pool cut ratio (RQ4) median=%.1f%%  vs  driver-empty rate (Viec c) mean=%.1f%%  (cung huong? %s)"
                  % (a, 100 * cut, 100 * de, "CO" if (cut > 0.5) == (de > 0.5) else "KIEM TRA"))
    return rows, monotone_ok


def part_ii_rq5_fd_price():
    print("\n" + "=" * 90)
    print("(ii) RQ5 V0/V5/V6 - K* rong theo gia FD, alignment=0.50 co dinh")
    print("=" * 90)
    variants = [("V5_fd075", 0.75), ("V0_baseline", 1.00), ("V6_fd125", 1.25)]
    rows = []
    for vname, mult in variants:
        for (ng, no) in C.RQ5_SUPPLY_BASE:
            for rep in range(15):
                d, o, tt, meta, th, q, tw = C.make_rq5_instance(vname, ng, no, rep, B=3)
                pool, _ = C.build_pool(tt, d, o, 3)
                nd, nempty, _ = kstar_empty_for_instance(pool, q)
                rows.append(dict(variant=vname, fd_multiplier=mult, n_gw=ng, n_od=no, rep=rep,
                                 n_drivers=nd, n_driver_kstar_empty=nempty,
                                 driver_empty_rate=nempty / float(nd),
                                 instance_fully_fd=(nempty == nd)))
    out = os.path.join(D, "kstar_empty_by_fd_price.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("-> %s" % out)

    print("\n| FD multiplier | %% driver K* rong (mean) | %% instance TOAN BO driver K* rong |")
    print("|---:|---:|---:|")
    by_v = {}
    for r in rows:
        by_v.setdefault(r["fd_multiplier"], []).append(r)
    prev_mean = None
    monotone_ok = True
    for mult in sorted(by_v):
        rs = by_v[mult]
        m = statistics.mean(r["driver_empty_rate"] for r in rs)
        fi = statistics.mean(1.0 if r["instance_fully_fd"] else 0.0 for r in rs)
        print("| x%.2f | %.1f%% | %.1f%% |" % (mult, 100 * m, 100 * fi))
        if prev_mean is not None and m > prev_mean + 1e-9:
            monotone_ok = False
        prev_mean = m
    print("\nDon dieu GIAM khi FD dat hon (bat buoc)? -> %s" % ("CO" if monotone_ok else "KHONG - DUNG LAI, kiem tra loi"))
    return rows, monotone_ok


if __name__ == "__main__":
    rows_i, ok_i = part_i_rq1_main_grid()
    rows_ii, ok_ii = part_ii_rq5_fd_price()
    print("\n" + "=" * 90)
    print("TONG KET Viec (c): don dieu (i)=%s  don dieu (ii)=%s  -> %s"
          % (ok_i, ok_ii, "CO THE BAO CAO" if (ok_i and ok_ii) else "CAN DIEU TRA TRUOC KHI BAO CAO"))
