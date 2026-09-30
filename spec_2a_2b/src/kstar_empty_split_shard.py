"""Shard wrapper cho kstar_empty_split.py phan (i) - RQ1 main grid (1500
instance), chay song song. Ghi 2 CSV/shard (per-driver, per-instance)."""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rq_common as C
from kstar_empty_split import kstar_split_for_instance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")


def main():
    shard, nsh = int(sys.argv[1]), int(sys.argv[2])
    jobs = [(a, n, ng, no, rep) for a in [0.10, 0.30, 0.50, 0.70, 0.90]
            for n in [10, 15, 20] for (ng, no) in [(2, 2), (3, 2), (2, 3), (3, 3)]
            for rep in range(25)]
    mine = [j for i, j in enumerate(jobs) if i % nsh == shard]

    out_d = os.path.join(D, "kstar_empty_split_shard%d_driver.csv" % shard)
    out_i = os.path.join(D, "kstar_empty_split_shard%d_instance.csv" % shard)
    done = set()
    if os.path.exists(out_i):
        with open(out_i, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add((r["alignment"], r["n"], r["n_gw"], r["n_od"], r["rep"]))

    fh_d, fh_i, wd, wi = None, None, None, None
    t0 = time.time()
    k = 0
    for (a, n, ng, no, rep) in mine:
        key = (str(a), str(n), str(ng), str(no), str(rep))
        if key in done:
            continue
        d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
        pool, _ = C.build_pool(tt, d, o, 3)
        per_driver = kstar_split_for_instance(pool, q)

        nd = len(per_driver)
        n_feas = sum(1 for r in per_driver if r["feasible_empty"])
        n_kst = sum(1 for r in per_driver if r["kstar_empty"])
        n_fd = sum(1 for r in per_driver if r["fd_dominated"])
        nonempty = [r for r in per_driver if not r["feasible_empty"]]
        row_i = dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, n_drivers=nd,
                    n_feasible_empty=n_feas, n_kstar_empty=n_kst, n_fd_dominated=n_fd,
                    all_feasible_empty=(n_feas == nd), all_kstar_empty=(n_kst == nd),
                    all_nonempty_fd_dominated=(len(nonempty) > 0 and all(r["fd_dominated"] for r in nonempty)),
                    n_nonempty=len(nonempty))

        if fh_d is None:
            new_d = not os.path.exists(out_d)
            new_i = not os.path.exists(out_i)
            fh_d = open(out_d, "a", newline="", encoding="utf-8")
            fh_i = open(out_i, "a", newline="", encoding="utf-8")
            wd = csv.DictWriter(fh_d, fieldnames=["alignment", "n", "n_gw", "n_od", "rep"] + list(per_driver[0].keys()))
            wi = csv.DictWriter(fh_i, fieldnames=list(row_i.keys()))
            if new_d:
                wd.writeheader()
            if new_i:
                wi.writeheader()
        for pd in per_driver:
            wd.writerow(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, **pd))
        wi.writerow(row_i)
        fh_d.flush(); fh_i.flush()
        k += 1
        if k % 50 == 0:
            print("[shard %d] %d/%d, %.1f min" % (shard, k, len(mine) - len(done), (time.time() - t0) / 60.0))
            sys.stdout.flush()
    print("[shard %d] FINISHED %d new instances in %.1f min" % (shard, k, (time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
