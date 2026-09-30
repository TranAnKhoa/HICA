"""Figure.md §2/§5 — registry of input files D1–D12 and loaders. Read-only: nothing here
re-solves, regenerates or interpolates anything."""
import glob
import json
import os
import re

import pandas as pd

ROOT = r"K:\Data Science\Q1 Research"
RES = os.path.join(ROOT, "spec_2a_2b", "results")
RQ = os.path.join(RES, "rq_all")
NT4 = os.path.join(ROOT, "New_t4", "files")


def _g(pattern):
    return sorted(glob.glob(pattern))


# code -> (description, list of real paths)
FILES = {
    "D1": ("RQ1 main grid (5 treatments x 1500 instances)", [os.path.join(RES, "rq1_main_grid_results.csv")]),
    "D1b": ("RQ1 per-cell analysis (old convention; used only as a cross-check for fig05b)",
            [os.path.join(RES, "rq1_analysis_by_cell.csv")]),
    "D2": ("RQ1 complementarity gain recomputed (MASTER §10)",
           [os.path.join(RQ, "rq1_comp_gain_recomputed.csv"), os.path.join(RQ, "rq1_comp_gain_recomputed_by_n.csv")]),
    "D3": ("RQ2 results (menus B1/B2/B3/B4/HEUR)", _g(os.path.join(RQ, "rq2_shard*.csv"))),
    "D4": ("RQ3 results (same files as D5)", _g(os.path.join(RQ, "rq34_shard*.csv"))),
    "D5": ("RQ4 results (same files as D4)", _g(os.path.join(RQ, "rq34_shard*.csv"))),
    "D6": ("RQ5 results", _g(os.path.join(RQ, "rq5_shard*.csv"))),
    "D7": ("K* empty split (feasible_empty / fd_dominated)",
           [os.path.join(RQ, "kstar_empty_split_by_alignment.csv"),
            os.path.join(RQ, "kstar_empty_split_by_alignment_instance.csv"),
            os.path.join(RQ, "kstar_empty_split_by_fd_price.csv")]),
    "D8": ("K* build time reconciliation (10 points)", [os.path.join(RQ, "kstar_build_time_reconciliation.csv")]),
    "D9": ("Label rule timing summaries (per-instance median/IQR over repeats) + B+C runtime",
           [os.path.join(NT4, "timing_medians_B3.json"), os.path.join(NT4, "timing_medians_B3_seeds999.json"),
            os.path.join(NT4, "timing_medians_B4.json"), os.path.join(RES, "compare_bc_runtime.csv")]),
    "D10": ("Label rule results report (fallback, not used: D9 has the numbers)",
            [os.path.join(NT4, "Final_t4_Speedup_RESULTS.md")]),
    "D11": ("T5 component distribution on full vs K* pool", [os.path.join(RQ, "component_distribution_kstar.csv")]),
    "D12": ("Lookup tables and locked parameters",
            [os.path.join(RQ, "rq_analysis_tables.md"), os.path.join(RQ, "rq_all_locked_params.json"),
             os.path.join(RES, "rq1_locked_params.json")]),
    "D13": ("Synthetic audit log for Theorem 10 (test_family_exact.py output, AUDIT_REPORT.md §3)",
            [os.path.join(ROOT, "T4_audit_scripts", "T4_audit", "AUDIT_REPORT.md")]),
}


def _concat(paths):
    return pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)


def d1():
    return pd.read_csv(FILES["D1"][1][0])


def d1b():
    return pd.read_csv(FILES["D1b"][1][0])


def d2():
    return pd.read_csv(FILES["D2"][1][0]), pd.read_csv(FILES["D2"][1][1])


def d3():
    return _concat(FILES["D3"][1])


def d45():
    return _concat(FILES["D5"][1])


def d6():
    return _concat(FILES["D6"][1])


def d7():
    p = FILES["D7"][1]
    return pd.read_csv(p[0]), pd.read_csv(p[1]), pd.read_csv(p[2])


def d8():
    return pd.read_csv(FILES["D8"][1][0])


def d9_label():
    p = FILES["D9"][1]
    b3 = json.load(open(p[0]))
    b3_999 = json.load(open(p[1]))
    b4 = json.load(open(p[2]))
    return b3, b3_999, b4


def d11():
    return pd.read_csv(FILES["D11"][1][0])


def rq1_locked():
    return json.load(open(FILES["D12"][1][2]))


def d13_price_of_locality():
    """Parse the four log lines of test_family_exact.py quoted verbatim in AUDIT_REPORT.md §3."""
    txt = open(FILES["D13"][1][0], encoding="utf-8").read()
    pat = re.compile(r"n=(\d+): \|pool gw\|=(\d+) = sum C\(n,k\)=(\d+); \|K\*\(gw\)\|=(\d+); "
                     r"q0=[\d.]+; gw optimal in (\d+)/(\d+) sampled profiles; analytic certificate: (\w+)")
    rows = [dict(n=int(m[0]), pool=int(m[1]), binom_sum=int(m[2]), kstar=int(m[3]),
                 optimal=int(m[4]), profiles=int(m[5]), certificate=(m[6] == "True"))
            for m in pat.findall(txt)]
    return pd.DataFrame(rows)


def assert_unique(df, key, what):
    dup = df.duplicated(subset=key).sum()
    assert dup == 0, "%s: instance key %s not unique (%d duplicates)" % (what, key, dup)
