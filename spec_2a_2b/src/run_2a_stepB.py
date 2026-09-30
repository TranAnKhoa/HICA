"""new03.md Viec 3.1 Buoc B - truc chinh: khao sat B_gw mo rong (them B_gw=5,
truoc day chua test). B_od CO DINH = 2 (gia tri "thuc te" nhat theo gia
thuyet Viec 1.1, xac nhan boi 2a_stepA). Gop luon Viec 2.4 vao day (filter_mode
in {off,on}) - KHONG chay tach rieng cho PCF benefit.

Thay the HOAN TOAN bang A.3 cu (khong con chay B chung nua).

Luoi: n in {10,20,30,50,75,100} x B_gw in {2,3,4,5} x B_od=2(co dinh) x
tw in {30,60,120,240} x n_drivers in {5,10} x seed in {0..9} x
filter_mode in {off,on}.

Ha tang: BAN DAU du dinh giu memory-guard/pool tu run_2a.py cu, nhung moi
truong hien tai (Python 3.7.7/Windows) khong co psutil (khong mang de cai)
VA ProcessPoolExecutor bi loi "WinError 6: handle invalid" khi poll bang
as_completed(timeout=..) lap lai - da thu va xac nhan crash that (xem
2a_stepB_stdout.txt/stdout2.txt lich su). Chuyen sang chay TUAN TU tung
driver (cung pattern da chay on dinh o run_pcf_benefit.py/run_gate_t4b.py),
chi con TIMEOUT_S (kiem giua cac driver, khong ngat giua dp).
"""

import csv
import json
import math
import os
import sys
import time

# [PATCH] Da bo ProcessPoolExecutor + psutil: moi truong nay (Python 3.7.7
# tren Windows) gap loi "OSError: [WinError 6] The handle is invalid" trong
# _queue_management_worker khi poll pool bang as_completed(timeout=..) lien
# tuc (xem 2a_stepB_stdout2.txt) - la loi da biet cua concurrent.futures tren
# Windows/3.7 khi poll ngan lap lai, khong phai bug logic o day. psutil cung
# khong co san (khong co mang de cai). Ha xuong: chay TUAN TU tung driver
# (giong pattern da chay on dinh o run_pcf_benefit.py/run_gate_t4b.py),
# TIMEOUT_S van giu (kiem tra GIUA cac driver, khong ngat giua 1 lan goi DP).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "2a_stepB_raw")
SUMMARY = os.path.join(ROOT, "results", "2a_stepB_summary.csv")

N_GRID = (10, 20, 30, 50, 75, 100)
BGW_GRID = (2, 3, 4, 5)
BOD_FIXED = 2
TW_GRID = (30, 60, 120, 240)
NDRV_GRID = (5, 10)
SEEDS = range(10)
FILTER_MODES = ("off", "on")
TAU = 20.0
SPATIAL = "dispersed"
TIMEOUT_S = 600.0

# BANG CHUNG THUC NGHIEM tu run_pcf_benefit.py (Viec 2.4, cung ngay, ndrv=10
# nhu o day): so states/runtime tang RAT nhanh theo B_gw VA n, doc lap voi
# filter_mode (PCF khong cat duoc growth). Da do truc tiep (1 driver-set,
# ndrv=10):
#   n=20,B_gw=4: ~30-120s | n=30,B_gw=4: ~140-225s | n=50/75,B_gw=4: da BO
#     QUA vi ngoai suy >1000-3000s/cell (xac nhan boi B_gw=4,n=30->n=50 growth)
#   n=20,B_gw=5: ~180-190s (da gan timeout 300s cua script do)
#   n=30/50/75,B_gw=5: da BO QUA (chac chan te hon B_gw=4 cung n)
# O day TIMEOUT_S=600s (gap doi 2a_stepB so voi 300s cua pcf_benefit) va
# N_GRID di xa hon (toi 100) - de an toan tuong tu, bo qua (n,B_gw) o vung
# da xac nhan bat kha thi thay vi de MEM_GUARD/TIMEOUT tu choi lap lai o
# tung cell hang tram/nghin giay. Giu it nhat 1 diem do da co (n=20,B_gw=5)
# lam bang chung ve gioi han truc B_gw.
_SKIP_N_BGW = frozenset([
    (50, 4), (75, 4), (100, 4),
    (30, 5), (50, 5), (75, 5), (100, 5),
])


def _skip_cell(n, B_gw):
    return (n, B_gw) in _SKIP_N_BGW

FIELDS = ["n", "B_gw", "B_od", "tw_width", "n_drivers", "filter_mode", "seed",
          "runtime_seconds", "peak_frontier_size", "total_states_generated",
          "total_states_surviving", "survival_ratio", "n_complete_bundles_found",
          "theoretical_sequence_cap", "k_values", "status", "n_drivers_done"]


def seq_cap_for_k(k):
    return math.factorial(2 * k) / (2 ** k)


