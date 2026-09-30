"""Shared plot helpers: §3.2 box + mean-CI, §3.3 two-line alignment ticks."""
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import columns as K
import data as D
import expected as E
from stats import mean_boot_ci

_fd_cache = {}


def fd_rate_by_alignment():
    """Mean over instances of the JOINT (=B3) FD rate, per alignment (see DATA_MANIFEST)."""
    if not _fd_cache:
        b3 = D.d3()
        b3 = b3[b3[K.MENU] == "B3"]
        D.assert_unique(b3, K.KEY, "D3/B3")
        assert len(b3) == 1500
        for a, g in b3.groupby(K.ALIGN):
            _fd_cache[round(a, 2)] = float(g[K.FD_RATE].mean())
    return dict(_fd_cache)


def check_fd_ticks(chk):
    fd = fd_rate_by_alignment()
    for a, exp in zip(E.ALIGNS, E.FD_RATE["vals"]):
        chk.close("FD rate mean @%.2f" % a, fd[a], exp, E.FD_RATE["dec"])
    return fd


def cat_x(ax):
    """Categorical x axis: no minor ticks."""
    ax.tick_params(axis="x", which="minor", bottom=False, top=False)


def align_ticklabels(aligns, fd):
    return ["%.2f\nFD %.2f" % (a, fd[round(a, 2)]) for a in aligns]


def box_ci(ax, pos, values, color, width=0.22, strip=True, rng_seed=0, hollow=False, zorder=2):
    """§3.2: box = IQR, median line, whiskers 1.5 IQR, no fliers; faint strip if n<=300;
    diamond = mean with 95% bootstrap CI."""
    v = np.asarray(values, dtype=float)
    bp = ax.boxplot([v], positions=[pos], widths=width, whis=1.5, showfliers=False,
                    patch_artist=True, manage_ticks=False, zorder=zorder)
    for b in bp["boxes"]:
        b.set_facecolor("white" if hollow else color)
        b.set_alpha(1.0 if hollow else 0.35)
        b.set_edgecolor(color)
        b.set_linewidth(0.8)
    for k in ("whiskers", "caps"):
        for l in bp[k]:
            l.set_color(color); l.set_linewidth(0.7)
    for l in bp["medians"]:
        l.set_color(color if hollow else "black"); l.set_linewidth(1.0)
    if strip and len(v) <= 300:
        r = np.random.default_rng(rng_seed)
        ax.scatter(pos + r.uniform(-width * 0.35, width * 0.35, len(v)), v, s=2, color=color,
                   alpha=0.15, linewidths=0, zorder=zorder - 1)
    m, lo, hi = mean_boot_ci(v)
    ax.errorbar([pos], [m], yerr=[[m - lo], [hi - m]], fmt="D", ms=3, color="black",
                mfc=color, mec="black", mew=0.5, elinewidth=0.8, capsize=1.5, zorder=zorder + 2)
    return m, lo, hi


def box_ci_legend_handles():
    return [Patch(facecolor="#bbbbbb", edgecolor="#555555", label="box: IQR, line: median"),
            Line2D([], [], marker="D", color="black", mfc="#bbbbbb", ms=3, lw=0.8,
                   label="mean with 95% CI")]
