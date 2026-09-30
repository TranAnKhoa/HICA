"""FIG 6 [M] — RQ2: (a) bundling gain vs B1 by menu (median + IQR band); (b) price of range B."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

import columns as K
import data as D
import expected as E
from checks import Checker
from common import align_ticklabels, box_ci, box_ci_legend_handles, cat_x, check_fd_ticks
from stats import mean_boot_ci, median_iqr
from style import DOUBLE, C, MK, LS, LABEL, N_COLORS, figsize, panel_label, save

NAME = "fig06_rq2_bundling"
MENUS = ["B2", "B3", "B4", "HEUR"]


def wide():
    d3 = D.d3()
    D.assert_unique(d3, K.KEY + [K.MENU], "D3")
    d3[K.ALIGN] = d3[K.ALIGN].round(2)
    # keep first-appearance (file) order of instances — pivot_table reorders, which changes a
    # bootstrap drawn with a fixed seed; MASTER iterated instances in file order
    inst = {}
    for r in d3.itertuples(index=False):
        k = tuple(getattr(r, c) for c in K.KEY)
        inst.setdefault(k, dict(zip(K.KEY, k)))[getattr(r, K.MENU)] = getattr(r, K.COST)
    w = pd.DataFrame(list(inst.values()))
    return d3, w


def gains(w, menu, base="B1"):
    m = w[[menu, base]].dropna()
    return 100 * (m[base] - m[menu]) / m[base], m.index


def run():
    chk = Checker("FIG 6")
    fd = check_fd_ticks(chk)
    d3, w = wide()
    chk.true("1500 instances", len(w) == 1500, str(len(w)))
    chk.true("B4 on 1000 instances (n<=15)", w["B4"].notna().sum() == 1000 and w.loc[w[K.N] == 20, "B4"].isna().all())
    w90 = w[w[K.ALIGN] == 0.90]
    for m in MENUS:
        g, _ = gains(w90, m)
        chk.close("median gain %s @0.90" % m, float(np.median(g)), E.FIG6["median090"][m], 2)
    # MASTER mean/CI used the order of instances as read from the shard files (as here)
    g_b3 = list(gains(w90, "B3")[0])
    mu, lo, hi = mean_boot_ci(g_b3, seed=E.FIG6["ci_seed"])
    chk.close("mean B3 @0.90", mu, E.FIG6["mean090_B3"], 2)
    chk.close("CI lo B3 @0.90 (MASTER seed)", lo, E.FIG6["ci090_B3"][0], 2)
    chk.close("CI hi B3 @0.90 (MASTER seed)", hi, E.FIG6["ci090_B3"][1], 2)
    g, _ = gains(w90, "B3", base="HEUR")
    chk.close("median B3 vs HEUR @0.90", float(np.median(g)), E.FIG6["b3_vs_heur_median090"], 2)
    pr = {}
    for a in E.ALIGNS:
        for n in (10, 15):
            s = w[(w[K.ALIGN] == a) & (w[K.N] == n)]
            pr[(a, n)] = list(100 * (s["B3"] - s["B4"]) / s["B4"])
    for n in (10, 15):
        chk.close("price of range median @0.90 n=%d" % n, float(np.median(pr[(0.90, n)])),
                  E.FIG6["price_range_median090"][n], 1)
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, (ax, bx) = plt.subplots(1, 2, figsize=figsize(DOUBLE, DOUBLE * 0.36),
                                 gridspec_kw=dict(width_ratios=[1.25, 1]))
    x = np.arange(len(E.ALIGNS))
    off = {"B2": -0.15, "B3": -0.05, "B4": 0.05, "HEUR": 0.15}
    for m in MENUS:
        med, q1, q3 = [], [], []
        for a in E.ALIGNS:
            g, _ = gains(w[w[K.ALIGN] == a], m)
            mm, a1, a3 = median_iqr(g)
            med.append(mm); q1.append(a1); q3.append(a3)
        xs = x + off[m]
        ax.fill_between(xs, q1, q3, color=C[m], alpha=0.06, lw=0)
        lab = LABEL[m] + (" ($n\\leq15$)" if m == "B4" else "")
        ax.errorbar(xs, med, yerr=[np.array(med) - q1, np.array(q3) - med], color=C[m], marker=MK[m],
                    ls=LS.get(m, "-"), ms=4, elinewidth=0.7, capsize=1.5, label=lab,
                    mfc="white" if m == "HEUR" else C[m])
    ax.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    ax.set_xticks(x); ax.set_xticklabels(align_ticklabels(E.ALIGNS, fd)); cat_x(ax)
    ax.set_xlabel("alignment (second row: fixed-fleet share of orders)")
    ax.set_ylabel(r"cost reduction vs. $B{=}1$ (%)")
    ax.legend(loc="upper left", title="median, IQR", title_fontsize=7)
    panel_label(ax, "a")

    offb = {10: -0.16, 15: 0.16}
    for i, a in enumerate(E.ALIGNS):
        for n in (10, 15):
            box_ci(bx, i + offb[n], pr[(a, n)], N_COLORS[n], width=0.28, rng_seed=i * 11 + n)
    bx.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    bx.set_xticks(x); bx.set_xticklabels(align_ticklabels(E.ALIGNS, fd)); cat_x(bx)
    bx.set_xlabel("alignment (second row: fixed-fleet share of orders)")
    bx.set_ylabel(r"price of range: $(C_{B3}-C_{B4})/C_{B4}$ (%)")
    h = [Patch(facecolor=N_COLORS[n], alpha=0.5, edgecolor=N_COLORS[n], label="$n=%d$" % n) for n in (10, 15)]
    bx.legend(handles=h + box_ci_legend_handles(), loc="upper left")
    panel_label(bx, "b")
    fig.tight_layout(w_pad=1.2)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])

