"""Shared setup for the FD-rule audit. Uses ONLY: spec_2a_2b/src (instance_gen, rq1_cost_gen,
dp_labeling, rq1_wdp, rq_common, kstar_zstar_payment_check), experiments/T2BFS (t6_dp, t8_cplex),
T4_audit_scripts/T4_audit (kstar_rule). Does NOT touch New_t4/files (older DFS engine)."""
import os, sys, random
ROOT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research")
for p in (os.path.join(ROOT, "T4_audit_scripts", "T4_audit"),
          os.path.join(ROOT, "experiments", "T2BFS"),
          os.path.join(ROOT, "spec_2a_2b", "src"),
          os.path.join(ROOT, "audit_fd_rule")):
    if p not in sys.path:
        sys.path.insert(0, p)
import instance_gen as IG
import rq1_cost_gen as RC
import dp_labeling as DL
import kstar_rule as KR
import fdrule_dp as F

LO, HI = RC.THETA_MIN, RC.THETA_MAX          # 18, 25 (locked)
LABEL_INSTANCES = [(12, 5, 42), (10, 4, 1), (15, 5, 7), (12, 6, 123), (10, 4, 999)]


def label_instance(n, nd, seed, B):
    """Same generator call as New_t4/files/dp_fast_rq1.build_hica_instance."""
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=120, n_drivers=nd, seed=seed, tau=30.0,
        spatial_mode="dispersed")
    q = RC.assign_q_o(orders, tt)
    return drivers, orders, tt, q


def sig(pool_by_driver):
    """Canonical signature set {(driver, frozenset(bundle), round(K,9), round(W,9))}."""
    return {(d, frozenset(S), round(K, 9), round(W, 9))
            for d, p in pool_by_driver.items() for S, kwl in p.items() for (K, W) in kwl}


def kstar_pool(pool_by_driver, q):
    import kstar_zstar_payment_check as KZ
    return KZ.prune_pool_by_kstar(pool_by_driver, q, LO, HI)
