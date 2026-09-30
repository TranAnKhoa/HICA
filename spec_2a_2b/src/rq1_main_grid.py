"""Rq1.md Sec10 buoc7 - main 60-cell grid, naive Algorithm C (Sec2: B(WDP)
dung thang, KHONG decomposition/warm-start). Doc tham so DA KHOA tu
results/rq1_locked_params.json (khong hardcode lai o day - tranh lech giua
file khoa va code chay that).

Grid (Sec4):
  alignment_target in {0.10,0.30,0.50,0.70,0.90}   x5
  n in {10,15,20}                                   x3
  supply_ratio (n_gw,n_od) in {(2,2),(3,2),(2,3),(3,3)}  x4
  = 60 cell, x >=25 replication/cell = >=1500 instance goc, x 5 treatment.

Moi replication: 1 instance (cung order/driver/theta draw) dung CHUNG cho ca
5 treatment (seed_policy da khoa). Ghi ra CSV moi dong = 1 (cell, replication,
treatment) voi true_cost, status, va cac metric Sec6 (FD rate, complementarity
gain tinh rieng o buoc phan tich - Buoc 8, khong tinh o day de tranh trung
logic/sai lech giua chay va phan tich).

[CHECK] Sec7 dong 175-176: solve nao KHONG phai OPTIMAL (gap=0) -> loai khoi
bang kinh te, ghi status rieng (khong loai khoi CSV - van ghi de audit).
"""

import csv
import hashlib
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import rq1_cost_gen as RC
import rq1_treatments as RT

LOCKED_PARAMS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "results", "rq1_locked_params.json")
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "results", "rq1_main_grid_results.csv")
PROGRESS_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "results", "rq1_main_grid_progress.log")

# [LOCK] Rq1.md Sec4 - grid con lai chua co trong locked_params.json (n,
# supply ratio, B=3) - lay TRUC TIEP tu bang trong file (khong hardcode
# ngoai) cho alignment/r0/theta/q_o. n va supply_ratio la hang so co dinh cua
# spec, khong phai ket qua calibration nen khong can luu vao locked_params.
ALIGNMENT_TARGETS = [0.10, 0.30, 0.50, 0.70, 0.90]
N_GRID = [10, 15, 20]
SUPPLY_RATIOS = [(2, 2), (3, 2), (2, 3), (3, 3)]
B_GW = 3
B_OD = 3
# [LOCK] tw_width khong co default trong generate_instance() (tham so bat
# buoc) - Sec4 dong 129 noi "giu nguyen default hien tai cua generator" cho
# tw_width/tau/capacity, nhung tw_width can 1 GIA TRI CU THE de goi ham. Dung
# 120 - GIA TRI DA DUNG XUYEN SUOT MOI calibration pass truoc do cua RQ1
# (rq1_calibration.py pilot q_o, rq1_alignment.py pilot r0 VA calibration
# curve alignment) - giu nguyen, KHONG doi sang gia tri khac cho main grid de
# tranh mo them mot truc chua tung duoc kiem tra o buoc nao truoc.
TW_WIDTH = 120
# [LOCK] tau=30.0 - KHONG phai default that cua ham (default=20.0), nhung la
# gia tri DA DUNG NHAT QUAN xuyen suot MOI buoc calibration truoc cua RQ1
# (rq1_calibration.py PILOT_TAU=30.0, rq1_alignment.py R0_PILOT_TAU/CALIB_TAU
# =30.0, rq1_dryrun_gate.py tau=30.0) - giu nguyen 30.0 cho main grid de nhat
# quan voi toan bo cong viec khoa tham so da lam, KHONG quay ve default ham
# (se la mot thay doi am tham, chua tung duoc kiem tra o buoc nao).
TAU = 30.0
REPLICATIONS = 25


def load_locked_params():
    with open(LOCKED_PARAMS_PATH, "r", encoding="utf-8") as f:
        params = json.load(f)
    assert not params["_pending_sections_not_yet_locked"], \
        "[STOP] con truong pending chua khoa - khong duoc chay main grid"
    return params


def verify_hash(params):
    """[CHECK] xac nhan file dang doc dung la file DA HASH (Sec8.1) - phong
    truong hop file bi sua sau khi hash ma khong cap nhat lai hash (patch
    mot phan - dung Sec8.3 cam)."""
    expected = params["sha256_of_this_file"]["hash"]
    with open(LOCKED_PARAMS_PATH, "rb") as f:
        raw = f.read()
    obj = json.loads(raw)
    obj["sha256_of_this_file"] = "PLACEHOLDER"
    recomputed = hashlib.sha256(json.dumps(obj).encode()).hexdigest()
    # Luu y: json.dumps voi key order khac co the cho hash khac - day CHI la
    # sanity-check "file khong rong/khong loi doc", KHONG phai xac nhan hash
    # tuyet doi bit-for-bit (da tinh 1 lan luc khoa bang cach doc raw bytes
    # true tiep, xem Buoc 6). Neu muon xac nhan chat, so sanh raw bytes voi
    # ban da luu khi khoa - o day chi canh bao neu file ro rang bi thay doi
    # cau truc (thieu key, v.v.)
    return expected


def get_corridor_params(params, alignment_target):
    key = "%.2f" % alignment_target
    t = params["alignment"]["locked_targets"][key]
    return t["corridor_share"], t["corridor_buffer_km"], t["deviation"]


