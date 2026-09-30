"""T4 - chay lai thuat toan cat nhanh tren dataset Atlanta (hica-s/instance/2.1).

Khac voi lan chay Test1 goc (Guideline/Test1.md muc 1): instance KHONG con sinh
tong hop tren ban do vuong 20x20 km, ma doc tu Dataset/instances/{main,scale_a}.
Thuat toan (muc 2), quy trinh do (muc 3) va metric (muc 4) giu nguyen 100%.

Ba khac biet cua du lieu buoc phai xu ly:
  1. Ma tran thoi gian T_pd BAT DOI XUNG (road network thuc).
     - DFS ground truth dung dung thoi gian co huong T_pd[a][b].
     - Can duoi dung do thi doi xung hoa bang min(T[a][b], T[b][a]); moi cung ma
       route thuc di qua deu co chi phi >= gia tri min do, nen MST tren do thi
       nay van la can duoi hop le (van sound).
  2. Driver GW co capacity 3 (khong phai 2) va chi co cung DI RA tu start
     (T_from_start). Route mo chi dung dung mot cung tu start nen dieu do du.
  3. Chi lay driver GW - dung tinh than muc 6 cua spec (khong dung OD).
"""

import itertools
import json
import os


class AtlInstance(object):
    __slots__ = ("iid", "n", "m", "T", "Tsym", "start_row", "release", "deadline",
                 "cap", "until", "meta", "gw_ids")

    def __init__(self, path, meta=None):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        self.iid = d["instance_id"]
        orders = d["orders"]
        self.n = len(orders)
        self.release = [o["ready_time"] for o in orders]
        self.deadline = [o["deadline"] for o in orders]

        tv = d["travel"]
        T = tv["T_pd"]                       # 2n x 2n, co huong
        self.T = T
        N = len(T)
        self.Tsym = [[0.0] * N for _ in range(N)]
        for a in range(N):
            Ta, Sa = T[a], self.Tsym[a]
            for b in range(N):
                x, y = Ta[b], T[b][a]
                Sa[b] = x if x < y else y

        gw = [dr for dr in d["drivers"] if dr["cls"] == "GW"]
        self.gw_ids = [dr["id"] for dr in gw]
        self.m = len(gw)
        self.start_row = [tv["T_from_start"][dr["id"]] for dr in gw]
        self.cap = [int(dr["capacity"]) for dr in gw]
        self.until = [float(dr["available_until"]) for dr in gw]
        self.meta = meta or {}


# ------------------------------------------------- 2.1 feasibility (truth)
def is_feasible(inst, i, S):
    k = len(S)
    if k == 0:
        return True
    T = inst.T
    row0 = inst.start_row[i]
    cap = inst.cap[i]
    until = inst.until[i]
    rel = inst.release
    dl = inst.deadline
    full = (1 << k) - 1

    def step(cur, nd):
        return row0[nd] if cur < 0 else T[cur][nd]

    def dfs(cur, t, picked, delivered, load):
        if delivered == full:
            return True
        for j in range(k):
            bit = 1 << j
            o = S[j]
            if not (picked & bit):
                if load < cap:
                    nd = 2 * o
                    at = t + step(cur, nd)
                    if at < rel[o]:
                        at = rel[o]
                    if at <= dl[o] and at <= until:
                        if dfs(nd, at, picked | bit, delivered, load + 1):
                            return True
            elif not (delivered & bit):
                nd = 2 * o + 1
                at = t + step(cur, nd)
                if at <= dl[o] and at <= until:
                    if dfs(nd, at, picked, delivered | bit, load - 1):
                        return True
        return False

    return dfs(-1, 0.0, 0, 0, 0)


# ------------------------------------------------------- 2.2 / 2.3 bounds
def _mst_weight(nodes, M):
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
        for x in range(m):
            if not in_tree[x] and dist[x] < best:
                best = dist[x]
                u = x
        in_tree[u] = True
        total += best
        Mu = M[nodes[u]]
        for x in range(m):
            if not in_tree[x]:
                w = Mu[nodes[x]]
                if w < dist[x]:
                    dist[x] = w
    return total


def _nodes(S):
    out = []
    for o in S:
        out.append(2 * o)
        out.append(2 * o + 1)
    return out


def mst_bound(inst, i, S):
    """MST tren {start} + cac node cua S. Cung tu start dung T_from_start,
    cung giua cac node don dung ma tran doi xung hoa (min)."""
    nodes = _nodes(S)
    row0 = inst.start_row[i]
    M = inst.Tsym
    m = len(nodes)
    INF = float("inf")
    # Prim bat dau tu start (chi so ao -1)
    dist = [row0[u] for u in nodes]
    in_tree = [False] * m
    total = 0.0
    for _ in range(m):
        u = -1
        best = INF
        for x in range(m):
            if not in_tree[x] and dist[x] < best:
                best = dist[x]
                u = x
        in_tree[u] = True
        total += best
        Mu = M[nodes[u]]
        for x in range(m):
            if not in_tree[x]:
                w = Mu[nodes[x]]
                if w < dist[x]:
                    dist[x] = w
    return total


def one_tree_bound(inst, i, S):
    nodes = _nodes(S)
    part = _mst_weight(nodes, inst.Tsym)
    row0 = inst.start_row[i]
    return part + min(row0[u] for u in nodes)


def budget(inst, S):
    return max(inst.deadline[o] for o in S)
