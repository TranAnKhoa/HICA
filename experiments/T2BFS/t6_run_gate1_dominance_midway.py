"""Test6.md Sec2.3 - kiem dominance ap dung GIUA CHUNG (IV != rong) co an
toan khong: chay DP_full (KHONG dominance dau) va DP_prune (dominance xuyen
suot, dung run_dp use_dominance=True), so sanh MOI label hoan chinh ma
DP_full tim duoc co bi DP_prune BO SOT (khong tim duoc label hoan chinh cung
C, K<=, W<=) hay khong.

Day la cau hoi trung tam cua Test6 - neu pass tuyet doi, gia thuyet Sec0
duoc xac nhan thuc nghiem (khac han Test4 Viec4 dominance GIUA cac route DA
XONG cua cac tap S khac nhau, o do KHONG sound).

DUNG: Output/Test6/gate1_sec23_violations.csv
"""

import csv
import itertools
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_gen as G
import t6_dp as D
import t6_run_gate1 as G1

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")

# Test6.1 Viec1: vá lỗ hổng seed cua Test6 goc (SEEDS_PER_CELL 4->8, khop Gate1
# chinh) VA mo rong n toi 6 (khop bien tren Gate1 chinh) - xem Test6.1.md Sec1.
# Da kiem: n=6,B=4,GW,tw=240 khong bung no (100415 label DP_full, 0.9s/instance).
N_ORDERS = (3, 4, 5, 6)
B_GRID = (2, 3, 4)
TW_WIDTH_GRID = G.TW_WIDTH_GRID
TAU_GRID = G.TAU_GRID
SEEDS_PER_CELL = 8   # Test6.1: khop dung Gate1 chinh (khong con 4 nhu Test6 goc)
EPS = 1e-6


def check_instance(tt, driver, orders, B):
    """Tra list violation (rong neu pass)."""
    full = D.run_dp(tt, driver, orders, B, use_dominance=False)
    prune = D.run_dp(tt, driver, orders, B, use_dominance=True)

    violations = []
    for Cset, full_labs in full["complete_by_C"].items():
        prune_labs = prune["complete_by_C"].get(Cset, [])
        for flab in full_labs:
            Kf, Wf = D.finalize_KW(driver, flab)
            found = False
            for plab in prune_labs:
                Kp, Wp = D.finalize_KW(driver, plab)
                if flab.v == plab.v and Kp <= Kf + EPS and Wp <= Wf + EPS:
                    found = True
                    break
            if not found:
                violations.append(dict(
                    C=sorted(Cset), v=flab.v, K_full=Kf, W_full=Wf,
                    path=[(a, vv) for a, vv, t, K, W in flab.path()],
                ))
    return violations, full, prune


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
                        rng = random.Random(G1.seed_from(n, B, cls, tw, tau, sd, "t6sec23"))
                        try:
                            driver, orders, tt, meta = G.build_instance(rng, 6, n, cls, tw, tau, B)
                        except SystemExit as e:
                            continue
                        if cls == "OD":
                            import t3_check_k1 as K1
                            rate, ok = K1.check_and_warn(driver, orders, tt, label="sec23")
                            if not ok:
                                continue
                        violations, full, prune = check_instance(tt, driver, orders, B)
                        n_instances += 1
                        if violations:
                            for v in violations:
                                v.update(n=n, B=B, cls=cls, tw=tw, tau=tau, seed=sd)
                            all_violations.extend(violations)
                            print("!!! SEC2.3 VIOLATION n=%d B=%d %s tw=%s tau=%s seed=%d: %d label(s) mat"
                                  % (n, B, cls, tw, tau, sd, len(violations)))
                            for v in violations[:3]:
                                print("    ", v)
                            _write(all_violations)
                            print("\n*** SEC2.3 FAILED - DUNG NGAY ***")
                            return 1
        print("  n=%d done, %.1fs, instances=%d" % (n, time.time() - t0, n_instances))

    _write(all_violations)
    print("\n=== SEC2.3 SUMMARY ===")
    print("instances checked: %d, violations: %d" % (n_instances, len(all_violations)))
    print("elapsed=%.1fs" % (time.time() - t0))
    return 0


def _write(violations):
    # Test6.1 Viec1: ghi file RIENG, KHONG de len gate1_sec23_violations.csv
    # cua Test6 goc - giu ca hai de doi chieu (spec Test6.1 Sec1: "so sanh 4
    # vs 8 co doi ket luan khong").
    path = os.path.join(OUT, "gate1_sec23_violations_v2_seed8.csv")
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
