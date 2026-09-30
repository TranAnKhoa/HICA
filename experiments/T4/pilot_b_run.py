"""PILOT-B (recreate1.md Sec0.1c/Sec5): time_saved breakeven point in B.

30 instance = B in {3,4,5} x 10 seed, cluster_mode=pickup_hub, share=0.6,
gamma=2.0 (Data Fix v2 PILOT winner).  Measures MST/1-tree prune recall and
time_saved exactly like the T4 rounds before it, GW drivers only.
"""
import csv, glob, itertools, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_atl as A

ROOT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Dataset",
                    "instances", "pilot_cluster_b")
OUT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "DataFixV2")

FIELDS = ["B", "instance_id", "driver", "k", "orders", "mst_bound",
          "one_tree_bound", "budget", "prune_mst", "prune_1tree", "feasible",
          "dfs_time_s", "mst_time_s", "one_tree_time_s"]


def measure(inst, i, S, B):
    t0 = time.perf_counter(); mb = A.mst_bound(inst, i, S)
    t1 = time.perf_counter(); ob = A.one_tree_bound(inst, i, S)
    t2 = time.perf_counter(); bud = A.budget(inst, S)
    pm = mb > bud; p1 = ob > bud
    t3 = time.perf_counter(); feas = A.is_feasible(inst, i, S)
    t4 = time.perf_counter()
    assert not (feas and (pm or p1)), "SOUNDNESS VIOLATION %s driver %d S %s" % (inst.iid, i, S)
    row = [B, inst.iid, i, len(S), "|".join(map(str, S)),
          "%.6f" % mb, "%.6f" % ob, "%.6f" % bud, int(pm), int(p1), int(feas),
          "%.9f" % (t4 - t3), "%.9f" % (t1 - t0), "%.9f" % (t2 - t1)]
    return feas, row


def run():
    files = sorted(f for f in glob.glob(os.path.join(ROOT, "*.json"))
                   if not f.endswith(".truth.json"))
    rows = []
    t_all = time.time()
    for fi, f in enumerate(files):
        inst = A.AtlInstance(f)
        with open(f) as fh:
            B = json.load(fh)["config"]["B"]
        t0 = time.perf_counter()
        for i in range(inst.m):
            surv = [o for o in range(inst.n) if A.is_feasible(inst, i, [o])]
            level = [[o] for o in surv]
            for k in range(2, B + 1):
                nxt, seen = [], set()
                for S in level:
                    for o in surv:
                        if o in S:
                            continue
                        S2 = tuple(sorted(S + [o]))
                        if S2 in seen:
                            continue
                        seen.add(S2)
                        feas, row = measure(inst, i, list(S2), B)
                        rows.append(row)
                        if feas:
                            nxt.append(list(S2))
                level = nxt
                if not level:
                    break
        print("  B=%d  %-45s  %.1fs  (%d/%d)" % (B, inst.iid[-45:],
              time.perf_counter() - t0, fi + 1, len(files)))
        sys.stdout.flush()

    with open(os.path.join(OUT, "PILOT_B_raw.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        w.writerows(rows)
    print("\n%d rows, %.1fs total" % (len(rows), time.time() - t_all))


if __name__ == "__main__":
    run()
