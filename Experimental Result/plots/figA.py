"""Appendix figures A1–A7 (Figure.md §4 Appendix)."""
from math import comb

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import columns as K
import data as D
import expected as E
from checks import Checker, missing
from common import cat_x
from style import SINGLE, C, figsize, save


def _pearson(x, y):
    return float(np.corrcoef(np.asarray(x, float), np.asarray(y, float))[0, 1])


# ---------------------------------------------------------------- A1
def run_a1():
    chk = Checker("FIG A1")
    d = D.d45(); d[K.ALIGN] = d[K.ALIGN].round(2)
    p10 = D.d8()
    chk.close("Pearson r (600)", _pearson(d[K.POOL_FULL], d[K.T_KSTAR]), E.FIGA1["r600"], 3)
    chk.close("Pearson r (10)", _pearson(p10["pool_size"], p10[K.T_BUILD]), E.FIGA1["r10"], 3)
    us = 1e6 * p10[K.T_BUILD] / p10["pool_size"]
    s2 = p10[K.SRC].str.startswith("[S2]")
    s2_other = us[s2 & ~p10[K.SRC].str.contains("n10 s1\\)")]
    chk.true("[S2] us/route in 33-41 (excl. n10 s1)",
             E.FIGA1["us_S2"][0] - 0.5 <= s2_other.min() and s2_other.max() <= E.FIGA1["us_S2"][1] + 0.5,
             "%s" % np.round(s2_other.values, 1))
    n10s1 = float(us[p10[K.SRC].str.contains("n10 s1\\)")].iloc[0])
    chk.close("[S2] n10 s1 us/route", n10s1, E.FIGA1["us_S2_n10s1"], 0, kind="time")
    rq = us[~s2]
    chk.true("RQ4 sample us/route in 48-54", E.FIGA1["us_RQ4"][0] - 0.5 <= rq.min() and
             rq.max() <= E.FIGA1["us_RQ4"][1] + 0.5, "%s" % np.round(rq.values, 1))
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(SINGLE, SINGLE * 0.8))
    for a, colr in ((0.50, C["REG050"]), (0.90, C["REG090"])):
        s = d[d[K.ALIGN] == a]
        ax.scatter(s[K.POOL_FULL], s[K.T_KSTAR], s=4, color=colr, alpha=0.35, linewidths=0,
                   label="RQ4, alignment %.2f" % a)
    lx, ly = np.log10(d[K.POOL_FULL]), np.log10(d[K.T_KSTAR])
    b, a0 = np.polyfit(lx, ly, 1)
    xs = np.logspace(lx.min(), lx.max(), 50)
    ax.plot(xs, 10 ** a0 * xs ** b, color="black", lw=0.9, label="log-log fit (slope %.2f)" % b)
    ax.scatter(p10[s2]["pool_size"], p10[s2][K.T_BUILD], s=28, facecolor="none", edgecolor="#D55E00",
               marker="s", linewidths=0.9, label="[S2] instances", zorder=4)
    ax.scatter(p10[~s2]["pool_size"], p10[~s2][K.T_BUILD], s=28, facecolor="none", edgecolor="black",
               marker="o", linewidths=0.9, label="RQ4 reconciliation sample", zorder=4)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("routes in pool (log scale)")
    ax.set_ylabel(r"construction time of $\mathcal{K}^\star$ (s, log scale)")
    ax.text(0.97, 0.04, "Pearson $r$ = %.3f (600), %.3f (10)" % (_pearson(d[K.POOL_FULL], d[K.T_KSTAR]),
            _pearson(p10["pool_size"], p10[K.T_BUILD])), transform=ax.transAxes, ha="right", fontsize=6.5)
    ax.legend(loc="upper left", fontsize=6)
    save(fig, "figA1_kstar_build_vs_pool")
    return "OK", chk


