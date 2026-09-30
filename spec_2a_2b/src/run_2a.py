"""Spec 2a - verify DP o quy mo lon (n den 100), do hieu nang.

Luoi da khoa: config/grid_2a.yaml (locked_at 2026-09-10T12:59:28Z).
1440 lan chay = 6 n x 3 B x 4 tw x 2 n_drivers x 10 seed.

Moi lan chay: sinh instance (spatial_mode=dispersed, tau=20 co dinh), chay
DP label-setting (t6_dp qua dp_labeling.run_pool) cho TUNG driver, tong hop.

Timeout 600s/instance -> status="timeout" (van GHI vao summary, KHONG loai).
Driver doc lap -> chay song song qua process pool (12 core). Timeout ap o
muc INSTANCE: neu tong thoi gian 1 instance > 600s, huy phan con lai, status
= "timeout", ghi lai phan da xong.

Early-skip theo o luoi (KHONG lam sai tinh trung thuc - blowup don dieu theo
n va tw da xac nhan boi probe_scaling.csv): neu seed=0 cua 1 o
(n,B,tw,n_drivers) bi timeout, cac seed con lai cua DUNG o do duoc ghi
status="timeout_skipped" (van xuat hien trong summary voi runtime=NA) thay
vi chay lai - chung chac chan cung timeout. Ghi ro trong report.

Ghi:
  results/2a_raw/<key>.json     1 file / lan chay da chay that
  results/2a_summary.csv        1 dong / lan chay (ke ca timeout_skipped)
"""

import csv
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import psutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "2a_raw")
SUMMARY = os.path.join(ROOT, "results", "2a_summary.csv")

N_GRID = (10, 20, 30, 50, 75, 100)
B_GRID = (2, 3, 4)
TW_GRID = (30, 60, 120, 240)
NDRV_GRID = (5, 10)
SEEDS = range(10)
TAU = 20.0
SPATIAL = "dispersed"
TIMEOUT_S = 600.0
MEM_GUARD_MB = 4096       # [PATCH new_01] gioi han RAM/worker - B=4,tw=60 da
#                           2 lan OOM ca may (kill process ngoai kip thoi) truoc
#                           khi timeout 600s kip kich hoat: frontier tang toc do
#                           qua nhanh (>4GB/worker chi trong <1 phut). Kiem tra
#                           RSS moi worker moi 2s qua psutil - neu 1 worker VUOT
#                           nguong nay, huy CA O (khong doi timeout), ghi
#                           status="memory_exceeded", tai tao pool moi. Day la
#                           "circuit breaker" theo bo nho THAY VI chi theo thoi
#                           gian - tranh OOM toan he thong ma khong can doan
#                           truoc RAM can bao nhieu la du.
MEM_POLL_S = 2.0
N_WORKERS = 3            # 10-way lam OOM o n=50 B=3 tw>=60 (frontier ~1M+ label x
#                          worker); 4-way on dinh truoc do. [PATCH new_01] da THU
#                          6-way (12 logical core) theo yeu cau dung nhieu tai
#                          nguyen hon - THAT BAI: free RAM roi tu ~11GB xuong
#                          ~0.5GB (WorkingSet cua nhieu worker vuot 2GB dong thoi,
#                          PowerShell WorkingSet overflow am - dau hieu ro) ngay
#                          o o luoi DAU TIEN (n=10,B=2,tw=30,ndrv=5) truoc khi
#                          kip in dong nao - da kill toan bo process tree va ha
#                          lai 4-way (2026-09-12, ~50 phut vao lan chay 6-way).
#                          4-way SAU DO cung THAT BAI: chay tot qua toan bo
#                          n=50,B=4,tw=30 (20/20 seed, 0 timeout) nhung OOM lai
#                          ngay o seed dau tien cua n=50,B=4,tw=60,ndrv=5 - free
#                          RAM roi tu ~7GB xuong <500MB trong ~10s (ca 4 worker
#                          dong thoi ~4GB moi worker = ~16GB tong, vuot kha nang
#                          may). Da kill lan 2, ha xuong 3-way (2026-09-12,
#                          ~3.95gio vao lan chay 4-way). KHONG thu lai 4-way
#                          cho B=4/tw>=60: bang chung 2 lan la du - frontier o
#                          B=4,tw=60 lon hon han B=4,tw=30, 4 worker dong thoi
#                          la qua nhieu bat ke may co 31GB RAM.
#                          KHONG thu lai 6-way: OD gio co route pool THAT (khac
#                          du lieu buggy cu), frontier lon hon han gia dinh ban dau.

FIELDS = ["n", "B", "tw_width", "n_drivers", "seed", "runtime_seconds",
          "peak_frontier_size", "total_states_generated", "total_states_surviving",
          "survival_ratio", "n_complete_bundles_found", "theoretical_sequence_cap",
          "k_values", "status", "n_drivers_done"]


