"""T4 rerun on Data Fix v2 (recreate1.md) full grid -- sampled, not exhaustive.

Axis: (n, gamma, cluster_share), cluster_mode=pickup_hub except share=0.0
(=random, the control).  n=30 dropped from the sample: pilot timing showed
a single n=30/cluster_share=0.9/gamma=2.0 driver alone taking 68s at B=5
(recreate1.md 0.1a's factorial warning realized), making a same-size sample
to n<=20 impractical within this session's budget.  See T4_report.md 1 for
the cost figures this decision is based on.
"""
import csv, glob, itertools, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_atl as A

ROOT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Dataset", "instances", "main")
OUT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "DataFixV2")
N_SAMPLE = (10, 15, 20)
GAMMA_SAMPLE = (0.0, 0.5, 1.0, 1.5, 2.0)
SHARE_SAMPLE = (0.0, 0.3, 0.6, 0.9)
PER_CELL = 2
LIMIT_S = 90.0   # per-instance wall clock cap (recreate1.md 7 spirit)

FIELDS = ["n_orders", "gamma", "cluster_mode", "cluster_share", "instance_id",
          "driver", "k", "orders", "mst_bound", "one_tree_bound", "budget",
          "prune_mst", "prune_1tree", "feasible",
          "dfs_time_s", "mst_time_s", "one_tree_time_s"]


def measure(inst, i, S, meta, viol, w):
    t0 = time.perf_counter(); mb = A.mst_bound(inst, i, S)
    t1 = time.perf_counter(); ob = A.one_tree_bound(inst, i, S)
    t2 = time.perf_counter(); bud = A.budget(inst, S)
    pm = mb > bud; p1 = ob > bud
    t3 = time.perf_counter(); feas = A.is_feasible(inst, i, S)
    t4 = time.perf_counter()
    if feas and (pm or p1):
        viol.append({"iid": inst.iid, "driver": i, "S": S})
    w.append(meta + [i, len(S), "|".join(map(str, S)), "%.6f" % mb, "%.6f" % ob,
                     "%.6f" % bud, int(pm), int(p1), int(feas),
                     "%.9f" % (t4 - t3), "%.9f" % (t1 - t0), "%.9f" % (t2 - t1)])
    return feas


def run():
    with open(os.path.join(ROOT, "MANIFEST.csv")) as f:
        man = {r["instance_id"]: r for r in csv.DictReader(f)}

    cells = {}
    for iid, r in man.items():
        n = int(r["n"]); g = float(r["gamma"]); cs = float(r["cluster_share"])
        if n not in N_SAMPLE or g not in GAMMA_SAMPLE or cs not in SHARE_SAMPLE:
            continue
        cells.setdefault((n, g, cs), []).append(iid)
    rng = random.Random(20260821)
    todo = []
    for key in sorted(cells):
        ids = sorted(cells[key])
        rng.shuffle(ids)
        todo.extend(ids[:PER_CELL])

    viol, skipped, nrows = [], [], 0
    t_all = time.time()
    fh = open(os.path.join(OUT, "T4_cluster_raw.csv"), "w", newline="", encoding="utf-8")
    w = csv.writer(fh); w.writerow(FIELDS)
    prev = None; cell_rows = cell_inst = 0; cell_t0 = time.time()
    for iid in todo:
        r = man[iid]
        path = os.path.join(ROOT, iid + ".json")
        inst = A.AtlInstance(path)
        meta = [int(r["n"]), float(r["gamma"]), r["cluster_mode"],
                float(r["cluster_share"]), iid]
        key = (int(r["n"]), float(r["gamma"]), float(r["cluster_share"]))
        if prev is not None and key != prev:
            print("  n=%-3d g=%.1f cs=%.1f  inst=%-2d rows=%-7d %.1fs"
                  % (prev[0], prev[1], prev[2], cell_inst, cell_rows, time.time() - cell_t0))
            sys.stdout.flush(); cell_rows = cell_inst = 0; cell_t0 = time.time()
        prev = key

        t0 = time.perf_counter(); buf = []; timed_out = False
        for i in range(inst.m):
            if time.perf_counter() - t0 > LIMIT_S:
                timed_out = True; break
            surv = [o for o in range(inst.n) if A.is_feasible(inst, i, [o])]
            level = [[o] for o in surv]
            for k in range(2, 6):
                nxt, seen = [], set()
                for S in level:
                    for o in surv:
                        if o in S:
                            continue
                        S2 = tuple(sorted(S + [o]))
                        if S2 in seen:
                            continue
                        seen.add(S2)
                        if measure(inst, i, list(S2), meta, viol, buf):
                            nxt.append(list(S2))
                level = nxt
                if viol:
                    fh.close()
                    print("\nSOUNDNESS FAIL"); print(viol[:5])
                    return 1
                if not level:
                    break
        if timed_out:
            skipped.append({"instance_id": iid, "elapsed_s": time.perf_counter() - t0})
            continue
        w.writerows(buf); nrows += len(buf)
        cell_rows += len(buf); cell_inst += 1
    if prev is not None:
        print("  n=%-3d g=%.1f cs=%.1f  inst=%-2d rows=%-7d %.1fs"
              % (prev[0], prev[1], prev[2], cell_inst, cell_rows, time.time() - cell_t0))
    fh.close()

    meta = {"n_sample": N_SAMPLE, "gamma_sample": GAMMA_SAMPLE, "share_sample": SHARE_SAMPLE,
            "per_cell": PER_CELL, "n_instances_selected": len(todo),
            "n_instances_run": len(todo) - len(skipped), "n_subset_rows": nrows,
            "soundness_violations": len(viol), "instances_skipped_timeout": skipped,
            "wall_clock_s": time.time() - t_all,
            "note": "n=30 excluded from sample -- see module docstring"}
    with open(os.path.join(OUT, "T4_cluster_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("\nTONG: %d instance, %d subset rows, %.1fs, violations=%d, skipped=%d"
          % (meta["n_instances_run"], nrows, meta["wall_clock_s"], len(viol), len(skipped)))
    return 0


if __name__ == "__main__":
    sys.exit(run())
