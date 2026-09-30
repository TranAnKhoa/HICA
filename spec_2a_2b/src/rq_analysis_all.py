"""RQ_Master.md §9 buoc 5 - phan tich RQ2/RQ3/RQ4/RQ5 + kiem tra X1.
Doc results/rq_all/*_shard*.csv, in bang markdown ra results/rq_all/rq_analysis_tables.md.
Pure Python (khong numpy)."""
import csv
import glob
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")
OUT = os.path.join(D, "rq_analysis_tables.md")
BOOT, BSEED = 2000, 20260927


def load(which):
    rows = []
    for fn in sorted(glob.glob(os.path.join(D, "%s_shard*.csv" % which))):
        with open(fn, encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def pct(sv, p):
    if not sv:
        return float("nan")
    k = (len(sv) - 1) * p
    f = int(k)
    return sv[f] + (sv[min(f + 1, len(sv) - 1)] - sv[f]) * (k - f)


def ci_mean(v):
    if not v:
        return (float("nan"), float("nan"))
    rng = random.Random(BSEED)
    n = len(v)
    ms = sorted(statistics.mean([v[rng.randrange(n)] for _ in range(n)]) for _ in range(BOOT))
    return pct(ms, 0.025), pct(ms, 0.975)


def summ(v, scale=100.0, dec=2):
    """median [IQR] mean (CI95) - gia tri * scale."""
    if not v:
        return "n/a"
    sv = sorted(v)
    lo, hi = ci_mean(v)
    f = "%%.%df" % dec
    return (f + " [" + f + ", " + f + "] · mean " + f + " (" + f + "–" + f + ")") % (
        scale * statistics.median(sv), scale * pct(sv, .25), scale * pct(sv, .75),
        scale * statistics.mean(v), scale * lo, scale * hi)


def fl(r, k):
    return float(r[k])


out = []
P = out.append

# =========================================================================== RQ2
r2 = load("rq2")
if r2:
    inst = {}
    for r in r2:
        key = (float(r["alignment"]), int(r["n"]), int(r["n_gw"]), int(r["n_od"]), int(r["rep"]))
        inst.setdefault(key, {})[r["menu"]] = r
    n_inst = len(inst)
    n_rows = len(r2)
    n_opt = sum(1 for r in r2 if "optimal" in r["status"])
    # X1
    rq1 = {}
    with open(os.path.join(ROOT, "results", "rq1_main_grid_results.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["treatment"] == "JOINT":
                rq1[(float(r["alignment_target"]), int(r["n"]), int(r["n_gw"]), int(r["n_od"]),
                     int(r["rep_idx"]))] = float(r["true_cost"])
    x1 = [abs(fl(m["B3"], "true_cost") - rq1[k]) for k, m in inst.items() if k in rq1]
    P("## RQ2\n")
    P("- Instance: %d, dòng (instance×menu): %d, OPTIMAL: %d/%d" % (n_inst, n_rows, n_opt, n_rows))
    P("- **X1** (C_B3 == JOINT RQ1): %d instance so, max |Δ| = %.2e, số lệch > 1e-6: %d\n"
      % (len(x1), max(x1) if x1 else float("nan"), sum(1 for x in x1 if x > 1e-6)))

    def gain(m, name, base="B1"):
        cb = fl(m[base], "true_cost")
        return (cb - fl(m[name], "true_cost")) / cb

    P("### Bundling gain so với B1 (%, median [IQR] · mean (CI95)), theo alignment\n")
    P("| alignment | B2 | B3 | B4 (n≤15) | HEUR | B3 vs HEUR |")
    P("|---:|---|---|---|---|---|")
    for a in [0.1, 0.3, 0.5, 0.7, 0.9]:
        ms = [m for k, m in inst.items() if abs(k[0] - a) < 1e-9]
        P("| %.2f | %s | %s | %s | %s | %s |" % (
            a, summ([gain(m, "B2") for m in ms]), summ([gain(m, "B3") for m in ms]),
            summ([gain(m, "B4") for m in ms if "B4" in m]), summ([gain(m, "HEUR") for m in ms]),
            summ([gain(m, "B3", "HEUR") for m in ms])))
    P("\n### Bundling gain B3 vs B1 theo alignment × n (median %%, mean %%)\n")
    P("| alignment | n=10 | n=15 | n=20 |")
    P("|---:|---|---|---|")
    for a in [0.1, 0.3, 0.5, 0.7, 0.9]:
        cells = []
        for n in [10, 15, 20]:
            g = [gain(m, "B3") for k, m in inst.items() if abs(k[0] - a) < 1e-9 and k[1] == n]
            cells.append("%.2f / %.2f" % (100 * statistics.median(g), 100 * statistics.mean(g)) if g else "n/a")
        P("| %.2f | %s |" % (a, " | ".join(cells)))
    P("\n### Price of range B: B3 so với B4 (n≤15), (C_B3 − C_B4)/C_B4 %%\n")
    P("| alignment | n=10 | n=15 |")
    P("|---:|---|---|")
    for a in [0.1, 0.3, 0.5, 0.7, 0.9]:
        cells = []
        for n in [10, 15]:
            g = [(fl(m["B3"], "true_cost") - fl(m["B4"], "true_cost")) / fl(m["B4"], "true_cost")
                 for k, m in inst.items() if abs(k[0] - a) < 1e-9 and k[1] == n and "B4" in m]
            cells.append(summ(g))
        P("| %.2f | %s |" % (a, " | ".join(cells)))
    P("\n### FD rate, bundle size, runtime (mean trên toàn grid)\n")
    P("| menu | FD rate | order/route thắng | pool size (mean) | t_A mean (s) | t_B mean (s) |")
    P("|---|---:|---:|---:|---:|---:|")
    for name in ["B1", "B2", "B3", "B4", "HEUR"]:
        rs = [m[name] for m in inst.values() if name in m]
        mb = [fl(r, "mean_bundle") for r in rs if int(r["n_routes"]) > 0]
        P("| %s | %.3f | %.2f | %.0f | %s | %.3f |" % (
            name, statistics.mean(fl(r, "fd_rate") for r in rs), statistics.mean(mb) if mb else 0,
            statistics.mean(fl(r, "pool_size") for r in rs),
            ("%.2f" % statistics.mean(fl(r, "t_A") for r in rs)) if name in ("B3", "B4") else "(lọc B3)",
            statistics.mean(fl(r, "t_B") for r in rs)))
    P("\n### t_A theo n (mean s): B3 / B4\n")
    for n in [10, 15, 20]:
        a3 = [fl(m["B3"], "t_A") for k, m in inst.items() if k[1] == n]
        a4 = [fl(m["B4"], "t_A") for k, m in inst.items() if k[1] == n and "B4" in m]
        P("- n=%d: B3 %.2f s, B4 %s" % (n, statistics.mean(a3), ("%.2f s" % statistics.mean(a4)) if a4 else "không chạy"))
    hb = [int(m["B3"]["n_heur_blocks"]) for m in inst.values()]
    P("- HEUR: số khối ≥2 order / instance: mean %.2f, min %d, max %d\n" % (statistics.mean(hb), min(hb), max(hb)))

# =========================================================================== RQ3/RQ4
r3 = load("rq34")
if r3:
    P("## RQ3\n")
    P("- Instance: %d; mọi solve OPTIMAL: %d/%d\n" % (len(r3), sum(1 for r in r3 if r["all_optimal"] == "True"), len(r3)))
    P("### Payout premium so với ORACLE (Z*), % — median [IQR] · mean (CI95)\n")
    P("| alignment | n | VCG | PAB-BR | POSTED (λ=%s) |" % r3[0]["posted_lambda"])
    P("|---:|---:|---|---|---|")
    for a in [0.5, 0.9]:
        for n in [10, 15, 20, None]:
            rs = [r for r in r3 if abs(fl(r, "alignment") - a) < 1e-9 and (n is None or int(r["n"]) == n)]
            if not rs:
                continue
            pr = lambda k: [(fl(r, k) - fl(r, "Z")) / fl(r, "Z") for r in rs]
            P("| %.2f | %s | %s | %s | %s |" % (a, n if n else "**all**", summ(pr("vcg_payout")),
                                                 summ(pr("pab_payout")), summ(pr("posted_payout"))))
    P("\n### Information rent và hiệu quả\n")
    P("| alignment | VCG overhead = rent/Σc_i (%) | PAB rent/Σc_i (%) | PAB efficiency loss (%) | POSTED efficiency loss (%) | FD rate: VCG / PAB / POSTED |")
    P("|---:|---|---|---|---|---|")
    for a in [0.5, 0.9]:
        rs = [r for r in r3 if abs(fl(r, "alignment") - a) < 1e-9]
        if not rs:
            continue
        ov = [fl(r, "vcg_rent") / fl(r, "winner_true_cost") for r in rs if fl(r, "winner_true_cost") > 0]
        pov = [fl(r, "pab_rent") / fl(r, "winner_true_cost") for r in rs if fl(r, "winner_true_cost") > 0]
        pe = [(fl(r, "pab_true_cost") - fl(r, "Z")) / fl(r, "Z") for r in rs]
        pse = [(fl(r, "posted_true_cost") - fl(r, "Z")) / fl(r, "Z") for r in rs]
        P("| %.2f | %s | %s | %s | %s | %.3f / %.3f / %.3f |" % (
            a, summ(ov), summ(pov), summ(pe), summ(pse),
            statistics.mean(fl(r, "fd_rate") for r in rs), statistics.mean(fl(r, "pab_fd_rate") for r in rs),
            statistics.mean(fl(r, "posted_fd_rate") for r in rs)))
    P("")
    for a in [0.5, 0.9]:
        rs = [r for r in r3 if abs(fl(r, "alignment") - a) < 1e-9]
        if not rs:
            continue
        P("- alignment %.2f: VCG payout > PAB-BR payout ở %d/%d instance; VCG payout < POSTED ở %d/%d; "
          "rent VCG chia GW/OD = %.1f%% / %.1f%%; số winner mean %.2f; PAB markup mean %.2f USD/h"
          % (a, sum(1 for r in rs if fl(r, "vcg_payout") > fl(r, "pab_payout") + 1e-9), len(rs),
             sum(1 for r in rs if fl(r, "vcg_payout") < fl(r, "posted_payout") - 1e-9), len(rs),
             100 * sum(fl(r, "vcg_rent_gw") for r in rs) / max(1e-12, sum(fl(r, "vcg_rent") for r in rs)),
             100 * sum(fl(r, "vcg_rent_od") for r in rs) / max(1e-12, sum(fl(r, "vcg_rent") for r in rs)),
             statistics.mean(fl(r, "n_winners") for r in rs), statistics.mean(fl(r, "pab_mean_markup") for r in rs)))

    P("\n## RQ4\n")
    ze = max(fl(r, "z_err") for r in r3)
    pe_ = max(fl(r, "pay_err") for r in r3)
    P("- Equality error: max |Z*_naive − Z*_accel| = %.2e, max |p_naive − p_accel| = %.2e trên %d instance (%d solve full+removal mỗi nhánh)"
      % (ze, pe_, len(r3), sum(int(r["n_solves"]) for r in r3)))
    P("- Instance có ≥1 winner: %d/%d; số winner mean %.2f"
      % (sum(1 for r in r3 if int(r["n_winners"]) > 0), len(r3), statistics.mean(fl(r, "n_winners") for r in r3)))
    P("\n| alignment | n | pool cut K* (%) | t_C naive (s, median) | t_C accel (s, median) | speed-up C (median [IQR]) | speed-up incl. K* build (median) | t_A (s, median) |")
    P("|---:|---:|---|---:|---:|---|---:|---:|")
    for a in [0.5, 0.9]:
        for n in [10, 15, 20]:
            rs = [r for r in r3 if abs(fl(r, "alignment") - a) < 1e-9 and int(r["n"]) == n]
            if not rs:
                continue
            cut = [1 - fl(r, "pool_kstar") / fl(r, "pool_full") for r in rs]
            sp = sorted(fl(r, "t_C_naive") / fl(r, "t_C_accel") for r in rs)
            sp2 = sorted(fl(r, "t_C_naive") / (fl(r, "t_C_accel") + fl(r, "t_kstar")) for r in rs)
            P("| %.2f | %d | %s | %.3f | %.3f | %.2f× [%.2f, %.2f] | %.2f× | %.2f |" % (
                a, n, summ(cut, dec=1), statistics.median(fl(r, "t_C_naive") for r in rs),
                statistics.median(fl(r, "t_C_accel") for r in rs), statistics.median(sp), pct(sp, .25),
                pct(sp, .75), statistics.median(sp2), statistics.median(fl(r, "t_A") for r in rs)))
    tn = sum(fl(r, "t_C_naive") for r in r3)
    ta = sum(fl(r, "t_C_accel") for r in r3)
    tk = sum(fl(r, "t_kstar") for r in r3)
    P("\n- Tổng: t_C naive %.1f s, accel %.1f s (+ K* build %.1f s) → %.2f× (không tính build), %.2f× (tính build)\n"
      % (tn, ta, tk, tn / ta, tn / (ta + tk)))

# =========================================================================== RQ5
r5 = load("rq5")
if r5:
    P("## RQ5\n")
    by = {}
    for r in r5:
        by.setdefault(r["variant"], {})[(int(r["n_gw"]), int(r["n_od"]), int(r["rep"]))] = r
    order = ["V0_baseline", "V1_tw60", "V2_tw240", "V3_tau20", "V4_tau45", "V5_fd075", "V6_fd125",
             "V7_clustered", "V8_theta15_30", "V9_n25", "V10_n30"]

    def comp(r):
        b = min(fl(r, "C_gw_only"), fl(r, "C_od_only"))
        return (b - fl(r, "Z")) / b

    def bund(r):
        return (fl(r, "C_B1") - fl(r, "Z")) / fl(r, "C_B1")

    def ovh(r):
        w = fl(r, "winner_true_cost")
        return fl(r, "vcg_rent") / w if w > 0 else None

    P("| biến thể | N | complementarity gain % | bundling gain B3 vs B1 % | VCG overhead rent/Σc % | FD rate | solve OPTIMAL | ≤300 s | t_total median (s) |")
    P("|---|---:|---|---|---|---:|---:|---:|---:|")
    for v in order:
        rs = list(by.get(v, {}).values())
        if not rs:
            continue
        ov = [x for x in (ovh(r) for r in rs) if x is not None]
        P("| %s | %d | %s | %s | %s | %.3f | %d/%d | %d/%d | %.2f |" % (
            v, len(rs), summ([comp(r) for r in rs]), summ([bund(r) for r in rs]), summ(ov),
            statistics.mean(fl(r, "fd_rate") for r in rs),
            sum(int(r["n_optimal"]) for r in rs), sum(int(r["n_solves"]) for r in rs),
            sum(1 for r in rs if fl(r, "t_total") <= 300), len(rs),
            statistics.median(fl(r, "t_total") for r in rs)))
    P("\n### Paired difference so với baseline (cùng seed; V1–V8), điểm % — mean (CI95)\n")
    P("| biến thể | Δ complementarity | Δ bundling gain | Δ VCG overhead |")
    P("|---|---|---|---|")
    base = by.get("V0_baseline", {})
    for v in order[1:9]:
        pairs = [(base[k], r) for k, r in by.get(v, {}).items() if k in base]
        if not pairs:
            continue

        def dd(f):
            x = [f(r0) - f(b) for b, r0 in pairs if f(b) is not None and f(r0) is not None]
            lo, hi = ci_mean(x)
            return "%.2f (%.2f–%.2f)" % (100 * statistics.mean(x), 100 * lo, 100 * hi)
        P("| %s | %s | %s | %s |" % (v, dd(comp), dd(bund), dd(ovh)))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(out))
