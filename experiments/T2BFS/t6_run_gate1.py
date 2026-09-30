"""Test6.md Viec 1 - Gate 1.A/1.B/1.C, GATE QUAN TRONG NHAT toan chuoi test.

Doi chieu run_dp() (t6_dp.py) voi brute_force() (t2_core.py, DA CO tu Test2,
KHONG viet lai) tren grid nho n<=6, B<=4, GW+OD.

Gate 1.A: bundle_exists_DP == bundle_exists_TRUTH, moi S, moi instance.
Gate 1.B: moi diem Pareto TRUTH, DP co diem (K'<=K, W'<=W) tuong ung.
Gate 1.C: moi diem Pareto DP, PHAI co sequence THAT (kiem lai bang
          is_feasible() GOC cua t2_core, khong phai feasibility rieng cua DP)
          dat dung (K,W) do.

BAT KY vi pham nao: DUNG NGAY, in phan vi du day du.
"""

import csv
import hashlib
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
import t6_dp as D

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")
SESSION = 6

N_ORDERS_SMALL = (3, 4, 5, 6)
B_GRID = (2, 3, 4)
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL
EPS = 1e-6


def seed_from(*parts):
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def _kw_of_walk(driver, travel_time, walk):
    ok, slack, sched = C.is_feasible(travel_time, driver, walk)
    if not ok:
        return None
    return P.K_W_of_route(driver, travel_time, walk, sched)


def pareto_filter_kw(kw_list):
    """kw_list: [(K,W,payload)]. Tra list con Pareto-optimal (minimize K,W)."""
    n = len(kw_list)
    dominated = [False] * n
    for i in range(n):
        Ki, Wi, _ = kw_list[i]
        for j in range(n):
            if i == j:
                continue
            Kj, Wj, _ = kw_list[j]
            if Kj <= Ki + EPS and Wj <= Wi + EPS and (Kj < Ki - EPS or Wj < Wi - EPS):
                dominated[i] = True
                break
    return [kw_list[i] for i in range(n) if not dominated[i]]


