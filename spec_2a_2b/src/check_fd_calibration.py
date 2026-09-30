"""RQ_following_check.md Viec (a) - kiem lai calibration gia FD.

Buoc 1: pilot calibration DA TIM THAY trong codebase - rq1_calibration.py +
rq1_locked_params.json (khong can doan). Ghi lai nguyen van o day.
Buoc 2-3: doc lai fd_rate THAT tren toan bo 1500 instance RQ1 main grid, tu
rq2_shard*.csv (menu B3 - dung CHINH XAC pool/allocation cua RQ1 JOINT, da
kiem X1 khop tuyet doi voi rq1_main_grid_results.csv, nen KHONG can giai lai
WDP o day - chi doc lai cot fd_rate da co san).
Buoc 4: trich fd_rate cua V0/V5/V6 tu rq5_shard*.csv (da co san, khong chay lai).
"""
import csv
import glob
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")
OUT = os.path.join(D, "fd_rate_by_cell.csv")


def load(pattern):
    rows = []
    for fn in sorted(glob.glob(os.path.join(D, pattern))):
        with open(fn, encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def main():
    print("=" * 90)
    print("Buoc 1 - Pilot calibration DA TIM THAY trong codebase")
    print("=" * 90)
    print("""
Script: spec_2a_2b/src/rq1_calibration.py (Rq1.md Sec1.4)
Khoa trong: spec_2a_2b/results/rq1_locked_params.json -> fd_cost_q_o.calibration_pass

  Muc tieu: fd_rate trong [0.10, 0.50] VA khong supply-ratio cell nao (trong 4
  cell (2,2)/(3,2)/(2,3)/(3,3)) co GW hoac OD thang 0 tuyet doi.
  Pilot instance: n=12, B_gw=B_od=3, tw_width=120, tau=30.0, spatial_mode=
    "dispersed" KHONG dung corridor_share/corridor_buffer_km (tham so nay
    CHUA TON TAI luc calibration pass chay - alignment control them SAU,
    2026-09-16, xem locked_targets trong cung file) -> pilot chay o mot
    "alignment tu nhien" khong kiem soat, KHONG phai o bat ky alignment target
    nao trong {0.10,...,0.90} cua main grid.
  Grid quet: base_fee in {2,3,4,5,6,8,10,14}, rate_per_km in {0.8,1.2,1.6,2.0,2.5,3.0},
    free_radius co dinh 1.0km. 4 supply ratio x 5 seed = 20 instance/combo.
  Bo THAT SU duoc chon (dau tien dat ca 2 tieu chi, dung lai):
    base_fee=8.0 rate_per_km=3.0 free_radius=1.0
    fd_rate=0.483  total_gw_wins=32  total_od_wins=24
    n_supply_cells_gw_zero=0  n_supply_cells_od_zero=0
""")

    print("=" * 90)
    print("Buoc 2-3 - FD rate THAT tren toan bo 1500 instance RQ1 main grid")
    print("(doc lai tu rq2_shard*.csv menu=B3 - CHINH LA pool/allocation JOINT")
    print(" cua RQ1, da xac nhan X1 khop tuyet doi rq1_main_grid_results.csv,")
    print(" khong giai lai WDP)")
    print("=" * 90)

    r2 = [r for r in load("rq2_shard*.csv") if r["menu"] == "B3"]
    assert len(r2) == 1500, "khong dung 1500 dong B3 (%d) - kiem tra shard co day du khong" % len(r2)

    by_an = {}
    for r in r2:
        key = (float(r["alignment"]), int(r["n"]))
        by_an.setdefault(key, []).append(float(r["fd_rate"]))

    rows_out = []
    print("\n| alignment | n | FD rate median | FD rate mean | n_instance | Trong [0.10,0.50] pilot? |")
    print("|---:|---:|---:|---:|---:|---|")
    for align in [0.10, 0.30, 0.50, 0.70, 0.90]:
        for n in [10, 15, 20]:
            vals = by_an[(align, n)]
            med, mean = statistics.median(vals), statistics.mean(vals)
            in_target = "CO" if 0.10 <= med <= 0.50 else "KHONG (lech)"
            print("| %.2f | %d | %.3f | %.3f | %d | %s |" % (align, n, med, mean, len(vals), in_target))
            rows_out.append(dict(alignment=align, n=n, fd_rate_median=med, fd_rate_mean=mean,
                                 n_instance=len(vals), pilot_target_lo=0.10, pilot_target_hi=0.50,
                                 in_pilot_target=(0.10 <= med <= 0.50)))

    all_vals = [float(r["fd_rate"]) for r in r2]
    n_out_of_target = sum(1 for r in rows_out if not r["in_pilot_target"])
    print("\nToan bo grid: FD rate median=%.3f mean=%.3f (n=%d instance)"
          % (statistics.median(all_vals), statistics.mean(all_vals), len(all_vals)))
    print("So cell (alignment x n) NGOAI khoang pilot [0.10,0.50]: %d / %d" % (n_out_of_target, len(rows_out)))

    os.makedirs(D, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    print("-> %s" % OUT)

    print("\n" + "=" * 90)
    print("KET LUAN Buoc 3 (mot cau):")
    print("=" * 90)
    lo_align = [r for r in rows_out if r["alignment"] <= 0.70]
    print("""Pilot nham fd_rate in [0.10, 0.50] tai n=12, mot alignment TU NHIEN
khong kiem soat (truoc khi corridor_share/buffer duoc them); nhung tren TOAN
BO 15/15 cell (alignment x n) cua main grid o alignment <= 0.70, fd_rate that
te nam NGOAI khoang do (cao hon, phia FD thang nhieu hon du kien) - chi tro ve
trong/gan khoang muc tieu o alignment=0.90. Pilot KHONG generalize sang phan
lon grid chinh: no dai dien dung cho "khong co corridor bias" (alignment tu
nhien ~0.35-0.50 theo do luong rieng cua alignment - xem rq1_locked_params.json),
nhung khi RQ1 sau do THEM corridor bias de dat alignment target thap (kien
order o gan/xa corridor OD), FD rate bi day len cao hon nhieu boi vi corridor
bias thay doi VI TRI order (anh huong ca kha nang GW/OD phuc vu), khong chi
"do trung lap khong gian" - hai truc nay tuong tac voi nhau va pilot chi kiem
mot truc.""")

    print("\n" + "=" * 90)
    print("Buoc 4 - Do nhay FD rate theo gia FD (RQ5 V0/V5/V6, da co san)")
    print("=" * 90)
    r5 = load("rq5_shard*.csv")
    for v, mult in [("V5_fd075", 0.75), ("V0_baseline", 1.00), ("V6_fd125", 1.25)]:
        sub = [float(r["fd_rate"]) for r in r5 if r["variant"] == v]
        print("  %-14s (FD x%.2f)  fd_rate median=%.3f mean=%.3f  (n=%d)"
              % (v, mult, statistics.median(sub), statistics.mean(sub), len(sub)))


if __name__ == "__main__":
    main()