def seq_cap_for_k(k):
    """(2k)! / 2^k  - so sequence pickup/delivery hop le precedence, |S|=k."""
    return math.factorial(2 * k) / (2 ** k)


# ---- worker: chay DP cho 1 (instance, driver_index) --------------------------
_CACHE = {}


def _driver_job(args):
    n, B, tw, ndrv, gen_seed, di = args
    ck = (n, B, tw, ndrv, gen_seed)
    if ck not in _CACHE:
        drivers, orders, tt, meta = IG.generate_instance(
            n=n, B=B, tw_width=tw, n_drivers=ndrv, seed=gen_seed,
            tau=TAU, spatial_mode=SPATIAL)
        _CACHE.clear()
        _CACHE[ck] = (drivers, orders, tt, meta)
    drivers, orders, tt, meta = _CACHE[ck]
    drv = drivers[di]
    t0 = time.time()
    r = DL.run_pool(tt, drv, orders, B)
    return di, time.time() - t0, dict(
        n_generated=r["n_generated"], n_surviving=r["n_surviving"],
        peak_frontier=r["peak_frontier"], n_bundles=r["n_bundles"],
        k_values=sorted(r["k_values"]))


def _pool_worker_pids(pool):
    """Lay PID cua toan bo worker process dang song trong pool (ProcessPoolExecutor)."""
    try:
        return [p.pid for p in pool._processes.values() if p.pid is not None]
    except AttributeError:
        return []


def _any_worker_over_mem(pids, limit_mb):
    """True neu BAT KY worker nao (theo PID) vuot limit_mb RSS. Bo qua PID
    khong con song (process co the da thoat/duoc thay the)."""
    for pid in pids:
        try:
            p = psutil.Process(pid)
            rss_mb = p.memory_info().rss / (1024.0 * 1024.0)
            if rss_mb > limit_mb:
                return True, pid, rss_mb
        except psutil.NoSuchProcess:
            continue
    return False, None, None


def _force_kill_pool(pool):
    """[PATCH new_01] pool.shutdown(cancel_futures=True) KHONG giet process
    OS tren Windows - worker straggler VAN SONG, van giu RAM, ngay ca sau khi
    tao pool moi (da xac nhan thuc te: worker cu 3.8-4.1GB + worker moi 1-1.2GB
    CUNG TON TAI mot luc, day RAM ve <1GB ngay sau khi guard vua kich hoat cho
    ndrv=5, truoc khi kip xu ly ndrv=10). Phai giet PID that qua psutil truoc
    khi tao pool moi, khong chi goi shutdown()."""
    pids = _pool_worker_pids(pool)
    pool.shutdown(wait=False, cancel_futures=True)
    for pid in pids:
        try:
            psutil.Process(pid).kill()
        except psutil.NoSuchProcess:
            pass
    # doi ngan de OS giai phong RAM truoc khi pool moi bat dau cap phat
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if all(not psutil.pid_exists(pid) for pid in pids):
            break
        time.sleep(0.2)


def run_one(pool, n, B, tw, ndrv, seed):
    key = "n%d_B%d_tw%d_d%d_s%d" % (n, B, tw, ndrv, seed)
    gen_seed = IG.stable_seed(n, B, tw, ndrv, seed, "spec2a")

    jobs = [(n, B, tw, ndrv, gen_seed, di) for di in range(ndrv)]
    futs = {pool.submit(_driver_job, j): j[-1] for j in jobs}

    t0 = time.time()
    n_generated = n_surviving = peak_frontier = n_bundles_total = 0
    k_values = set()
    n_done = 0
    status = "completed"

    pending = set(futs.keys())
    try:
        while pending:
            remaining = TIMEOUT_S - (time.time() - t0)
            if remaining <= 0:
                status = "timeout"
                break
            poll = min(MEM_POLL_S, remaining)
            done, pending = _wait_any(pending, poll)
            if done:
                for fut in done:
                    di, rt, m = fut.result()
                    n_generated += m["n_generated"]
                    n_surviving += m["n_surviving"]
                    peak_frontier = max(peak_frontier, m["peak_frontier"])
                    n_bundles_total += m["n_bundles"]
                    k_values |= set(m["k_values"])
                    n_done += 1
                continue
            # khong future nao xong trong khoang poll - kiem tra RAM worker
            over, bad_pid, rss_mb = _any_worker_over_mem(_pool_worker_pids(pool), MEM_GUARD_MB)
            if over:
                status = "memory_exceeded"
                print("    !! worker pid=%s vuot %.0fMB (gioi han %.0fMB) - huy o nay ngay"
                      % (bad_pid, rss_mb, MEM_GUARD_MB))
                break
    finally:
        for fut in pending:
            fut.cancel()

    runtime = time.time() - t0
    survival_ratio = (n_surviving / n_generated) if n_generated else 0.0
    theo_cap = sum(seq_cap_for_k(k) for k in k_values) if k_values else 0.0

    rec = dict(
        n=n, B=B, tw_width=tw, n_drivers=ndrv, seed=seed,
        runtime_seconds=round(runtime, 4),
        peak_frontier_size=peak_frontier,
        total_states_generated=n_generated,
        total_states_surviving=n_surviving,
        survival_ratio=round(survival_ratio, 6),
        n_complete_bundles_found=n_bundles_total,
        theoretical_sequence_cap=theo_cap,
        k_values=sorted(k_values),
        status=status,
        n_drivers_done=n_done,
    )
    with open(os.path.join(RAW, key + ".json"), "w", encoding="utf-8") as f:
        json.dump({"record": rec}, f, indent=1)
    return rec


