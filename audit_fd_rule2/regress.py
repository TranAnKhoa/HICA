"""STOP 2 regression: C1 == production dp_labeling.run_pool ; C4 (rule off) R == C1 R. Plus a K* smoke test."""
import sys, time
from variants import *
ok1 = ok4 = True
smoke = {}
for B in (3, 4):
    for (n, nd, seed) in LABEL_INSTANCES:
        drivers, orders, tt, q = label_instance(n, nd, seed, B)
        P = {}; ref = {}
        t0 = time.perf_counter()
        for dr in drivers:
            ref[dr["id"]] = DL.run_pool(tt, dr, orders, B, B)["pool"]
        tprod = time.perf_counter() - t0
        res = {}
        for nm in ("C1", "C3", "C4", "C5", "C6", "C7"):
            t0 = time.perf_counter()
            p, per = build_all(nm, tt, drivers, orders, q, B)
            res[nm] = (p, per, time.perf_counter() - t0)
        s_ref = sig(ref)
        same1 = sig(res["C1"][0]) == s_ref
        same4 = sig(res["C4"][0]) == s_ref
        ok1 &= same1; ok4 &= same4
        kref = sig(kstar_pool(ref, q))
        ks = {}
        for nm in ("C1", "C3", "C4", "C6"):
            ks[nm] = sig(kstar_pool(res[nm][0], q)) == kref
        for nm in ("C5", "C7"):
            ks[nm] = sig(res[nm][0]) == kref
        e = {nm: sum(c["ext_attempts"] for _, c in res[nm][1].values()) for nm in res}
        print("B=%d n=%d s=%d | C1==prod %s | C4 R==C1 R %s | K*==K*(C1): %s | ext %s | secs prod %.2f %s"
              % (B, n, seed, same1, same4, ks, e, tprod,
                 {nm: round(res[nm][2], 2) for nm in res}))
        sys.stdout.flush()
print("REGRESSION C1==production:", "PASS" if ok1 else "FAIL", "| C4 R == C1 R:", "PASS" if ok4 else "FAIL")
