"""Shard wrapper cho kstar_empty_rate.py part (i) - RQ1 main grid (1500
instance), de chay song song. Ghi ra CSV rieng theo shard, gop lai o
kstar_empty_rate_merge.py."""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rq_common as C
import kstar_empty_rate as CC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "results", "rq_all")


def main():
    shard, nsh = int(sys.argv[1]), int(sys.argv[2])
    jobs = [(a, n, ng, no, rep) for a in [0.10, 0.30, 0.50, 0.70, 0.90]
            for n in [10, 15, 20] for (ng, no) in [(2, 2), (3, 2), (2, 3), (3, 3)]
            for rep in range(25)]
    mine = [j for i, j in enumerate(jobs) if i % nsh == shard]
    out = os.path.join(D, "kstar_empty_shard%d.csv" % shard)
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add((r["alignment"], r["n"], r["n_gw"], r["n_od"], r["rep"]))
    fh, writer = None, None
    t0 = time.time()
    k = 0
    for (a, n, ng, no, rep) in mine:
        key = (str(a), str(n), str(ng), str(no), str(rep))
        if key in done:
            continue
        d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
        pool, _ = C.build_pool(tt, d, o, 3)
        nd, nempty, _ = CC.kstar_empty_for_instance(pool, q)
        row = dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, n_drivers=nd,
                  n_driver_kstar_empty=nempty, driver_empty_rate=nempty / float(nd),
                  instance_fully_fd=(nempty == nd))
        if fh is None:
            new = not os.path.exists(out)
            fh = open(out, "a", newline="", encoding="utf-8")
            writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
            if new:
                writer.writeheader()
        writer.writerow(row)
        fh.flush()
        k += 1
        if k % 50 == 0:
            print("[shard %d] %d/%d, %.1f min" % (shard, k, len(mine) - len(done), (time.time() - t0) / 60.0))
            sys.stdout.flush()
    print("[shard %d] FINISHED %d new rows in %.1f min" % (shard, k, (time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
