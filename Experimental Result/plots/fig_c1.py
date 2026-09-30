"""FIG C1 [M] — local margins in Example 11 (analytic, no data)."""
import numpy as np
import matplotlib.pyplot as plt

import expected as E
from checks import Checker
from style import DOUBLE, C, figsize, panel_label, save

NAME = "fig_c1_frontier_intuition"
LO, HI = 18.0, 25.0
q1, q2 = 15.0, 45.0


def routes():
    ra = dict(c=lambda b: 6 + 0.6 * b, branches=[lambda b: 0 * b + q1], lbl=r"(a) $r_a \notin \mathcal{K}^\star$")
    rb = dict(c=lambda b: 8 + 0.8 * b, branches=[lambda b: 0 * b + q2], lbl=r"(b) $r_b \in \mathcal{K}^\star$")
    rc = dict(c=lambda b: 11 + 1.2 * b,
              branches=[lambda b: 0 * b + (q1 + q2), lambda b: 51 + 0.6 * b, lambda b: 23 + 0.8 * b],
              lbl=r"(c) $r_c \in \mathcal{K}^\star$")
    return [ra, rb, rc]


def run():
    chk = Checker("FIG C1")
    rs = routes()
    E_rc = lambda b: min(f(b) for f in rs[2]["branches"])
    chk.close("E_rc(18)", E_rc(18), *E.FIG_C1["E_rc_18"])
    chk.close("c_rc(18)", rs[2]["c"](18), *E.FIG_C1["c_rc_18"])
    chk.close("c_ra(18)", rs[0]["c"](18), *E.FIG_C1["c_ra_18"])
    chk.close("c_ra = E_ra at b", (q1 - 6) / 0.6, *E.FIG_C1["cross_ra"])
    chk.true("cross outside Theta", (q1 - 6) / 0.6 < LO)
    if not chk.ok():
        return "CHECK_FAIL", chk
    b = np.linspace(0, 35, 701)
    fig, axes = plt.subplots(1, 3, figsize=figsize(DOUBLE, DOUBLE * 0.30), sharey=True)
    for ax, r, letter in zip(axes, rs, "abc"):
        c = r["c"](b)
        env = np.min([f(b) for f in r["branches"]], axis=0)
        ax.axvspan(LO, HI, color="#e6e6e6", zorder=0, lw=0)
        if len(r["branches"]) > 1:
            for f in r["branches"]:
                ax.plot(b, f(b), color=C["FD"], lw=0.6, ls=":", alpha=0.7, zorder=1)
        inside = (b >= LO) & (b <= HI)
        ax.fill_between(b, c, env, where=inside & (env > c), color="#9ecae1", alpha=0.7, lw=0, zorder=1)
        ax.plot(b, env, color=C["FD"], ls="--", lw=1.2, label=r"envelope $E_r(b)$", zorder=3)
        ax.plot(b, c, color=C["GW"], ls="-", lw=1.2, label=r"cost $c_r(b)$", zorder=3)
        ax.set_xlim(0, 35)
        ax.set_ylim(0, 78)
        ax.set_xlabel(r"report $b$ (cost units/h)")
        ax.text(0.03, 0.96, r["lbl"][4:], transform=ax.transAxes, va="top", ha="left", fontsize=7)
        panel_label(ax, letter)
        ax.text((LO + HI) / 2, 2, r"$\Theta$", ha="center", va="bottom", fontsize=7, color="#555555")
    axes[0].set_ylabel("cost units")
    axes[0].legend(loc="center left", bbox_to_anchor=(0.0, 0.62), handlelength=1.8)
    fig.tight_layout(w_pad=0.6)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    print(run()[0])
