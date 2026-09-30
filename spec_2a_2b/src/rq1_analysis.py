"""Rq1.md Sec10 buoc8 - phan tich ket qua main grid (60 cell), theo dung Sec6:

  Complementarity gain = [min(C_GW-only, C_OD-only) - C_joint] / min(C_GW-only, C_OD-only)

- true cost (da co san trong CSV tu rq1_main_grid.py, dung theta THAT - Sec6).
- Median + IQR + 95% bootstrap CI, CLUSTERED theo replication (khong coi 5
  treatment tren cung 1 instance la doc lap - vi gain tinh TREN CUNG 1 bo 5
  gia tri true_cost cua 1 replication, tu no da la 1 don vi cluster, KHONG
  can thao tac gi them - nhung khi RESAMPLE (bootstrap) phai resample theo
  DON VI REPLICATION, khong resample tung dong CSV rieng le, neu khong se pha
  vo tinh "paired" cua du lieu).
- So sanh JOINT voi CA GW-only/OD-only LAN sequential treatment (Sec6 dong
  163-165): neu JOINT thang single-class nhung thua sequential, la ket luan
  KHAC ("thu tu quan trong hon viec cung bid").
- Bao cao TOAN BO 60 cell, KHONG cherry-pick (Sec8 dong 184-185).

KHONG dung numpy/scipy (khong co tren may nay) - tu viet median/percentile/
bootstrap bang pure Python (random.Random, deterministic seed rieng cho
resampling - KHAC seed sinh instance, chi de tai lap ket qua bootstrap).
"""

import csv
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "results", "rq1_main_grid_results.csv")
OUT_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "results", "rq1_analysis_by_cell.csv")

BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 20260916   # tag rieng cho resampling, KHONG dung lai seed sinh instance


def load_rows():
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_by_replication(rows):
    """Tra {(align,n,n_gw,n_od,rep_idx): {treatment: true_cost}}."""
    out = {}
    for r in rows:
        key = (r["alignment_target"], r["n"], r["n_gw"], r["n_od"], r["rep_idx"])
        out.setdefault(key, {})[r["treatment"]] = float(r["true_cost"])
    return out


def complementarity_gain(costs):
    """costs: dict co JOINT, GW-ONLY, OD-ONLY. Tra None neu min single-class
    cost = 0 (khong the chia)."""
    best_single = min(costs["GW-ONLY"], costs["OD-ONLY"])
    if best_single == 0:
        return None
    return (best_single - costs["JOINT"]) / best_single


def gain_vs_sequential(costs, seq_name):
    """Sec6 dong 163-165: so JOINT voi sequential treatment (OD-FIRST hoac
    GW-FIRST rieng, KHONG phai min(GW-only,OD-only)) - dinh nghia gain tuong
    tu nhung mau so la cost cua CHINH sequential do (KHONG phai
    min(GW-only,OD-only)), de tra loi cau hoi 'JOINT co thang thu tu tuan tu
    khong', tach biet voi cau hoi 'JOINT co thang single-class khong'."""
    c_seq = costs[seq_name]
    if c_seq == 0:
        return None
    return (c_seq - costs["JOINT"]) / c_seq


def _percentile(sorted_vals, pct):
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (pct / 100.0) * (n - 1)
    f = int(k)
    c = f + 1 if f + 1 < n else f
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def bootstrap_ci(values, n_boot=BOOTSTRAP_N, seed=BOOTSTRAP_SEED):
    """values: list gain (1 gia tri/replication - da la 1 don vi cluster,
    Sec6 dong 167-168: 'clustered theo session/instance goc'). Resample
    NGUYEN mot replication moi lan (khong resample 5 treatment rieng), dung
    seed CO DINH rieng cho bootstrap - KHONG lien quan seed sinh instance,
    chi de bootstrap tai lap duoc giua cac lan chay phan tich."""
    rng = random.Random(seed)
    n = len(values)
    if n == 0:
        return None, None
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    lo = _percentile(means, 2.5)
    hi = _percentile(means, 97.5)
    return lo, hi


