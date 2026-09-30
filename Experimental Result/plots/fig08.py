"""FIG 8 [M] — regimes and pre-auction certification.
(a) FD rate (mean over instances, 95% CI) by alignment, hue n;
(b) per-driver split feasible_empty / fd_dominated / non-empty frontier by alignment;
(c) same split by FD tariff multiplier (RQ5, alignment 0.50)."""
import matplotlib.pyplot as plt
import numpy as np

import columns as K
import data as D
import expected as E
from checks import Checker
from common import align_ticklabels, cat_x, check_fd_ticks
from stats import mean_boot_ci
from style import DOUBLE, C, N_COLORS, N_MARKERS, figsize, panel_label, save

NAME = "fig08_regimes_certificate"


def split_pct(df):
    fe = 100 * df[K.FEAS_EMPTY].astype(bool).mean()
    fdd = 100 * df[K.FD_DOM].astype(bool).mean()
    return fe, fdd, 100 - fe - fdd


def stacked(ax, xs, rows, width=0.6):
    fe = np.array([r[0] for r in rows]); fd = np.array([r[1] for r in rows]); rest = np.array([r[2] for r in rows])
    ax.bar(xs, fe, width, color="#555555", hatch="//", edgecolor="white", linewidth=0.3,
           label="no feasible route ($R_i=\\emptyset$)")
    ax.bar(xs, fd, width, bottom=fe, color=C["GW"], edgecolor="white", linewidth=0.3,
           label="certified FD-dominated ($R_i\\neq\\emptyset$, $\\mathcal{K}^\\star_i=\\emptyset$)")
    ax.bar(xs, rest, width, bottom=fe + fd, color="white", edgecolor="#333333", linewidth=0.6,
           label="non-empty frontier")
    for x, a, b in zip(xs, fe, fd):
        if b >= 4:
            ax.text(x, a + b / 2, "%.1f" % b, ha="center", va="center", color="white", fontsize=6)
        if a >= 4:
            ax.text(x, a / 2, "%.1f" % a, ha="center", va="center", color="white", fontsize=6,
                    bbox=dict(facecolor="#555555", edgecolor="none", pad=0.4))
    ax.set_ylim(0, 100)


def run():
    chk = Checker("FIG 8")
    fd = check_fd_ticks(chk)
    drv, inst, fdp = D.d7()
    drv[K.ALIGN] = drv[K.ALIGN].round(2)
    chk.true("7500 driver rows", len(drv) == 7500)
    chk.true("1500 instance rows", len(inst) == 1500)
    rows_a = []
    for i, a in enumerate(E.ALIGNS):
        fe, fdd, rest = split_pct(drv[drv[K.ALIGN] == a])
        chk.close("feasible_empty @%.2f" % a, fe, E.FIG8["feas_empty"][i], 1)
        chk.close("fd_dominated @%.2f" % a, fdd, E.FIG8["fd_dom"][i], 1)
        rows_a.append((fe, fdd, rest))
    mults = [0.75, 1.00, 1.25]
    rows_f = [split_pct(fdp[fdp[K.FD_MULT] == m]) for m in mults]
    fes = [r[0] for r in rows_f]
    chk.true("feasible_empty identical across tariffs", max(fes) - min(fes) == 0.0, str(fes))
    chk.close("feasible_empty (tariff)", fes[0], E.FIG8["fd_feas_empty"], 1)
    for m, r, exp in zip(mults, rows_f, E.FIG8["fd_fd_dom"]):
        chk.close("fd_dominated x%.2f" % m, r[1], exp, 1)
    chk.true("fd_dominated decreasing in tariff", rows_f[0][1] > rows_f[1][1] > rows_f[2][1])
    if not chk.ok():
        return "CHECK_FAIL", chk

    # (a) FD rate per instance from D3/B3 (see DATA_MANIFEST), by alignment and n
    b3 = D.d3(); b3 = b3[b3[K.MENU] == "B3"].copy(); b3[K.ALIGN] = b3[K.ALIGN].round(2)
    locked = D.rq1_locked()["alignment"]["locked_targets"]

    fig, axs = plt.subplots(1, 3, figsize=figsize(DOUBLE, DOUBLE * 0.36),
                            gridspec_kw=dict(width_ratios=[1.25, 1.25, 0.75]))
    ax = axs[0]
    x = np.arange(len(E.ALIGNS))
    off = {10: -0.18, 15: 0.0, 20: 0.18}
    for n in (10, 15, 20):
        m, lo, hi = zip(*[mean_boot_ci(b3[(b3[K.ALIGN] == a) & (b3[K.N] == n)][K.FD_RATE]) for a in E.ALIGNS])
        ax.errorbar(x + off[n], m, yerr=[np.array(m) - lo, np.array(hi) - m], color=N_COLORS[n],
                    marker=N_MARKERS[n], ls="-", ms=3.5, elinewidth=0.7, capsize=1.5, label="$n=%d$" % n)
    for i, a in enumerate(E.ALIGNS):
        cs = locked["%.2f" % a]["corridor_share"]
        ax.text(i, 0.02, "cs=%.1f" % cs, ha="center", va="bottom", fontsize=6, color="#555555")
    ax.set_xticks(x); ax.set_xticklabels(["%.2f" % a for a in E.ALIGNS]); cat_x(ax)
    ax.set_xlabel("alignment (cs: corridor share of generator)")
    ax.set_ylabel("fixed-fleet share of orders")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.08), title="mean, 95% CI", title_fontsize=7)
    panel_label(ax, "a")

    bx = axs[1]
    stacked(bx, x, rows_a)
    bx.set_xticks(x); bx.set_xticklabels(align_ticklabels(E.ALIGNS, fd)); cat_x(bx)
    bx.set_xlabel("alignment (second row: fixed-fleet share)")
    bx.set_ylabel("share of drivers (%)")
    panel_label(bx, "b")

    cx = axs[2]
    stacked(cx, np.arange(3), rows_f)
    cx.set_xticks(range(3)); cx.set_xticklabels([r"$\times0.75$", r"$\times1.00$", r"$\times1.25$"]); cat_x(cx)
    cx.set_xlabel("FD tariff (alignment 0.50)")
    cx.set_ylabel("share of drivers (%)")
    panel_label(cx, "c")
    h, l = bx.get_legend_handles_labels()
    fig.tight_layout(w_pad=1.0, rect=(0, 0.07, 1, 1))
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.62, 0.0))
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])
