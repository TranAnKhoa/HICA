"""Spec2a,2b_addition_1.md - Viec 1: uoc luong speedup THAT tu du lieu 2b da
co (KHONG chay lai gi). Doc toan bo results/2b_raw/*.json, dung
'component_sizes' (list day du) da luu san.

speedup_estimate(component_sizes, n_winners_per_component, p) =
    cost_naive / cost_decomposed
  cost_naive      = n_winners_total * N^p          (giai WDP -{i} tren CA instance)
  cost_decomposed = sum_P  n_w(P) * size(P)^p       (giai tren TUNG component rieng)

2 kich ban BAT BUOC theo spec goc (khong chon truoc 1 cai):
  (a) uniform : n_w(P) = n_winners_total * (|P| / N)   (ty le thuan kich thuoc)
  (b) upper-bound (xau nhat VE TONG SO winner) : MOI driver la winner ->
      n_winners_total = N, va n_w(P) = |P| (moi component "day" winner) - day
      la CAN TREN CHI PHI, khong phai ky vong thuc te.

+2 kich ban BO SUNG (theo yeu cau addition tiep theo cua nguoi dung, 2026-09-
11) - danh gia do NHAY VOI CACH PHAN BO winner GIUA cac component (khac voi
(a)/(b) chi thay doi TONG SO winner nhung van phan bo TY LE THUAN kich thuoc):
  (c) worst-case-cho-decomposition: TOAN BO winner don vao DUNG component LON
      NHAT (n_w(P_max) = n_winners_total, moi component khac = 0). Day la
      kich ban XAU NHAT thuc su cho T5 - vi WDP chon winner theo CHI PHI
      THAP NHAT, khong ngau nhien, va KHONG CO LY DO GI de tin no rai deu
      theo ty le kich thuoc (dieu (a)/(b) ngam gia dinh). Neu component lon
      nhat "hut" het winner (hop ly ve truc giac: component lon = nhieu
      driver/order dinh lien nhau = nhieu co hoi thang), decomposition
      KHONG tiet kiem gi ca so voi giai het tren component do.
  (d) best-case-cho-decomposition: TOAN BO winner la driver SINGLETON (size=1
      component). Day la kich ban TOT NHAT thuc su - moi singleton giai
      GAN O(1) thay vi O(N^p). RANG BUOC: n_winners_total <= n_singleton
      (khong the co nhieu winner hon so singleton) - neu instance co qua it
      singleton, kich ban nay KHONG kha thi voi moi winner_frac, ghi ro
      thay vi gia vo tinh duoc.

Voi (b), cong thuc rut gon dep: cost_naive = N * N^p = N^(p+1)
                                cost_decomposed = sum_P |P| * |P|^p = sum_P |P|^(p+1)
speedup(b) = N^(p+1) / sum_P |P|^(p+1)   - CHI phu thuoc component_sizes, khong
phu thuoc n_winners_total (vi da the het N vao). Day la con so "tot nhat co the"
cho decomposition boi cau truc component quan sat duoc.

### PHAT HIEN TOAN HOC (quan trong, anh huong cach doc ket qua):

Thay cong thuc (a) [n_w(P) = n_winners_total * (|P|/N)] vao ty so:

    cost_naive       = n_winners_total * N^p
    cost_decomposed  = sum_P [n_winners_total * (|P|/N)] * |P|^p
                      = (n_winners_total / N) * sum_P |P|^(p+1)

    speedup(a) = cost_naive / cost_decomposed
               = N^p / [(1/N) * sum_P |P|^(p+1)]
               = N^(p+1) / sum_P |P|^(p+1)

`n_winners_total` TRIET TIEU HOAN TOAN trong ty so - day la he qua DAI SO cua
chinh cong thuc (a) trong spec (phan bo winner TY LE THUAN kich thuoc
component), KHONG PHAI loi cai dat. Va cong thuc nay TRUNG KHOP tuyet doi voi
(b) (n_w(P)=|P|, tuc n_winners_total=N):

    speedup(b) = N*N^p / sum_P |P|*|P|^p = N^(p+1) / sum_P |P|^(p+1)

=> Voi CACH PHAN BO "ty le thuan kich thuoc" (chinh la dinh nghia (a) trong
spec), speedup_estimate BAT BIEN voi gia dinh so luong winner tong the - chi
phu thuoc CAU TRUC kich thuoc component va p. Day la mot ket qua toan hoc that
cua mo hinh chi phi duoc spec chi dinh (cost ~ size^p, phan winner ty le
thuan), khong phai gia dinh them cua nguoi thuc thi - duoc bao cao tuong minh
o day thay vi an di trong code, dung tinh than "khong chon truoc 1 gia tri roi
chi bao cao gia tri do".

Ta VAN quet `winner_frac` (ty le n_winners_total/N < 1, tuc KHONG PHAI moi
driver deu thang) de kiem tra tinh bat bien nay bang thuc nghiem (ket qua:
bat bien dung nhu dai so du doan - xem output). Day KHONG phai "chon 1 gia
tri roi bao cao" - la quet ca 3 gia tri va XAC NHAN chung deu bang nhau, roi
bao cao ca hien tuong nay.
"""

