"""Correctness gates for the dead-end filter (C4h/C5h) and for C8h (= C5h + Layer 3).

  R   R(C4h) == R(C1) per driver (the filter must not change the pool at all):
      10 label configurations (B=3,4), 20 main-grid instances, 80 random instances (n=6..9)
  G1  K*(C5h) == K*(C8h) == K*(C1) per driver on the same instances
  G4  brute force n=5,6, seeds 0-2: K*(brute) == K*(C5h) == K*(C8h)
  DA  dead-end audit: every label removed by the filter (n10_s1, n10_s999 at B=3, B=4 and the six brute-force
      instances) must have NO feasible completion, checked by enumerating continuations with the independent
      evaluator of gate_c8.py (re-simulation from the stop sequence)
  M   mutations of the filter must be caught by R or DA: (a) home deadline tightened by 5 minutes;
      (b) delivery deadlines tightened by 5 minutes. Valid control: test (a) of the filter only (weaker) passes.

Usage: python gate_h.py   (writes ../audit_logs3/gate_h.json)
"""
import json
import sys
import time

import paths  # noqa: F401
import variants_h as VH
import fastrule as FR
from variants_h import build_all
from common import IG, RC, label_instance, sig, kstar_pool, LABEL_INSTANCES
import rq_common as RQ
import brute_force as BF

OUT = {}
FAILS = []


def log(*a):
    print(*a)
    sys.stdout.flush()


def per_driver(pool, did):
    return sig({did: pool.get(did, {})})


def check(tag, tt, drivers, orders, q, B, with_c8h=True):
    r1, _ = build_all("C1", tt, drivers, orders, q, B)
    k1 = kstar_pool(r1, q)
    r4h, per4h = build_all("C4h", tt, drivers, orders, q, B)
    p5h, per5h = build_all("C5h", tt, drivers, orders, q, B)
    row = dict(tag=tag, B=B, R=len(sig(r1)), Kstar=len(sig(k1)))
    row["R_equal"] = all(per_driver(r4h, d["id"]) == per_driver(r1, d["id"]) for d in drivers)
    row["C5h_kstar_equal"] = all(per_driver(p5h, d["id"]) == per_driver(k1, d["id"]) for d in drivers)
    row["dead_kills_GW"] = sum(c["killed_dead"] for cl, c in per5h.values() if cl == "GW")
    row["dead_kills_OD"] = sum(c["killed_dead"] for cl, c in per5h.values() if cl == "OD")
    if with_c8h:
        TT, KK = FR.make_tables(tt, FR.node_ids(drivers, orders))
        p8h, _ = VH.build_all_c8h(tt, drivers, orders, q, B, (TT, KK))
        row["C8h_kstar_equal"] = all(per_driver(p8h, d["id"]) == per_driver(k1, d["id"]) for d in drivers)
    ok = row["R_equal"] and row["C5h_kstar_equal"] and row.get("C8h_kstar_equal", True)
    if not ok:
        FAILS.append((tag, B, row))
    return row