def _wait_any(futs, timeout):
    """Cho it nhat 1 future xong hoac het timeout. Tra (done_set, still_pending)."""
    done = set()
    try:
        for fut in as_completed(futs, timeout=timeout):
            done.add(fut)
            break
    except TimeoutError:
        return set(), futs
    return done, futs - done


def _skipped_rec(n, B, tw, ndrv, seed, reason="timeout"):
    return dict(
        n=n, B=B, tw_width=tw, n_drivers=ndrv, seed=seed,
        runtime_seconds="", peak_frontier_size="", total_states_generated="",
        total_states_surviving="", survival_ratio="", n_complete_bundles_found="",
        theoretical_sequence_cap="", k_values=[],
        status="%s_skipped" % reason,
        n_drivers_done=0)


def _load_done():
    """Resume: doc (n,B,tw,ndrv,seed) da co trong summary (neu file ton tai)."""
    seen = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B"]), int(r["tw_width"]),
                              int(r["n_drivers"]), int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    rows = []
    total = len(N_GRID) * len(B_GRID) * len(TW_GRID) * len(NDRV_GRID) * len(SEEDS)
    done = 0

    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))

    pool = ProcessPoolExecutor(max_workers=N_WORKERS)
    try:
        with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if not already:
                w.writeheader()
            for n in N_GRID:
                for B in B_GRID:
                    for tw in TW_GRID:
                        for ndrv in NDRV_GRID:
                            cell_stop_reason = None
                            rec = None
                            for sd in SEEDS:
                                if (n, B, tw, ndrv, sd) in already:
                                    done += 1
                                    continue
                                if cell_stop_reason is not None:
                                    rec = _skipped_rec(n, B, tw, ndrv, sd, reason=cell_stop_reason)
                                else:
                                    rec = run_one(pool, n, B, tw, ndrv, sd)
                                    if rec["status"] in ("timeout", "memory_exceeded"):
                                        cell_stop_reason = rec["status"]
                                        # giet worker That (PID) truoc khi tao pool moi -
                                        # shutdown() KHONG du tren Windows, xem _force_kill_pool
                                        _force_kill_pool(pool)
                                        pool = ProcessPoolExecutor(max_workers=N_WORKERS)
                                row = {k: rec[k] for k in FIELDS}
                                row["k_values"] = "|".join(str(x) for x in rec["k_values"])
                                w.writerow(row)
                                f.flush()
                                rows.append(rec)
                                done += 1
                            if rec is None:
                                continue   # ca o da co trong resume-set, khong in
                            print("  [%d/%d] n=%d B=%d tw=%d d=%d  elapsed=%.1fs  last_rt=%ss status=%s%s"
                                  % (done, total, n, B, tw, ndrv, time.time() - t_start,
                                     rec.get("runtime_seconds", "NA"), rec["status"],
                                     "  [cell: rest skipped, reason=%s]" % cell_stop_reason
                                     if cell_stop_reason else ""))
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    n_to = sum(1 for r in rows if r["status"] == "timeout")
    n_sk = sum(1 for r in rows if r["status"] == "timeout_skipped")
    n_me = sum(1 for r in rows if r["status"] == "memory_exceeded")
    n_mesk = sum(1 for r in rows if r["status"] == "memory_exceeded_skipped")
    n_ok = sum(1 for r in rows if r["status"] == "completed")
    print("\n=== 2a DONE ===  runs=%d  completed=%d  timeout=%d  timeout_skipped=%d  "
          "memory_exceeded=%d  memory_exceeded_skipped=%d  elapsed=%.1fs"
          % (len(rows), n_ok, n_to, n_sk, n_me, n_mesk, time.time() - t_start))


if __name__ == "__main__":
    main()
