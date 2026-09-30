"""T4 - runner tren dataset Atlanta (mau, khong chay het).

Mau:
  main    : 20 instance / o (n x tw_tightness_factor), 4x3 o  -> 240 instance
            (dung so luong voi lan chay tong hop Test1 goc de so sanh duoc)
  scale_a : 3 instance / o cho n in {50,75,100,150}          -> 36 instance
Chi driver GW. Quy trinh do va soundness gate giu nguyen spec muc 3 / 2.5.
"""
import csv, glob, itertools, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_atl as A

ROOT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Dataset", "instances")
OUT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "T4_ATL")
LIMIT = 60.0
SAMPLE_MAIN = 20
SAMPLE_SCALE = 3
SCALE_N = [50, 75, 100]

FIELDS = ["source", "instance_id", "n_orders", "tw_factor", "session", "rho_gw",
          "od_alignment", "driver", "k", "orders", "mst_bound", "one_tree_bound",
          "budget", "prune_mst", "prune_1tree", "feasible",
          "dfs_time_s", "mst_time_s", "one_tree_time_s"]


def manifest(sub):
    rows = {}
    with open(os.path.join(ROOT, sub, "MANIFEST.csv"), "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["instance_id"]] = r
    return rows


def pick(sub, n_values, per_cell, rng):
    man = manifest(sub)
    cells = {}
    for iid, r in man.items():
        n = int(r["n"]); tw = float(r["tw_tightness_factor"])
        if n not in n_values:
            continue
        cells.setdefault((n, tw), []).append(iid)
    out = []
    for key in sorted(cells):
        ids = sorted(cells[key])
        rng.shuffle(ids)
        for iid in ids[:per_cell]:
            out.append((sub, iid, man[iid]))
    return out


def measure(inst, i, S, meta, viol, w):
    t0 = time.perf_counter(); mb = A.mst_bound(inst, i, S)
    t1 = time.perf_counter(); ob = A.one_tree_bound(inst, i, S)
    t2 = time.perf_counter(); bud = A.budget(inst, S)
    pm = mb > bud; p1 = ob > bud
    t3 = time.perf_counter(); feas = A.is_feasible(inst, i, S)
    t4 = time.perf_counter()
    if feas and (pm or p1):                     # ---- SOUNDNESS GATE (2.5) ----
        viol.append({"iid": inst.iid, "driver": i, "S": S, "mst": mb,
                     "one_tree": ob, "budget": bud})
    w.append(meta + [i, len(S), "|".join(map(str, S)), "%.6f" % mb, "%.6f" % ob,
                     "%.6f" % bud, int(pm), int(p1), int(feas),
                     "%.9f" % (t4 - t3), "%.9f" % (t1 - t0), "%.9f" % (t2 - t1)])
    return feas


def run():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    rng = random.Random(20260821)
    todo = pick("main", {10, 15, 20, 30}, SAMPLE_MAIN, rng)
    todo += pick("scale_a", set(SCALE_N), SAMPLE_SCALE, rng)

    viol = []; skipped = []; nrows = 0
    t_all = time.time()
    fh = open(os.path.join(OUT, "T4_ATL_raw.csv"), "w", newline="", encoding="utf-8")
    w = csv.writer(fh); w.writerow(FIELDS)

    prev = None
    cell_rows = cell_inst = 0; cell_t0 = time.time()
    for sub, iid, r in todo:
        path = os.path.join(ROOT, sub, iid + ".json")
        inst = A.AtlInstance(path)
        meta = [sub, iid, int(r["n"]), float(r["tw_tightness_factor"]),
                int(r["session"]), float(r["rho_GW"]), float(r["od_alignment"])]
        key = (sub, int(r["n"]), float(r["tw_tightness_factor"]))
        if prev is not None and key != prev:
            print("  %-8s n=%-4d tw=%.2f  inst=%-3d rows=%-7d %.1fs"
                  % (prev[0], prev[1], prev[2], cell_inst, cell_rows, time.time() - cell_t0))
            sys.stdout.flush(); cell_rows = cell_inst = 0; cell_t0 = time.time()
        prev = key

        t0 = time.perf_counter(); buf = []; timed_out = False
        for i in range(inst.m):
            if time.perf_counter() - t0 > LIMIT:
                timed_out = True; break
            surv = [o for o in range(inst.n) if A.is_feasible(inst, i, [o])]
            pairs = []
            for S in itertools.combinations(surv, 2):
                S = list(S)
                if measure(inst, i, S, meta, viol, buf):
                    pairs.append(S)
            seen = set()
            for S2 in pairs:
                for o in surv:
                    if o in S2:
                        continue
                    S3 = tuple(sorted(S2 + [o]))
                    if S3 in seen:
                        continue
                    seen.add(S3)
                    measure(inst, i, list(S3), meta, viol, buf)
            if viol:
                fh.close()
                print("\n" + "!" * 70)
                print("SOUNDNESS GATE FAIL - DUNG NGAY (spec 2.5)")
                for v in viol[:10]:
                    print(json.dumps(v))
                return 1
        if timed_out:
            skipped.append({"instance_id": iid, "elapsed_s": time.perf_counter() - t0})
            continue
        w.writerows(buf); nrows += len(buf)
        cell_rows += len(buf); cell_inst += 1
    if prev is not None:
        print("  %-8s n=%-4d tw=%.2f  inst=%-3d rows=%-7d %.1fs"
              % (prev[0], prev[1], prev[2], cell_inst, cell_rows, time.time() - cell_t0))
    fh.close()

    meta = {"dataset": "Dataset/instances (hica-s/instance/2.1, Atlanta ARC,Road)",
            "spec": "Guideline/Test1.md (thuat toan muc 2-4 giu nguyen)",
            "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sampling": {"main_per_cell": SAMPLE_MAIN, "scale_a_per_cell": SAMPLE_SCALE,
                         "scale_a_n": SCALE_N, "rng_seed": 20260821,
                         "urgency_folder": "khong dung (theo yeu cau)"},
            "n_instances_run": len(todo) - len(skipped),
            "n_instances_selected": len(todo),
            "n_subset_rows": nrows,
            "drivers": "chi GW (capacity theo dataset, = 3)",
            "bounds_on_symmetrized_graph": "min(T[a][b], T[b][a]) - van la can duoi hop le",
            "soundness_violations": len(viol),
            "instances_skipped_timeout": skipped,
            "wall_clock_s": time.time() - t_all}
    with open(os.path.join(OUT, "T4_ATL_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print("\nTONG: %d instance, %d subset rows, %.1fs, violations=%d, skipped=%d"
          % (meta["n_instances_run"], nrows, meta["wall_clock_s"], len(viol), len(skipped)))
    return 0


if __name__ == "__main__":
    sys.exit(run())