def main():
    t0 = time.time()
    import gate_c8_eval as EV                       # independent evaluator (copy of gate_c8.py functions)
    rows = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            d, o, tt, q = label_instance(n, nd, seed, B)
            r = check("label n%d_s%d" % (n, seed), tt, d, o, q, B)
            rows.append(r)
            log("%-18s B=%d | R(C4h)=R(C1): %s | K* C5h: %s C8h: %s | dead kills GW %d OD %d"
                % (r["tag"], B, r["R_equal"], r["C5h_kstar_equal"], r["C8h_kstar_equal"],
                   r["dead_kills_GW"], r["dead_kills_OD"]))
    for align in (0.90, 0.50):
        for rep in range(10):
            d, o, tt, meta, th, q = RQ.make_rq1_instance(align, 15, 3, 3, rep, B=3)
            r = check("grid a%.2f_rep%d" % (align, rep), tt, d, o, q, 3)
            rows.append(r)
    log("grid sample (20 instances): R equal %s | K* C5h %s | K* C8h %s"
        % (all(r["R_equal"] for r in rows[-20:]), all(r["C5h_kstar_equal"] for r in rows[-20:]),
           all(r["C8h_kstar_equal"] for r in rows[-20:])))
    hunt = dict(instances=0, ok=0)
    for n in (6, 7, 8, 9):
        for seed in range(100, 120):
            d, o, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4, seed=seed,
                                                  tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(o, tt)
            r = check("hunt n%d_s%d" % (n, seed), tt, d, o, q, 3)
            hunt["instances"] += 1
            hunt["ok"] += int(r["R_equal"] and r["C5h_kstar_equal"] and r["C8h_kstar_equal"])
    log("HUNT 80 random instances (n=6..9, B=3): all equal on %d of %d" % (hunt["ok"], hunt["instances"]))
    OUT["rows"] = rows
    OUT["hunt"] = hunt

    small = []
    g4 = []
    for n in (5, 6):
        for seed in range(3):
            d, o, tt, meta = IG.generate_instance(n=n, B_gw=3, B_od=3, tw_width=120, n_drivers=4, seed=seed,
                                                  tau=30.0, spatial_mode="dispersed")
            q = RC.assign_q_o(o, tt)
            small.append(("brute_n%d_s%d" % (n, seed), d, o, tt, q, 3))
            bf = {dr["id"]: BF.brute_pool_for_driver(tt, dr, o, 3, 3) for dr in d}
            kb = sig(kstar_pool(bf, q))
            p5h, _ = build_all("C5h", tt, d, o, q, 3)
            TT, KK = FR.make_tables(tt, FR.node_ids(d, o))
            p8h, _ = VH.build_all_c8h(tt, d, o, q, 3, (TT, KK))
            ok = sig(p5h) == kb and sig(p8h) == kb
            g4.append(dict(n=n, seed=seed, ok=ok))
            if not ok:
                FAILS.append(("G4", n, seed))
    log("G4 brute force n=5,6 (6 instances): %s" % ("PASS" if all(x["ok"] for x in g4) else "FAIL"))
    OUT["G4"] = g4

    for (n, nd, seed) in [(10, 4, 1), (10, 4, 999)]:
        for B in (3, 4):
            d, o, tt, q = label_instance(n, nd, seed, B)
            small.insert(0, ("n%d_s%d_B%d" % (n, seed, B), d, o, tt, q, B))

    def dead_audit(variant_dead=None):
        tot = dict(dead_labels=0, with_feasible_completion=0, GW=0, OD=0, first=None)
        for (name, drivers, orders, tt, q, B) in small:
            for dr in drivers:
                dl = []
                if variant_dead is None:
                    VH.run_tier_h(tt, dr, orders, B, q=q, inloop=True, dead_log=dl)
                else:
                    saved = VH.make_dead
                    VH.make_dead = variant_dead
                    try:
                        VH.run_tier_h(tt, dr, orders, B, q=q, inloop=True, dead_log=dl)
                    finally:
                        VH.make_dead = saved
                for L in dl:
                    tot["dead_labels"] += 1
                    tot[dr["cls"]] += 1
                    comps = EV.completions(tt, dr, orders, EV.seq_of(L), B)
                    if comps:
                        tot["with_feasible_completion"] += 1
                        tot["first"] = tot["first"] or dict(instance=name, driver=dr["id"], seq=EV.seq_of(L),
                                                            completion=comps[0])
        return tot

    da = dead_audit()
    log("DA dead-end audit: %d removed labels (GW %d, OD %d), %d with a feasible completion"
        % (da["dead_labels"], da["GW"], da["OD"], da["with_feasible_completion"]))
    if da["with_feasible_completion"]:
        FAILS.append(("DA", da["first"]))
    OUT["DA"] = da

    # mutations of the filter
    orig_make = VH.make_dead

    def mut_home(tt, pd, home):
        if home is not None:
            class H(object):
                pass
            h = H(); h.id, h.l, h.e, h.s = home.id, home.l - 5.0, home.e, home.s
            return orig_make(tt, pd, h)
        return orig_make(tt, pd, home)

    def mut_deliv(tt, pd, home):
        class N(object):
            pass
        pd2 = {}
        for j, (p, d) in pd.items():
            d2 = N(); d2.id, d2.e, d2.s, d2.l = d.id, d.e, d.s, d.l - 5.0
            pd2[j] = (p, d2)
        return orig_make(tt, pd2, home)

    def control_weaker(tt, pd, home):        # only test (a): valid, removes fewer labels
        return orig_make(tt, pd, None)

    M = {}
    for name, fn, valid in (("home_deadline_minus5", mut_home, False), ("delivery_deadline_minus5", mut_deliv, False),
                            ("control_test_a_only", control_weaker, True)):
        VH.make_dead = fn
        try:
            r_bad = []
            for (n, nd, seed) in LABEL_INSTANCES:
                d, o, tt, q = label_instance(n, nd, seed, 3)
                r1, _ = build_all("C1", tt, d, o, q, 3)
                r4h, _ = build_all("C4h", tt, d, o, q, 3)
                if sig(r4h) != sig(r1):
                    r_bad.append("n%d_s%d" % (n, seed))
        finally:
            VH.make_dead = orig_make
        dam = dead_audit(fn)
        detected = bool(r_bad) or dam["with_feasible_completion"] > 0
        M[name] = dict(valid=valid, R_fails=r_bad, DA_dead=dam["dead_labels"],
                       DA_with_completion=dam["with_feasible_completion"], detected=detected)
        log("M %-26s (%s): R differs on %s | DA: %d removed, %d with a feasible completion | detected=%s"
            % (name, "valid control" if valid else "invalid", r_bad, dam["dead_labels"],
               dam["with_feasible_completion"], detected))
        if valid == detected:
            FAILS.append(("M", name))
    OUT["M"] = M
    OUT["fails"] = [list(map(str, f)) for f in FAILS]
    json.dump(OUT, open("../audit_logs3/gate_h.json", "w"), indent=1, default=str)
    log("\nSUMMARY gate_h: fails=%d  [%.0fs]" % (len(FAILS), time.time() - t0))


main()
