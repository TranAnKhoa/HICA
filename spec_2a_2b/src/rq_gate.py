"""RQ_Master.md §7 - Gate G1 (RQ2), G2 (RQ3), G3 (RQ4) truoc main run.

Oracle doc lap: pool = brute_force.brute_pool_for_driver (da audit doc lap o
Gate 0/616/160, RQ1 dry-run gate), WDP = duyet exhaustive thuan Python (khong
CPLEX). Pipeline = rq_common (dp_labeling + CPLEX).
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)

import instance_gen as IG
import brute_force as BF
import rq1_cost_gen as RC
import rq_common as C
from kstar_zstar_payment_check import prune_pool_by_kstar

TOL = 1e-6


def exhaustive(pools, cost_fn, q, order_ids, driver_ids=None, excluded=None, restrict=None):
    ids = [d for d in (driver_ids or list(pools)) if d != excluded]
    target = set(order_ids) if restrict is None else set(restrict)
    opts = {}
    for d in ids:
        lst = [(None, 0.0, None)]
        for S, kwl in pools[d].items():
            if not S or not set(S) <= target:
                continue
            for (K, W) in kwl:
                c = cost_fn(d, S, K, W)
                if c is not None:
                    lst.append((S, c, (K, W)))
        opts[d] = lst
    best = [None, None]

    def rec(i, cov, cost, asg):
        if i == len(ids):
            tot = cost + sum(q[o] for o in target - cov)
            if best[0] is None or tot < best[0] - 1e-12:
                best[0], best[1] = tot, dict(asg)
            return
        d = ids[i]
        for (S, c, kw) in opts[d]:
            if S is None:
                rec(i + 1, cov, cost, asg)
            elif not (S & cov):
                asg[d] = (S, kw[0], kw[1], c)
                rec(i + 1, cov | S, cost + c, asg)
                del asg[d]
    rec(0, frozenset(), 0.0, {})
    return best[0], best[1]


def pools_equal(a, b):
    if set(a) != set(b):
        return False
    for d in a:
        if set(a[d]) != set(b[d]):
            return False
        for S in a[d]:
            x, y = sorted(a[d][S]), sorted(b[d][S])
            if len(x) != len(y) or any(abs(p[0] - r[0]) > 1e-9 or abs(p[1] - r[1]) > 1e-9
                                       for p, r in zip(x, y)):
                return False
    return True


def main():
    fails = {"G1a": 0, "G1b": 0, "G1c": 0, "G2_vcg": 0, "G2_posted": 0, "G2_pab": 0,
             "G3": 0}
    checks = {k: 0 for k in fails}
    msgs = []
    n_inst = 0
    for n in [3, 4, 5, 6]:
        for tw in [60, 120]:
            for seed in [0, 1, 2]:
                n_inst += 1
                gs = IG.stable_seed(n, tw, seed, "rq_all_gate")
                mk = lambda B: IG.generate_instance(n=n, B_gw=B, B_od=B, tw_width=tw, n_drivers=4,
                                                    seed=gs, tau=30.0, spatial_mode="dispersed")
                drivers, orders, tt, meta = mk(3)
                theta = RC.assign_theta(random.Random(gs + 1), drivers)
                q = RC.assign_q_o(orders, tt)
                oids = list(orders)
                p3, _ = C.build_pool(tt, drivers, orders, 3)

                # G1a: filter == direct for B=1,2
                for B in [1, 2]:
                    dB, oB, ttB, _ = mk(B)
                    pd, _ = C.build_pool(ttB, dB, oB, B)
                    checks["G1a"] += 1
                    if not pools_equal(C.filter_pool(p3, B), C.filter_pool(pd, B)):
                        fails["G1a"] += 1
                        msgs.append("G1a n=%d tw=%d seed=%d B=%d" % (n, tw, seed, B))
                # G1b: capacity-4 pool filtered to <=3 == B3 pool
                d4, o4, tt4, _ = mk(4)
                p4, _ = C.build_pool(tt4, d4, o4, 4)
                checks["G1b"] += 1
                if not pools_equal(C.filter_pool(p4, 3), C.filter_pool(p3, 3)):
                    fails["G1b"] += 1
                    msgs.append("G1b n=%d tw=%d seed=%d" % (n, tw, seed))

                # oracle pools (brute force, capacity 3)
                bp = {d["id"]: BF.brute_pool_for_driver(tt, d, orders, 3, 3) for d in drivers}
                blocks = C.heur_blocks(orders, tt, tw)
                cf = C.true_cost_fn(theta)
                menus = {"B1": (C.filter_pool(p3, 1), C.filter_pool(bp, 1)),
                         "B2": (C.filter_pool(p3, 2), C.filter_pool(bp, 2)),
                         "B3": (C.filter_pool(p3, 3), C.filter_pool(bp, 3)),
                         "HEUR": (C.heur_pool(C.filter_pool(p3, 3), blocks),
                                  C.heur_pool(C.filter_pool(bp, 3), blocks))}
                for name, (pp, op) in menus.items():
                    z = C.solve(pp, cf, q, oids)["z"]
                    zo, _ = exhaustive(op, cf, q, oids)
                    checks["G1c"] += 1
                    if abs(z - zo) > TOL:
                        fails["G1c"] += 1
                        msgs.append("G1c %s n=%d tw=%d seed=%d %.6f vs %.6f" % (name, n, tw, seed, z, zo))

                # G2 VCG: Z*, every Z*_{-i}
                pool = C.filter_pool(p3, 3)
                opool = C.filter_pool(bp, 3)
                v = C.vcg(pool, theta, q, oids)
                zo, _ = exhaustive(opool, cf, q, oids)
                checks["G2_vcg"] += 1
                bad = abs(v["Z"] - zo) > TOL
                for d in pool:
                    zm = C.solve(pool, cf, q, oids, excluded=d)["z"]
                    zmo, _ = exhaustive(opool, cf, q, oids, excluded=d)
                    checks["G2_vcg"] += 1
                    if abs(zm - zmo) > TOL:
                        bad = True
                    if d in v["zminus"] and abs(v["zminus"][d] - zmo) > TOL:
                        bad = True
                    if d in v["pay"]:
                        S, K, W, c = v["full"]["assign"][d]
                        p_or = c + zmo - zo
                        if abs(v["pay"][d] - p_or) > TOL:
                            bad = True
                if bad:
                    fails["G2_vcg"] += 1
                    msgs.append("G2_vcg n=%d tw=%d seed=%d" % (n, tw, seed))

                # G2 posted price
                for lam in [0.6, 0.8, 1.0]:
                    pr = C.posted(pool, theta, q, oids, lam)
                    price = {o: lam * q[o] for o in q}
                    pcf = (lambda price: lambda d, S, K, W: (sum(price[o] for o in S)
                           if sum(price[o] for o in S) >= K + theta[d] * W - 1e-9 else None))(price)
                    zo, _ = exhaustive(opool, pcf, q, oids)
                    checks["G2_posted"] += 1
                    if abs(pr["payout"] - zo) > TOL:
                        fails["G2_posted"] += 1
                        msgs.append("G2_posted lam=%.1f n=%d tw=%d seed=%d %.6f vs %.6f"
                                    % (lam, n, tw, seed, pr["payout"], zo))

                # G2 pay-as-bid: Z at every visited grid point
                pb = C.pab_br(pool, theta, q, oids, trace=True)
                for d, tr in pb["trace"].items():
                    for (b, z) in tr:
                        th = dict(theta)
                        th[d] = b
                        zo, _ = exhaustive(opool, C.true_cost_fn(th), q, oids)
                        checks["G2_pab"] += 1
                        if abs(z - zo) > TOL:
                            fails["G2_pab"] += 1
                            msgs.append("G2_pab d=%s b=%.2f n=%d tw=%d seed=%d" % (d, b, n, tw, seed))
                zo, _ = exhaustive(opool, C.true_cost_fn(pb["bids"]), q, oids)
                checks["G2_pab"] += 1
                if abs(pb["payout"] - zo) > TOL:
                    fails["G2_pab"] += 1
                    msgs.append("G2_pab final n=%d tw=%d seed=%d" % (n, tw, seed))

                # G3: K*-pruned pool gives same Z*, Z*_{-i}
                pk = prune_pool_by_kstar(pool, q, C.THETA_LO, C.THETA_HI)
                rng = random.Random(gs + 7)
                for _bp in range(3):
                    th = {d: rng.uniform(C.THETA_LO, C.THETA_HI) for d in pool}
                    for ex in [None] + list(pool):
                        a = C.solve(pool, C.true_cost_fn(th), q, oids, excluded=ex)["z"]
                        b = C.solve(pk, C.true_cost_fn(th), q, oids, excluded=ex)["z"]
                        checks["G3"] += 1
                        if abs(a - b) > TOL:
                            fails["G3"] += 1
                            msgs.append("G3 n=%d tw=%d seed=%d ex=%s" % (n, tw, seed, ex))
    print("Gate RQ_Master.md §7 - %d instance (n in 3..6, tw in {60,120}, 3 seed, 4 driver)" % n_inst)
    for k in fails:
        print("  %-10s %4d fail / %5d check  -> %s" % (k, fails[k], checks[k],
                                                        "PASS" if fails[k] == 0 else "FAIL"))
    for m in msgs[:40]:
        print("   ", m)
    print("OVERALL:", "PASS" if sum(fails.values()) == 0 else "FAIL")


if __name__ == "__main__":
    main()
