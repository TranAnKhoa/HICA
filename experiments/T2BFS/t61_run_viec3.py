"""Test6.1.md Viec 3 - kiem bang brute-force DOC LAP, khong dung logic
t6_dp.py CHO PHAN TINH K/W (chi dung run_dp() de lay Front_DP, nhung K/W cua
CA HAI phia deu tinh qua compute_KW_independent() rieng o day - KHONG import
t4_profile, de loai rui ro "cung diem mu" (Sec3.2 spec: neu ca hai dung
chung 1 ham quy doi km/phut sai, Gate 1 goc se pass gia).

Mo rong n toi 7 (Test6 goc chi toi 6).

DUNG: Output/Test6/viec3_independent_check.csv
"""

import csv
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t6_dp as D
import t6_run_gate1 as G1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")

N_ORDERS = (4, 5, 6, 7)   # mo rong toi 7 (Test6 goc chi toi 6)
B_GRID = (2, 3, 4)
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = G.SEEDS_PER_CELL
EPS = 1e-6
KAPPA = 1.0   # HANG SO RIENG, khong import tu t4_profile.KAPPA (du gia tri
              # giong nhau - day la 1 lua chon DOC LAP, khong phai tham chieu)


def _kw_independent_from_walk(travel_time_fn, driver, walk, speed_kmh):
    """Tinh K (kappa*km), W (gio) TU DAU tu walk + travel_time_fn, hoan toan
    KHONG goi t4_profile. speed_kmh truyen vao TUONG MINH (khong import
    G.SPEED_KMH ngam dinh o dau khac - o day VAN dung t2_gen.SPEED_KMH vi do
    la THAM SO MO HINH khong phai logic tinh toan, nhung phep quy doi
    phut->km duoc VIET LAI o day, khong goi ham co san nao)."""
    total_min = 0.0
    for i in range(1, len(walk)):
        total_min += travel_time_fn(walk[i - 1].id, walk[i].id)
    dist_km = total_min * speed_kmh / 60.0

    ok, slack, sched = C.is_feasible(travel_time_fn, driver, walk)
    if not ok:
        return None
    active_time_min = sched[-1][2] - driver["t0"]

    if driver["cls"] == "OD":
        direct_dist_km = driver["direct_time"] * speed_kmh / 60.0
        K = KAPPA * max(0.0, dist_km - direct_dist_km)
        W = max(0.0, (active_time_min - driver["direct_time"]) / 60.0)
    else:
        K = KAPPA * dist_km
        W = active_time_min / 60.0
    return K, W


def _walk_from_dp_label(driver, orders, lab):
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


def pareto_filter_kw(pts):
    n = len(pts)
    dominated = [False] * n
    for i in range(n):
        Ki, Wi = pts[i]
        for j in range(n):
            if i == j:
                continue
            Kj, Wj = pts[j]
            if Kj <= Ki + EPS and Wj <= Wi + EPS and (Kj < Ki - EPS or Wj < Wi - EPS):
                dominated[i] = True
                break
    return [pts[i] for i in range(n) if not dominated[i]]


def check_instance(travel_time, driver, orders, B, speed_kmh):
    order_ids = sorted(orders.keys())
    bf, bf_stats = C.brute_force(travel_time, driver, orders, B)
    dp_result = D.run_dp(travel_time, driver, orders, B, use_dominance=True)

    violations = []
    for k in range(1, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            truth_entries = bf.get(S, [])
            truth_exists = len(truth_entries) > 0
            dp_labels = dp_result["complete_by_C"].get(S, [])
            dp_exists = len(dp_labels) > 0

            if truth_exists != dp_exists:
                violations.append(dict(S=sorted(S), issue="EXISTENCE_MISMATCH",
                                        truth_exists=truth_exists, dp_exists=dp_exists))
                continue
            if not truth_exists:
                continue

            truth_kw = []
            for canon, slack, walk in truth_entries:
                kw = _kw_independent_from_walk(travel_time, driver, walk, speed_kmh)
                if kw is not None:
                    truth_kw.append(kw)
            truth_pareto = pareto_filter_kw(truth_kw)

            dp_kw = []
            for lab in dp_labels:
                walk = _walk_from_dp_label(driver, orders, lab)
                kw = _kw_independent_from_walk(travel_time, driver, walk, speed_kmh)
                if kw is not None:
                    dp_kw.append(kw)
            dp_pareto = pareto_filter_kw(dp_kw)

            for (Kt, Wt) in truth_pareto:
                if not any(Kd <= Kt + EPS and Wd <= Wt + EPS for (Kd, Wd) in dp_pareto):
                    violations.append(dict(S=sorted(S), issue="TRUTH_MISSING_IN_DP",
                                            point="(%.4f,%.4f)" % (Kt, Wt)))
            for (Kd, Wd) in dp_pareto:
                if not any(Kt <= Kd + EPS and Wt <= Wd + EPS for (Kt, Wt) in truth_pareto):
                    violations.append(dict(S=sorted(S), issue="DP_NOT_IN_TRUTH_PARETO",
                                            point="(%.4f,%.4f)" % (Kd, Wd)))
    return violations


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    all_violations = []
    t0 = time.time()
    n_instances = 0

    for n in N_ORDERS:
        for B in B_GRID:
            if n < B:
                continue
            for cls in ("GW", "OD"):
                grid = TW_WIDTH_GRID if cls == "GW" else TAU_GRID
                for twtau in grid:
                    for sd in range(SEEDS_PER_CELL):
                        if cls == "GW":
                            tw, tau = twtau, None
                        else:
                            tw, tau = 240, twtau
                        rng = random.Random(G1.seed_from(n, B, cls, tw, tau, sd, "t61viec3"))
                        try:
                            driver, orders, tt, meta = G.build_instance(rng, G1.SESSION, n, cls, tw, tau, B)
                        except SystemExit as e:
                            continue
                        if cls == "OD":
                            import t3_check_k1 as K1
                            rate, ok = K1.check_and_warn(driver, orders, tt, label="t61viec3")
                            if not ok:
                                continue
                        violations = check_instance(tt, driver, orders, B, G.SPEED_KMH)
                        n_instances += 1
                        if violations:
                            for v in violations:
                                v.update(n=n, B=B, cls=cls, tw=tw, tau=tau, seed=sd)
                            all_violations.extend(violations)
                            print("!!! VIEC3 VIOLATION n=%d B=%d %s tw=%s tau=%s seed=%d: %d"
                                  % (n, B, cls, tw, tau, sd, len(violations)))
                            for v in violations[:5]:
                                print("    ", v)
                            _write(all_violations)
                            print("\n*** VIEC3 FAILED - kiem xem Gate1 goc co bo sot khong ***")
                            return 1
        print("  n=%d done, %.1fs, instances=%d" % (n, time.time() - t0, n_instances))

    _write(all_violations)
    print("\n=== VIEC3 (independent brute-force) SUMMARY ===")
    print("instances checked: %d, violations: %d" % (n_instances, len(all_violations)))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


def _write(violations):
    path = os.path.join(OUT, "viec3_independent_check.csv")
    if not violations:
        with open(path, "w", newline="", encoding="utf-8") as f:
            f.write("no violations\n")
        return
    fields = sorted(set(k for v in violations for k in v.keys()))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(violations)


if __name__ == "__main__":
    sys.exit(main())
