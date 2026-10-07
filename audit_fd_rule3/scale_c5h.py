"""Scale study of the final pipeline: Algorithm A = C5h (variants_h.py), Algorithms B and C with HiGHS (wdp_highs.py).

Instances: the paper's main-grid generator (rq_common.make_rq1_instance), B = 3, alignment 0.90 (crowd competitive) and
0.50 (FD dominant), area 8 x 8 km as in the paper, so larger n also means denser demand.
  n = 20, 30, 40, 50 with supply (3,3), reps 0-4
  n = 30, 50 with supply (5,5) and (10,10), reps 0-2
  n = 75, 100 with supply (3,3), reps 0-2
Per instance: time of C5h for every driver (A_sum = one core; A_max = one core per driver, drivers in parallel),
extension attempts, frontier size, B = base WDP, C = one removal solve per winner, solver statuses, peak memory.
Check jobs: at n = 30, supply (3,3), reps 0-1, the frontier of C5h is compared with the production Algorithm A (C1)
followed by the frontier (common.kstar_pool).
One process per job (3 in parallel on 4 cores), garbage collection off while a driver runs.
Output: ../audit_logs3/scale_c5h.jsonl (one line per job; the script skips jobs already present).
"""
import gc
import json
import multiprocessing as mp
import os
import resource
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "audit_logs3", "scale_c5h.jsonl")


def jobs():
    J = []
    for a in (0.90, 0.50):
        for n in (20, 30, 40, 50):
            for rep in range(5):
                J.append((a, n, 3, 3, rep))
        for n in (30, 50):
            for sup in ((5, 5), (10, 10)):
                for rep in range(3):
                    J.append((a, n, sup[0], sup[1], rep))
        for n in (75, 100):
            for rep in range(3):
                J.append((a, n, 3, 3, rep))
    J.sort(key=lambda j: -(j[1] ** 3) * (j[2] + 1))      # largest first
    return J


def key(j):
    return "a%.2f_n%d_s%d-%d_rep%d" % j


def run(j):
    sys.path.insert(0, HERE)
    import paths  # noqa: F401
    import variants_h as VH
    import rq_common as RQ
    import wdp_highs as WH
    a, n, ng, no, rep = j
    d, o, tt, meta, th, q = RQ.make_rq1_instance(a, n, ng, no, rep, B=3)
    pool, per = {}, []
    for dr in d:
        gc.collect(); gc.disable()
        t0 = time.perf_counter()
        p, c = VH.run_tier_h(tt, dr, o, 3, q=q, inloop=True)
        t = time.perf_counter() - t0
        gc.enable()
        pool[dr["id"]] = p
        per.append(dict(id=dr["id"], cls=dr["cls"], t=t, ext=c["ext_attempts"], kstar=c["routes_kept"]))
    v = WH.vcg(pool, th, q, sorted(o))
    row = dict(key=key(j), alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, drivers=per,
               A_sum=sum(x["t"] for x in per), A_max=max(x["t"] for x in per),
               A_gw_mean=sum(x["t"] for x in per if x["cls"] == "GW") / max(1, sum(1 for x in per if x["cls"] == "GW")),
               ext=sum(x["ext"] for x in per), kstar=sum(x["kstar"] for x in per),
               t_B=v["t_B"], t_C=v["t_C"], winners=v["winners"], fd=v["fd"], n_cols=v["n_cols"],
               Z=v["Z"], statuses=sorted(set(v["statuses"])), n_solves=len(v["statuses"]),
               peak_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)
    if n == 30 and (ng, no) == (3, 3) and rep in (0, 1):
        from variants_h import build_all
        from common import kstar_pool, sig
        r1, _ = build_all("C1", tt, d, o, q, 3)
        row["check_kstar_equal_C1"] = sig(kstar_pool(r1, q)) == sig(pool)
    return row


def main():
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["key"] for l in open(OUT) if l.strip()}
    todo = [j for j in jobs() if key(j) not in done]
    print("jobs: %d total, %d to do" % (len(jobs()), len(todo)), flush=True)
    with mp.get_context("fork").Pool(3, maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(run, todo):
            with open(OUT, "a") as f:
                f.write(json.dumps(row) + "\n")
            print("%s  A_sum %.1f A_max %.1f  B %.2f C %.2f  winners %d  K* %d  %s  %.0f MB%s" % (
                row["key"], row["A_sum"], row["A_max"], row["t_B"], row["t_C"], row["winners"], row["kstar"],
                row["statuses"], row["peak_mb"],
                ("  check=%s" % row["check_kstar_equal_C1"]) if "check_kstar_equal_C1" in row else ""), flush=True)


if __name__ == "__main__":
    main()