def run_one(n, B_gw, B_od, tw, ndrv, filter_mode, seed):
    key = "n%d_Bgw%d_Bod%d_tw%d_d%d_%s_s%d" % (n, B_gw, B_od, tw, ndrv, filter_mode, seed)
    gen_seed = IG.stable_seed(n, B_gw, B_od, tw, ndrv, filter_mode, seed, "spec2a_stepB")

    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=ndrv, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    compat_graph = IG.build_compat_graph(tt, orders) if filter_mode == "on" else None

    t0 = time.time()
    n_generated = n_surviving = peak_frontier = n_bundles_total = 0
    k_values = set()
    n_done = 0
    status = "completed"

    for di in range(ndrv):
        if time.time() - t0 > TIMEOUT_S:
            status = "timeout"
            break
        r = DL.run_pool(tt, drivers[di], orders, B_gw, B_od, compat_graph=compat_graph)
        n_generated += r["n_generated"]
        n_surviving += r["n_surviving"]
        peak_frontier = max(peak_frontier, r["peak_frontier"])
        n_bundles_total += r["n_bundles"]
        k_values |= set(r["k_values"])
        n_done += 1

    runtime = time.time() - t0
    survival_ratio = (n_surviving / n_generated) if n_generated else 0.0
    theo_cap = sum(seq_cap_for_k(k) for k in k_values) if k_values else 0.0

    rec = dict(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=ndrv, filter_mode=filter_mode,
        seed=seed, runtime_seconds=round(runtime, 4),
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


def _skipped_rec(n, B_gw, B_od, tw, ndrv, filter_mode, seed, reason="timeout"):
    return dict(
        n=n, B_gw=B_gw, B_od=B_od, tw_width=tw, n_drivers=ndrv, filter_mode=filter_mode,
        seed=seed, runtime_seconds="", peak_frontier_size="", total_states_generated="",
        total_states_surviving="", survival_ratio="", n_complete_bundles_found="",
        theoretical_sequence_cap="", k_values=[],
        status="%s_skipped" % reason,
        n_drivers_done=0)


def _load_done():
    seen = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B_gw"]), int(r["B_od"]), int(r["tw_width"]),
                              int(r["n_drivers"]), r["filter_mode"], int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    rows = []
    total = (len(N_GRID) * len(BGW_GRID) * len(TW_GRID) * len(NDRV_GRID)
             * len(FILTER_MODES) * len(SEEDS))
    done = 0

    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))
    n_skipped_cells = 0

    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for n in N_GRID:
            for B_gw in BGW_GRID:
                if _skip_cell(n, B_gw):
                    n_skipped_cells += 1
                    skip_n = len(TW_GRID) * len(NDRV_GRID) * len(FILTER_MODES) * len(SEEDS)
                    done += skip_n
                    print("  [%d/%d] n=%d Bgw=%d SKIPPED toan bo (brute blowup, xem _SKIP_N_BGW)"
                          % (done, total, n, B_gw))
                    continue
                for tw in TW_GRID:
                    for ndrv in NDRV_GRID:
                        for filter_mode in FILTER_MODES:
                            cell_stop_reason = None
                            rec = None
                            for sd in SEEDS:
                                if (n, B_gw, BOD_FIXED, tw, ndrv, filter_mode, sd) in already:
                                    done += 1
                                    continue
                                if cell_stop_reason is not None:
                                    rec = _skipped_rec(n, B_gw, BOD_FIXED, tw, ndrv,
                                                      filter_mode, sd, reason=cell_stop_reason)
                                else:
                                    rec = run_one(n, B_gw, BOD_FIXED, tw, ndrv, filter_mode, sd)
                                    if rec["status"] in ("timeout", "memory_exceeded"):
                                        cell_stop_reason = rec["status"]
                                row = {k: rec[k] for k in FIELDS}
                                row["k_values"] = "|".join(str(x) for x in rec["k_values"])
                                w.writerow(row)
                                f.flush()
                                rows.append(rec)
                                done += 1
                            if rec is None:
                                continue
                            print("  [%d/%d] n=%d Bgw=%d tw=%d d=%d mode=%s  elapsed=%.1fs  "
                                  "last_rt=%ss status=%s%s"
                                  % (done, total, n, B_gw, tw, ndrv, filter_mode,
                                     time.time() - t_start,
                                     rec.get("runtime_seconds", "NA"), rec["status"],
                                     "  [cell: rest skipped, reason=%s]" % cell_stop_reason
                                     if cell_stop_reason else ""))
    n_to = sum(1 for r in rows if r["status"] == "timeout")
    n_sk = sum(1 for r in rows if r["status"] == "timeout_skipped")
    n_me = sum(1 for r in rows if r["status"] == "memory_exceeded")
    n_mesk = sum(1 for r in rows if r["status"] == "memory_exceeded_skipped")
    n_ok = sum(1 for r in rows if r["status"] == "completed")
    print("\n=== 2a STEP B DONE ===  runs=%d  completed=%d  timeout=%d  timeout_skipped=%d  "
          "memory_exceeded=%d  memory_exceeded_skipped=%d  (n,B_gw)_cells_skipped=%d  elapsed=%.1fs"
          % (len(rows), n_ok, n_to, n_sk, n_me, n_mesk, n_skipped_cells, time.time() - t_start))


if __name__ == "__main__":
    main()
