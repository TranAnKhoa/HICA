"""Checklist_diagnosis.md - Phan A (pickup-clustering, H1) + Phan B (route-pool
richness, H2). KHONG chay lai run_2b_v2.py - doc lai 720 file 2b_v2_raw/*.json
(meta co du tham so de tai tao DUNG instance qua stable_seed + generate_instance,
dung cong thuc GIONG HET run_2b_v2.run_one), cong voi pool_sizes_by_driver da
luu san trong JSON cho phan B.

Khong dung CPLEX, khong giai DP lai - chi doc meta + tai tao instance (nhe, rat
nhanh) de lay orders/pickup_node.
"""

import csv
import glob
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_GLOB = os.path.join(ROOT, "results", "2b_v2_raw", "*.json")
OUT_CSV = os.path.join(ROOT, "results", "checklist_diagnosis.csv")


def load_all():
    files = sorted(glob.glob(RAW_GLOB))
    rows = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        rec = d["record"]
        meta = d["meta"]
        if rec.get("status") != "completed":
            continue

        n = meta["n"]; B_gw = meta["B_gw"]; B_od = meta["B_od"]
        tau = meta["tau"]; spatial_mode = meta["spatial_mode"]
        supply_ratio = meta["supply_ratio"] if "supply_ratio" in meta else rec["supply_ratio"]
        seed = meta["seed"]
        n_drivers = meta["n_drivers"]

        gen_seed = IG.stable_seed(n, B_gw, B_od, tau, spatial_mode, supply_ratio, seed, "spec2b_v2")
        drivers, orders, tt, _meta2 = IG.generate_instance(
            n=n, B_gw=B_gw, B_od=B_od, tw_width=meta["tw_width"], n_drivers=n_drivers,
            seed=gen_seed, tau=float(tau), spatial_mode=spatial_mode)

        # ---- A1/A2: pickup-node clustering ---------------------------------
        pickup_nodes = [o["pickup_node"] for o in orders.values()]
        n_orders = len(pickup_nodes)
        n_distinct_pickup = len(set(pickup_nodes))
        ratio = n_distinct_pickup / n_orders if n_orders > 0 else None

        from collections import Counter
        cnt = Counter(pickup_nodes)
        top_count = max(cnt.values()) if cnt else 0
        top1_share = top_count / n_orders if n_orders > 0 else None
        top2_share = (sum(c for _, c in cnt.most_common(2)) / n_orders) if n_orders > 0 else None

        # ---- B1: route-pool richness ----------------------------------------
        pool_sizes = d.get("pool_sizes_by_driver", {})
        avg_pool_size = statistics.mean(pool_sizes.values()) if pool_sizes else None
        max_pool_size = max(pool_sizes.values()) if pool_sizes else None

        lcf = rec["largest_component_fraction"]

        rows.append(dict(
            n=n, B_gw=B_gw, B_od=B_od, tau=tau, spatial_mode=spatial_mode,
            supply_ratio=supply_ratio, seed=seed, n_drivers=n_drivers,
            n_orders=n_orders, n_distinct_pickup=n_distinct_pickup, ratio=ratio,
            top1_share=top1_share, top2_share=top2_share,
            avg_pool_size=avg_pool_size, max_pool_size=max_pool_size,
            n_components=rec["n_components"], largest_component_fraction=lcf,
            component_sizes=rec["component_sizes"],
        ))
    return rows


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def rank(vals):
        idx = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and vals[idx[j + 1]] == vals[idx[i]]:
                j += 1
            avg_rank = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                ranks[idx[k]] = avg_rank
            i = j + 1
        return ranks
    return pearson(rank(xs), rank(ys))


def mean(vals):
    vals = [v for v in vals if v is not None]
    return statistics.mean(vals) if vals else None


