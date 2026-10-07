"""G3: on 20 report profiles per instance (truthful + 19 uniform[18,25], fixed seed), V, every V_-k and every
payment of each variant's K* pool equal C1's within 1e-9.  Python 3.7.7 + CPLEX 12.10, single thread."""
import sys, json, random
from variants import *
import rq_common as RQ          # noqa: F401
import rq1_wdp as RW
import t8_cplex as T8

VARS = ["C3", "C4", "C5", "C6", "C7"]


def solve(pool, orders, theta, q, excl=None):
    wd = RW.build_wdp_drivers(pool, theta)
    r = RW.solve_wdp_for_instance(pool, orders, theta, q, excluded_driver=excl)
    am = T8.build_full_alloc_map(wd, r["alloc_x"])
    return r["z"], {d: (frozenset(ofs), round(c, 9)) for d, (rid, ofs, c) in am.items()}, {d: c for d, (rid, ofs, c) in am.items()}


def pay_profile(pool, orders, th, q):
    Z, alloc, cost = solve(pool, orders, th, q)
    Zk, pay = {}, {}
    for k in cost:
        Zk[k], _, _ = solve(pool, orders, th, q, excl=k)
        pay[k] = cost[k] + Zk[k] - Z
    return Z, alloc, Zk, pay


def main():
    out = []
    worst = dict((nm, 0.0) for nm in VARS)
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            dids = [d["id"] for d in drivers]
            pools = {}
            for nm in ["C1"] + VARS:
                p, _ = build_all(nm, tt, drivers, orders, q, B)
                pools[nm] = p if nm in INLOOP else kstar_pool(p, q)
            rng = random.Random(20261002 + seed * 10 + B)
            profiles = [RC.assign_theta(random.Random(7000 + seed), drivers)]
            for _ in range(19):
                profiles.append({d: rng.uniform(LO, HI) for d in dids})
            row = dict(B=B, inst="n%d_s%d" % (n, seed), profiles=len(profiles))
            ref = [pay_profile(pools["C1"], orders, th, q) for th in profiles]
            for nm in VARS:
                mdV = mdVk = mdP = 0.0
                adiff = 0
                for th, (Z1, a1, Zk1, p1) in zip(profiles, ref):
                    Z2, a2, Zk2, p2 = pay_profile(pools[nm], orders, th, q)
                    mdV = max(mdV, abs(Z1 - Z2))
                    for k in set(Zk1) & set(Zk2):
                        mdVk = max(mdVk, abs(Zk1[k] - Zk2[k]))
                    for k in set(p1) & set(p2):
                        mdP = max(mdP, abs(p1[k] - p2[k]))
                    if set(p1) != set(p2):
                        mdP = max(mdP, 1e9)          # a different winner set is a failure
                    if a1 != a2:
                        adiff += 1
                row[nm] = dict(max_dV=mdV, max_dVk=mdVk, max_dPay=mdP, alloc_diff_profiles=adiff,
                               kstar_identical=(sig(pools[nm]) == sig(pools["C1"])))
                worst[nm] = max(worst[nm], mdV, mdVk, mdP)
            out.append(row)
            print(B, row["inst"], {nm: ("%.1e/%.1e/%.1e" % (row[nm]["max_dV"], row[nm]["max_dVk"], row[nm]["max_dPay"]),
                                        row[nm]["alloc_diff_profiles"]) for nm in VARS})
            sys.stdout.flush()
    json.dump(dict(rows=out, worst=worst), open("../audit_logs2/gate_wdp.json", "w"), indent=1)
    print("G3 worst deviation per variant:", worst, "->", "PASS" if max(worst.values()) <= 1e-9 else "FAIL")


main()
