"""Phase 3 §4.3 (5): n<=6, 3 seeds: K*(brute-force) == K*(C2, rule ON) (and == K*(C1))."""
import sys
from common import *
import brute_force as BF
ok = True
for n in (5, 6):
    for seed in range(3):
        drivers, orders, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4, seed=seed, tau=30.0, spatial_mode="dispersed")
        q = RC.assign_q_o(orders, tt)
        bf = {dr["id"]: BF.brute_pool_for_driver(tt, dr, orders, 3, 3) for dr in drivers}
        p1 = {}; p2 = {}; kills = 0
        for dr in drivers:
            p1[dr["id"]], _ = F.run_pool_audit(tt, dr, orders, 3, use_layer1=True, use_rule=False, q=q, lo=LO)
            p2[dr["id"]], c = F.run_pool_audit(tt, dr, orders, 3, use_layer1=True, use_rule=True, q=q, lo=LO)
            kills += c["killed_layer3"]
        kb, k1, k2 = sig(kstar_pool(bf, q)), sig(kstar_pool(p1, q)), sig(kstar_pool(p2, q))
        same = (kb == k2 == k1); ok &= same
        print("n=%d seed=%d  rule kills=%d  K*: brute %d, C1 %d, C2 %d  equal=%s" % (n, seed, kills, len(kb), len(k1), len(k2), same)); sys.stdout.flush()
print("BRUTE-FORCE", "PASS" if ok else "FAIL")
