"""Check of the scale-study pipeline (C5h + HiGHS) against the paper's recorded results (production Algorithm A +
CPLEX 12.10, spec_2a_2b/results/rq_all/rq34_shard*.csv): the optimal value Z and the total VCG payout must agree.
Theorem 1(a) and Corollary 1 say that the frontier changes neither. Instances: rep 0-1 of every (alignment, n, supply)
cell present in the files. Output: ../audit_logs3/check_highs.log."""
import csv
import glob
import os

import paths  # noqa: F401
import variants_h as VH
import rq_common as RQ
import wdp_highs as WH

HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for f in sorted(glob.glob(os.path.join(HERE, "..", "spec_2a_2b", "results", "rq_all", "rq34_shard*.csv"))):
    rows += list(csv.DictReader(open(f)))
sel = [r for r in rows if int(r["rep"]) in (0, 1)]
worst_z, worst_p, bad = 0.0, 0.0, 0
for r in sel:
    a, n, ng, no, rep = float(r["alignment"]), int(r["n"]), int(r["n_gw"]), int(r["n_od"]), int(r["rep"])
    d, o, tt, meta, th, q = RQ.make_rq1_instance(a, n, ng, no, rep, B=3)
    pool = {dr["id"]: VH.run_tier_h(tt, dr, o, 3, q=q, inloop=True)[0] for dr in d}
    v = WH.vcg(pool, th, q, sorted(o))
    # payout as in rq_common.vcg: payments to winners + FD prices of the orders sent to FD
    base = WH.solve_wdp(pool, th, q, sorted(o))
    payout = sum(v["pay"].values()) + sum(q[x] for x in base["fd"])
    dz = abs(v["Z"] - float(r["Z"]))
    dp = abs(payout - float(r["vcg_payout"]))
    worst_z, worst_p = max(worst_z, dz), max(worst_p, dp)
    ok = dz < 1e-6 and dp < 1e-6 and all(s == "Optimal" for s in v["statuses"])
    bad += not ok
    print("a%.2f n%d (%d,%d) rep%d | Z %.6f vs %.6f | payout %.6f vs %.6f | %s" % (
        a, n, ng, no, rep, v["Z"], float(r["Z"]), payout, float(r["vcg_payout"]), "OK" if ok else "MISMATCH"), flush=True)
print("SUMMARY: %d instances, %d mismatches, max |dZ| %.2e, max |d payout| %.2e" % (len(sel), bad, worst_z, worst_p))
