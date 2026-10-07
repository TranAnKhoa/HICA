"""G5 (completion-level audit of FD-dominance) and G6 (mutation test) for C6.

Independent evaluator: a route is re-simulated FROM SCRATCH from its stop sequence (no label arithmetic,
no _try_* functions), using only the instance data and the travel-time function.
For every discard (L2 by L1, T): enumerate ALL feasible completions sigma of L2 and check
  (1) L1.sigma is feasible, (2) c(L2.sigma) - c(L1.sigma) >= q(T) - 1e-9 at theta = 18.
"""
import sys, json, time
from variants import *
import t2_gen as G

SPEED = G.SPEED_KMH
THETA = LO
ABS = 1e-9


def simulate(tt, driver, orders, seq, B):
    """Return state (t, node, dist_km, load, done) or None if the stop sequence is infeasible."""
    t = driver["t0"]
    node = driver["start_node"]
    dist = 0.0
    load, done = set(), set()
    for kind, oid in seq:
        o = orders[oid]
        if kind == "p":
            if oid in load or oid in done or len(load) + len(done) >= B:
                return None
            nid, e, l = o["pickup_node"], o["ready_time_p"], o["deadline_p"]
        else:
            if oid not in load:
                return None
            nid, e, l = o["delivery_node"], o["ready_time_d"], o["deadline_d"]
        tr = tt(node, nid)
        dist += tr * SPEED / 60.0
        arr = t + tr
        st = arr if arr > e else e
        if st > l + 1e-9:
            return None
        t = st + o["service_time"]
        node = nid
        if kind == "p":
            load.add(oid)
        else:
            load.discard(oid)
            done.add(oid)
    return (t, node, dist, frozenset(load), frozenset(done))


def finish(tt, driver, state):
    """Cost (K, W) of the finished route, or None. Empty route -> (0, 0). OD returns home."""
    t, node, dist, load, done = state
    if load:
        return None
    if not done:
        return (0.0, 0.0)
    if driver["cls"] == "OD":
        tr = tt(node, driver["home_node"])
        dist += tr * SPEED / 60.0
        arr = t + tr
        st = arr if arr > 0.0 else 0.0
        if st > driver["t0"] + driver["direct_time"] + driver["tau"] + 1e-9:
            return None
        t = st
        K = D.KAPPA * max(0.0, dist - driver["direct_time"] * SPEED / 60.0)
        W = max(0.0, (t - driver["t0"] - driver["direct_time"]) / 60.0)
    else:
        K = D.KAPPA * dist
        W = (t - driver["t0"]) / 60.0
    return (K, W)


def seq_of(label):
    out = []
    for act, v, t, K, W in label.path():
        if act is None or act[0] == "home":
            continue
        out.append(("p" if act[0] == "pickup" else "d", act[1]))
    return out


def completions(tt, driver, orders, base_seq, B):
    """All sigma with base_seq+sigma feasible and complete (GW: load empty & >=1 delivered; OD: + home)."""
    ids = sorted(orders.keys())
    out = []

    def rec(sigma):
        st = simulate(tt, driver, orders, base_seq + sigma, B)
        if st is None:
            return
        t, node, dist, load, done = st
        if not load and done and finish(tt, driver, st) is not None:
            out.append(list(sigma))
        if len(load) + len(done) < B:
            for j in ids:
                if j not in load and j not in done:
                    rec(sigma + [("p", j)])
        for j in sorted(load):
            rec(sigma + [("d", j)])
    rec([])
    return out


def audit_firings(tt, driver, orders, q, B, log):
    n_fire = n_comp = viol = 0
    worst = 1e18
    first_viol = None
    for (L2, L1, T) in log:
        n_fire += 1
        s2, s1 = seq_of(L2), seq_of(L1)
        qT = sum(q[o] for o in T)
        for sigma in completions(tt, driver, orders, s2, B):
            n_comp += 1
            st2 = simulate(tt, driver, orders, s2 + sigma, B)
            K2, W2 = finish(tt, driver, st2)
            st1 = simulate(tt, driver, orders, s1 + sigma, B)
            if st1 is None or finish(tt, driver, st1) is None:
                viol += 1
                first_viol = first_viol or dict(driver=driver["id"], L2=s2, L1=s1, T=sorted(T), sigma=sigma, why="L1.sigma infeasible")
                continue
            K1, W1 = finish(tt, driver, st1)
            margin = (K2 + THETA * W2) - (K1 + THETA * W1) - qT
            worst = min(worst, margin)
            if margin < -ABS:
                viol += 1
                first_viol = first_viol or dict(driver=driver["id"], L2=s2, L1=s1, T=sorted(T), sigma=sigma,
                                                cost_gap=(K2 + THETA * W2) - (K1 + THETA * W1), qT=qT)
    return n_fire, n_comp, viol, worst, first_viol


