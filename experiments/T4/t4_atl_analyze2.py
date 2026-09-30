"""T4 Atlanta - tong hop metric. Don vi lap lai (thay cho 'seed') = instance."""
import json, os, sys
import numpy as np, pandas as pd

OUT = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "T4_ATL2")
RAW = os.path.join(OUT, "T4_ATL2_raw.csv")


def per_inst(df, keys):
    g = df.groupby(keys + ["instance_id"], observed=True)
    out = g.apply(lambda d: pd.Series({
        "n_subsets": len(d),
        "n_infeasible": int(d["feasible"].eq(0).sum()),
        "prune_rate_mst": d["prune_mst"].mean(),
        "prune_rate_1tree": d["prune_1tree"].mean(),
        "infeasible_rate": 1.0 - d["feasible"].mean(),
        "recall_mst": (np.nan if d["feasible"].eq(0).sum() == 0
                       else d.loc[d["feasible"].eq(0), "prune_mst"].mean()),
        "recall_1tree": (np.nan if d["feasible"].eq(0).sum() == 0
                         else d.loc[d["feasible"].eq(0), "prune_1tree"].mean()),
    }), include_groups=False).reset_index()
    out["improvement_1tree_over_mst"] = out["recall_1tree"] - out["recall_mst"]
    return out


def mi(s):
    s = s.dropna()
    return "n/a" if len(s) == 0 else "%.3f [%.3f-%.3f]" % (
        s.median(), s.quantile(0.25), s.quantile(0.75))


def summarize(idf, keys):
    rows = []
    for key, d in idf.groupby(keys, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        r = dict(zip(keys, key))
        r["n_instances"] = len(d)
        r["subsets_total"] = int(d["n_subsets"].sum())
        r["infeasible_total"] = int(d["n_infeasible"].sum())
        for m in ["infeasible_rate", "prune_rate_mst", "prune_rate_1tree",
                  "recall_mst", "recall_1tree", "improvement_1tree_over_mst"]:
            r[m] = mi(d[m])
        rows.append(r)
    return pd.DataFrame(rows)


def pooled_block(d):
    inf = d["feasible"].eq(0)
    p = {"n_subsets": int(len(d)), "n_infeasible": int(inf.sum()),
         "infeasible_rate": float(inf.mean()),
         "prune_rate_mst": float(d["prune_mst"].mean()),
         "prune_rate_1tree": float(d["prune_1tree"].mean()),
         "recall_mst": float(d.loc[inf, "prune_mst"].mean()),
         "recall_1tree": float(d.loc[inf, "prune_1tree"].mean()),
         "false_prune_mst": int((d["prune_mst"].eq(1) & ~inf).sum()),
         "false_prune_1tree": int((d["prune_1tree"].eq(1) & ~inf).sum()),
         "avg_dfs_time_s": float(d["dfs_time_s"].mean()),
         "avg_mst_time_s": float(d["mst_time_s"].mean()),
         "avg_one_tree_time_s": float(d["one_tree_time_s"].mean())}
    p["improvement_1tree_over_mst"] = p["recall_1tree"] - p["recall_mst"]
    p["time_saved_mst_s"] = float(d["prune_mst"].sum() * p["avg_dfs_time_s"]
                                  - len(d) * p["avg_mst_time_s"])
    p["time_saved_1tree_s"] = float(d["prune_1tree"].sum() * p["avg_dfs_time_s"]
                                    - len(d) * p["avg_one_tree_time_s"])
    return p


def main():
    df = pd.read_csv(RAW)
    mn = df[df["source"] == "main"]

    tabs = {}
    tabs["MAIN_TABLE"] = summarize(per_inst(mn, ["n_orders", "gamma"]),
                                   ["n_orders", "gamma"]).sort_values(["n_orders", "gamma"])
    tabs["BY_GAMMA"] = summarize(per_inst(mn, ["gamma"]), ["gamma"]).sort_values("gamma")
    tabs["BY_K"] = summarize(per_inst(mn, ["gamma", "k"]),
                             ["gamma", "k"]).sort_values(["gamma", "k"])
    tabs["BY_K_FULL"] = summarize(per_inst(mn, ["n_orders", "gamma", "k"]),
                                  ["n_orders", "gamma", "k"]).sort_values(["n_orders", "gamma", "k"])
    sc = df[df["source"] == "scale_a"]
    tabs["SCALE_A"] = summarize(per_inst(sc, ["n_orders", "gamma"]),
                                ["n_orders", "gamma"]).sort_values(["n_orders", "gamma"])
    for k, v in tabs.items():
        v.to_csv(os.path.join(OUT, "T4_ATL2_%s.csv" % k), index=False)

    pooled = {"main": pooled_block(mn), "scale_a": pooled_block(sc),
              "all": pooled_block(df)}
    for g in sorted(mn["gamma"].unique()):
        pooled["main_gamma%.1f" % g] = pooled_block(mn[mn["gamma"] == g])
    for tf in sorted(mn["tau_floor"].unique()):
        pooled["main_taufloor%.0f" % tf] = pooled_block(mn[mn["tau_floor"] == tf])
    with open(os.path.join(OUT, "T4_ATL2_POOLED.json"), "w", encoding="utf-8") as f:
        json.dump(pooled, f, indent=2)

    pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40)
    tabs["BY_TAUFLOOR"] = summarize(per_inst(mn, ["tau_floor"]), ["tau_floor"]).sort_values("tau_floor")
    tabs["BY_TAUFLOOR"].to_csv(os.path.join(OUT, "T4_ATL2_BY_TAUFLOOR.csv"), index=False)
    cols = ["subsets_total", "infeasible_rate", "prune_rate_mst", "prune_rate_1tree",
            "recall_mst", "recall_1tree", "improvement_1tree_over_mst"]
    for name in ["MAIN_TABLE", "BY_GAMMA", "BY_TAUFLOOR", "BY_K", "SCALE_A"]:
        print("=== %s ===" % name)
        t = tabs[name]
        keys = [c for c in ["n_orders", "gamma", "k"] if c in t.columns]
        print(t[keys + ["n_instances"] + cols].to_string(index=False)); print()
    print("=== POOLED ===")
    print(json.dumps(pooled, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
