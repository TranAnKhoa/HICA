"""Phase 3 §4.3 (3,4): V, V_-k, payments, allocation on the K* pools of C1 and C2, 20 profiles/instance
(truthful + 19 uniform[18,25], fixed seed). Python 3.7.7 + CPLEX."""
import sys, json, random
from common import *
import rq1_wdp as RW
import t8_cplex as T8

def solve(pool, orders, theta, q, excl=None):
    wd = RW.build_wdp_drivers(pool, theta)
    r = RW.solve_wdp_for_instance(pool, orders, theta, q, excluded_driver=excl)
    am = T8.build_full_alloc_map(wd, r["alloc_x"])
    return r["z"], {d: (frozenset(ofs), round(c, 9)) for d, (rid, ofs, c) in am.items()}, {d: c for d, (rid, ofs, c) in am.items()}

def main():
    out = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            dids = [d["id"] for d in drivers]
            pools = {}
            for nm, rule in (("C1", False), ("C2", True)):
                p = {}
                for dr in drivers:
                    p[dr["id"]], _ = F.run_pool_audit(tt, dr, orders, B, use_layer1=True, use_rule=rule, q=q, lo=LO)
                pools[nm] = kstar_pool(p, q)
            rng = random.Random(20261001 + seed * 10 + B)
            profiles = [RC.assign_theta(random.Random(7000 + seed), drivers)]
            for _ in range(19):
                profiles.append({d: rng.uniform(LO, HI) for d in dids})
            mdV = mdVk = mdP = 0.0; alloc_diff = alloc_diff_tie = 0; nprof = 0
            for th in profiles:
                res = {}
                for nm in ("C1", "C2"):
                    Z, alloc, cost = solve(pools[nm], orders, th, q)
                    Zk, pay = {}, {}
                    for k in cost:
                        Zk[k], _, _ = solve(pools[nm], orders, th, q, excl=k)
                        pay[k] = cost[k] + Zk[k] - Z
                    res[nm] = (Z, alloc, Zk, pay)
                (Z1, a1, Zk1, p1), (Z2, a2, Zk2, p2) = res["C1"], res["C2"]
                mdV = max(mdV, abs(Z1 - Z2))
                for k in set(Zk1) | set(Zk2):
                    if k in Zk1 and k in Zk2:
                        mdVk = max(mdVk, abs(Zk1[k] - Zk2[k]))
                for k in set(p1) | set(p2):
                    mdP = max(mdP, abs(p1.get(k, 0.0) - p2.get(k, 0.0)) if (k in p1 and k in p2) else 0.0)
                if a1 != a2:
                    alloc_diff += 1
                    if abs(Z1 - Z2) < 1e-9: alloc_diff_tie += 1
                nprof += 1
            row = dict(B=B, inst="n%d_s%d" % (n, seed), profiles=nprof, max_dV=mdV, max_dVk=mdVk, max_dPay=mdP,
                       alloc_diff=alloc_diff, alloc_diff_with_equal_Z=alloc_diff_tie,
                       kstar_identical=(sig(pools["C1"]) == sig(pools["C2"])))
            out.append(row); print(row); sys.stdout.flush()
    json.dump(out, open("../audit_logs/wdp_equality.json", "w"), indent=1)
main()
