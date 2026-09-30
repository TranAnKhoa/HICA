"""Unit test cho ground truth is_feasible() (spec 2.1 yeu cau test rieng).

Dung mot Instance gia voi toa do dat tay de kiem soat chinh xac thoi gian.
Nho: time = distance_km * 3 (phut).
"""

import sys
import os
import itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import t4_core as C


class FakeInstance(object):
    """Instance dung toa do/deadline dat tay."""

    def __init__(self, order_coords, driver_coords, release, deadline):
        self.n = len(order_coords)
        self.m = len(driver_coords)
        coords = []
        for p, d in order_coords:
            coords.append(p)
            coords.append(d)
        coords.extend(driver_coords)
        self.coords = coords
        self.release = release
        self.deadline = deadline
        N = len(coords)
        T = [[0.0] * N for _ in range(N)]
        for a in range(N):
            for b in range(N):
                T[a][b] = ((coords[a][0] - coords[b][0]) ** 2 +
                           (coords[a][1] - coords[b][1]) ** 2) ** 0.5 * C.MIN_PER_KM
        self.T = T

    def driver_node(self, i):
        return 2 * self.n + i


def brute_force_feasible(inst, driver_i, S):
    """Tham chieu doc lap: liet ke TAT CA hoan vi cua 2k event, loc thu tu hop le,
    mo phong tuan tu. Cham nhung hien nhien dung."""
    k = len(S)
    events = []
    for j, o in enumerate(S):
        events.append((j, "P", 2 * o))
        events.append((j, "D", 2 * o + 1))
    for perm in itertools.permutations(events):
        seen_pickup = set()
        ok = True
        for j, kind, _ in perm:
            if kind == "P":
                seen_pickup.add(j)
            else:
                if j not in seen_pickup:
                    ok = False
                    break
        if not ok:
            continue
        t = C.AVAILABLE_FROM
        cur = inst.driver_node(driver_i)
        load = 0
        good = True
        for j, kind, node in perm:
            o = S[j]
            t = t + inst.T[cur][node]
            if kind == "P":
                if t < inst.release[o]:
                    t = inst.release[o]
                load += 1
                if load > C.DRIVER_CAPACITY:
                    good = False
                    break
            else:
                load -= 1
                if load < 0:
                    good = False
                    break
            if t > inst.deadline[o] or t > C.AVAILABLE_UNTIL:
                good = False
                break
            cur = node
        if good:
            return True
    return False


def check(name, got, want):
    status = "PASS" if got == want else "FAIL"
    print("[%s] %s  (got=%s want=%s)" % (status, name, got, want))
    return got == want


def main():
    ok = True

    # --- T1: mot don, du thoi gian -------------------------------------
    # driver (0,0), pickup (0,0), delivery (1,0) -> 3 phut. deadline 100.
    inst = FakeInstance([((0.0, 0.0), (1.0, 0.0))], [(0.0, 0.0)], [0.0], [100.0])
    ok &= check("T1 single order feasible", C.is_feasible(inst, 0, [0]), True)

    # --- T2: cung hinh, deadline qua chat -------------------------------
    inst = FakeInstance([((0.0, 0.0), (1.0, 0.0))], [(0.0, 0.0)], [0.0], [2.0])
    ok &= check("T2 single order deadline vi pham", C.is_feasible(inst, 0, [0]), False)

    # --- T3: release bat tai xe cho -> tre deadline ---------------------
    # release=50, deadline=51: pickup luc 50, delivery luc 53 > 51 -> infeasible
    inst = FakeInstance([((0.0, 0.0), (1.0, 0.0))], [(0.0, 0.0)], [50.0], [51.0])
    ok &= check("T3 cho release lam tre deadline", C.is_feasible(inst, 0, [0]), False)
    # deadline=55 -> kip
    inst = FakeInstance([((0.0, 0.0), (1.0, 0.0))], [(0.0, 0.0)], [50.0], [55.0])
    ok &= check("T3b cho release van kip", C.is_feasible(inst, 0, [0]), True)

    # --- T4: available_until = 240 chan -------------------------------
    # pickup xa: (0,0)->(90,0) = 270 phut > 240
    inst = FakeInstance([((90.0, 0.0), (91.0, 0.0))], [(0.0, 0.0)], [0.0], [1e9])
    ok &= check("T4 vuot available_until", C.is_feasible(inst, 0, [0]), False)

    # --- T5: capacity = 2 chan bundle 3 don khong the xen ke -----------
    # 3 don pickup cung cho, delivery cung cho, khoang cach 0 het.
    # Neu deadline rong thi VAN feasible vi co the lam tuan tu P-D-P-D-P-D.
    z = (0.0, 0.0)
    inst = FakeInstance([(z, z), (z, z), (z, z)], [z], [0.0] * 3, [1e6] * 3)
    ok &= check("T5 ba don khoang cach 0", C.is_feasible(inst, 0, [0, 1, 2]), True)

    # --- T6: doi chieu voi brute force tren instance ngau nhien --------
    mismatch = 0
    tested = 0
    for n, tw, seed in [(10, "TIGHT", 0), (10, "MEDIUM", 1), (15, "LOOSE", 2)]:
        real = C.Instance(n, tw, seed)
        for d in range(real.m):
            for S in itertools.combinations(range(real.n), 2):
                if tested >= 400:
                    break
                a = C.is_feasible(real, d, list(S))
                b = brute_force_feasible(real, d, list(S))
                tested += 1
                if a != b:
                    mismatch += 1
                    print("   MISMATCH n=%d tw=%s seed=%d driver=%d S=%s dfs=%s bf=%s"
                          % (n, tw, seed, d, S, a, b))
    for n, tw, seed in [(10, "MEDIUM", 3), (10, "LOOSE", 4)]:
        real = C.Instance(n, tw, seed)
        cnt = 0
        for d in range(real.m):
            for S in itertools.combinations(range(real.n), 3):
                if cnt >= 150:
                    break
                a = C.is_feasible(real, d, list(S))
                b = brute_force_feasible(real, d, list(S))
                cnt += 1
                tested += 1
                if a != b:
                    mismatch += 1
                    print("   MISMATCH k=3 n=%d tw=%s seed=%d driver=%d S=%s dfs=%s bf=%s"
                          % (n, tw, seed, d, S, a, b))
    ok &= check("T6 DFS == brute force tren %d subset" % tested, mismatch, 0)

    # --- T7: tinh chat cua can (bound <= thoi gian di chuyen that) ------
    # kiem tra 1-tree >= MST khong bat buoc, nhung ca hai phai >= 0
    real = C.Instance(10, "MEDIUM", 0)
    bad = 0
    for d in range(real.m):
        for S in itertools.combinations(range(real.n), 2):
            mb = C.mst_bound(real, d, list(S))
            ob = C.one_tree_bound(real, d, list(S))
            if mb < 0 or ob < 0:
                bad += 1
    ok &= check("T7 bound khong am", bad, 0)

    print()
    print("KET QUA: %s" % ("TAT CA PASS" if ok else "CO TEST FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