# ---------------------------------------------------------------- A2
def run_a2():
    chk = Checker("FIG A2")
    d = D.d45(); d[K.ALIGN] = d[K.ALIGN].round(2)
    d["cut"] = 100 * (1 - d[K.POOL_KSTAR] / d[K.POOL_FULL])
    chk.close("median cut @0.50", float(np.median(d[d[K.ALIGN] == 0.50]["cut"])), E.FIGA2["cut050"], 1)
    for n, exp in zip((10, 15, 20), E.FIGA2["cut090"]):
        chk.close("median cut @0.90 n=%d" % n, float(np.median(d[(d[K.ALIGN] == 0.90) & (d[K.N] == n)]["cut"])), exp, 1)
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(SINGLE, SINGLE * 0.8))
    for a, colr, mk in ((0.50, C["REG050"], "o"), (0.90, C["REG090"], "s")):
        s = d[d[K.ALIGN] == a]
        ax.scatter(s[K.POOL_FULL], s[K.POOL_KSTAR] + 1, s=5, color=colr, marker=mk, alpha=0.45, linewidths=0,
                   label="alignment %.2f" % a)
    xs = np.logspace(np.log10(d[K.POOL_FULL].min()), np.log10(d[K.POOL_FULL].max()), 20)
    ax.plot(xs, xs, color="black", lw=0.8, ls="-", label="$y=x$ (no pruning)")
    ax.plot(xs, 0.25 * xs, color="black", lw=0.8, ls="--", label="$y=0.25x$ (75% pruned)")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("routes in full pool (log scale)")
    ax.set_ylabel(r"routes in $\mathcal{K}^\star$ + 1 (log scale)")
    ax.legend(loc="upper left", fontsize=6)
    save(fig, "figA2_pool_compression")
    return "OK", chk


# ---------------------------------------------------------------- A3
def run_a3():
    chk = Checker("FIG A3")
    d = D.d11(); d[K.ALIGN] = d[K.ALIGN].round(2)
    chk.close("median full @0.90", float(np.median(d[d[K.ALIGN] == 0.90][K.LCF_FULL])), E.FIGA3["full090"], 3)
    chk.close("median K* @0.90", float(np.median(d[d[K.ALIGN] == 0.90][K.LCF_K])), E.FIGA3["k090"], 3)
    chk.close("median K* @0.50", float(np.median(d[d[K.ALIGN] == 0.50][K.LCF_K])), E.FIGA3["k050"], 3)
    s9 = d[d[K.ALIGN] == 0.90]
    got = (int((s9[K.NCOMP_K] >= 2).sum()), len(s9))
    chk.true(">=2 components on K* @0.90 = 22/300", got == E.FIGA3["multi_k090"], str(got))
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(SINGLE, SINGLE * 0.8))
    for a, colr in ((0.50, C["REG050"]), (0.90, C["REG090"])):
        s = d[d[K.ALIGN] == a]
        for col, ls, lab in ((K.LCF_FULL, "-", "full pool"), (K.LCF_K, "--", r"$\mathcal{K}^\star$")):
            v = np.sort(s[col].values)
            ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=colr, ls=ls, lw=1.1,
                    label="%s, alignment %.2f" % (lab, a))
    ax.axvline(0.85, color="#D55E00", lw=0.8, ls=":")
    ax.text(0.845, 0.5, "pre-registered\nstop threshold 0.85", ha="right", va="center", fontsize=6, color="#D55E00")
    ax.set_xlim(0, 1.02); ax.set_ylim(0, 1.02)
    ax.set_xlabel(r"largest component / $n_{\mathrm{drivers}}$")
    ax.set_ylabel("cumulative share of instances")
    ax.legend(loc="upper left", fontsize=6)
    save(fig, "figA3_t5_components")
    return "OK", chk


# ---------------------------------------------------------------- A4
def run_a4():
    chk = Checker("FIG A4 (synthetic)")
    t = D.d13_price_of_locality()
    chk.true("four audit lines n=3,5,7,9 parsed", list(t["n"]) == [3, 5, 7, 9], str(list(t["n"])))
    for r in t.itertuples():
        exp = sum(comb(r.n, k) for k in range(1, 4))
        chk.true("n=%d |K*|=|pool|=sum_{k<=3} C(n,k)" % r.n, r.kstar == r.pool == r.binom_sum == exp,
                 "%d %d %d %d" % (r.kstar, r.pool, r.binom_sum, exp))
        chk.true("n=%d gw never optimal" % r.n, r.optimal == 0 and r.certificate)
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(SINGLE, SINGLE * 0.75))
    ns = np.arange(3, 10)
    ax.plot(ns, [sum(comb(n, k) for k in range(1, 4)) for n in ns], color="black", lw=0.9,
            label=r"$\sum_{k=1}^{B}\binom{n}{k}$, $B=3$")
    ax.scatter(t["n"], t["kstar"], s=26, marker="o", facecolor=C["GW"], edgecolor="black", linewidths=0.5,
               zorder=3, label=r"observed $|\mathcal{K}^\star_g|$")
    ax.set_yscale("log")
    ax.set_xticks([3, 5, 7, 9]); cat_x(ax)
    ax.set_xlabel("number of orders $n$")
    ax.set_ylabel(r"routes of gigworker $g$ in $\mathcal{K}^\star$ (log scale)")
    ax.text(0.97, 0.05, "routes of $g$ optimal for any of\n%d sampled bid profiles: 0" % int(t["profiles"].iloc[0]),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5)
    ax.legend(loc="upper left", fontsize=6.5)
    save(fig, "figA4_synthetic_price_of_locality")
    return "OK", chk


