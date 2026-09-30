"""T4 - tong hop metric (spec Guideline/Test1.md, muc 4-5).

Bao cao median + IQR qua 20 seed (khong bao chi trung binh).
Ty le trong moi seed = gop tat ca driver cua instance do.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

OUT_DIR = os.path.join("k:" + os.sep, "Data Science", "Q1 Research", "Output", "T4")
RAW_CSV = os.path.join(OUT_DIR, "T4_raw.csv")

TW_ORDER = ["TIGHT", "MEDIUM", "LOOSE"]


def per_seed_stats(df, keys):
    """Tinh ty le trong tung seed roi tra ve dataframe theo keys+seed."""
    g = df.groupby(keys + ["seed"], observed=True)
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
        "fpr_mst": (np.nan if d["feasible"].eq(1).sum() == 0
                    else d.loc[d["feasible"].eq(1), "prune_mst"].mean()),
    }), include_groups=False).reset_index()
    out["improvement_1tree_over_mst"] = out["recall_1tree"] - out["recall_mst"]
    return out


def med_iqr(s):
    s = s.dropna()
    if len(s) == 0:
        return "n/a"
    return "%.3f [%.3f-%.3f]" % (s.median(), s.quantile(0.25), s.quantile(0.75))


def summarize(seed_df, keys):
    rows = []
    for key, d in seed_df.groupby(keys, observed=True):
        if not isinstance(key, tuple):
            key = (key,)
        r = dict(zip(keys, key))
        r["n_seeds"] = len(d)
        r["subsets_total"] = int(d["n_subsets"].sum())
        r["infeasible_total"] = int(d["n_infeasible"].sum())
        for m in ["prune_rate_mst", "prune_rate_1tree", "infeasible_rate",
                  "recall_mst", "recall_1tree", "improvement_1tree_over_mst",
                  "fpr_mst"]:
            r[m] = med_iqr(d[m])
            r[m + "_median"] = d[m].dropna().median() if d[m].notna().any() else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(RAW_CSV)
    df["tw"] = pd.Categorical(df["tw"], TW_ORDER, ordered=True)

    # ---------------- bang chinh: n_orders x TW -------------------------
    seed_main = per_seed_stats(df, ["n_orders", "tw"])
    main = summarize(seed_main, ["n_orders", "tw"]).sort_values(["n_orders", "tw"])
    main.to_csv(os.path.join(OUT_DIR, "T4_MAIN_TABLE.csv"), index=False)

    # ---------------- bang phu: theo k ----------------------------------
    seed_k = per_seed_stats(df, ["n_orders", "tw", "k"])
    byk = summarize(seed_k, ["n_orders", "tw", "k"]).sort_values(["n_orders", "tw", "k"])
    byk.to_csv(os.path.join(OUT_DIR, "T4_BY_K.csv"), index=False)

    seed_kk = per_seed_stats(df, ["tw", "k"])
    byk_tw = summarize(seed_kk, ["tw", "k"]).sort_values(["tw", "k"])
    byk_tw.to_csv(os.path.join(OUT_DIR, "T4_BY_K_POOLED.csv"), index=False)

    # ---------------- tong hop theo TW ----------------------------------
    seed_tw = per_seed_stats(df, ["tw"])
    tw_tab = summarize(seed_tw, ["tw"]).sort_values("tw")
    tw_tab.to_csv(os.path.join(OUT_DIR, "T4_BY_TW.csv"), index=False)

    # ---------------- pooled toan bo (dem tho) --------------------------
    inf = df["feasible"].eq(0)
    pooled = {
        "n_subsets": int(len(df)),
        "n_infeasible": int(inf.sum()),
        "infeasible_rate": float(inf.mean()),
        "prune_rate_mst": float(df["prune_mst"].mean()),
        "prune_rate_1tree": float(df["prune_1tree"].mean()),
        "recall_mst": float(df.loc[inf, "prune_mst"].mean()),
        "recall_1tree": float(df.loc[inf, "prune_1tree"].mean()),
        "false_prune_mst": int((df["prune_mst"].eq(1) & ~inf).sum()),
        "false_prune_1tree": int((df["prune_1tree"].eq(1) & ~inf).sum()),
        "avg_dfs_time_s": float(df["dfs_time_s"].mean()),
        "avg_mst_time_s": float(df["mst_time_s"].mean()),
        "avg_one_tree_time_s": float(df["one_tree_time_s"].mean()),
    }
    pooled["improvement_1tree_over_mst"] = pooled["recall_1tree"] - pooled["recall_mst"]
    pooled["time_saved_mst_s"] = (df["prune_mst"].sum() * pooled["avg_dfs_time_s"]
                                  - len(df) * pooled["avg_mst_time_s"])
    pooled["time_saved_1tree_s"] = (df["prune_1tree"].sum() * pooled["avg_dfs_time_s"]
                                    - len(df) * pooled["avg_one_tree_time_s"])
    for tw in TW_ORDER:
        d = df[df["tw"] == tw]
        i = d["feasible"].eq(0)
        pooled["time_saved_mst_s_" + tw] = float(
            d["prune_mst"].sum() * d["dfs_time_s"].mean()
            - len(d) * d["mst_time_s"].mean())
        pooled["time_saved_1tree_s_" + tw] = float(
            d["prune_1tree"].sum() * d["dfs_time_s"].mean()
            - len(d) * d["one_tree_time_s"].mean())
        pooled["recall_mst_" + tw] = float(d.loc[i, "prune_mst"].mean())
        pooled["recall_1tree_" + tw] = float(d.loc[i, "prune_1tree"].mean())
        pooled["prune_rate_mst_" + tw] = float(d["prune_mst"].mean())
        pooled["prune_rate_1tree_" + tw] = float(d["prune_1tree"].mean())
        pooled["infeasible_rate_" + tw] = float(i.mean())
    with open(os.path.join(OUT_DIR, "T4_POOLED.json"), "w", encoding="utf-8") as f:
        json.dump(pooled, f, indent=2)

    # ---------------- in ra man hinh ------------------------------------
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 50)
    print("=== BANG CHINH (median [IQR] qua 20 seed) ===")
    print(main[["n_orders", "tw", "subsets_total", "infeasible_rate",
                "prune_rate_mst", "prune_rate_1tree",
                "recall_mst", "recall_1tree", "improvement_1tree_over_mst"]]
          .to_string(index=False))
    print("\n=== THEO TW (gop moi n) ===")
    print(tw_tab[["tw", "subsets_total", "infeasible_rate", "prune_rate_mst",
                  "prune_rate_1tree", "recall_mst", "recall_1tree",
                  "improvement_1tree_over_mst"]].to_string(index=False))
    print("\n=== THEO k (gop moi n) ===")
    print(byk_tw[["tw", "k", "subsets_total", "infeasible_rate", "prune_rate_mst",
                  "prune_rate_1tree", "recall_mst", "recall_1tree",
                  "improvement_1tree_over_mst"]].to_string(index=False))
    print("\n=== POOLED ===")
    print(json.dumps(pooled, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