def run_instance_gate(travel_time, driver, orders, B, n, tw, tau, seed_idx, cls):
    order_ids = sorted(orders.keys())
    bf, bf_stats = C.brute_force(travel_time, driver, orders, B)

    dp_result = D.run_dp(travel_time, driver, orders, B, use_dominance=True)
    complete_by_C = dp_result["complete_by_C"]

    violations = []

    for k in range(1, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            truth_entries = bf.get(S, [])
            bundle_exists_truth = len(truth_entries) > 0
            dp_labels = complete_by_C.get(S, [])
            bundle_exists_dp = len(dp_labels) > 0

            # Gate 1.A
            if bundle_exists_dp != bundle_exists_truth:
                violations.append(dict(
                    gate="1.A", n=n, B=B, cls=cls, tw=tw, tau=tau, seed=seed_idx,
                    S=sorted(S), detail="DP=%s TRUTH=%s" % (bundle_exists_dp, bundle_exists_truth),
                ))
                continue
            if not bundle_exists_truth:
                continue

            # Pareto TRUTH: tinh K/W tren walk that (dung is_feasible goc + K_W_of_route)
            truth_kw = []
            for canon, slack, walk in truth_entries:
                kw = _kw_of_walk(driver, travel_time, walk)
                if kw is None:
                    continue   # khong the xay ra (walk da feasible tu brute_force) - an toan
                K, W = kw
                truth_kw.append((K, W, canon))
            truth_pareto = pareto_filter_kw(truth_kw)

            # Pareto DP: finalize K/W tu moi label hoan chinh, loc Pareto
            dp_kw = []
            for lab in dp_labels:
                K, W = D.finalize_KW(driver, lab)
                dp_kw.append((K, W, lab))
            dp_pareto = pareto_filter_kw(dp_kw)

            # Gate 1.B: moi diem TRUTH pareto phai co diem DP (K'<=K,W'<=W)
            for (Kt, Wt, canon_t) in truth_pareto:
                found = any(Kd <= Kt + EPS and Wd <= Wt + EPS for (Kd, Wd, _) in dp_pareto)
                if not found:
                    violations.append(dict(
                        gate="1.B", n=n, B=B, cls=cls, tw=tw, tau=tau, seed=seed_idx,
                        S=sorted(S), detail="TRUTH point (K=%.4f,W=%.4f) canon=%s KHONG co DP diem tuong ung; DP_pareto=%s"
                                             % (Kt, Wt, canon_t, [(round(K,4), round(W,4)) for K,W,_ in dp_pareto]),
                    ))

            # Gate 1.C: moi diem DP pareto phai co sequence THAT dat dung (K,W)
            # (kiem bang is_feasible GOC cua walk truy vet tu label - walk suy
            # tu label.path(), roi doi chieu is_feasible + K_W_of_route)
            for (Kd, Wd, lab) in dp_pareto:
                walk = _walk_from_label(driver, orders, lab)
                ok, slack, sched = C.is_feasible(travel_time, driver, walk)
                if not ok:
                    violations.append(dict(
                        gate="1.C", n=n, B=B, cls=cls, tw=tw, tau=tau, seed=seed_idx,
                        S=sorted(S), detail="DP diem (K=%.4f,W=%.4f) label path=%s KHONG feasible khi kiem lai bang is_feasible goc"
                                             % (Kd, Wd, [a for a,v,t,K,W in lab.path()]),
                    ))
                    continue
                K_real, W_real = P.K_W_of_route(driver, travel_time, walk, sched)
                if abs(K_real - Kd) > 1e-4 or abs(W_real - Wd) > 1e-4:
                    violations.append(dict(
                        gate="1.C", n=n, B=B, cls=cls, tw=tw, tau=tau, seed=seed_idx,
                        S=sorted(S), detail="DP bao (K=%.4f,W=%.4f) nhung walk that dat (K=%.4f,W=%.4f) - lech cong thuc K/W"
                                             % (Kd, Wd, K_real, W_real),
                    ))

    return violations, dp_result


def _walk_from_label(driver, orders, lab):
    """Truy vet path cua label, tra walk = [WNode,...] tuong ung de kiem lai
    bang is_feasible GOC cua t2_core."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    walk = [start]
    for action, v, t, K, W in lab.path()[1:]:
        kind, oid = action
        if kind == "pickup":
            walk.append(pd[oid][0])
        elif kind == "delivery":
            walk.append(pd[oid][1])
        elif kind == "home":
            walk.append(home)
    return walk


def run_cell(rng, n, B, cls, tw, tau, seed_idx):
    driver, orders, tt, meta = G.build_instance(rng, SESSION, n, cls, tw, tau, B)
    if cls == "OD":
        import t3_check_k1 as K1
        rate, ok = K1.check_and_warn(driver, orders, tt,
            label="n=%d B=%d %s tw=%d tau=%s seed=%d" % (n, B, cls, tw, tau, seed_idx))
        if not ok:
            return [], None
    violations, dp_result = run_instance_gate(tt, driver, orders, B, n, tw, tau, seed_idx, cls)
    return violations, dp_result


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_violations = []
    t0 = time.time()
    n_cells = 0
    n_instances = 0

    for n in N_ORDERS_SMALL:
        for B in B_GRID:
            if n < B:
                continue
            for cls in ("GW", "OD"):
                tw_or_tau_grid = TW_WIDTH_GRID if cls == "GW" else TAU_GRID
                for twtau in tw_or_tau_grid:
                    for sd in range(SEEDS_PER_CELL):
                        n_cells += 1
                        if cls == "GW":
                            tw, tau = twtau, None
                        else:
                            tw, tau = 240, twtau   # OD: tw_width co dinh, quet tau (giong Test3/4 pattern)
                        rng = random.Random(seed_from(n, B, cls, tw, tau, sd, "t6gate1"))
                        try:
                            violations, dp_result = run_cell(rng, n, B, cls, tw, tau, sd)
                        except SystemExit as e:
                            print("  [skip] %s" % e)
                            continue
                        if violations is None:
                            continue
                        n_instances += 1
                        if violations:
                            all_violations.extend(violations)
                            print("!!! %d VIOLATION(S) tai n=%d B=%d %s tw=%s tau=%s seed=%d"
                                  % (len(violations), n, B, cls, tw, tau, sd))
                            for v in violations[:3]:
                                print("    ", v)
                            # DUNG NGAY theo spec Sec2.2/Sec6
                            _write_violations(all_violations)
                            print("\n*** GATE FAILED - DUNG NGAY theo spec Test6 Sec2.2/Sec6 ***")
                            print("elapsed=%.1fs, instances checked=%d" % (time.time() - t0, n_instances))
                            return 1
        print("  n=%d done, %.1fs, instances=%d, violations=%d"
              % (n, time.time() - t0, n_instances, len(all_violations)))

    _write_violations(all_violations)
    print("\n=== GATE1 SUMMARY ===")
    print("instances checked: %d, cells: %d" % (n_instances, n_cells))
    print("violations: %d" % len(all_violations))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


def _write_violations(violations):
    with open(os.path.join(OUT, "gate1_violations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gate", "n", "B", "cls", "tw", "tau", "seed", "S", "detail"])
        w.writeheader()
        w.writerows(violations)


if __name__ == "__main__":
    sys.exit(main())
