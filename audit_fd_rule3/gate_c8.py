"""Correctness gates for C8 (= C5 + Layer 3) and C8f (same rule, faster implementation).

  R0  regression: C5copy == C5 (pools); C8f == C8 (pools and every counter)
  G1  K*(C8) == K*(C8f) == K*(C1) for every driver: 10 label configurations (B=3,4) and the
      main-grid sample (n=15, supply (3,3), alignment 0.90/0.50, reps 0-9, B=3)
  G4  brute force n=5,6, seeds 0-2: K*(brute) == K*(C8)
  H   counterexample hunt: 80 random instances (n=6..9, seeds 100-119, B=3): K*(C8) == Frontier(R_C1)
  G5  completion-level audit of every Layer-3 firing of C8 (n10_s1, n10_s999 at B=3 and the six
      brute-force instances): for the fired label L with witness j, enumerate ALL feasible
      completions sigma with an independent evaluator (re-simulation from the stop sequence) and
      check that L.sigma without j's stops is feasible and that
      c(L.sigma) - c(L.sigma minus j) >= q_j - 1e-9 at theta = 18 (Proposition 1 / Theorem 3).
  G6  mutations of the rule (A = 0; no junction terms) must be caught by G1 or G5.

Usage: python gate_c8.py   (writes ../audit_logs3/gate_c8.json)
"""
import json
import sys
import time
from collections import defaultdict

import paths  # noqa: F401
import variants3 as V3
import fastrule as FR
from variants3 import build_all, INLOOP
from common import IG, RC, label_instance, sig, kstar_pool, LABEL_INSTANCES, LO
import variants as V
import rq_common as RQ
import brute_force as BF
import t2_gen as G

D = V.D
SPEED = G.SPEED_KMH
THETA = LO
OUT = {}
FAILS = []


# ------------------------------------------------ independent evaluator (copied from audit_fd_rule2/gate_audit.py,
# which cannot be imported because it runs its main() at import time)
def simulate(tt, driver, orders, seq, B):
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


def cost(kw):
    return kw[0] + THETA * kw[1]


def audit_rule_firings(tt, driver, orders, q, B, log):
    n_fire = n_comp = viol = 0
    worst = float("inf")
    first = None
    for (L, j) in log:
        n_fire += 1
        s = seq_of(L)
        for sigma in completions(tt, driver, orders, s, B):
            n_comp += 1
            full = s + sigma
            kw_full = finish(tt, driver, simulate(tt, driver, orders, full, B))
            red = [x for x in full if x[1] != j]
            st = simulate(tt, driver, orders, red, B)
            kw_red = finish(tt, driver, st) if st is not None else None
            if kw_red is None:
                viol += 1
                first = first or dict(driver=driver["id"], L=s, j=j, sigma=sigma, why="route without j infeasible")
                continue
            margin = cost(kw_full) - cost(kw_red) - q[j]
            worst = min(worst, margin)
            if margin < -1e-9:
                viol += 1
                first = first or dict(driver=driver["id"], L=s, j=j, sigma=sigma, margin=margin)
    return n_fire, n_comp, viol, worst, first


# ------------------------------------------------ mutated rules (for G6), built from fastrule's source
def mutated_build(kind):
    src = open(FR.__file__).read()
    if kind == "A0":        # ignore absorption: credit the whole time saving
        src = src.replace("        d = delta0 - A\n", "        d = delta0\n")
    elif kind == "nojunction":   # drop the junction terms d(v',v_m), tau(v',v_m)
        src = src.replace("        jt = TTj[v]\n        dK = K - Kj - KK[vj][v]\n",
                          "        jt = 0.0\n        dK = K - Kj\n")
    else:
        raise ValueError(kind)
    assert src != open(FR.__file__).read(), kind
    ns = {"__name__": "fastrule_mut_" + kind}
    exec(compile(src, "fastrule_mut_" + kind, "exec"), ns)
    return ns


def log(*a):
    print(*a)
    sys.stdout.flush()


def per_driver(pool, did):
    return sig({did: pool.get(did, {})})


