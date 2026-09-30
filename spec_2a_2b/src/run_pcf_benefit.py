"""new03.md Viec 2.4 - do loi ich THAT cua PCF (runtime, peak_frontier_size),
CHI chay sau khi Gate T4-B PASS tuyet doi. So sanh filter_mode in {off, on}
TREN CUNG tham so (cung instance, cung seed) - day la cau tra loi truc tiep
cho cau hoi "PCF co giup T4 nhanh hon khong".

Luoi (new03.md Sec2.4): n in {20,30,50,75} x B_gw in {3,4,5} x
tw_width in {60,120,240} x filter_mode in {off,on} x seed in {0..4}.
B_od co dinh = 2 (gia tri "thuc te" theo gia thuyet Viec 1.1).

KHONG co nguong ap dat truoc - bao cao trung thuc runtime/frontier ca 2 che
do, doc ket qua theo dung new03.md Sec2.4 (diem "vo" co bi day lui khong).
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import dp_labeling as DL

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "pcf_benefit_raw")
SUMMARY = os.path.join(ROOT, "results", "pcf_benefit_summary.csv")

N_GRID = (20, 30, 50, 75)
BGW_GRID = (3, 4, 5)
BOD_FIXED = 2
TW_GRID = (60, 120, 240)
FILTER_MODES = ("off", "on")
NDRV = 10
SEEDS = range(5)
TAU = 20.0
SPATIAL = "dispersed"
TIMEOUT_S = 300.0    # nho hon 2a (600s) - day la o do BENEFIT, khong phai scaling gate

# BANG CHUNG THUC NGHIEM (chay thuc te, khong doan): so states sinh ra tang
# RAT nhanh theo B_gw VA theo n (doc lap voi filter_mode - PCF khong cat duoc
# growth nay, chi la dieu kien can khong du):
#   n=20,B_gw=3: ~2-5s/driver-set
#   n=20,B_gw=4: ~15-145s   | n=30,B_gw=4: ~93-200s (4-6x/+10n o tw=60)
#   n=20,B_gw=5: ~100-360s+, da CHAM timeout 300s ngay ca o n=20
# => ngoai suy: n=50,B_gw=4 se ~1000-3000s+/cell; B_gw=5 o n>=30 con te hon.
# Bo qua som de tranh treo hang gio, GIU LAI cac diem da do (n=20,30 cho
# B_gw=4; n=20 cho B_gw=5) lam bang chung ve gioi han that su cua PCF -
# KHONG xoa het khoi luoi, chi bo cac o da xac nhan bat kha thi.
_SKIP_N_BGW = frozenset([
    (50, 4), (75, 4),
    (30, 5), (50, 5), (75, 5),
])


def _skip_cell(n, B_gw):
    return (n, B_gw) in _SKIP_N_BGW

FIELDS = ["n", "B_gw", "B_od", "tw_width", "filter_mode", "seed",
          "runtime_seconds", "peak_frontier_size", "total_states_generated",
          "total_states_surviving", "n_complete_bundles_found", "status"]


def run_one(n, B_gw, tw, filter_mode, seed):
    key = "n%d_Bgw%d_tw%d_%s_s%d" % (n, B_gw, tw, filter_mode, seed)
    gen_seed = IG.stable_seed(n, B_gw, BOD_FIXED, tw, filter_mode, seed, "pcf_benefit")

    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=BOD_FIXED, tw_width=tw, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)

    compat_graph = None
    if filter_mode == "on":
        compat_graph = IG.build_compat_graph(tt, orders)

    t0 = time.time()
    n_generated = n_surviving = peak_frontier = n_bundles_total = 0
    status = "completed"
    try:
        for drv in drivers:
            if time.time() - t0 > TIMEOUT_S:
                status = "timeout"
                break
            r = DL.run_pool(tt, drv, orders, B_gw, BOD_FIXED, compat_graph=compat_graph)
            n_generated += r["n_generated"]
            n_surviving += r["n_surviving"]
            peak_frontier = max(peak_frontier, r["peak_frontier"])
            n_bundles_total += r["n_bundles"]
    except MemoryError:
        status = "memory_exceeded"

    runtime = time.time() - t0
    rec = dict(
        n=n, B_gw=B_gw, B_od=BOD_FIXED, tw_width=tw, filter_mode=filter_mode, seed=seed,
        runtime_seconds=round(runtime, 4),
        peak_frontier_size=peak_frontier,
        total_states_generated=n_generated,
        total_states_surviving=n_surviving,
        n_complete_bundles_found=n_bundles_total,
        status=status,
    )
    with open(os.path.join(RAW, key + ".json"), "w", encoding="utf-8") as f:
        import json
        json.dump({"record": rec}, f, indent=1)
    return rec


def _load_done():
    seen = set()
    if os.path.isfile(SUMMARY):
        with open(SUMMARY, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    seen.add((int(r["n"]), int(r["B_gw"]), int(r["tw_width"]),
                              r["filter_mode"], int(r["seed"])))
                except (ValueError, KeyError):
                    pass
    return seen


def main():
    if not os.path.isdir(RAW):
        os.makedirs(RAW)
    t_start = time.time()
    total = len(N_GRID) * len(BGW_GRID) * len(TW_GRID) * len(FILTER_MODES) * len(SEEDS)
    done = 0

    already = _load_done()
    mode = "a" if already else "w"
    if already:
        print("RESUME: %d rows already in summary, skipping those." % len(already))

    with open(SUMMARY, mode, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not already:
            w.writeheader()
        for n in N_GRID:
            for B_gw in BGW_GRID:
                if _skip_cell(n, B_gw):
                    done += len(TW_GRID) * len(FILTER_MODES) * len(SEEDS)
                    print("  [%d/%d] n=%d B_gw=%d SKIPPED (brute blowup, xem _SKIP_N_BGW)"
                          % (done, total, n, B_gw))
                    continue
                for tw in TW_GRID:
                    for filter_mode in FILTER_MODES:
                        cell_stop = False
                        for sd in SEEDS:
                            if (n, B_gw, tw, filter_mode, sd) in already:
                                done += 1
                                continue
                            if cell_stop:
                                rec = dict(n=n, B_gw=B_gw, B_od=BOD_FIXED, tw_width=tw,
                                          filter_mode=filter_mode, seed=sd,
                                          runtime_seconds="", peak_frontier_size="",
                                          total_states_generated="", total_states_surviving="",
                                          n_complete_bundles_found="", status="timeout_skipped")
                            else:
                                rec = run_one(n, B_gw, tw, filter_mode, sd)
                                if rec["status"] != "completed":
                                    cell_stop = True
                            w.writerow(rec)
                            f.flush()
                            done += 1
                        print("  [%d/%d] n=%d B_gw=%d tw=%d mode=%s  elapsed=%.1fs"
                              % (done, total, n, B_gw, tw, filter_mode, time.time() - t_start))
    print("\n=== PCF BENEFIT DONE ===  elapsed=%.1fs" % (time.time() - t_start))


if __name__ == "__main__":
    main()
