"""FIG 7 [M] — RQ3 at alignment 0.90: (a) payout premium by n and mechanism;
(b) payout premium vs efficiency loss per instance."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import columns as K
import data as D
import expected as E
from checks import Checker
from common import box_ci, box_ci_legend_handles, cat_x
from stats import mean_boot_ci
from style import DOUBLE, C, MK, LABEL, figsize, panel_label, save

NAME = "fig07_rq3_mechanisms"
MECH = [("VCG", K.VCG_PAY, None), ("PAB", K.PAB_PAY, K.PAB_TRUE), ("POSTED", K.POST_PAY, K.POST_TRUE)]


def run():
    chk = Checker("FIG 7")
    d = D.d45()
    D.assert_unique(d, K.KEY, "D4")
    d[K.ALIGN] = d[K.ALIGN].round(2)
    chk.true("600 instances", len(d) == 600)
    s = d[d[K.ALIGN] == 0.90].copy()          # file order kept (boolean mask)
    chk.true("300 instances @0.90", len(s) == 300)
    for m, pay, tc in MECH:
        s["prem_" + m] = 100 * (s[pay] - s[K.Z]) / s[K.Z]
        s["eff_" + m] = 0.0 if tc is None else 100 * (s[tc] - s[K.Z]) / s[K.Z]
        chk.close("premium median %s" % m, float(np.median(s["prem_" + m])), E.FIG7["premium_median"][m], 2)
    mu, lo, hi = mean_boot_ci(list(s["prem_VCG"]), seed=E.FIG7["ci_seed"])
    chk.close("VCG premium mean", mu, E.FIG7["vcg_mean"], 2)
    chk.close("VCG CI lo (MASTER seed)", lo, E.FIG7["vcg_ci"][0], 2)
    chk.close("VCG CI hi (MASTER seed)", hi, E.FIG7["vcg_ci"][1], 2)
    for m in ("POSTED", "PAB"):
        chk.close("eff loss median %s" % m, float(np.median(s["eff_" + m])), E.FIG7["effloss_median"][m], 2)
    gt = int((s[K.VCG_PAY] > s[K.PAB_PAY] + 1e-9).sum())
    chk.true("VCG > PAB-BR 300/300", (gt, len(s)) == E.FIG7["vcg_gt_pab"], "%d/%d" % (gt, len(s)))
    chk.true("all solves optimal", bool(d["all_optimal"].all()))
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, (ax, bx) = plt.subplots(1, 2, figsize=figsize(DOUBLE, DOUBLE * 0.36))
    off = {"VCG": -0.26, "PAB": 0.0, "POSTED": 0.26}
    for i, n in enumerate((10, 15, 20)):
        sn = s[s[K.N] == n]
        for m, _, _ in MECH:
            box_ci(ax, i + off[m], sn["prem_" + m], C[m], width=0.22, rng_seed=i * 5 + len(m))
    ax.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    ax.set_xticks(range(3)); ax.set_xticklabels(["$n=10$", "$n=15$", "$n=20$"]); cat_x(ax)
    ax.set_xlabel("number of orders")
    ax.set_ylabel("payout premium over first-best (%)")
    h = [Patch(facecolor=C[m], alpha=0.5, edgecolor=C[m], label=LABEL[m]) for m, _, _ in MECH]
    ax.legend(handles=h + box_ci_legend_handles(), loc="upper left", ncol=2)
    ax.set_ylim(bottom=-2)
    panel_label(ax, "a")

    for m, _, _ in MECH:
        bx.scatter(s["eff_" + m], s["prem_" + m], s=5, marker=MK[m], color=C[m], alpha=0.4,
                   linewidths=0, label=LABEL[m])
    for m, _, _ in MECH:
        bx.scatter([np.median(s["eff_" + m])], [np.median(s["prem_" + m])], s=55, marker=MK[m],
                   facecolor=C[m], edgecolor="black", linewidth=0.8, zorder=5)
    bx.axvline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    bx.axhline(0, color="#555555", lw=0.6, ls="--", zorder=0)
    bx.set_xlabel("efficiency loss vs. first-best allocation (%)")
    bx.set_ylabel("payout premium over first-best (%)")
    hh = [Line2D([], [], marker=MK[m], ls="", color=C[m], ms=4, label=LABEL[m]) for m, _, _ in MECH]
    hh.append(Line2D([], [], marker="o", ls="", mfc="white", mec="black", ms=6, label="median"))
    bx.legend(handles=hh, loc="upper right")
    panel_label(bx, "b")
    fig.tight_layout(w_pad=1.2)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])

