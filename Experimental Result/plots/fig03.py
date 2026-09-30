"""FIG 3 [M] — speed-up of exact payment computation on K* (per instance, log scale):
payment step only (filled) vs including frontier construction (hollow)."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import columns as K
import data as D
import expected as E
from checks import Checker
from common import box_ci, cat_x
from stats import speedup_pooled
from style import ONEHALF, C, figsize, save

NAME = "fig03_payment_speedup"
NS = [10, 15, 20]


def run():
    chk = Checker("FIG 3")
    d = D.d45(); d[K.ALIGN] = d[K.ALIGN].round(2)
    d["sp_pay"] = d[K.T_C_NAIVE] / d[K.T_C_ACCEL]
    d["sp_incl"] = d[K.T_C_NAIVE] / (d[K.T_C_ACCEL] + d[K.T_KSTAR])
    for a in (0.50, 0.90):
        for n, e1, e2 in zip(NS, E.FIG3["pay_only"][a], E.FIG3["incl_build"][a]):
            s = d[(d[K.ALIGN] == a) & (d[K.N] == n)]
            chk.close("median pay-only @%.2f n=%d" % (a, n), float(np.median(s["sp_pay"])), e1, 2, kind="time")
            chk.close("median incl-build @%.2f n=%d" % (a, n), float(np.median(s["sp_incl"])), e2, 2, kind="time")
    pp = speedup_pooled(d, K.T_C_NAIVE, K.T_C_ACCEL)
    pi = d[K.T_C_NAIVE].sum() / (d[K.T_C_ACCEL].sum() + d[K.T_KSTAR].sum())
    chk.close("pooled pay-only", pp, E.FIG3["pooled_pay"], 2, kind="time")
    chk.close("pooled incl-build", pi, E.FIG3["pooled_incl"], 2, kind="time")
    mx = float(d[K.PAY_ERR].max())
    chk.true("max |dp| rounds to %s" % E.FIG3["max_pay_err"], "%.1e" % mx == E.FIG3["max_pay_err"], "%.3e" % mx)
    chk.true("max |dZ| <= max |dp| bound", float(d[K.Z_ERR].max()) < 1e-12)
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, ax = plt.subplots(figsize=figsize(ONEHALF))
    pos, labels = [], []
    for g, a in enumerate((0.50, 0.90)):
        colr = C["REG050"] if a == 0.50 else C["REG090"]
        for j, n in enumerate(NS):
            x = g * 3.6 + j * 1.1
            s = d[(d[K.ALIGN] == a) & (d[K.N] == n)]
            box_ci(ax, x - 0.2, np.log10(s["sp_pay"]), colr, width=0.34, rng_seed=g * 10 + j)
            box_ci(ax, x + 0.2, np.log10(s["sp_incl"]), colr, width=0.34, rng_seed=g * 10 + j + 5, hollow=True)
            pos.append(x); labels.append("$n=%d$" % n)
    ax.axhline(0, color="#555555", lw=0.7, ls="--", zorder=0)
    ax.set_xticks(pos); ax.set_xticklabels(labels); cat_x(ax)
    for g, lab in enumerate(("alignment 0.50\n(fixed-fleet dominated)", "alignment 0.90\n(crowd competitive)")):
        ax.text(g * 3.6 + 1.1, -0.09, lab, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=7)
    ticks = [0.5, 1, 2, 5, 10, 20, 50]
    ax.set_yticks(np.log10(ticks)); ax.set_yticklabels(["%g" % t for t in ticks])
    ax.tick_params(axis="y", which="minor", left=False, right=False)
    ax.set_ylabel(r"speed-up vs. full pool ($\times$, log scale)")
    ax.text(0.99, 0.97, "pooled: %.2f$\\times$ (payment only),\n%.2f$\\times$ (incl. construction)" % (pp, pi),
            transform=ax.transAxes, ha="right", va="top", fontsize=7,
            bbox=dict(facecolor="white", edgecolor="#999999", lw=0.5, pad=2))
    h = [Patch(facecolor="#888888", alpha=0.4, edgecolor="#555555", label="payment step only"),
         Patch(facecolor="white", edgecolor="#555555", label="incl. frontier construction"),
         Line2D([], [], marker="D", color="black", mfc="#bbbbbb", ms=3, lw=0.8,
                label="geometric mean with 95% CI")]
    ax.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, borderaxespad=0.2)
    ax.set_ylim(np.log10(0.2), np.log10(120))
    fig.subplots_adjust(bottom=0.2)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])
