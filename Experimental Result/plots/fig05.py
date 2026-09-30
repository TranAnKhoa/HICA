"""FIG 5 [M] — RQ1 complementarity gain per instance, by alignment and n (recomputed from D1).
Optional FIG 5b [A] — loss of sequential procurement vs JOINT, per instance (§0.4)."""
import matplotlib.pyplot as plt
import numpy as np

import columns as K
import data as D
import expected as E
from checks import Checker
from common import align_ticklabels, box_ci, box_ci_legend_handles, cat_x, check_fd_ticks
from stats import mean_boot_ci
from style import ONEHALF, N_COLORS, figsize, save
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

NAME, NAME_B = "fig05_rq1_complementarity", "fig05b_sequential"


def per_instance():
    """Rows in D1 file order -> one record per instance, with gains in %."""
    d1 = D.d1()
    recs = {}
    for _, r in d1.iterrows():
        k = tuple(r[c] for c in K.KEY_RQ1)
        recs.setdefault(k, {})[r[K.TREAT]] = r[K.TRUE_COST]
    out = []
    for (a, n, ng, no, rep), c in recs.items():
        best = min(c[K.GW_ONLY], c[K.OD_ONLY])
        out.append(dict(alignment=round(a, 2), n=n, n_gw=ng, n_od=no, rep=rep,
                        comp=None if best == 0 else 100 * (best - c[K.JOINT]) / best,
                        odf=100 * (c[K.OD_FIRST] - c[K.JOINT]) / c[K.OD_FIRST],
                        gwf=100 * (c[K.GW_FIRST] - c[K.JOINT]) / c[K.GW_FIRST]))
    return out


def run():
    chk = Checker("FIG 5")
    fd = check_fd_ticks(chk)
    recs = per_instance()
    chk.true("1500 instances", len(recs) == 1500, str(len(recs)))
    dropped = sum(1 for r in recs if r["comp"] is None)
    chk.true("dropped == 0", dropped == E.FIG5["dropped"], str(dropped))
    by_a = {a: [r["comp"] for r in recs if r["alignment"] == a and r["comp"] is not None] for a in E.ALIGNS}
    for i, a in enumerate(E.ALIGNS):
        chk.true("n=300 @%.2f" % a, len(by_a[a]) == 300, str(len(by_a[a])))
        chk.close("median @%.2f" % a, float(np.median(by_a[a])), E.FIG5["median"][i], 2)
        chk.close("mean @%.2f" % a, float(np.mean(by_a[a])), E.FIG5["mean"][i], 2)
    _, lo, hi = mean_boot_ci(by_a[0.90], seed=E.FIG5["ci_seed"])
    chk.close("CI lo @0.90 (MASTER seed)", lo, E.FIG5["ci090"][0], 2)
    chk.close("CI hi @0.90 (MASTER seed)", hi, E.FIG5["ci090"][1], 2)
    for n, exp in zip([10, 15, 20], E.FIG5["median090_by_n"]):
        v = [r["comp"] for r in recs if r["alignment"] == 0.90 and r["n"] == n]
        chk.close("median @0.90 n=%d" % n, float(np.median(v)), exp, 2)
    # cross-check with D2 (file written by the recompute script)
    d2, _ = D.d2()
    for _, r in d2.iterrows():
        chk.close("D2 mean @%.2f" % r["alignment"], float(np.mean(by_a[round(r["alignment"], 2)])), r["mean"], 4)
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, ax = plt.subplots(figsize=figsize(ONEHALF))
    off = {10: -0.26, 15: 0.0, 20: 0.26}
    for i, a in enumerate(E.ALIGNS):
        for n in (10, 15, 20):
            v = [r["comp"] for r in recs if r["alignment"] == a and r["n"] == n]
            box_ci(ax, i + off[n], v, N_COLORS[n], width=0.22, rng_seed=i * 100 + n)
    ax.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    ax.set_xticks(range(len(E.ALIGNS)))
    ax.set_xticklabels(align_ticklabels(E.ALIGNS, fd)); cat_x(ax)
    ax.set_xlabel("alignment (second row: fixed-fleet share of orders)")
    ax.set_ylabel("complementarity gain (%)")
    ax.set_xlim(-0.55, len(E.ALIGNS) - 0.45)
    h = [Patch(facecolor=N_COLORS[n], alpha=0.5, edgecolor=N_COLORS[n], label="$n=%d$" % n) for n in (10, 15, 20)]
    ax.legend(handles=h + box_ci_legend_handles(), loc="upper left", ncol=1)
    save(fig, NAME)
    return "OK", chk


def run_b():
    """Optional appendix: per-instance loss of sequential procurement vs JOINT (§0.4).
    Sanity: per-cell medians recomputed here must equal the per-cell medians already stored
    in rq1_analysis_by_cell.csv (D1b)."""
    chk = Checker("FIG 5b")
    fd = check_fd_ticks(chk)
    recs = per_instance()
    d1b = D.d1b()
    for _, c in d1b.iterrows():
        cell = [r for r in recs if r["alignment"] == round(c["alignment_target"], 2) and r["n"] == c["n"]
                and r["n_gw"] == c["n_gw"] and r["n_od"] == c["n_od"]]
        tag = "a=%.2f n=%d (%d,%d)" % (c["alignment_target"], c["n"], c["n_gw"], c["n_od"])
        chk.close("cell OD-first median " + tag,
                  float(np.median([r["odf"] for r in cell])), 100 * c["gain_vs_odfirst_median"], 4)
        chk.close("cell GW-first median " + tag,
                  float(np.median([r["gwf"] for r in cell])), 100 * c["gain_vs_gwfirst_median"], 4)
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(ONEHALF))
    cols = {"odf": "#D55E00", "gwf": "#0072B2"}
    for i, a in enumerate(E.ALIGNS):
        for key, o in (("odf", -0.17), ("gwf", 0.17)):
            v = [r[key] for r in recs if r["alignment"] == a]
            box_ci(ax, i + o, v, cols[key], width=0.28, rng_seed=i * 7 + (1 if key == "odf" else 2))
    ax.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    ax.set_xticks(range(len(E.ALIGNS)))
    ax.set_xticklabels(align_ticklabels(E.ALIGNS, fd)); cat_x(ax)
    ax.set_xlabel("alignment (second row: fixed-fleet share of orders)")
    ax.set_ylabel("cost increase of sequential\nprocurement over joint (%)")
    ax.set_xlim(-0.55, len(E.ALIGNS) - 0.45)
    h = [Patch(facecolor=cols["odf"], alpha=0.5, edgecolor=cols["odf"], label="OD first, then GW"),
         Patch(facecolor=cols["gwf"], alpha=0.5, edgecolor=cols["gwf"], label="GW first, then OD")]
    ax.legend(handles=h + box_ci_legend_handles(), loc="upper left")
    save(fig, NAME_B)
    return "OK", chk


if __name__ == "__main__":
    for f in (run, run_b):
        s, c = f()
        print(f.__name__, s, c.summary(), c.fails[:5])

