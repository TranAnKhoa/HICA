"""Algorithms B and C with HiGHS (CPLEX is not available in this container).

The model is the one of experiments/T2BFS/t8_cplex.py, unchanged: one binary x per route, one binary z per order
(order to FD at price q_o), every order covered exactly once, every driver at most one route; minimise total cost.
Single thread, relative and absolute MIP gap 0. Algorithm C = naive Clarke pivots: one re-solve without each winner.
"""
import time

import highspy
import numpy as np


TIME_LIMIT = 600.0   # seconds per MIP solve; a solve that hits it is reported, not hidden


def solve_wdp(pool, theta, q, order_ids, excluded=None):
    """pool: {driver: {bundle: [(K, W), ...]}}. Returns dict(z, status, assign {driver: (S, cost)}, fd, wall)."""
    oidx = {o: k for k, o in enumerate(order_ids)}
    cols = []                                     # (cost, rows, driver, bundle)
    for did, p in pool.items():
        if did == excluded:
            continue
        for S, kws in p.items():
            if not S:
                continue
            for (K, W) in kws:
                cols.append((K + theta[did] * W, [oidx[o] for o in S], did, S))
    for o in order_ids:
        cols.append((q[o], [oidx[o]], None, frozenset([o])))
    drivers = sorted({c[2] for c in cols if c[2] is not None})
    didx = {d: len(order_ids) + k for k, d in enumerate(drivers)}
    n_rows = len(order_ids) + len(drivers)
    starts, index, value = [], [], []
    for (c, rows, did, S) in cols:
        starts.append(len(index))
        rr = list(rows) + ([didx[did]] if did is not None else [])
        index.extend(rr)
        value.extend([1.0] * len(rr))
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("threads", 1)
    h.setOptionValue("mip_rel_gap", 0.0)
    h.setOptionValue("mip_abs_gap", 0.0)
    h.setOptionValue("time_limit", TIME_LIMIT)
    lp = highspy.HighsLp()
    nc = len(cols)
    lp.num_col_ = nc
    lp.num_row_ = n_rows
    lp.col_cost_ = np.array([c[0] for c in cols], dtype=float)
    lp.col_lower_ = np.zeros(nc)
    lp.col_upper_ = np.ones(nc)
    lp.row_lower_ = np.array([1.0] * len(order_ids) + [-highspy.kHighsInf] * len(drivers))
    lp.row_upper_ = np.ones(n_rows)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(starts + [len(index)], dtype=np.int32)
    lp.a_matrix_.index_ = np.array(index, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(value, dtype=float)
    lp.integrality_ = [highspy.HighsVarType.kInteger] * nc
    h.passModel(lp)
    t0 = time.perf_counter()
    h.run()
    wall = time.perf_counter() - t0
    status = h.modelStatusToString(h.getModelStatus())
    x = h.getSolution().col_value
    assign, fd = {}, []
    for k, (c, rows, did, S) in enumerate(cols):
        if x[k] > 0.5:
            if did is None:
                fd.extend(S)
            else:
                assign[did] = (S, c)
    return dict(z=h.getInfo().objective_function_value, status=status, assign=assign, fd=fd, wall=wall,
                n_cols=nc)


def vcg(pool, theta, q, order_ids):
    """Algorithm B (base solve) + Algorithm C (one removal solve per winner)."""
    base = solve_wdp(pool, theta, q, order_ids)
    pay, statuses, t_c = {}, [base["status"]], 0.0
    for did, (S, c) in base["assign"].items():
        rm = solve_wdp(pool, theta, q, order_ids, excluded=did)
        statuses.append(rm["status"])
        t_c += rm["wall"]
        pay[did] = c + rm["z"] - base["z"]
    return dict(Z=base["z"], pay=pay, winners=len(base["assign"]), fd=len(base["fd"]), t_B=base["wall"],
                t_C=t_c, statuses=statuses, n_cols=base["n_cols"])
