"""Figure.md §5 — run every figure script; print and store the summary table.
Also writes figures/captions.tex and grayscale previews (QA, §7) for saved figures."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks
import discover
import fig_c1, fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, figA
from style import FIG_DIR

JOBS = [
    ("C1", "fig_c1_frontier_intuition", fig_c1.run), ("1", "fig01_pool_growth", fig01.run),
    ("2", "fig02_runtime_breakdown", fig02.run), ("3", "fig03_payment_speedup", fig03.run),
    ("4", "fig04_label_rule", fig04.run), ("5", "fig05_rq1_complementarity", fig05.run),
    ("5b", "fig05b_sequential", fig05.run_b), ("6", "fig06_rq2_bundling", fig06.run),
    ("7", "fig07_rq3_mechanisms", fig07.run), ("8", "fig08_regimes_certificate", fig08.run),
    ("9", "fig09_rq5_forest", fig09.run),
    ("A1", "figA1_kstar_build_vs_pool", figA.run_a1), ("A2", "figA2_pool_compression", figA.run_a2),
    ("A3", "figA3_t5_components", figA.run_a3), ("A4", "figA4_synthetic_price_of_locality", figA.run_a4),
    ("A5", "figA5_pipeline_scaling", figA.run_a5), ("A6", "figA6_synthetic_label_rule_fd_price", figA.run_a6),
    ("A7", "figA7_single_parameter_menu", figA.run_a7),
]


def gray_previews(names):
    from PIL import Image
    gdir = os.path.join(FIG_DIR, "_gray")
    os.makedirs(gdir, exist_ok=True)
    for n in names:
        p = os.path.join(FIG_DIR, n + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("L")
            im.thumbnail((2000, 2000))
            im.save(os.path.join(gdir, n + "_gray.png"))


def main():
    discover.main()
    checks.reset_logs()
    # remove stale outputs so a failing figure can never leave an old file behind
    for _, name, _ in JOBS:
        for ext in (".pdf", ".png"):
            p = os.path.join(FIG_DIR, name + ext)
            if os.path.exists(p):
                os.remove(p)
    rows, ok_names = [], []
    for fid, name, f in JOBS:
        try:
            status, chk = f()
        except Exception as e:  # report, never hide
            status, chk = "ERROR: %s" % e, None
        note = ""
        if chk is not None and chk.fails:
            note = "; ".join(chk.fails)
        rows.append((fid, name, status, chk.summary() if chk else "-", note))
        if status == "OK":
            ok_names.append(name)
    gray_previews(ok_names)
    lines = ["| Figure | File | Status | Checks passed | Notes |", "|---|---|---|---|---|"]
    lines += ["| %s | `%s` | %s | %s | %s |" % r for r in rows]
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(FIG_DIR, "STATUS.md"), "w", encoding="utf-8") as fh:
        fh.write("# Figure run status\n\n" + txt + "\n")


if __name__ == "__main__":
    main()
