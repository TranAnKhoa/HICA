"""Final_run_checkilist.md Viec B (Hica_S_Master_Writeup.md Sec18.4/Sec0.4) -
tinh lai complementarity gain RQ1 theo quy uoc da khoa: median [IQR] * mean
(95% bootstrap CI), tren INSTANCE (khong phai "mean cua median cell" nhu bang
cu trong [S4]/[S5]). Doc lai rq1_main_grid_results.csv, khong giai lai gi.
"""
import csv
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN = os.path.join(ROOT, "results", "rq1_main_grid_results.csv")
OUT = os.path.join(ROOT, "results", "rq_all", "rq1_comp_gain_recomputed.csv")
OUT_BY_N = os.path.join(ROOT, "results", "rq_all", "rq1_comp_gain_recomputed_by_n.csv")

BOOT, BSEED = 2000, 20260928


def pct(sv, p):
    n = len(sv)
    if n == 1:
        return sv[0]
    k = (p / 100.0) * (n - 1)
    f = int(k)
    c = min(f + 1, n - 1)
    return sv[f] + (sv[c] - sv[f]) * (k - f)


def bootstrap_ci(vals, n_boot=BOOT, seed=BSEED):
    rng = random.Random(seed)
    n = len(vals)
    if n == 0:
        return float("nan"), float("nan")
    means = sorted(statistics.mean(vals[rng.randrange(n)] for _ in range(n)) for _ in range(n_boot))
    return pct(means, 2.5), pct(means, 97.5)


def load_by_instance():
    """Tra {(alignment,n,n_gw,n_od,rep): {treatment: true_cost}}."""
    by = {}
    with open(CSV_IN, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (float(r["alignment_target"]), int(r["n"]), int(r["n_gw"]), int(r["n_od"]), int(r["rep_idx"]))
            by.setdefault(key, {})[r["treatment"]] = float(r["true_cost"])
    return by


def comp_gain(costs):
    best_single = min(costs["GW-ONLY"], costs["OD-ONLY"])
    if best_single == 0:
        return None
    return (best_single - costs["JOINT"]) / best_single


def summarize(vals):
    sv = sorted(vals)
    lo, hi = bootstrap_ci(vals)
    return dict(n=len(vals), median=100 * statistics.median(sv), iqr_lo=100 * pct(sv, 25),
               iqr_hi=100 * pct(sv, 75), mean=100 * statistics.mean(vals), ci_lo=100 * lo, ci_hi=100 * hi)


def main():
    by_inst = load_by_instance()
    assert len(by_inst) == 1500, len(by_inst)

    gains = {}   # alignment -> list of gain
    gains_n = {}  # (alignment, n) -> list
    n_dropped = 0
    for (a, n, ng, no, rep), costs in by_inst.items():
        g = comp_gain(costs)
        if g is None:
            n_dropped += 1
            continue
        gains.setdefault(a, []).append(g)
        gains_n.setdefault((a, n), []).append(g)

    rows = []
    print("=" * 90)
    print("RQ1 complementarity gain, quy uoc da khoa (median [IQR] * mean (95%% CI), tren instance)")
    print("=" * 90)
    print("Instance bi loai (min(GW-only,OD-only)=0): %d / 1500" % n_dropped)
    print("\n| alignment | median [IQR] * mean (95%% CI), %% | n instance |")
    print("|---:|---|---:|")
    for a in sorted(gains):
        s = summarize(gains[a])
        print("| %.2f | %.2f [%.2f, %.2f] · %.2f (%.2f, %.2f) | %d |"
              % (a, s["median"], s["iqr_lo"], s["iqr_hi"], s["mean"], s["ci_lo"], s["ci_hi"], s["n"]))
        rows.append(dict(alignment=a, median=s["median"], iqr_lo=s["iqr_lo"], iqr_hi=s["iqr_hi"],
                         mean=s["mean"], ci_lo=s["ci_lo"], ci_hi=s["ci_hi"], n=s["n"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("\n-> %s" % OUT)

    # so voi bang cu "mean cua median cell"
    old = {0.10: 0.01, 0.30: 0.08, 0.50: 0.00, 0.70: 0.93, 0.90: 5.86}
    print("\nSo voi bang cu (mean cua median cell, KHONG dung trong paper nua):")
    print("| alignment | cu (mean cua median cell) | moi mean (tren instance) | moi median (tren instance) |")
    print("|---:|---:|---:|---:|")
    for a in sorted(gains):
        s = summarize(gains[a])
        print("| %.2f | %.2f%% | %.2f%% | %.2f%% |" % (a, old.get(a, float("nan")), s["mean"], s["median"]))

    rows_n = []
    print("\n### Bang phu theo alignment x n (median / mean %%)")
    print("| alignment | n=10 | n=15 | n=20 |")
    print("|---:|---|---|---|")
    for a in sorted(gains):
        cells = []
        for n in [10, 15, 20]:
            vals = gains_n.get((a, n), [])
            if vals:
                s = summarize(vals)
                cells.append("%.2f / %.2f" % (s["median"], s["mean"]))
                rows_n.append(dict(alignment=a, n=n, median=s["median"], mean=s["mean"], n_instance=s["n"]))
            else:
                cells.append("n/a")
        print("| %.2f | %s |" % (a, " | ".join(cells)))

    with open(OUT_BY_N, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_n[0].keys()))
        w.writeheader(); w.writerows(rows_n)
    print("\n-> %s" % OUT_BY_N)

    # check hinh dang: van phai lom nhat o 0.50 (giu nguyen huong nhu ban cu)
    order = sorted(gains)
    means = [summarize(gains[a])["mean"] for a in order]
    idx_min = means.index(min(means))
    print("\n[CHECK] Hinh dang giu nguyen? min mean tai alignment=%.2f (ky vong 0.50) -> %s"
          % (order[idx_min], "KHOP" if abs(order[idx_min] - 0.50) < 1e-9 else "KHAC - doi chieu voi FD rate truoc khi bao cao"))


if __name__ == "__main__":
    main()
