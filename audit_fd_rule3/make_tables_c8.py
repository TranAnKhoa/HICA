"""Markdown tables for EXPERIMENT_REPORT_C8.md from ../audit_logs3/timing_*.json (no hand copying)."""
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(os.path.dirname(HERE), "audit_logs3")


def load(name):
    p = os.path.join(LOGS, name)
    return json.load(open(p)) if os.path.exists(p) else None


def pooled(rows, nm, ref):
    a = sum(r[ref]["tTot"] for r in rows)
    b = sum(r[nm]["tTot"] for r in rows)
    return a / b


def label_table(rows, names, title):
    out = ["### " + title, ""]
    hdr = "| instance | B | " + " | ".join("%s total (s)" % n for n in names) + " | " + \
          " | ".join("%s x vs C1" % n for n in names if n != "C1") + " | " + \
          " | ".join("%s x vs C5" % n for n in names if n not in ("C1", "C5")) + " |"
    out.append(hdr)
    out.append("|" + "---|" * (2 + len(names) + (len(names) - 1) + (len(names) - 2)))
    for r in rows:
        cells = ["%.3f" % r[n]["tTot"] for n in names]
        cells += ["%.2f [%.2f-%.2f]" % (r[n]["speedup_vs_C1"], r[n]["speedup_iqr"][0], r[n]["speedup_iqr"][1])
                  for n in names if n != "C1"]
        cells += ["%.2f [%.2f-%.2f]" % (r[n]["speedup_vs_C5"], r[n]["speedup_vs_C5_iqr"][0],
                                        r[n]["speedup_vs_C5_iqr"][1]) for n in names if n not in ("C1", "C5")]
        out.append("| %s | %d | " % (r["tag"], r["B"]) + " | ".join(cells) + " |")
    out.append("")
    for B in sorted(set(r["B"] for r in rows)):
        rb = [r for r in rows if r["B"] == B]
        out.append("B=%d: median per-instance speed-up vs C1: %s; pooled ratio of totals vs C1: %s; "
                   "median per-instance speed-up vs C5: %s" % (
                       B,
                       ", ".join("%s %.2f" % (n, statistics.median([r[n]["speedup_vs_C1"] for r in rb]))
                                 for n in names if n != "C1"),
                       ", ".join("%s %.2f" % (n, pooled(rb, n, "C1")) for n in names if n != "C1"),
                       ", ".join("%s %.2f" % (n, statistics.median([r[n]["speedup_vs_C5"] for r in rb]))
                                 for n in names if n not in ("C1", "C5"))))
        out.append("")
    out.append("K* identical to C1 in every run: %s" % all(r[n]["kstar_equal_C1"] for r in rows for n in names))
    out.append("")
    return out


def work_table(rows, names):
    out = ["### Work (extension attempts; sums over all drivers)", "",
           "| instance | B | " + " | ".join("ext %s" % n for n in names) + " | rule kills (C8) | A evaluations (C8) | ext saved C8 vs C5 |",
           "|" + "---|" * (2 + len(names) + 3)]
    for r in rows:
        out.append("| %s | %d | " % (r["tag"], r["B"]) + " | ".join("%d" % r[n]["ext"] for n in names) +
                   " | %d | %d | %.1f%% |" % (r["C8f"]["killed_rule"], r["C8f"]["a_evals"],
                                              100.0 * (1 - r["C8f"]["ext"] / r["C5"]["ext"])))
    out.append("")
    return out


def grid_table(rows, names, title):
    out = ["### " + title, "", "| alignment | " + " | ".join("%s t_total (s, sum)" % n for n in names) +
           " | " + " | ".join("%s pooled x vs C1" % n for n in names if n != "C1") +
           " | " + " | ".join("%s median x vs C5" % n for n in names if n not in ("C1", "C5")) + " |",
           "|" + "---|" * (1 + len(names) + (len(names) - 1) + (len(names) - 2))]
    for al in (0.90, 0.50):
        rb = [r for r in rows if abs(r["alignment"] - al) < 1e-9]
        out.append("| %.2f | " % al + " | ".join("%.2f" % sum(r[n]["tTot"] for r in rb) for n in names) + " | " +
                   " | ".join("%.2f" % pooled(rb, n, "C1") for n in names if n != "C1") + " | " +
                   " | ".join("%.2f" % statistics.median([r[n]["speedup_vs_C5"] for r in rb])
                              for n in names if n not in ("C1", "C5")) + " |")
    out.append("")
    out.append("K* identical to C1 on every grid instance: %s" % all(r[n]["kstar_equal_C1"] for r in rows for n in names))
    out.append("")
    return out


def main():
    md = []
    ol = load("timing_orig_label.json")
    if ol:
        names = ["C1", "C3", "C4", "C5", "C7", "C8", "C8f"]
        md += label_table(ol, names, "Table B1: label instances, original travel-time function (as in EXPERIMENT_REPORT.md)")
        md += work_table(ol, names)
    ml = load("timing_matrix_label.json")
    if ml:
        md += label_table(ml, ["C1", "C4", "C5", "C8f"],
                          "Table B2: label instances, precomputed travel-time table for every variant")
    og = load("timing_orig_grid.json")
    if og:
        md += grid_table(og, ["C1", "C3", "C4", "C5", "C7", "C8", "C8f"],
                         "Table D1: main-grid sample (n=15, supply (3,3), B=3, reps 0-9), original travel-time function")
    mg = load("timing_matrix_grid.json")
    if mg:
        md += grid_table(mg, ["C1", "C4", "C5", "C8f"],
                         "Table D2: main-grid sample, precomputed travel-time table for every variant")
    open(os.path.join(LOGS, "tables_c8.md"), "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()


def compact():
    """Compact table: per instance, time to K* of C1, C5, C8, C8f (orig setting) and C8f (matrix), ratios vs C5."""
    ol = load("timing_orig_label.json")
    ml = load("timing_matrix_label.json")
    if not ol:
        return []
    mm = {(r["tag"], r["B"]): r for r in (ml or [])}
    out = ["| instance | B | C1 (s) | C5 (s) | C8 = C5 + Layer 3 (s) | C8f, fast rule code (s) | C5 vs C1 | C8 vs C5 | C8f vs C5 | C8f vs C5, shared table |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in ol:
        m = mm.get((r["tag"], r["B"]))
        out.append("| %s | %d | %.3f | %.3f | %.3f | %.3f | %.2fx | %.2fx | %.2fx | %s |" % (
            r["tag"], r["B"], r["C1"]["tTot"], r["C5"]["tTot"], r["C8"]["tTot"], r["C8f"]["tTot"],
            r["C5"]["speedup_vs_C1"], r["C8"]["speedup_vs_C5"], r["C8f"]["speedup_vs_C5"],
            ("%.2fx" % m["C8f"]["speedup_vs_C5"]) if m else "-"))
    return out


if __name__ == "__main__":
    print("\n".join(compact()))
