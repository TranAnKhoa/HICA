"""Figure.md §2.4 — logical name -> real column name. Plot scripts use only these names."""
# instance keys
KEY_RQ1 = ["alignment_target", "n", "n_gw", "n_od", "rep_idx"]   # D1
KEY = ["alignment", "n", "n_gw", "n_od", "rep"]                  # D3, D4/D5, D7, D11
KEY_RQ5 = ["variant", "n_gw", "n_od", "rep"]                      # D6 (pairing key within variant)
PAIR_RQ5 = ["n_gw", "n_od", "rep"]                                # V_k vs V0 pairing

# D1
ALIGN_RQ1, TREAT, TRUE_COST = "alignment_target", "treatment", "true_cost"
JOINT, GW_ONLY, OD_ONLY, OD_FIRST, GW_FIRST = "JOINT", "GW-ONLY", "OD-ONLY", "OD-FIRST", "GW-FIRST"

# D3
ALIGN, N, MENU, COST = "alignment", "n", "menu", "true_cost"
FD_RATE, POOL, T_A, T_B = "fd_rate", "pool_size", "t_A", "t_B"

# D4/D5
Z, VCG_PAY, PAB_PAY, POST_PAY = "Z", "vcg_payout", "pab_payout", "posted_payout"
PAB_TRUE, POST_TRUE = "pab_true_cost", "posted_true_cost"
POOL_FULL, POOL_KSTAR = "pool_full", "pool_kstar"
T_KSTAR, T_C_NAIVE, T_C_ACCEL, PAY_ERR, Z_ERR = "t_kstar", "t_C_naive", "t_C_accel", "pay_err", "z_err"

# D6
VARIANT, C_GW, C_OD, C_B1 = "variant", "C_gw_only", "C_od_only", "C_B1"
RENT, WIN_COST, T_TOTAL, N_SOLVES, N_OPT = "vcg_rent", "winner_true_cost", "t_total", "n_solves", "n_optimal"

# D7
FEAS_EMPTY, KSTAR_EMPTY, FD_DOM, FD_MULT = "feasible_empty", "kstar_empty", "fd_dominated", "fd_multiplier"

# D8
SRC, T_BUILD = "source", "t_kstar_build_s"

# D11
LCF_FULL, LCF_K, NCOMP_K = "largest_component_full_frac", "largest_component_kstar_frac", "n_components_kstar"
