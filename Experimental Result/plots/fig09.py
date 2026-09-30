"""FIG 9 [M] — RQ5 one-at-a-time robustness: paired differences from V0 (mean, 95% CI) for
complementarity gain, bundling gain (B3 vs B1) and VCG payment overhead."""
import matplotlib.pyplot as plt
import numpy as np

import columns as K
import data as D
import expected as E
from checks import Checker
from stats import PLOT_SEED, paired_diff_boot_ci
from style import DOUBLE, C, figsize, panel_label, save

NAME = "fig09_rq5_forest"
VARS = [("V1_tw60", "TW 60"), ("V2_tw240", "TW 240"), ("V3_tau20", "Detour 20"), ("V4_tau45", "Detour 45"),
        ("V5_fd075", r"FD $\times$0.75"), ("V6_fd125", r"FD $\times$1.25"), ("V7_clustered", "Clustered"),
        ("V8_theta15_30", r"$\theta\sim U[15,30]$")]


def comp(r):
    b = min(r[K.C_GW], r[K.C_OD])
    return 100 * (b - r[K.Z]) / b


def bund(r):
    return 100 * (r[K.C_B1] - r[K.Z]) / r[K.C_B1]


def ovh(r):
    return 100 * r[K.RENT] / r[K.WIN_COST] if r[K.WIN_COST] > 0 else None


METRICS = [("complementarity gain", comp), ("bundling gain ($B{=}3$ vs $B{=}1$)", bund),
           ("VCG payment overhead", ovh)]


def run():
    chk = Checker("FIG 9")
    d = D.d6()
    D.assert_unique(d, K.KEY_RQ5, "D6")
    base = d[d[K.VARIANT] == "V0_baseline"]
    chk.true("V0 has 60 instances", len(base) == 60)

    def ci(v, f, seed):
        (m, lo, hi), _ = paired_diff_boot_ci(base, d[d[K.VARIANT] == v], K.PAIR_RQ5, f, seed=seed)
        return m, lo, hi

    s = E.FIG9["ci_seed"]
    for name, f, key in (("V6_fd125", bund, "V6_dbund"), ("V5_fd075", ovh, "V5_dvcg"), ("V1_tw60", bund, "V1_dbund")):
        m, lo, hi = ci(name, f, s)
        for lab, got, exp in zip(("mean", "lo", "hi"), (m, lo, hi), E.FIG9[key]):
            chk.close("%s %s (MASTER seed)" % (key, lab), got, exp, 2)
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, axs = plt.subplots(1, 3, figsize=figsize(DOUBLE, DOUBLE * 0.34), sharey=True,
                            gridspec_kw=dict(width_ratios=[1, 1, 1.2]))
    y = np.arange(len(VARS))[::-1]
    for ax, (title, f), letter in zip(axs, METRICS, "abc"):
        for yy, (v, lab) in zip(y, VARS):
            m, lo, hi = ci(v, f, PLOT_SEED)
            sig = lo > 0 or hi < 0
            ax.errorbar([m], [yy], xerr=[[m - lo], [hi - m]], fmt="o", color=C["GW"], ms=3.5,
                        mfc=C["GW"] if sig else "white", elinewidth=0.9, capsize=1.5)
        ax.axvline(0, color="#555555", lw=0.7, ls="--")
        ax.set_xlabel("$\\Delta$ %s (pp)" % title)
        ax.grid(True, axis="x", alpha=0.3); ax.grid(False, axis="y")
        ax.tick_params(axis="y", which="minor", left=False, right=False)
        panel_label(ax, letter)
    axs[0].set_yticks(y); axs[0].set_yticklabels([lab for _, lab in VARS])
    fig.tight_layout(w_pad=0.8)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])