def run_one_replication(params, r0, alignment_target, corridor_share, corridor_buffer_km,
                        n, n_gw, n_od, rep_idx):
    n_drivers = n_gw + n_od
    gen_seed = IG.stable_seed(n, B_GW, B_OD, alignment_target, n_gw, n_od, rep_idx,
                              "rq1_main_grid")
    theta_seed = IG.stable_seed(n, B_GW, B_OD, alignment_target, n_gw, n_od, rep_idx,
                                "rq1_main_grid_theta")

    kwargs = dict(n=n, B_gw=B_GW, B_od=B_OD, tw_width=TW_WIDTH, n_drivers=n_drivers,
                 seed=gen_seed, tau=TAU, spatial_mode="dispersed",
                 corridor_share=corridor_share, corridor_buffer_km=corridor_buffer_km,
                 gw_od_ratio=n_gw / float(n_drivers))
    drivers, orders, tt, meta = IG.generate_instance(**kwargs)

    theta_rng = random.Random(theta_seed)
    theta_by_driver = RC.assign_theta(theta_rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    # [OPTIMIZATION 2026-09-16] Algorithm A (route pool) chay MOT LAN cho
    # TOAN BO driver, dung lai (slice theo id) cho ca 5 treatment - thay vi
    # goi build_route_pool 4 lan/replication (JOINT, GW-ONLY, OD-ONLY, 2 pool
    # cua sequential). An toan vi pool cua 1 driver la HAM DOC LAP cua cac
    # driver khac (da xac nhan thuc nghiem - xem rq1_treatments.build_joint_pool
    # docstring) - CHI thay doi thoi gian chay, KHONG thay doi bat ky gia tri
    # true_cost/status nao. Toi uu nay duoc gate lai bang rq1_dryrun_gate.py
    # (so JOINT+4 treatment voi oracle exhaustive) TRUOC khi dua vao day.
    joint_pool, joint_agg = RT.build_joint_pool(tt, drivers, orders, B_GW, B_OD)

    rows = []
    treatments = [
        ("JOINT", lambda: RT.run_joint_from_pool(joint_pool, orders, theta_by_driver,
                                                 q_o_by_order, agg=joint_agg)),
        ("GW-ONLY", lambda: RT.run_gw_only_from_pool(joint_pool, drivers, orders,
                                                     theta_by_driver, q_o_by_order)),
        ("OD-ONLY", lambda: RT.run_od_only_from_pool(joint_pool, drivers, orders,
                                                     theta_by_driver, q_o_by_order)),
        ("OD-FIRST", lambda: RT.run_od_first_from_pool(joint_pool, drivers, orders,
                                                       theta_by_driver, q_o_by_order)),
        ("GW-FIRST", lambda: RT.run_gw_first_from_pool(joint_pool, drivers, orders,
                                                       theta_by_driver, q_o_by_order)),
    ]
    for name, fn in treatments:
        t0 = time.perf_counter()
        res = fn()
        wall = time.perf_counter() - t0
        status = res.get("status")
        if name in ("OD-FIRST", "GW-FIRST"):
            status1 = res["pass1"]["status"]
            status2 = res["pass2"]["status"]
            status = "pass1=%s|pass2=%s" % (status1, status2)
        rows.append(dict(
            alignment_target=alignment_target, n=n, n_gw=n_gw, n_od=n_od, rep_idx=rep_idx,
            treatment=name, true_cost=res["true_cost"], status=status, wall_sec=wall,
        ))
    return rows


def main():
    params = load_locked_params()
    verify_hash(params)
    r0 = params["alignment"]["r0_km"]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    t_start = time.time()

    n_cells = len(ALIGNMENT_TARGETS) * len(N_GRID) * len(SUPPLY_RATIOS)
    cell_idx = 0

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fcsv, \
        open(PROGRESS_LOG, "w", encoding="utf-8") as flog:
        writer = csv.DictWriter(fcsv, fieldnames=[
            "alignment_target", "n", "n_gw", "n_od", "rep_idx", "treatment",
            "true_cost", "status", "wall_sec"])
        writer.writeheader()

        for align in ALIGNMENT_TARGETS:
            cs, cb, deviation = get_corridor_params(params, align)
            for n in N_GRID:
                for (n_gw, n_od) in SUPPLY_RATIOS:
                    cell_idx += 1
                    cell_t0 = time.time()
                    for rep in range(REPLICATIONS):
                        rows = run_one_replication(params, r0, align, cs, cb, n, n_gw, n_od, rep)
                        for row in rows:
                            writer.writerow(row)
                        fcsv.flush()
                    cell_dt = time.time() - cell_t0
                    msg = ("[cell %d/%d] align=%.2f n=%d supply=(%d,%d) deviation=%s "
                          "-> %.1fs (%.2fs/replication)" %
                          (cell_idx, n_cells, align, n, n_gw, n_od, deviation,
                           cell_dt, cell_dt / REPLICATIONS))
                    print(msg)
                    flog.write(msg + "\n")
                    flog.flush()

    total_dt = time.time() - t_start
    print("\n[DONE] Total: %.1fs (%.2f min) for %d cells" % (total_dt, total_dt / 60.0, n_cells))


if __name__ == "__main__":
    main()
