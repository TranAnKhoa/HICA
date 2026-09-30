"""Phase 3 §4.3 (1,2) + Tables A (work) for C1 (L1 on, rule off) vs C2 (L1 on, rule on)."""
import sys, json, time
from common import *

def build(tt, drivers, orders, q, B, rule):
    pool, per = {}, {}
    t0 = time.perf_counter()
    for dr in drivers:
        p, c = F.run_pool_audit(tt, dr, orders, B, use_layer1=True, use_rule=rule, q=q, lo=LO)
        pool[dr["id"]] = p; per[dr["id"]] = (dr["cls"], c)
    return pool, per, time.perf_counter() - t0

def main():
    print("LO=%r HI=%r" % (LO, HI))
    rows, all_ok = [], True
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            p1, c1, tA1 = build(tt, drivers, orders, q, B, False)
            p2, c2, tA2 = build(tt, drivers, orders, q, B, True)
            k1, k2 = kstar_pool(p1, q), kstar_pool(p2, q)
            s1, s2, ks1, ks2 = sig(p1), sig(p2), sig(k1), sig(k2)
            ident = ks1 == ks2
            nd_ident = sum(1 for d in p1 if sig({d: k1[d]}) == sig({d: k2[d]}))
            sub = len(s2 - s1)           # routes in C2 pool that are NOT in C1 pool
            kin = ks1 <= s2 and ks2 <= s1  # every K* route present in both pools
            all_ok &= ident
            e1 = sum(c["ext_attempts"] for _, c in c1.values()); e2 = sum(c["ext_attempts"] for _, c in c2.values())
            k3 = sum(c["killed_layer3"] for _, c in c2.values())
            print("B=%d n=%d s=%d | ext %d -> %d (saved %.1f%%) kill3=%d | L2 pool %d -> %d (extra-in-C2=%d) | K* %d/%d  identical=%s drivers %d/%d K*inBoth=%s"
                  % (B, n, seed, e1, e2, 100 * (1 - e2 / e1), k3, len(s1), len(s2), sub, len(ks1), len(ks2), ident, nd_ident, len(p1), kin))
            for d in p1:
                if not sig({d: k1[d]}) == sig({d: k2[d]}):
                    print("   !! K* DIFFERS driver", d, "C1-only", len(sig({d: k1[d]}) - sig({d: k2[d]})), "C2-only", len(sig({d: k2[d]}) - sig({d: k1[d]})))
            sys.stdout.flush()
    print("K* EQUALITY", "PASS" if all_ok else "FAIL")
main()
