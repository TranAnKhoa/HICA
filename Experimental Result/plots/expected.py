"""Figure.md §4 'Sanity' blocks — every expected value, with its [MASTER] section.
(value, printed decimals). Do not edit to fit data."""

ALIGNS = [0.10, 0.30, 0.50, 0.70, 0.90]

# §3.3 / FIG 8a — [MASTER] §15.1, mean over instances of JOINT/B3 FD rate
FD_RATE = {"vals": [0.830, 0.812, 0.949, 0.691, 0.374], "dec": 3}

FIG_C1 = {"E_rc_18": (37.4, 1), "c_rc_18": (32.6, 1), "c_ra_18": (16.8, 1), "cross_ra": (15.0, 1)}

# FIG 2 — [MASTER] §13 table (medians, s)
FIG2 = {
    0.90: {"t_A": [0.65, 2.20, 7.40], "t_C_naive": [0.134, 0.248, 0.655], "t_C_accel": [0.060, 0.144, 0.259]},
    0.50: {"t_A": [0.26, 1.00, 2.56], "t_C_naive": [0.039, 0.086, 0.186]},
}

# FIG 3 — [MASTER] §13
FIG3 = {
    "pay_only": {0.50: [11.20, 17.98, 30.40], 0.90: [2.34, 1.81, 2.72]},
    "incl_build": {0.50: [1.13, 0.63, 0.60], 0.90: [1.44, 1.05, 1.24]},
    "pooled_pay": 3.01, "pooled_incl": 1.06, "max_pay_err": "1.1e-13",
}

# FIG 4 — [MASTER] §1.3 item 3, [S2]
FIG4 = {
    "median_per_inst": {3: 1.48, 4: 2.19}, "pooled": {3: 1.72, 4: 2.94},
    "ext_saved": {3: [44.2, 35.5, 57.3, 50.1, 39.4], 4: [61.0, 49.5, 76.2, 69.7, 55.8]},
}
LABEL_INSTANCES = ["n12_seed42", "n10_seed1", "n15_seed7", "n12_seed123", "n10_seed999"]

# FIG 5 — [MASTER] §10 (bootstrap seed used there: 20260928)
FIG5 = {"median": [0.00, 0.00, 0.00, 0.77, 5.84], "mean": [0.33, 0.51, 0.04, 1.39, 6.06],
        "ci090": (5.68, 6.46), "ci_seed": 20260928, "median090_by_n": [5.01, 5.84, 7.00], "dropped": 0}

# FIG 6 — [MASTER] §11.1–11.2 (bootstrap seed used there: 20260927)
FIG6 = {"median090": {"B2": 6.37, "B3": 11.32, "B4": 15.16, "HEUR": 4.94},
        "mean090_B3": 11.47, "ci090_B3": (10.92, 12.02), "ci_seed": 20260927,
        "b3_vs_heur_median090": 5.61,
        # MASTER §11.2 "4.0% (n=10) and 5.7% (n=15)" = median (rq_analysis_tables.md: 4.02 / 5.66)
        "price_range_median090": {10: 4.0, 15: 5.7}}

# FIG 7 — [MASTER] §12.1–12.2 (seed 20260927)
FIG7 = {"premium_median": {"VCG": 14.13, "PAB": 5.78, "POSTED": 9.12},
        "vcg_mean": 15.05, "vcg_ci": (14.30, 15.79), "ci_seed": 20260927,
        "effloss_median": {"POSTED": 3.99, "PAB": 0.00}, "vcg_gt_pab": (300, 300)}

# FIG 8 — [MASTER] §15.1, §15.3
FIG8 = {"feas_empty": [14.8, 12.3, 43.1, 2.5, 0.1], "fd_dom": [20.4, 19.5, 34.3, 10.5, 1.0],
        "fd_feas_empty": 43.7, "fd_fd_dom": [52.0, 33.3, 13.0]}   # FD x0.75 / x1.00 / x1.25

# FIG 9 — [MASTER] §14 (seed 20260927)
FIG9 = {"V6_dbund": (1.38, 0.97, 1.81), "V5_dvcg": (-28.64, -43.31, -4.28),
        "V1_dbund": (-0.09, -0.17, -0.04), "ci_seed": 20260927}

# Appendix
FIGA1 = {"r600": 0.979, "r10": 0.988, "us_S2": (33, 41), "us_S2_n10s1": 66, "us_RQ4": (48, 54)}
FIGA2 = {"cut050": 100.0, "cut090": [75.2, 76.6, 77.2]}
FIGA3 = {"full090": 1.000, "k090": 1.000, "k050": 0.250, "multi_k090": (22, 300)}
FIGA5 = {"median": [1.34, 9.95, 18.48], "within300": 60}