import glob
import json
import os
import statistics
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW_GLOB = os.path.join(ROOT, "results", "2b_v2_raw", "*.json")
OUT_CSV = os.path.join(ROOT, "results", "viec1_speedup_estimate_v2.csv")

P_GRID = (1.0, 1.5, 2.0, 3.0)
WINNER_FRAC_GRID_A = (0.2, 0.5, 1.0)   # ty le n_winners_total / N cho kich ban (a)


def speedup_a(component_sizes, N, p, winner_frac):
    """Kich ban (a) uniform: n_winners_total = winner_frac * N, phan bo ty le
    thuan kich thuoc component: n_w(P) = n_winners_total * (|P|/N)."""
    n_winners_total = winner_frac * N
    cost_naive = n_winners_total * (N ** p)
    cost_dec = sum((n_winners_total * (size / N)) * (size ** p) for size in component_sizes)
    if cost_dec <= 0:
        return None
    return cost_naive / cost_dec


def speedup_b(component_sizes, N, p):
    """Kich ban (b) upper-bound: MOI driver la winner (n_winners_total = N,
    n_w(P) = |P|). speedup = N^(p+1) / sum(|P|^(p+1))."""
    cost_naive = N * (N ** p)
    cost_dec = sum(size * (size ** p) for size in component_sizes)
    if cost_dec <= 0:
        return None
    return cost_naive / cost_dec


def speedup_c_worst(component_sizes, N, p, winner_frac):
    """Kich ban (c) worst-case: TOAN BO winner (n_winners_total=winner_frac*N)
    don vao component LON NHAT. cost_dec = n_winners_total * size_max^p.
    speedup = N^p / size_max^p = (N/size_max)^p - BAT BIEN voi winner_frac
    (giong (a)/(b), vi ca tu + mau deu ty le thuan n_winners_total)."""
    size_max = max(component_sizes)
    if size_max <= 0:
        return None
    n_winners_total = winner_frac * N
    cost_naive = n_winners_total * (N ** p)
    cost_dec = n_winners_total * (size_max ** p)
    if cost_dec <= 0:
        return None
    return cost_naive / cost_dec


def speedup_d_best(component_sizes, N, p, winner_frac):
    """Kich ban (d) best-case: TOAN BO winner la driver singleton (size=1).
    RANG BUOC: n_winners_total <= n_singleton, neu khong thoa -> None (kich
    ban khong kha thi cho instance nay o winner_frac do).
    cost_dec = n_winners_total * 1^p = n_winners_total.
    speedup = N^p (KHONG phu thuoc winner_frac, vi n_winners_total tu trieu
    tieu truc tiep trong ty so 1-bien, khac co che trieu tieu cua (a)/(b)/(c)
    la qua chuan hoa ca tu-mau theo N)."""
    n_singleton = sum(1 for s in component_sizes if s == 1)
    n_winners_total = winner_frac * N
    if n_winners_total > n_singleton:
        return None   # khong kha thi: khong du singleton de chua het winner gia dinh
    cost_naive = n_winners_total * (N ** p)
    cost_dec = n_winners_total * 1.0
    if cost_dec <= 0:
        return None
    return cost_naive / cost_dec


