"""FIG 2 [M] — runtime breakdown by n (log scale), (a) alignment 0.50, (b) alignment 0.90.
t_A, t_C naive/accel, t_build(K*) from D5; t_B from D3 menu B3 on the same instance key."""
import matplotlib.pyplot as plt
import numpy as np

import columns as K
import data as D
import expected as E
from checks import Checker
from common import cat_x
from stats import median_iqr
from style import DOUBLE, figsize, panel_label, save

NAME = "fig02_runtime_breakdown"
NS = [10, 15, 20]
SERIES = [  # (column, label, color, marker, ls, hollow)
    (K.T_A, "Algorithm A (route generation)", "#000000", "o", "-", False),
    (K.T_B, "Algorithm B (one WDP solve)", "#7F7F7F", "^", ":", False),
    (K.T_C_NAIVE, "Algorithm B+C, naive (full pool)", "#0072B2", "s", "--", True),
    (K.T_C_ACCEL, r"Algorithm B+C on $\mathcal{K}^\star$", "#0072B2", "s", "-", False),
    (K.T_KSTAR, r"construction of $\mathcal{K}^\star$", "#D55E00", "D", "-.", False),
]


def load():
    d = D.d45()
    d[K.ALIGN] = d[K.ALIGN].round(2)
    b3 = D.d3(); b3 = b3[b3[K.MENU] == "B3"][K.KEY + [K.T_B]].copy(); b3[K.ALIGN] = b3[K.ALIGN].round(2)
    m = d.merge(b3, on=K.KEY, how="left", validate="one_to_one")
    return m


def run():
    chk = Checker("FIG 2")
    m = load()
    chk.true("t_B matched for all 600", m[K.T_B].notna().all() and len(m) == 600)
    for a, cols in E.FIG2.items():
        for col, exps in cols.items():
            for n, exp in zip(NS, exps):
                got = float(np.median(m[(m[K.ALIGN] == a) & (m[K.N] == n)][col]))
                chk.close("%s median @%.2f n=%d" % (col, a, n), got, exp, len(str(exp).split(".")[1]), kind="time")
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, axs = plt.subplots(1, 2, figsize=figsize(DOUBLE, DOUBLE * 0.36), sharey=True)
    for ax, a, letter, title in zip(axs, (0.50, 0.90), "ab",
                                    ("alignment 0.50 (fixed-fleet dominated)", "alignment 0.90 (crowd competitive)")):
        s = m[m[K.ALIGN] == a]
        for col, lab, colr, mk, ls, hollow in SERIES:
            med, q1, q3 = zip(*[median_iqr(s[s[K.N] == n][col]) for n in NS])
            ax.fill_between(NS, q1, q3, color=colr, alpha=0.10, lw=0)
            ax.plot(NS, med, color=colr, marker=mk, ls=ls, ms=4, label=lab,
                    mfc="white" if hollow else colr)
        ax.set_yscale("log")
        ax.set_xticks(NS); cat_x(ax)
        ax.set_xlabel("number of orders $n$")
        ax.text(0.03, 0.97, title, transform=ax.transAxes, va="top", ha="left", fontsize=7)
        ax.grid(True, which="major", axis="y", alpha=0.3)
        panel_label(ax, letter)
    axs[0].set_ylabel("time per instance (s, log scale)")
    h, l = axs[0].get_legend_handles_labels()
    fig.tight_layout(w_pad=0.8, rect=(0, 0.1, 1, 1))
    fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0))
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])