def main():
    rows = load_all()
    print("Loaded %d completed cells from 2b_v2_raw/" % len(rows))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [k for k in rows[0].keys() if k != "component_sizes"] + ["component_sizes"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            row = dict(r)
            row["component_sizes"] = "|".join(str(x) for x in r["component_sizes"])
            w.writerow(row)
    print("-> %s" % OUT_CSV)

    # ================= A1: overall ratio distribution =====================
    print("\n=== A1: ratio = n_distinct_pickup / n_orders (toan bo %d cell) ===" % len(rows))
    ratios = [r["ratio"] for r in rows]
    print("mean=%.4f  min=%.4f  max=%.4f  median=%.4f"
          % (mean(ratios), min(ratios), max(ratios), statistics.median(ratios)))

    def group_mean(key_fn):
        g = {}
        for r in rows:
            k = key_fn(r)
            g.setdefault(k, []).append(r["ratio"])
        return {k: (mean(v), len(v)) for k, v in g.items()}

    print("\n-- ratio theo n --")
    for k, (m, c) in sorted(group_mean(lambda r: r["n"]).items()):
        print("  n=%s  mean(ratio)=%.4f  (n_obs=%d)" % (k, m, c))

    print("\n-- ratio theo spatial_mode --")
    for k, (m, c) in sorted(group_mean(lambda r: r["spatial_mode"]).items()):
        print("  mode=%s  mean(ratio)=%.4f  (n_obs=%d)" % (k, m, c))

    print("\n-- ratio theo supply_ratio --")
    for k, (m, c) in sorted(group_mean(lambda r: r["supply_ratio"]).items()):
        print("  supply_ratio=%s  mean(ratio)=%.4f  (n_obs=%d)" % (k, m, c))

    # ============= C2: dispersed vs clustered tren CUNG n, seed ============
    print("\n=== C2: dispersed vs clustered tren CUNG (n, tau, supply_ratio, seed) ===")
    by_key = {}
    for r in rows:
        k = (r["n"], r["B_gw"], r["B_od"], r["tau"], r["supply_ratio"], r["seed"])
        by_key.setdefault(k, {})[r["spatial_mode"]] = r["ratio"]
    diffs = []
    for k, v in by_key.items():
        if "dispersed" in v and "clustered" in v:
            diffs.append(v["dispersed"] - v["clustered"])
    if diffs:
        print("n_pairs=%d  mean(dispersed-clustered)=%.5f  max|diff|=%.5f"
              % (len(diffs), mean(diffs), max(abs(x) for x in diffs)))
    else:
        print("Khong tim thay cap dispersed/clustered cung tham so con lai.")

    # ================= A3: 18 cell lech vs con lai =========================
    print("\n=== A3: ratio cua cell lcf<1.000 vs cell lcf=1.000 ===")
    dev = [r for r in rows if r["largest_component_fraction"] < 0.999]
    rest = [r for r in rows if r["largest_component_fraction"] >= 0.999]
    print("n cell lcf<0.999: %d   n cell lcf>=0.999: %d" % (len(dev), len(rest)))
    if dev:
        print("  mean(ratio) cell LECH     = %.4f" % mean([r["ratio"] for r in dev]))
    if rest:
        print("  mean(ratio) cell KHONG lech = %.4f" % mean([r["ratio"] for r in rest]))

    # ================= B1: avg_pool_size vs lcf =============================
    print("\n=== B1: avg_pool_size vs largest_component_fraction ===")
    xs = [r["avg_pool_size"] for r in rows]
    ys = [r["largest_component_fraction"] for r in rows]
    pr = pearson(xs, ys)
    sr = spearman(xs, ys)
    print("avg_pool_size: mean=%.1f  min=%.1f  max=%.1f" % (mean(xs), min(xs), max(xs)))
    print("Pearson(avg_pool_size, lcf)  = %s" % ("%.4f" % pr if pr is not None else "N/A"))
    print("Spearman(avg_pool_size, lcf) = %s" % ("%.4f" % sr if sr is not None else "N/A"))

    print("\n-- avg_pool_size theo B_gw,B_od --")
    g = {}
    for r in rows:
        g.setdefault((r["B_gw"], r["B_od"]), []).append(r["avg_pool_size"])
    for k, v in sorted(g.items()):
        print("  (Bgw,Bod)=%s  mean(avg_pool_size)=%.1f  (n_obs=%d)" % (k, mean(v), len(v)))

    # ================= B2: xac suat chong lap ly thuyet tho =================
    print("\n=== B2: xac suat chong lap ly thuyet tho (mo hinh route chon ngau nhien B order) ===")
    # P(2 route KHONG giao nhau) xap xi ((n-B)/n)^B cho 1 cap route; ap dung tho
    # cho ca pool: P(2 driver KHONG co bat ky cap route nao giao nhau) rat nho
    # neu pool lon - chi bao cao 1 uoc luong ĐON GIAN cho 1 cap route dai dien
    # (B = capacity trung binh cua GW/OD, n = n_orders cell).
    sample = rows[:5] + rows[len(rows) // 2:len(rows) // 2 + 5] + rows[-5:]
    for r in sample:
        n_o = r["n_orders"]
        B_avg = (r["B_gw"] + r["B_od"]) / 2.0
        if n_o > B_avg:
            p_no_overlap_1pair = ((n_o - B_avg) / n_o) ** B_avg
        else:
            p_no_overlap_1pair = 0.0
        p_overlap_1pair = 1 - p_no_overlap_1pair
        print("  n=%d Bgw=%d Bod=%d avg_pool=%.0f  P(2 route giao nhau, tho)=%.4f  lcf_that=%.4f"
              % (r["n"], r["B_gw"], r["B_od"], r["avg_pool_size"], p_overlap_1pair,
                 r["largest_component_fraction"]))

    return rows


if __name__ == "__main__" and (len(sys.argv) <= 1 or sys.argv[1] != "c1"):
    main()


# ============================================================================
# Phan C1: tau la bien chinh hay phu? Dac diem driver bi co lap trong 18 cell
# ============================================================================

def part_c1():
    import conflict_graph as CG
    import dp_labeling as DL

    files = sorted(glob.glob(RAW_GLOB))
    out_rows = []
    n_dev_cells = 0
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        rec = d["record"]
        meta = d["meta"]
        if rec.get("status") != "completed":
            continue
        if rec["largest_component_fraction"] >= 0.999:
            continue
        n_dev_cells += 1

        n = meta["n"]; B_gw = meta["B_gw"]; B_od = meta["B_od"]
        tau = meta["tau"]; spatial_mode = meta["spatial_mode"]
        supply_ratio = rec["supply_ratio"]; seed = meta["seed"]
        n_drivers = meta["n_drivers"]

        gen_seed = IG.stable_seed(n, B_gw, B_od, tau, spatial_mode, supply_ratio, seed, "spec2b_v2")
        drivers, orders, tt, _m = IG.generate_instance(
            n=n, B_gw=B_gw, B_od=B_od, tw_width=meta["tw_width"], n_drivers=n_drivers,
            seed=gen_seed, tau=float(tau), spatial_mode=spatial_mode)

        pool_by_driver, agg = DL.build_route_pool(tt, drivers, orders, B_gw, B_od)
        nodes, edges = CG.build_conflict_graph(pool_by_driver)

        adj = {nd: set() for nd in nodes}
        for e in edges:
            a, b = tuple(e)
            adj[a].add(b); adj[b].add(a)

        isolated = [nd for nd in nodes if len(adj[nd]) == 0]
        pool_sizes = d.get("pool_sizes_by_driver", {})
        driver_by_id = {dv["id"]: dv for dv in drivers}

        for iso in isolated:
            dv = driver_by_id.get(iso, {})
            out_rows.append(dict(
                n=n, B_gw=B_gw, B_od=B_od, tau=tau, spatial_mode=spatial_mode,
                supply_ratio=supply_ratio, seed=seed,
                isolated_driver=iso, cls=dv.get("cls"),
                pool_size_isolated=pool_sizes.get(iso),
                avg_pool_size_others=statistics.mean(
                    v for k, v in pool_sizes.items() if k != iso) if len(pool_sizes) > 1 else None,
                lcf=rec["largest_component_fraction"],
            ))

    print("\n=== C1: dac diem driver bi co lap trong %d cell lech ===" % n_dev_cells)
    print("Tong so driver co lap tim duoc: %d" % len(out_rows))
    n_gw_iso = sum(1 for r in out_rows if r["cls"] == "GW")
    n_od_iso = sum(1 for r in out_rows if r["cls"] == "OD")
    print("  GW co lap: %d   OD co lap: %d" % (n_gw_iso, n_od_iso))

    pool_iso = [r["pool_size_isolated"] for r in out_rows if r["pool_size_isolated"] is not None]
    pool_others = [r["avg_pool_size_others"] for r in out_rows if r["avg_pool_size_others"] is not None]
    if pool_iso:
        print("  mean(pool_size cua driver CO LAP)      = %.1f" % statistics.mean(pool_iso))
    if pool_others:
        print("  mean(avg_pool_size cua driver KHAC trong cung cell) = %.1f" % statistics.mean(pool_others))

    out_csv = os.path.join(ROOT, "results", "checklist_diagnosis_c1_isolated.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        if out_rows:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            for r in out_rows:
                w.writerow(r)
    print("-> %s" % out_csv)
    return out_rows


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "c1":
    part_c1()