def check_instance(tag, tt, drivers, orders, q, B):
    ref, _ = build_all("C1", tt, drivers, orders, q, B)
    kref = kstar_pool(ref, q)
    p5, per5 = build_all("C5", tt, drivers, orders, q, B)
    p5c, _ = build_all("C5copy", tt, drivers, orders, q, B)
    p8, per8 = build_all("C8", tt, drivers, orders, q, B)
    TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
    p8f, per8f = FR.build_all_fast(tt, drivers, orders, q, B, (TT, KK))
    row = dict(tag=tag, B=B, Kstar=len(sig(kref)), R_C1=len(sig(ref)))
    row["R0_C5copy_eq_C5"] = sig(p5c) == sig(p5)
    row["R0_C8f_eq_C8"] = (sig(p8f) == sig(p8)) and all(per8[d][1] == per8f[d][1] for d in per8)
    for nm, p in (("C5", p5), ("C8", p8), ("C8f", p8f)):
        bad = [d["id"] for d in drivers if per_driver(p, d["id"]) != per_driver(kref, d["id"])]
        row[nm + "_kstar_equal"] = not bad
        if bad:
            FAILS.append((tag, "G1", nm, bad))
    if not (row["R0_C5copy_eq_C5"] and row["R0_C8f_eq_C8"]):
        FAILS.append((tag, "R0"))
    row["C8_killed_rule"] = sum(c["killed_rule"] for _, c in per8.values())
    row["C8_fired_GW"] = sum(1 for _, (cl, c) in per8.items() if cl == "GW" and c["killed_rule"] > 0)
    row["C8_fired_OD"] = sum(1 for _, (cl, c) in per8.items() if cl == "OD" and c["killed_rule"] > 0)
    log("%-20s B=%d K*=%4d | R0 C5copy=C5:%s C8f=C8:%s | G1 C5:%s C8:%s C8f:%s | rule kills %d (GW drivers %d, OD drivers %d)"
        % (tag, B, row["Kstar"], row["R0_C5copy_eq_C5"], row["R0_C8f_eq_C8"], row["C5_kstar_equal"],
           row["C8_kstar_equal"], row["C8f_kstar_equal"], row["C8_killed_rule"], row["C8_fired_GW"], row["C8_fired_OD"]))
    return row


