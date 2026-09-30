"""FIG 4 [M] — FD-completion label rule on Algorithm A, 5 RQ1 instances.
(a) speed-up per instance: median and IQR over repeated runs (B=3, B=4), log x;
(b) share of label extensions avoided.
Source D9 JSON (per-instance summaries; raw per-repeat times were not stored, so no strip)."""
import matplotlib.pyplot as plt
import numpy as np

import data as D
import expected as E
from checks import Checker
from style import DOUBLE, figsize, panel_label, save

NAME = "fig04_label_rule"
INST = E.LABEL_INSTANCES
NICE = {"n12_seed42": "n12 s42", "n10_seed1": "n10 s1", "n15_seed7": "n15 s7",
        "n12_seed123": "n12 s123", "n10_seed999": "n10 s999"}
COL = {3: "#56B4E9", 4: "#003B5C"}
MKR = {3: "o", 4: "D"}


def tables():
    b3, b3_999, b4 = D.d9_label()
    t3 = {k: dict(b3[k]) for k in INST}
    t3["n10_seed999"] = dict(b3_999["n10_seed999"])   # N=20 rerun, as reported in MASTER
    t4 = {k: dict(b4[k]) for k in INST}
    return {3: t3, 4: t4}, {3: b3["ALL"]["median_speedup"], 4: b4["ALL"]["median_speedup"]}


def run():
    chk = Checker("FIG 4")
    t, pooled = tables()
    chk.true("B3 n10s999 is the N=20 rerun", t[3]["n10_seed999"]["n_repeats"] == 20)
    for B in (3, 4):
        med = float(np.median([t[B][k]["median_speedup"] for k in INST]))
        chk.close("median per-instance B=%d" % B, med, E.FIG4["median_per_inst"][B], 2, kind="time")
        chk.close("pooled B=%d" % B, pooled[B], E.FIG4["pooled"][B], 2, kind="time")
        for k, exp in zip(INST, E.FIG4["ext_saved"][B]):
            chk.close("ext saved B=%d %s" % (B, k), 100 * t[B][k]["ext_saved"], exp, 1)
    if not chk.ok():
        return "CHECK_FAIL", chk

    fig, (ax, bx) = plt.subplots(1, 2, figsize=figsize(DOUBLE, DOUBLE * 0.30), sharey=True)
    y = np.arange(len(INST))[::-1]
    for B, dy in ((3, 0.13), (4, -0.13)):
        m = np.array([t[B][k]["median_speedup"] for k in INST])
        q1 = np.array([t[B][k]["q1_speedup"] for k in INST])
        q3 = np.array([t[B][k]["q3_speedup"] for k in INST])
        ax.errorbar(m, y + dy, xerr=[m - q1, q3 - m], fmt=MKR[B], color=COL[B], ms=4, elinewidth=0.9,
                    capsize=1.5, label="$B=%d$ (median %.2f$\\times$; pooled %.2f$\\times$)"
                    % (B, np.median(m), pooled[B]))
    ax.axvline(1, color="#555555", lw=0.7, ls="--")
    ax.set_xscale("log")
    ax.set_xticks([1, 1.5, 2, 3, 4]); ax.set_xticklabels(["1", "1.5", "2", "3", "4"])
    ax.tick_params(axis="x", which="minor", bottom=False, top=False)
    ax.set_xlim(0.9, 4.5)
    ax.set_yticks(y); ax.set_yticklabels([NICE[k] for k in INST])
    ax.tick_params(axis="y", which="minor", left=False, right=False)
    ax.set_xlabel(r"speed-up of Algorithm A ($\times$, log scale; median, IQR over runs)")
    ax.grid(True, axis="x", alpha=0.3); ax.grid(False, axis="y")
    ax.set_ylim(-0.6, len(INST) + 0.35)
    ax.legend(loc="upper center", fontsize=6.5, ncol=2, columnspacing=1.0, handletextpad=0.3,
              frameon=True, facecolor="white", edgecolor="none", framealpha=1)
    panel_label(ax, "a")

    for B, dy in ((3, 0.18), (4, -0.18)):
        v = [100 * t[B][k]["ext_saved"] for k in INST]
        bx.barh(y + dy, v, height=0.34, color=COL[B], edgecolor="black", linewidth=0.4,
                hatch=None if B == 3 else "//", label="$B=%d$" % B)
        for yy, vv in zip(y + dy, v):
            bx.text(vv + 1, yy, "%.1f" % vv, va="center", fontsize=6)
    bx.set_xlim(0, 90)
    bx.set_xlabel("label extensions avoided (%)")
    bx.grid(True, axis="x", alpha=0.3); bx.grid(False, axis="y")
    bx.tick_params(axis="y", which="minor", left=False, right=False)
    bx.legend(loc="upper right", ncol=2)
    panel_label(bx, "b")
    fig.tight_layout(w_pad=1.0)
    save(fig, NAME)
    return "OK", chk


if __name__ == "__main__":
    s, c = run()
    print(s, c.summary(), c.fails[:6])
