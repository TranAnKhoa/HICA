import time, cProfile, pstats, io, gc
from common import *
print("== C0 (Layer1 OFF, rule OFF), B=3, single run; pool must equal C1")
for (n, nd, seed) in LABEL_INSTANCES:
    dr_, o, tt, q = label_instance(n, nd, seed, 3)
    res = {}
    for nm, l1 in (("C0", False), ("C1", True)):
        gc.collect(); t0 = time.perf_counter(); pool = {}; ext = 0; cre = 0
        for d in dr_:
            pool[d["id"]], c = F.run_pool_audit(tt, d, o, 3, use_layer1=l1, use_rule=False); ext += c["ext_attempts"]; cre += c["labels_created"]
        res[nm] = (time.perf_counter() - t0, ext, cre, pool)
    print("n%d_s%d  C0 ext=%d t=%.2fs | C1 ext=%d t=%.2fs | C0/C1 time %.1fx | pools equal=%s"
          % (n, seed, res["C0"][1], res["C0"][0], res["C1"][1], res["C1"][0], res["C0"][0] / res["C1"][0], sig(res["C0"][3]) == sig(res["C1"][3])))
print("== cProfile n12_s42 B=3, C2")
dr_, o, tt, q = label_instance(12, 5, 42, 3)
pr = cProfile.Profile(); pr.enable()
for d in dr_: F.run_pool_audit(tt, d, o, 3, use_layer1=True, use_rule=True, q=q, lo=LO)
pr.disable(); s = io.StringIO(); pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(14); print(s.getvalue()[:3500])
