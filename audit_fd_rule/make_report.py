import json, statistics
L = json.load(open("../audit_logs/timing_label.json")); G = json.load(open("../audit_logs/timing_grid.json"))
W = json.load(open("../audit_logs/wdp_equality.json"))
f = lambda x: float(x)
o = []
o.append("### Table A: work saved (label-rule instances; ext = calls to _try_pickup/_try_delivery/_try_home)\n")
o.append("| instance | B | ext C1 | ext C2 | saved % | killed_layer3 | routes_layer2 C1 | routes_layer2 C2 | routes_kstar C1 / C2 (identical) |\n|---|---|---|---|---|---|---|---|---|")
for r in L:
    o.append("| %s | %d | %s | %s | %.1f | %s | %s | %s | %s / %s (%s) |" % (r["tag"], r["B"], r["ext_C1"], r["ext_C2"], 100*(1-f(r["ext_C2"])/f(r["ext_C1"])), r["killed_L3_C2"], r["L2_C1"], r["L2_C2"], r["kstar_C1"], r["kstar_C2"], r["kstar_identical"]))
o.append("\n### Table B: time (s, median of 10 alternating runs; t_total = t_A + t_F)\n")
o.append("| instance | B | t_A C1 | t_A C2 | t_F C1 | t_F C2 | t_total C1 | t_total C2 | speed-up C1/C2 total [IQR] |\n|---|---|---|---|---|---|---|---|---|")
for r in L:
    o.append("| %s | %d | %.3f | %.3f | %.4f | %.4f | %.3f | %.3f | %.2f [%s] |" % (r["tag"], r["B"], f(r["tA_C1"]), f(r["tA_C2"]), f(r["tF_C1"]), f(r["tF_C2"]), f(r["tTot_C1"]), f(r["tTot_C2"]), f(r["speedup_median"]), r["speedup_iqr"]))
for B in (3, 4):
    rs = [r for r in L if r["B"] == B]; n = len(rs[0]["_raw"]["C1A"]) if isinstance(rs[0]["_raw"], dict) else 0
    raw = [r["_raw"] for r in rs]
    pooled = [sum(x["C1A"][i] + x["C1F"][i] for x in raw) / sum(x["C2A"][i] + x["C2F"][i] for x in raw) for i in range(len(raw[0]["C1A"]))]
    o.append("\nB=%d: median per-instance speed-up %.2f; pooled total-time ratio (C1/C2) median %.2f" % (B, statistics.median([f(r["speedup_median"]) for r in rs]), statistics.median(pooled)))
o.append("\n### Table C: equality C1 vs C2 (K* pools, 20 profiles: truthful + 19 uniform[18,25]; CPLEX 12.10)\n")
o.append("| instance | B | K* identical? | max abs dV | max abs dV_-k | max abs dPayment | allocation identical? (ties?) |\n|---|---|---|---|---|---|---|")
for r in W:
    o.append("| %s | %d | %s | %.1e | %.1e | %.1e | %s (differs in %d profiles, %d of them equal-Z ties) |" % (r["inst"], r["B"], r["kstar_identical"], r["max_dV"], r["max_dVk"], r["max_dPay"], "yes" if r["alloc_diff"] == 0 else "NO", r["alloc_diff"], r["alloc_diff_with_equal_Z"]))
o.append("\n### Table D: main-grid sample (n=15, supply (3,3), B=3, reps 0-9; sums over 10 instances)\n")
o.append("| alignment | ext C1 | ext C2 | saved % | routes_L2 C1 | routes_L2 C2 | K* C1 / C2 | t_A C1 | t_A C2 | t_F C1 | t_F C2 | t_total C1 | t_total C2 | ratio C1/C2 | drivers with rule fired GW | OD |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for a in (0.9, 0.5):
    r = [x for x in G if x["alignment"] == a]; s = lambda k: sum(f(x[k]) for x in r)
    o.append("| %.2f | %d | %d | %.1f | %d | %d | %d / %d | %.2f | %.2f | %.3f | %.3f | %.2f | %.2f | %.2f | %d/%d | %d/%d |" % (a, s("ext_C1"), s("ext_C2"), 100*(1-s("ext_C2")/s("ext_C1")), s("L2_C1"), s("L2_C2"), s("kstar_C1"), s("kstar_C2"), s("tA_C1"), s("tA_C2"), s("tF_C1"), s("tF_C2"), s("tTot_C1"), s("tTot_C2"), s("tTot_C1")/s("tTot_C2"), s("drivers_fired_GW"), s("n_GW"), s("drivers_fired_OD"), s("n_OD")))
o.append("\nK* identical on every one of the 20 grid instances: %s" % all(x["kstar_identical"] in (True, "True") for x in G))
open("../audit_logs/tables.md", "w").write("\n".join(o)); print("\n".join(o))
