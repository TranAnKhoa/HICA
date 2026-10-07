"""Writes ../audit_logs3/report_h_part.md: report section on the dead-end filter (C5h, C8h), from saved results."""
import json
import os
import statistics

L3 = "../audit_logs3/"


def load(name):
    p = L3 + name
    return json.load(open(p)) if os.path.exists(p) else None


def label_block(rows, setting):
    out = ["| instance | B | C1 (s) | C5 (s) | C5h (s) | C8h = C5h + Layer 3 (s) | C5 vs C1 | C5h vs C1 | C5h vs C5 | C8h vs C5h | ext C5 | ext C5h | OD ext C5 -> C5h |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        c8h_vs_c5h = statistics.median([a / b for a, b in zip(r["C5h"]["raw"], r["C8h"]["raw"])])
        out.append("| %s | %d | %.3f | %.3f | %.3f | %.3f | %.2fx | %.2fx | %.2fx | %.2fx | %d | %d | %d -> %d |" % (
            r["tag"], r["B"], r["C1"]["t"], r["C5"]["t"], r["C5h"]["t"], r["C8h"]["t"],
            r["C5"]["x_vs_C1"], r["C5h"]["x_vs_C1"], r["C5h"]["x_vs_C5"], c8h_vs_c5h,
            r["C5"]["ext"], r["C5h"]["ext"], r["C5"]["ext_OD"], r["C5h"]["ext_OD"]))
    out.append("")
    for B in (3, 4):
        rb = [r for r in rows if r["B"] == B]
        if not rb:
            continue
        out.append("B=%d (%s): median per-instance speed-up C5h vs C1 %.2fx, C5h vs C5 %.2fx, C8h vs C5h %.2fx; "
                   "pooled C5h vs C1 %.2fx; extension attempts C5h vs C5 %.0f%% fewer." % (
                       B, setting,
                       statistics.median([r["C5h"]["x_vs_C1"] for r in rb]),
                       statistics.median([r["C5h"]["x_vs_C5"] for r in rb]),
                       statistics.median([statistics.median([a / b for a, b in zip(r["C5h"]["raw"], r["C8h"]["raw"])]) for r in rb]),
                       sum(r["C1"]["t"] for r in rb) / sum(r["C5h"]["t"] for r in rb),
                       100 * (1 - sum(r["C5h"]["ext"] for r in rb) / sum(r["C5"]["ext"] for r in rb))))
        out.append("")
    out.append("K* identical in every run: %s" % all(r[n]["kstar_equal"] for r in rows for n in ("C5", "C5h", "C8h", "C1")))
    out.append("")
    return out


def grid_block(rows, setting):
    out = ["| setting | alignment | C1 (s, sum) | C5 (s, sum) | C5h (s, sum) | C8h (s, sum) | C5 vs C1 | C5h vs C1 | C5h vs C5 | C8h vs C5h per instance: min / median / max | ext C5 -> C5h |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"]
    for al in (0.90, 0.50):
        rb = [r for r in rows if abs(r.get("alignment", 0) - al) < 1e-9]
        if not rb:
            continue
        s = lambda n: sum(r[n]["t"] for r in rb)
        sp = [statistics.median([a / b for a, b in zip(r["C5h"]["raw"], r["C8h"]["raw"])]) for r in rb]
        out.append("| %s | %.2f | %.2f | %.2f | %.2f | %.2f | %.2fx | %.2fx | %.2fx | %.2f / %.2f / %.2f | %d -> %d |" % (
            setting, al, s("C1"), s("C5"), s("C5h"), s("C8h"), s("C1") / s("C5"), s("C1") / s("C5h"), s("C5") / s("C5h"),
            min(sp), statistics.median(sp), max(sp), sum(r["C5"]["ext"] for r in rb), sum(r["C5h"]["ext"] for r in rb)))
    return out


def scale_block(rows):
    out = ["| instance | B | C1 (s) | C5 (s) | C5h (s) | C8h (s) | C5h vs C5 | C5h vs C1 | C8h vs C5h | ext C5 | ext C5h |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        c1 = r.get("C1")
        c8h_vs_c5h = statistics.median([a / b for a, b in zip(r["C5h"]["raw"], r["C8h"]["raw"])])
        out.append("| %s | %d | %s | %.2f | %.2f | %.2f | %.2fx | %s | %.2fx | %d | %d |" % (
            r["tag"], r["B"], ("%.2f" % c1["t"]) if c1 else "-", r["C5"]["t"], r["C5h"]["t"], r["C8h"]["t"],
            r["C5h"]["x_vs_C5"], ("%.2fx" % r["C5h"]["x_vs_C1"]) if c1 else "-", c8h_vs_c5h,
            r["C5"]["ext"], r["C5h"]["ext"]))
    out.append("")
    out.append("K* identical in every run: %s" % all(r[n]["kstar_equal"] for r in rows for n in ("C5", "C5h", "C8h")))
    return out


def main():
    md = []
    ol = load("timing_h_orig_label.json")
    if ol:
        md += ["#### Label instances, generator's travel-time function (`timing_h_orig_label.json`)", ""] + label_block(ol, "travel-time function")
    ml = load("timing_h_matrix_label.json")
    if ml:
        md += ["#### Label instances, shared travel-time table (`timing_h_matrix_label.json`)", ""] + label_block(ml, "shared table")
    og, mg = load("timing_h_orig_grid.json"), load("timing_h_matrix_grid.json")
    if og or mg:
        md += ["#### Main-grid sample, n=15, supply (3,3), B=3, reps 0-9 (`timing_h_*_grid.json`)", ""]
        rows = []
        if og:
            rows += grid_block(og, "travel-time function")
        if mg:
            g = grid_block(mg, "shared table")
            rows += g[2:] if rows else g
        md += rows + [""]
    sc = load("timing_h_matrix_scale.json")
    if sc:
        md += ["#### n = 20, shared travel-time table, 3 timed runs (`timing_h_matrix_scale.json`)", ""] + scale_block(sc) + [""]
    open(L3 + "report_h_part.md", "w").write("\n".join(md))
    print("\n".join(md))


main()
