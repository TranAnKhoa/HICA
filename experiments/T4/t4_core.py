"""T4 diagnostic experiment - core routines.

Spec: Guideline/Test1.md
Chi implement dung nhung gi spec yeu cau: sinh instance, DFS ground truth,
can duoi MST, can duoi 1-tree, luat cat. Khong OD, khong bid, khong toi uu hoa.
"""

import math
import random

# ---------------------------------------------------------------- constants
MAP_KM = 20.0
SPEED_KMH = 20.0
MIN_PER_KM = 60.0 / SPEED_KMH          # = 3 phut/km  (spec 1.1)
SERVICE_TIME = 0.0
BUNDLE_CAP = 3                          # B
DRIVER_CAPACITY = 2
AVAILABLE_FROM = 0.0
AVAILABLE_UNTIL = 240.0
RELEASE_MAX = 60.0

TW_GRID = {                             # spec 1.3 - KHOA, khong duoc sua
    "TIGHT": (10.0, 30.0),
    "MEDIUM": (30.0, 60.0),
    "LOOSE": (60.0, 120.0),
}
N_ORDERS_GRID = [10, 15, 20, 30]
N_SEEDS = 20


# ---------------------------------------------------------------- instance
class Instance(object):
    """Node indexing (global, dung chung cho ma tran thoi gian T):
        order o : pickup = 2*o, delivery = 2*o + 1
        driver i: start  = 2*n + i
    """

    __slots__ = ("n", "m", "tw", "seed", "coords", "release", "deadline", "T")

    def __init__(self, n, tw_name, seed):
        self.n = n
        self.m = max(3, n // 4)
        self.tw = tw_name
        self.seed = seed

        # RNG tach doi: hinh hoc chi phu thuoc (n, seed) => 3 cau hinh TW dung
        # CHUNG mot ban do va cung mot bo release  -> so sanh TIGHT/MEDIUM/LOOSE
        # la so sanh cap (paired), khac biet chi den tu slack.
        rng_geo = random.Random(1_000_000 + 1000 * n + seed)
        rng_slack = random.Random(9_000_000 + 1000 * n + seed)

        coords = []
        for _ in range(n):
            coords.append((rng_geo.uniform(0, MAP_KM), rng_geo.uniform(0, MAP_KM)))  # pickup
            coords.append((rng_geo.uniform(0, MAP_KM), rng_geo.uniform(0, MAP_KM)))  # delivery
        for _ in range(self.m):
            coords.append((rng_geo.uniform(0, MAP_KM), rng_geo.uniform(0, MAP_KM)))  # driver start
        self.coords = coords

        release = [rng_geo.uniform(0, RELEASE_MAX) for _ in range(n)]
        self.release = release

        lo, hi = TW_GRID[tw_name]
        deadline = []
        for o in range(n):
            px, py = coords[2 * o]
            dx, dy = coords[2 * o + 1]
            direct = math.hypot(px - dx, py - dy) * MIN_PER_KM
            deadline.append(release[o] + direct + rng_slack.uniform(lo, hi))
        self.deadline = deadline

        N = len(coords)
        T = [[0.0] * N for _ in range(N)]
        for a in range(N):
            xa, ya = coords[a]
            Ta = T[a]
            for b in range(a + 1, N):
                xb, yb = coords[b]
                w = math.hypot(xa - xb, ya - yb) * MIN_PER_KM
                Ta[b] = w
                T[b][a] = w
        self.T = T

    def driver_node(self, i):
        return 2 * self.n + i


# ------------------------------------------------- 2.1 feasibility (truth)
def is_feasible(inst, driver_i, S):
    """Ground truth. Duyet MOI thu tu pickup-delivery hop le (DFS, cat nhanh khi
    da vi pham deadline - vi thoi gian chi tang nen cat nay khong lam mat nghiem).
    Tra True ngay khi tim thay MOT thu tu kha thi.

    Rang buoc: pickup truoc delivery; load trong [0, capacity]; arrival <= deadline
    cua node (den som thi cho toi release, duoc phep); route xong truoc
    available_until.
    """
    k = len(S)
    if k == 0:
        return True
    T = inst.T
    release = inst.release
    deadline = inst.deadline
    full = (1 << k) - 1
    start = inst.driver_node(driver_i)

    def dfs(cur, t, picked, delivered, load):
        if delivered == full:
            return True
        Tc = T[cur]
        for j in range(k):
            bit = 1 << j
            o = S[j]
            if not (picked & bit):
                if load < DRIVER_CAPACITY:
                    nd = 2 * o
                    at = t + Tc[nd]
                    if at < release[o]:
                        at = release[o]
                    if at <= deadline[o] and at <= AVAILABLE_UNTIL:
                        if dfs(nd, at + SERVICE_TIME, picked | bit, delivered, load + 1):
                            return True
            elif not (delivered & bit):
                nd = 2 * o + 1
                at = t + Tc[nd]
                if at <= deadline[o] and at <= AVAILABLE_UNTIL:
                    if dfs(nd, at + SERVICE_TIME, picked, delivered | bit, load - 1):
                        return True
        return False

    return dfs(start, AVAILABLE_FROM, 0, 0, 0)


# ------------------------------------------------------ MST / 1-tree bounds
def _mst_weight(nodes, T):
    """Prim tren do thi day du (nodes = list chi so node global)."""
    m = len(nodes)
    if m <= 1:
        return 0.0
    INF = float("inf")
    in_tree = [False] * m
    dist = [INF] * m
    dist[0] = 0.0
    total = 0.0
    for _ in range(m):
        u = -1
        best = INF
        for i in range(m):
            if not in_tree[i] and dist[i] < best:
                best = dist[i]
                u = i
        in_tree[u] = True
        total += best
        Tu = T[nodes[u]]
        for i in range(m):
            if not in_tree[i]:
                w = Tu[nodes[i]]
                if w < dist[i]:
                    dist[i] = w
    return total


def mst_bound(inst, driver_i, S):
    nodes = [inst.driver_node(driver_i)]
    for o in S:
        nodes.append(2 * o)
        nodes.append(2 * o + 1)
    return _mst_weight(nodes, inst.T)


def one_tree_bound(inst, driver_i, S):
    nodes = []
    for o in S:
        nodes.append(2 * o)
        nodes.append(2 * o + 1)
    part = _mst_weight(nodes, inst.T)
    Tv = inst.T[inst.driver_node(driver_i)]
    cheapest = min(Tv[u] for u in nodes)
    return part + cheapest


# ----------------------------------------------------------- 2.4 luat cat
def budget(inst, S):
    return max(inst.deadline[o] for o in S)      # max, KHONG phai min
