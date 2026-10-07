"""Phase 2 regression: instrumented code, rule OFF, Layer 1 ON  ==  production dp_labeling.run_pool."""
import sys, time
from common import *
ok = True
for B in (3, 4):
    for (n, nd, seed) in LABEL_INSTANCES:
        drivers, orders, tt, q = label_instance(n, nd, seed, B)
        for dr in drivers:
            t0 = time.perf_counter()
            ref = DL.run_pool(tt, dr, orders, B, B)["pool"]
            t1 = time.perf_counter()
            mine, cnt = F.run_pool_audit(tt, dr, orders, B, use_layer1=True, use_rule=False)
            t2 = time.perf_counter()
            same = sig({dr["id"]: ref}) == sig({dr["id"]: mine})
            ok &= same
            print("B=%d n=%d s=%d %s %s  routes %d/%d  prod %.2fs audit %.2fs  ext=%d"
                  % (B, n, seed, dr["id"], "SAME" if same else "DIFF",
                     sum(map(len, ref.values())), cnt["routes_layer2"], t1 - t0, t2 - t1,
                     cnt["ext_attempts"]))
            sys.stdout.flush()
print("REGRESSION", "PASS" if ok else "FAIL")