# ---------------------------------------------------------------- A5
def run_a5():
    chk = Checker("FIG A5")
    d = D.d6()
    lv = [("V0_baseline", 15), ("V9_n25", 25), ("V10_n30", 30)]
    for (v, n), exp in zip(lv, E.FIGA5["median"]):
        s = d[d[K.VARIANT] == v]
        chk.close("median t_total %s" % v, float(np.median(s[K.T_TOTAL])), exp, 2, kind="time")
        chk.true("%s all <=300 s" % v, int((s[K.T_TOTAL] <= 300).sum()) == E.FIGA5["within300"])
    if not chk.ok():
        return "CHECK_FAIL", chk
    fig, ax = plt.subplots(figsize=figsize(SINGLE, SINGLE * 0.75))
    for i, (v, n) in enumerate(lv):
        s = d[d[K.VARIANT] == v]
        bp = ax.boxplot([s[K.T_TOTAL]], positions=[i], widths=0.45, whis=1.5, showfliers=False,
                        patch_artist=True, manage_ticks=False)
        bp["boxes"][0].set_facecolor(C["GW"]); bp["boxes"][0].set_alpha(0.35)
        bp["boxes"][0].set_edgecolor(C["GW"]); bp["boxes"][0].set_linewidth(0.8)
        for l in bp["medians"]:
            l.set_color("black"); l.set_linewidth(1.0)
        for l in bp["whiskers"] + bp["caps"]:
            l.set_color(C["GW"]); l.set_linewidth(0.7)
        r = np.random.default_rng(i)
        ax.scatter(i + r.uniform(-0.15, 0.15, len(s)), s[K.T_TOTAL], s=2.5, color=C["GW"], alpha=0.3, linewidths=0)
        ax.text(i, 400, "%d/%d optimal" % (int(s[K.N_OPT].sum()), int(s[K.N_SOLVES].sum())),
                ha="center", va="bottom", fontsize=6)
    ax.axhline(300, color="#D55E00", lw=0.8, ls="--")
    ax.set_xlim(-0.5, 2.5)
    ax.text(-0.38, 280, "300 s budget", ha="left", va="top", fontsize=6, color="#D55E00")
    ax.set_yscale("log"); ax.set_ylim(0.3, 900)
    ax.set_xticks(range(3)); ax.set_xticklabels(["$n=15$\n(V0)", "$n=25$\n(V9)", "$n=30$\n(V10)"]); cat_x(ax)
    ax.set_ylabel("full pipeline A+B+C per instance\n(s, log scale)")
    save(fig, "figA5_pipeline_scaling")
    return "OK", chk


# ---------------------------------------------------------------- A6, A7 (missing)
def run_a6():
    missing("FIG A6 — figA6_synthetic_label_rule_fd_price.pdf",
            "per-seed (or per-driver) label-extension saving and wall-clock speed-up of the label rule at "
            "FD price scales 0.6 / 1.0 / 1.4 (synthetic instances)",
            "New_t4/files/*.csv|*.json (only RQ1 timing files present); T4_Label_Rule.tex §'Work and time'; "
            "AUDIT_REPORT_LABEL_RULE.md §3.3",
            "Only a summary table exists: ranges 73–76% / 27–30% / 7–9% and speed-ups 2.8–3.1× / "
            "'≈1.0×' / 0.75×. The middle speed-up is not a number, so plotting it would be an estimate. "
            "Raw output of the synthetic runs was not saved; regenerating it = re-running the enumerator "
            "(forbidden by §0.1). Option: cite the table in text instead of a figure.")
    return "MISSING", None


def run_a7():
    missing("FIG A7 — figA7_single_parameter_menu.pdf",
            "bundle-menu (d(B), t(B)) points of a representative driver, angular deviation sigma_psi, "
            "welfare loss of the one-parameter projection",
            "whole repo except `Not Using (dont reed this folder)`",
            "The only files with sigma_psi / gap data (v9, v9_1 outputs) sit in "
            "`Not Using (dont reed this folder)`, which the user asked not to read. Not opened. "
            "If the user wants this figure, confirm that folder may be used as a data source.")
    return "MISSING", None


RUNS = [("A1", run_a1), ("A2", run_a2), ("A3", run_a3), ("A4", run_a4), ("A5", run_a5),
        ("A6", run_a6), ("A7", run_a7)]

if __name__ == "__main__":
    for name, f in RUNS:
        s, c = f()
        print(name, s, c.summary() if c else "", c.fails[:6] if c else "")
