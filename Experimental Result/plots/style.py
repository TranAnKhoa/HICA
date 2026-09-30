"""Figure.md §1.3–1.4 — shared style: SciencePlots base, Elsevier sizes, Okabe–Ito palette."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  (registers the "science" styles)

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(os.path.dirname(HERE), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

MM = 1 / 25.4
SINGLE, ONEHALF, DOUBLE = 90 * MM, 140 * MM, 190 * MM
ASPECT = 0.62

plt.style.use(["science", "no-latex"])
plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "lines.linewidth": 1.0, "lines.markersize": 3.5,
    "axes.grid": True, "axes.grid.axis": "y", "grid.alpha": 0.3, "grid.linewidth": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "legend.frameon": False,
    "figure.dpi": 150,
})

# §1.4 fixed encodings
C = {
    "GW": "#0072B2", "OD": "#D55E00", "FD": "#7F7F7F",
    "B1": "#CCCCCC", "B2": "#56B4E9", "B3": "#0072B2", "B4": "#003B5C", "HEUR": "#E69F00",
    "ORACLE": "#000000", "VCG": "#0072B2", "PAB": "#009E73", "POSTED": "#CC79A7",
    "n10": "#9ecae1", "n15": "#4292c6", "n20": "#08519c",
    "REG050": "#7F7F7F", "REG090": "#0072B2",
}
MK = {
    "GW": "o", "OD": "s", "FD": "^",
    "B1": ".", "B2": "v", "B3": "o", "B4": "D", "HEUR": "x",
    "ORACLE": "*", "VCG": "o", "PAB": "s", "POSTED": "^",
    "n10": "o", "n15": "s", "n20": "D",
}
LS = {"GW": "-", "OD": "--", "FD": ":", "HEUR": "-.", "B2": "-", "B3": "-", "B4": "-"}
LABEL = {"B1": "$B{=}1$", "B2": "$B{=}2$", "B3": "$B{=}3$", "B4": "$B{=}4$", "HEUR": "HEUR",
         "VCG": "VCG", "PAB": "PAB-BR", "POSTED": "Posted price", "ORACLE": "First-best"}
N_COLORS = {10: C["n10"], 15: C["n15"], 20: C["n20"]}
N_MARKERS = {10: "o", 15: "s", 20: "D"}


def figsize(width, height=None, ratio=ASPECT):
    return (width, height if height is not None else width * ratio)


def panel_label(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, "(%s)" % letter, transform=ax.transAxes, fontweight="bold",
            fontsize=8, ha="right", va="bottom")


def save(fig, name):
    """Write PDF (vector) + PNG (600 dpi). Returns the two paths."""
    pdf = os.path.join(FIG_DIR, name + ".pdf")
    png = os.path.join(FIG_DIR, name + ".png")
    fig.savefig(pdf)
    fig.savefig(png, dpi=600)
    plt.close(fig)
    return pdf, png