def analyze_cell(reps_in_cell):
    """reps_in_cell: list dict {treatment: true_cost} (1 phan tu/replication
    trong 1 cell). Tra dict summary day du."""
    gains_joint = []
    gains_odfirst = []
    gains_gwfirst = []
    n_dropped_zero_single = 0

    for costs in reps_in_cell:
        g = complementarity_gain(costs)
        if g is None:
            n_dropped_zero_single += 1
            continue
        gains_joint.append(g)
        g_od = gain_vs_sequential(costs, "OD-FIRST")
        g_gw = gain_vs_sequential(costs, "GW-FIRST")
        if g_od is not None:
            gains_odfirst.append(g_od)
        if g_gw is not None:
            gains_gwfirst.append(g_gw)

    def summarize(vals):
        if not vals:
            return dict(n=0, median=None, q1=None, q3=None, ci_lo=None, ci_hi=None)
        sv = sorted(vals)
        lo, hi = bootstrap_ci(vals)
        return dict(n=len(vals), median=statistics.median(sv),
                   q1=_percentile(sv, 25.0), q3=_percentile(sv, 75.0),
                   ci_lo=lo, ci_hi=hi)

    return dict(
        n_replications=len(reps_in_cell),
        n_dropped_zero_single_cost=n_dropped_zero_single,
        joint_vs_best_single=summarize(gains_joint),
        joint_vs_odfirst=summarize(gains_odfirst),
        joint_vs_gwfirst=summarize(gains_gwfirst),
    )


def main():
    rows = load_rows()
    by_rep = group_by_replication(rows)

    cells = {}
    for key, costs in by_rep.items():
        align, n, n_gw, n_od, rep_idx = key
        cell_key = (align, n, n_gw, n_od)
        cells.setdefault(cell_key, []).append(costs)

    print("=== Rq1.md Sec6/Sec8 - Complementarity gain, TOAN BO %d cell, KHONG cherry-pick ===\n"
         % len(cells))

    out_rows = []
    for cell_key in sorted(cells.keys(), key=lambda k: (float(k[0]), int(k[1]), k[2], k[3])):
        align, n, n_gw, n_od = cell_key
        reps = cells[cell_key]
        summary = analyze_cell(reps)

        jvs = summary["joint_vs_best_single"]
        jvo = summary["joint_vs_odfirst"]
        jvg = summary["joint_vs_gwfirst"]

        def fmt(s):
            if s["n"] == 0 or s["median"] is None:
                return "n/a"
            return "median=%.4f IQR=[%.4f,%.4f] CI95=[%.4f,%.4f] (n=%d)" % (
                s["median"], s["q1"], s["q3"], s["ci_lo"], s["ci_hi"], s["n"])

        print("align=%s n=%s supply=(%s,%s):" % (align, n, n_gw, n_od))
        print("  JOINT vs best(GW-only,OD-only): %s" % fmt(jvs))
        print("  JOINT vs OD-FIRST->GW:          %s" % fmt(jvo))
        print("  JOINT vs GW-FIRST->OD:          %s" % fmt(jvg))
        if summary["n_dropped_zero_single_cost"] > 0:
            print("  [NOTE] %d/%d replication bi loai (min(GW-only,OD-only) cost = 0)"
                 % (summary["n_dropped_zero_single_cost"], summary["n_replications"]))
        print()

        out_rows.append(dict(
            alignment_target=align, n=n, n_gw=n_gw, n_od=n_od,
            n_replications=summary["n_replications"],
            n_dropped_zero_single_cost=summary["n_dropped_zero_single_cost"],
            gain_vs_best_single_median=jvs["median"], gain_vs_best_single_q1=jvs["q1"],
            gain_vs_best_single_q3=jvs["q3"], gain_vs_best_single_ci_lo=jvs["ci_lo"],
            gain_vs_best_single_ci_hi=jvs["ci_hi"], gain_vs_best_single_n=jvs["n"],
            gain_vs_odfirst_median=jvo["median"], gain_vs_odfirst_n=jvo["n"],
            gain_vs_gwfirst_median=jvg["median"], gain_vs_gwfirst_n=jvg["n"],
        ))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = list(out_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print("[OK] Ghi %d dong vao %s" % (len(out_rows), OUT_CSV))

    return out_rows


if __name__ == "__main__":
    main()