def main():
    t0 = time.time()
    rows = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            rows.append(check_instance("label n%d_s%d" % (n, seed), tt, drivers, orders, q, B))
    for align in (0.90, 0.50):
        for rep in range(10):
            d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
            rows.append(check_instance("grid a%.2f_rep%d" % (align, rep), tt, d, o, q, 3))
    OUT["G1_rows"] = rows

    g4 = []
    small = []
    for n in (5, 6):
        for seed in range(3):
            drivers, orders, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4,
                                                             seed=seed, tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(orders, tt)
            small.append(("brute_n%d_s%d" % (n, seed), drivers, orders, tt, q, 3))
            bf = {dr["id"]: BF.brute_pool_for_driver(tt, dr, orders, 3, 3) for dr in drivers}
            kb = sig(kstar_pool(bf, q))
            p8, _ = build_all("C8", tt, drivers, orders, q, 3)
            ok = sig(p8) == kb
            if not ok:
                FAILS.append(("brute n%d s%d" % (n, seed), "G4"))
            g4.append(dict(n=n, seed=seed, K_brute=len(kb), C8_equal=ok))
            log("G4 brute n=%d seed=%d K*(brute)=%d C8:%s" % (n, seed, len(kb), "ok" if ok else "FAIL"))
    OUT["G4"] = g4

    hunt = dict(instances=0, drivers=0, mismatches=0)
    for n in (6, 7, 8, 9):
        for seed in range(100, 120):
            drivers, orders, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4,
                                                             seed=seed, tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(orders, tt)
            R, _ = build_all("C1", tt, drivers, orders, q, 3)
            K = kstar_pool(R, q)
            p8, _ = build_all("C8", tt, drivers, orders, q, 3)
            for d in drivers:
                hunt["drivers"] += 1
                if per_driver(p8, d["id"]) != per_driver(K, d["id"]):
                    hunt["mismatches"] += 1
                    FAILS.append(("hunt n%d s%d" % (n, seed), "H", d["id"]))
            hunt["instances"] += 1
    OUT["hunt"] = hunt
    log("HUNT (80 random instances n=6..9, B=3): %s" % hunt)

    for (n, nd, seed) in [(10, 4, 1), (10, 4, 999)]:
        d, o, tt, q = label_instance(n, nd, seed, 3)
        small.insert(0, ("n%d_s%d" % (n, seed), d, o, tt, q, 3))
    g5 = dict(firings=0, completions=0, violations=0, GW=0, OD=0, min_margin=None, first_violation=None)
    worst = float("inf")
    for (name, drivers, orders, tt, q, B) in small:
        for dr in drivers:
            flog = []
            V3.run_tier_rule(tt, dr, orders, B, q=q, rule=True, inloop=True, fire_log=flog)
            nf, nc, nv, w, fv = audit_rule_firings(tt, dr, orders, q, B, flog)
            g5["firings"] += nf; g5["completions"] += nc; g5["violations"] += nv; g5[dr["cls"]] += nf
            worst = min(worst, w)
            g5["first_violation"] = g5["first_violation"] or fv
    g5["min_margin"] = None if worst == float("inf") else worst
    if g5["violations"]:
        FAILS.append(("G5", g5["first_violation"]))
    OUT["G5"] = g5
    log("G5 (real C8): firings=%d (GW %d, OD %d) completions=%d violations=%d min margin=%s"
        % (g5["firings"], g5["GW"], g5["OD"], g5["completions"], g5["violations"], g5["min_margin"]))

    # G6: mutations must be detected (G1 on the label instances at B=3, or G5 on the small set)
    g6 = {}
    for kind in ("A0", "nojunction"):
        ns = mutated_build(kind)
        g1bad = []
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, 3)
            ref, _ = build_all("C1", tt, drivers, orders, q, 3)
            TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
            pm, _ = ns["build_all_fast"](tt, drivers, orders, q, 3, (TT, KK))
            if sig(pm) != sig(kstar_pool(ref, q)):
                g1bad.append("n%d_s%d" % (n, seed))
        tot = dict(firings=0, completions=0, violations=0)
        for (name, drivers, orders, tt, q, B) in small:
            TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
            for dr in drivers:
                flog = []
                # re-run the mutated rule with a logging rule_pass: wrap rule_fires to record witnesses
                fires = ns["rule_fires_fast"]

                def logged(nl, nsc, TT_, pd, q_, lo, B_, max_e, cnt, KK_, _f=fires, _log=flog):
                    if _f(nl, nsc, TT_, pd, q_, lo, B_, max_e, cnt, KK_):
                        for j in sorted(nsc):
                            if _f(nl, {j: nsc[j]}, TT_, pd, q_, lo, B_, max_e, dict(a_evals=0), KK_):
                                _log.append((nl, j))
                                break
                        return True
                    return False
                ns["rule_fires_fast"] = logged
                ns["run_tier_rule_fast"](tt, dr, orders, B, q=q, inloop=True, tables=(TT, KK))
                ns["rule_fires_fast"] = fires
                nf, nc, nv, w, fv = audit_rule_firings(tt, dr, orders, q, B, flog)
                tot["firings"] += nf; tot["completions"] += nc; tot["violations"] += nv
        detected = bool(g1bad) or tot["violations"] > 0
        g6[kind] = dict(G1_failed=g1bad, G5=tot, detected=detected)
        log("G6 mutation %-10s G1 fails on %s | G5 firings=%d completions=%d violations=%d | detected=%s"
            % (kind, g1bad, tot["firings"], tot["completions"], tot["violations"], detected))
        if not detected:
            FAILS.append(("G6 not detected", kind))
    OUT["G6"] = g6
    OUT["fails"] = [list(map(str, f)) for f in FAILS]
    json.dump(OUT, open("../audit_logs3/gate_c8.json", "w"), indent=1, default=str)
    log("\nSUMMARY: fails=%d  [%.0fs]" % (len(FAILS), time.time() - t0))


main()
