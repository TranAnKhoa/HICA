"""Writes ../audit_logs3/report_c8_part.md: report sections 4-5 (C8) generated from the saved results."""
import json
import statistics

import make_tables_c8 as mt

L3 = "../audit_logs3/"


def gridsum(f):
    rows = json.load(open(L3 + f))
    out = []
    for al in (0.9, 0.5):
        rb = [r for r in rows if abs(r['alignment'] - al) < 1e-9]
        sp = [r['C8f']['speedup_vs_C5'] for r in rb]
        out.append((al, sum(r['C1']['tTot'] for r in rb) / sum(r['C5']['tTot'] for r in rb),
                    sum(r['C5']['tTot'] for r in rb) / sum(r['C8f']['tTot'] for r in rb),
                    min(sp), statistics.median(sp), max(sp), sum(1 for x in sp if x > 1),
                    sum(r['C5']['ext'] for r in rb), sum(r['C8f']['ext'] for r in rb)))
    return out


def main():
    kd = json.load(open(L3 + 'kill_depth.json'))
    ex = json.load(open(L3 + 'explore_open_policy.json'))
    lines = ["## 4. Timing of C8 (Layer 3 added to C5)", "",
             "Machine: Intel Xeon @ 2.10 GHz (cloud container, 4 cores, one used), Linux, Python 3.13.16. The ranking of",
             "C1, C3, C4, C5 and C7 reproduces `EXPERIMENT_REPORT.md` (Ryzen, Windows, Python 3.7): e.g. C5 is 1.21-1.24x",
             "faster than C1 at B=3 here (1.15-1.23x there) and 1.30-1.46x at B=4 (1.33-1.43x there). Protocol of",
             "`audit_fd_rule2/timing.py`: one warm-up, 10 timed runs per variant in alternating order, gc disabled, medians",
             "of the paired ratios. Every time is the time to K\\* (C1 includes its post-hoc frontier).", "",
             "### 4.1 Label instances (`timing_orig_label.json`, `timing_matrix_label.json`)", ""]
    lines += mt.compact()
    lines += ["",
              "Ratios are medians of paired per-run ratios; a value below 1 in the last three columns means **slower than C5**.",
              "The last column is the fair setting in which every variant reads the same precomputed travel-time table.",
              "C8 is never faster than C5: 0.60-0.80x. Even the fast implementation C8f stays below C5 on every one of the",
              "10 configurations: 0.75-0.95x with the generator's travel-time function, 0.73-0.89x when all variants share the table.",
              ""]
    lines += mt.work_table(mt.load('timing_orig_label.json'), ["C1", "C3", "C4", "C5", "C7", "C8", "C8f"])
    lines += ["Layer 3 does what it promises on work: 14.5-32.2% fewer extension attempts than C5 with K\\* unchanged. The time",
              "it costs to test every surviving label is larger than the time those extensions would have taken.", "",
              "### 4.2 Main-grid sample (n=15, supply (3,3), B=3, reps 0-9; 5 timed runs; `timing_*_grid.json`)", "",
              "| setting | alignment | C5 vs C1 (pooled) | C8f vs C5 (pooled) | C8f vs C5 per instance: min / median / max | instances where C8f is faster | ext C5 -> C8f (sum) |",
              "|---|---|---:|---:|---|---:|---|"]
    for f, name in (('timing_orig_grid.json', 'travel-time function'), ('timing_matrix_grid.json', 'shared table')):
        for (al, c5c1, c8c5, mn, md, mx, nf, e5, e8) in gridsum(f):
            lines.append("| %s | %.2f | %.2fx | %.2fx | %.2f / %.2f / %.2f | %d of 10 | %d -> %d (-%.0f%%) |" % (
                name, al, c5c1, c8c5, mn, md, mx, nf, e5, e8, 100 * (1 - e8 / e5)))
    lines += ["",
              "Where the crowd competes (alignment 0.90), Layer 3 removes 23-47% of the extensions and C8f breaks even with C5",
              "on aggregate (faster on about half of the instances, slower on the other half). Where the fixed fleet dominates",
              "(alignment 0.50), it is slower on every instance. Full tables: `audit_logs3/tables_c8.md`.", "",
              "## 5. Why Layer 3 does not pay: where it fires", "",
              "For every label removed by Layer 3 in C8 we recorded |P(L)| = |IV| + |C| (`kill_depth.py`, `kill_depth.json`).", "",
              "| instance | B | labels removed by Layer 3 | share with \\|P(L)\\| = B | share with nothing on board |",
              "|---|---|---:|---:|---:|"]
    for r in kd:
        lines.append("| %s | %d | %d | %.1f%% | %.1f%% |" % (r['tag'], r['B'], r['kills'], 100 * r['share_full'],
                                                          100 * r['share_no_order_on_board']))
    lines += ["",
              "94.7-98.7% of the labels that Layer 3 removes already carry B orders (|P(L)| = B: no further pickup is",
              "possible). Such a label can only be followed by its remaining deliveries (and, for an occasional driver, the",
              "home leg), so each removal saves a handful of extensions. The test, however, runs on every label that survives",
              "Layer 1, and the shortcut states cost O(B) per label. The bound of Definition 3 becomes strong only late, when",
              "the detour spent on an order is known, which is exactly where pruning is worth least. The decision-identical",
              "fast implementation C8f narrows the gap but does not close it, so this is a property of the rule on these",
              "instances rather than of one implementation.", "",
              "### 5.1 Exploratory: test only labels that can still pick up an order (`explore_open_policy.py`)", "",
              "Chosen **after** seeing the table above, so it is exploratory. Applying Layer 3 only when |P(L)| < B keeps K\\*",
              "(Theorem 3 allows the rule on any subset of labels), but it removes few labels (1-5% of those",
              "that C8f removes) and is slower than C5 on 9 of the 10 configurations (0.86-0.96x; 1.04x on n10_s1 at B=3, within",
              "run-to-run noise). Shared travel-time table, 5 runs:", "",
              "| instance | B | C5 (s) | C8f (s) | C8open (s) | ext C5 | ext C8open | Layer-3 removals in C8open | C8open vs C5 |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in ex:
        lines.append("| %s | %d | %.3f | %.3f | %.3f | %d | %d | %d | %.2fx |" % (
            r['tag'], r['B'], r['C5']['t'], r['C8f']['t'], r['C8open']['t'], r['C5']['ext'], r['C8open']['ext'],
            r['C8open']['kills'], r['C8open_vs_C5']))
    lines.append("")
    open(L3 + 'report_c8_part.md', 'w').write("\n".join(lines))
    print("\n".join(lines))


main()
