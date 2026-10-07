"""Build Tables A-D (+ closeness-to-K*) as Markdown from the saved JSON logs -> ../audit_logs2/tables.md"""
import json, statistics
L = json.load(open("../audit_logs2/timing_label.json"))
G = json.load(open("../audit_logs2/timing_grid.json"))
P1 = json.load(open("../audit_logs2/phase1_ceiling.json"))
P2 = json.load(open("../audit_logs2/phase1_after_tier.json"))
CFG = ["C1", "C3", "C4", "C5", "C6", "C7"]
out = []
def w(s=""): out.append(s)

w("### Table A: work (label-rule instances; sums over all drivers of the instance)\n")
w("| instance | B | ext C1 | ext C3 | ext C4 | ext C6 | killed by FD-dominance (C6) | killed by Layer 1 C1 | killed by Layer 1 C4 | routes kept R: C1 / C4 / C6 | K* (C5=C7=C1) |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|")
for r in L:
    w("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %d / %d / %d | %d |" % (
        r["tag"], r["B"], r["C1"]["ext"], r["C3"]["ext"], r["C4"]["ext"], r["C6"]["ext"],
        r["C6"]["killed_rule"], r["C1"]["killed_L1"], r["C4"]["killed_L1"],
        r["C1"]["routes_kept"], r["C4"]["routes_kept"], r["C6"]["routes_kept"], r["C1"]["kstar"]))
w("\nExtension savings vs C1 (percent): ")
w("\n| instance | B | C3 | C4 | C6 |\n|---|---|---:|---:|---:|")
for r in L:
    w("| %s | %d | %.1f | %.1f | %.1f |" % (r["tag"], r["B"], *[100 * (1 - r[k]["ext"] / r["C1"]["ext"]) for k in ("C3", "C4", "C6")]))

w("\n### Table B: time (s, median of the timed runs; t_total = t_A + t_F; speed-up = median of paired t_total(C1)/t_total(variant), >1 = variant faster)\n")
w("| instance | B | reps | C1 t_A | C1 t_F | C1 total | C3 total | C4 total | C5 total | C6 total | C7 total | C3 x | C4 x | C5 x | C6 x | C7 x |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in L:
    w("| %s | %d | %d | %.3f | %.4f | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %s |" % (
        r["tag"], r["B"], r["reps"], r["C1"]["tA"], r["C1"]["tF"], r["C1"]["tTot"],
        *[r[k]["tTot"] for k in ("C3", "C4", "C5", "C6", "C7")],
        " | ".join("%.2f [%.2f-%.2f]" % (r[k]["speedup_vs_C1"], *r[k]["speedup_iqr"]) for k in ("C3", "C4", "C5", "C6", "C7"))))
w("")
for B in (3, 4):
    rs = [r for r in L if r["B"] == B]
    med = {k: statistics.median([r[k]["speedup_vs_C1"] for r in rs]) for k in CFG[1:]}
    pooled = {k: sum(r["C1"]["tTot"] for r in rs) / sum(r[k]["tTot"] for r in rs) for k in CFG[1:]}
    w("B=%d: median per-instance speed-up %s ; pooled ratio of total times %s" % (
        B, ", ".join("%s %.2f" % (k, v) for k, v in med.items()), ", ".join("%s %.2f" % (k, v) for k, v in pooled.items())))

w("\n### Table C: ceiling vs reality (wasted_share = wasted_children / ext_attempts)\n")
w("| B | instance | wasted_share C1 (Phase 1.3) | wasted_share after tiering (C4) | cross-batch pairs C1 | after tiering | duplicates expanded after |")
w("|---|---|---:|---:|---:|---:|---:|")
for a in P1:
    b = [x for x in P2 if x["B"] == a["B"] and x["inst"] == a["inst"]][0]
    w("| %d | %s | %.2f%% | %.2f%% | %d | %d | %d |" % (a["B"], a["inst"], 100 * a["wasted_share"], 100 * b["wasted_share"],
                                                       a["cross_batch_pairs"], b["cross_batch_pairs"], b["dup_expanded"]))

w("\n### Table D: main-grid sample (n=15, supply (3,3), B=3, reps 0-9; sums over 10 instances per alignment)\n")
w("| alignment | variant | ext | t_A | t_F | t_total | ratio C1/variant (pooled) | median per-instance ratio | routes kept | K* equal on all | FD fired GW drivers | FD fired OD drivers |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
for al in (0.90, 0.50):
    rs = [r for r in G if r["alignment"] == al]
    base = sum(r["C1"]["tTot"] for r in rs)
    for k in CFG:
        tA = sum(r[k]["tA"] for r in rs); tF = sum(r[k]["tF"] for r in rs); tot = sum(r[k]["tTot"] for r in rs)
        med = statistics.median([r[k]["speedup_vs_C1"] for r in rs])
        fg = sum(r[k]["fired_GW"] for r in rs); ng = sum(r[k]["n_GW"] for r in rs)
        fo = sum(r[k]["fired_OD"] for r in rs); no = sum(r[k]["n_OD"] for r in rs)
        w("| %.2f | %s | %d | %.2f | %.3f | %.2f | %.2f | %.2f | %d | %s | %s | %s |" % (
            al, k, sum(r[k]["ext"] for r in rs), tA, tF, tot, base / tot, med, sum(r[k]["routes_kept"] for r in rs),
            all(r[k]["kstar_equal_C1"] for r in rs), ("%d/%d" % (fg, ng)) if k in ("C3", "C6", "C7") else "-",
            ("%d/%d" % (fo, no)) if k in ("C3", "C6", "C7") else "-"))

w("\n### Closeness to K*: |routes kept| / |K*|\n")
w("| set | C1 | C3 | C6 | C5 / C7 |\n|---|---:|---:|---:|---|")
for B in (3, 4):
    rs = [r for r in L if r["B"] == B]
    f = lambda k: sum(r[k]["routes_kept"] for r in rs) / sum(r["C1"]["kstar"] for r in rs)
    w("| label instances B=%d (pooled) | %.2f | %.2f | %.2f | 1 |" % (B, f("C1"), f("C3"), f("C6")))
for al in (0.90, 0.50):
    rs = [r for r in G if r["alignment"] == al]
    f = lambda k: sum(r[k]["routes_kept"] for r in rs) / sum(r["C1"]["kstar"] for r in rs)
    w("| grid alignment %.2f (pooled) | %.2f | %.2f | %.2f | 1 |" % (al, f("C1"), f("C3"), f("C6")))
open("../audit_logs2/tables.md", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