def validate_evaluator(tt, drivers, orders, B):
    """The independent evaluator must reproduce finalize_KW on every complete label of the production DP."""
    bad = tot = 0
    for dr in drivers:
        res = D.run_dp(tt, dr, orders, B, use_dominance=True)
        for Cset, labs in res["complete_by_C"].items():
            for lab in labs:
                st = simulate(tt, dr, orders, seq_of(lab), B)
                kw = finish(tt, dr, st) if st is not None else None
                ref = D.finalize_KW(dr, lab)
                tot += 1
                if kw is None or abs(kw[0] - ref[0]) > 1e-7 or abs(kw[1] - ref[1]) > 1e-7:
                    bad += 1
    return tot, bad


def run_g5(instances, mut=None, tag=""):
    tot = dict(firings=0, completions=0, violations=0, GW=0, OD=0)
    worst = 1e18
    firstv = None
    for (name, drivers, orders, tt, q, B) in instances:
        for dr in drivers:
            log = []
            run_tier(tt, dr, orders, B, q=q, fd_dom=True, mut=mut, fire_log=log)
            nf, nc, nv, w, fv = audit_firings(tt, dr, orders, q, B, log)
            tot["firings"] += nf; tot["completions"] += nc; tot["violations"] += nv
            tot[dr["cls"]] += nf
            worst = min(worst, w)
            firstv = firstv or fv
    tot["min_margin"] = None if worst > 1e17 else worst
    tot["first_violation"] = firstv
    return tot


def g1_kstar(instances, mut):
    bad = []
    for (name, drivers, orders, tt, q, B) in instances:
        ref, _ = build_all("C1", tt, drivers, orders, q, B)
        kref = kstar_pool(ref, q)
        p = {}
        for dr in drivers:
            p[dr["id"]], _c = run_tier(tt, dr, orders, B, q=q, fd_dom=True, mut=mut)
        k = kstar_pool(p, q)
        if sig(k) != sig(kref):
            bad.append(name)
    return bad


def main():
    small = []
    for (n, nd, seed) in [(10, 4, 1), (10, 4, 999)]:
        d, o, tt, q = label_instance(n, nd, seed, 3)
        small.append(("n%d_s%d" % (n, seed), d, o, tt, q, 3))
    for n in (5, 6):
        for seed in range(3):
            d, o, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4, seed=seed,
                                                  tau=30.0, spatial_mode="dispersed")
            small.append(("brute_n%d_s%d" % (n, seed), d, o, tt, RC.assign_q_o(o, tt), 3))
    # evaluator sanity
    tv = bv = 0
    for (name, d, o, tt, q, B) in small[:2]:
        a, b = validate_evaluator(tt, d, o, B)
        tv += a; bv += b
    print("EVALUATOR VALIDATION: %d complete labels, %d mismatches vs finalize_KW" % (tv, bv)); sys.stdout.flush()

    t0 = time.time()
    g5 = run_g5(small)
    print("G5 (real C6): %s  [%.0fs]" % (json.dumps({k: v for k, v in g5.items() if k != 'first_violation'}), time.time() - t0))
    if g5["first_violation"]:
        print("   first violation:", g5["first_violation"])
    sys.stdout.flush()

    g1set = []
    for (n, nd, seed) in LABEL_INSTANCES:
        d, o, tt, q = label_instance(n, nd, seed, 3)
        g1set.append(("n%d_s%d" % (n, seed), d, o, tt, q, 3))
    d, o, tt, q = label_instance(10, 4, 999, 4)
    g1set.append(("n10_s999_B4", d, o, tt, q, 4))
    out = dict(evaluator=dict(labels=tv, mismatches=bv), g5_real=g5, mutations={})
    for mut, kind in (("A0", "invalid"), ("noK", "invalid"), ("t5", "invalid"), ("minus1", "invalid(extra)"),
                      ("plus1", "valid control")):
        t0 = time.time()
        bad = g1_kstar(g1set, mut)
        g5m = run_g5(small, mut=mut)
        out["mutations"][mut] = dict(kind=kind, g1_failed_instances=bad, g5=g5m)
        print("G6 mutation %-7s (%s): G1 fails on %s | G5 firings=%d completions=%d violations=%d min_margin=%s  [%.0fs]"
              % (mut, kind, bad, g5m["firings"], g5m["completions"], g5m["violations"], g5m["min_margin"], time.time() - t0))
        sys.stdout.flush()
    json.dump(out, open("../audit_logs2/gate_audit.json", "w"), indent=1, default=str)


main()
