"""Gates G1 (K* equal to C1), G2 (C4 R == C1 R), G4 (brute force n=5,6), G7 (in-loop K* == Frontier(R)),
plus an extra counterexample hunt for the in-loop hypothesis on random small instances.
Usage: python gate_equal.py  (writes ../audit_logs2/gate_equal.json and prints a summary)"""
import sys, json, time
from variants import *
import rq_common as RQ
import brute_force as BF

VARS = ["C3", "C4", "C5", "C6", "C7"]
rows = []
fails = []


def per_driver_sig(pool, d):
    return sig({d: pool[d]})


def check_instance(tag, tt, drivers, orders, q, B, extra=None):
    ref_R, ref_per = build_all("C1", tt, drivers, orders, q, B)
    ref_K = kstar_pool(ref_R, q)
    sref = sig(ref_R)
    row = dict(tag=tag, B=B, n_drivers=len(drivers), R_C1=len(sref), Kstar=len(sig(ref_K)))
    for nm in VARS:
        p, per = build_all(nm, tt, drivers, orders, q, B)
        K = p if nm in INLOOP else kstar_pool(p, q)
        bad = [d["id"] for d in drivers if per_driver_sig(K, d["id"]) != per_driver_sig(ref_K, d["id"])]
        row[nm + "_kstar_equal"] = not bad
        row[nm + "_bad_drivers"] = bad
        row[nm + "_routes_kept"] = len(sig(p))
        if nm == "C4":
            row["G2_R_equal"] = (sig(p) == sref)
            if sig(p) != sref:
                fails.append((tag, "G2", "C4"))
        if nm in ("C3", "C6"):
            s = sig(p)
            row[nm + "_R_subset_of_C1"] = s <= sref
            row[nm + "_extra_vs_C1"] = len(s - sref)
        if bad:
            fails.append((tag, "G1/G7", nm, bad))
            for d in bad:
                a, b = per_driver_sig(K, d), per_driver_sig(ref_K, d)
                row[nm + "_counterexample_" + d] = dict(variant_only=sorted(map(str, a - b))[:3],
                                                        c1_only=sorted(map(str, b - a))[:3])
    rows.append(row)
    ok = all(row[nm + "_kstar_equal"] for nm in VARS) and row["G2_R_equal"]
    print("%-22s B=%d | K*(C1)=%d | %s" % (tag, B, row["Kstar"],
          " ".join("%s:%s" % (nm, "ok" if row[nm + "_kstar_equal"] else "FAIL") for nm in VARS)),
          "| G2 R(C4)==R(C1):", row["G2_R_equal"])
    sys.stdout.flush()
    return ok


def main():
    allok = True
    # label instances, B = 3, 4
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            allok &= check_instance("label n%d_s%d" % (n, seed), tt, drivers, orders, q, B)
    # main-grid sample, B = 3
    for align in (0.90, 0.50):
        for rep in range(10):
            d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
            allok &= check_instance("grid a%.2f_rep%d" % (align, rep), tt, d, o, q, 3)
    # G4: brute force (n=5,6; 3 seeds each)
    g4 = []
    for n in (5, 6):
        for seed in range(3):
            drivers, orders, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4,
                                                             seed=seed, tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(orders, tt)
            bf = {dr["id"]: BF.brute_pool_for_driver(tt, dr, orders, 3, 3) for dr in drivers}
            kb = sig(kstar_pool(bf, q))
            r = dict(n=n, seed=seed, K_brute=len(kb))
            for nm in ["C1"] + VARS:
                p, per = build_all(nm, tt, drivers, orders, q, 3)
                K = p if nm in INLOOP else kstar_pool(p, q)
                r[nm] = (sig(K) == kb)
                if sig(K) != kb:
                    fails.append(("brute n%d s%d" % (n, seed), "G4", nm))
            g4.append(r)
            print("G4 brute n=%d seed=%d K*(brute)=%d  %s" % (n, seed, len(kb),
                  " ".join("%s:%s" % (k, "ok" if v else "FAIL") for k, v in r.items() if k.startswith("C"))))
            sys.stdout.flush()
    # extra hunt for counterexamples to the in-loop hypothesis (and to FD-dominance): random small instances
    hunt = dict(instances=0, drivers=0, mismatches=0)
    for n in (6, 7, 8, 9):
        for seed in range(100, 120):
            drivers, orders, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4,
                                                             seed=seed, tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(orders, tt)
            R, _ = build_all("C1", tt, drivers, orders, q, 3)
            K = kstar_pool(R, q)
            for nm in ("C5", "C6", "C7"):
                p, _ = build_all(nm, tt, drivers, orders, q, 3)
                Kv = p if nm in INLOOP else kstar_pool(p, q)
                for d in drivers:
                    hunt["drivers"] += 1
                    if sig({d["id"]: Kv[d["id"]]}) != sig({d["id"]: K[d["id"]]}):
                        hunt["mismatches"] += 1
                        fails.append(("hunt n%d s%d" % (n, seed), nm, d["id"]))
            hunt["instances"] += 1
    print("HUNT (random n=6..9, 80 instances, B=3; C5,C6,C7 vs Frontier(R_C1)):", hunt)
    json.dump(dict(rows=rows, g4=g4, hunt=hunt, fails=[list(map(str, f)) for f in fails]),
              open("../audit_logs2/gate_equal.json", "w"), indent=1)
    print("\nG1/G2/G7 on label+grid instances:", "PASS" if allok else "FAIL",
          "| G4:", "PASS" if all(all(v for k, v in r.items() if k.startswith("C")) for r in g4) else "FAIL",
          "| hunt mismatches:", hunt["mismatches"], "| fails:", len(fails))


main()