def main():
    files = sorted(glob.glob(RAW_GLOB))
    print("Doc %d file tu 2b_raw/ ..." % len(files))

    rows = []   # 1 dong / (instance, p, kich_ban)
    skipped = 0
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        rec = d["record"]
        if rec.get("status") != "completed":
            skipped += 1
            continue
        sizes = rec["component_sizes"]
        N = sum(sizes)
        if N <= 0:
            skipped += 1
            continue
        n_singleton = sum(1 for s in sizes if s == 1)
        meta_common = dict(
            n=rec["n"], tau=rec["tau"], spatial_mode=rec["spatial_mode"],
            supply_ratio=rec["supply_ratio"], seed=rec["seed"],
            n_drivers=rec["n_drivers"], n_components=rec["n_components"],
            largest_component_fraction=rec["largest_component_fraction"],
            n_singleton=n_singleton,
        )
        for p in P_GRID:
            sb = speedup_b(sizes, N, p)
            if sb is not None:
                rows.append(dict(meta_common, p=p, scenario="b_upper_bound",
                                 winner_frac="", speedup_estimate=sb))
            for wf in WINNER_FRAC_GRID_A:
                sa = speedup_a(sizes, N, p, wf)
                if sa is not None:
                    rows.append(dict(meta_common, p=p, scenario="a_uniform",
                                     winner_frac=wf, speedup_estimate=sa))
                sc = speedup_c_worst(sizes, N, p, wf)
                if sc is not None:
                    rows.append(dict(meta_common, p=p, scenario="c_worst_biggest",
                                     winner_frac=wf, speedup_estimate=sc))
                sd = speedup_d_best(sizes, N, p, wf)
                if sd is not None:
                    rows.append(dict(meta_common, p=p, scenario="d_best_singleton",
                                     winner_frac=wf, speedup_estimate=sd))
                else:
                    # ghi lai infeasible tuong minh (khong du singleton), khong
                    # am tham bo qua - dung tinh than "bao cao toan bo"
                    rows.append(dict(meta_common, p=p, scenario="d_best_singleton",
                                     winner_frac=wf, speedup_estimate=""))

    print("Instance dung (status=completed): %d, bo qua: %d" % (len(files) - skipped, skipped))
    print("Tong dong ket qua (instance x p x kich_ban): %d" % len(rows))

    # ---- ghi CSV chi tiet -------------------------------------------------
    import csv
    fieldnames = ["n", "tau", "spatial_mode", "supply_ratio", "seed", "n_drivers",
                  "n_components", "largest_component_fraction", "n_singleton", "p",
                  "scenario", "winner_frac", "speedup_estimate"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("-> %s" % OUT_CSV)

    # ---- bang tong hop: median + IQR theo (p, scenario[, winner_frac]) ----
    def iqr(xs):
        xs = sorted(xs)
        n = len(xs)
        if n < 2:
            return (xs[0], xs[0]) if xs else (None, None)
        q1 = xs[int(0.25 * (n - 1))]
        q3 = xs[int(0.75 * (n - 1))]
        return q1, q3

    print("\n=== TONG HOP: median(speedup_estimate) qua toan bo instance ===")
    print("%-20s %-6s %-10s %10s %10s %10s %8s" %
          ("scenario", "p", "winner_f", "median", "Q1", "Q3", "n_obs"))
    agg = defaultdict(list)
    n_infeasible_d = 0
    for r in rows:
        if r["speedup_estimate"] == "":
            n_infeasible_d += 1
            continue
        key = (r["scenario"], r["p"], r["winner_frac"])
        agg[key].append(r["speedup_estimate"])
    for key in sorted(agg, key=lambda k: (k[0], k[1], str(k[2]))):
        vals = agg[key]
        med = statistics.median(vals)
        q1, q3 = iqr(vals)
        print("%-20s %-6.1f %-10s %10.3f %10.3f %10.3f %8d" %
              (key[0], key[1], str(key[2]), med, q1, q3, len(vals)))
    print("\n(d_best_singleton) dong khong kha thi (winner_frac*N > n_singleton, "
          "khong du singleton chua het winner gia dinh): %d" % n_infeasible_d)

    # ---- % instance voi speedup(a, p=1, winner_frac=0.2) > 5x (nguong doc ket qua) ----
    print("\n=== Nguong doc ket qua GOC (khoa TRUOC khi xem so, tu addition_1) ===")
    for wf in WINNER_FRAC_GRID_A:
        key_a_p1 = ("a_uniform", 1.0, wf)
        vals = agg.get(key_a_p1, [])
        if not vals:
            continue
        pct_gt5 = 100 * sum(1 for v in vals if v > 5.0) / len(vals)
        print("kich ban (a) p=1 winner_frac=%.1f: speedup>5x o %.1f%% instance (n=%d)"
              % (wf, pct_gt5, len(vals)))

    all_vals = [r["speedup_estimate"] for r in rows if r["speedup_estimate"] != ""]
    pct_lt2 = 100 * sum(1 for v in all_vals if v < 2.0) / len(all_vals)
    print("TOAN BO 4 kich ban (moi p, moi winner_frac): speedup<2x o %.1f%% dong (n=%d)"
          % (pct_lt2, len(all_vals)))

    # ---- kich ban (c)/(d) moi - khoang dao dong thuc te theo cach phan bo winner ----
    print("\n=== Kich ban (c) worst-case / (d) best-case (p=1, winner_frac=0.2) ===")
    for scen in ("a_uniform", "c_worst_biggest", "d_best_singleton"):
        vals = agg.get((scen, 1.0, 0.2), [])
        if not vals:
            print("%-20s : KHONG CO du lieu kha thi" % scen)
            continue
        print("%-20s : median=%.3f  Q1=%.3f  Q3=%.3f  min=%.3f  max=%.3f  n=%d"
              % (scen, statistics.median(vals), *iqr(vals), min(vals), max(vals), len(vals)))


if __name__ == "__main__":
    main()
