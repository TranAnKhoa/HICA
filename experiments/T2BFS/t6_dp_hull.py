"""Testb_hull_final.md - BAN COPY rieng cua t6_dp.py de thu nghiem hull filter
tai DP intermediate state, KHONG sua t6_dp.py goc (module da PASS Gate
0/616/160 nhieu lan, moi pipeline khac - 2a/2b, RQ1, Test8 - dang phu thuoc
no nguyen ven). Quyet dinh nguoi dung 2026-09-16: tao ban rieng thay vi sua
truc tiep, de an toan tuyet doi cho cac thu nghiem khac.

CHI THAY DOI DUY NHAT so voi t6_dp.py: sau moi lan goi _filter_dominated_labels
(dominance/Pareto filter tai 1 key (v,IV,Cd)), THEM buoc hull_filter_on_pareto()
(Testb_hull_final.md Sec2) truoc khi dung lam nguon mo rong round ke tiep.
Dung LAI dung ham lower_hull_on_pareto() da viet va audit doc lap (0 mismatch
tren 5 group, brute-force numeric) trong convex_hull_test_v2.py - KHONG viet
lai logic hull tu dau, tranh lap lai bug turns_right() da tung mac phai.

Moi phan con lai COPY Y HET t6_dp.py (Label, _dominates_label,
_filter_dominated_labels, _try_pickup/_try_delivery/_try_home, finalize_KW) -
KHONG sua logic feasibility/dominance goc, chi them 1 buoc loc sau.
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P
from convex_hull_test_v2 import lower_hull_on_pareto  # noqa: E402 - da audit doc lap

EPS = 1e-9
KAPPA = P.KAPPA


class Label(object):
    __slots__ = ("v", "IV", "Cd", "t", "K", "W", "parent", "action")

    def __init__(self, v, IV, Cd, t, K, W, parent=None, action=None):
        self.v = v
        self.IV = IV
        self.Cd = Cd
        self.t = t
        self.K = K
        self.W = W
        self.parent = parent
        self.action = action

    def key(self):
        return (self.v, self.IV, self.Cd)

    def path(self):
        out = []
        cur = self
        while cur is not None:
            out.append((cur.action, cur.v, cur.t, cur.K, cur.W))
            cur = cur.parent
        return list(reversed(out))


def _dominates_label(a, b):
    if a.t > b.t + EPS or a.K > b.K + EPS or a.W > b.W + EPS:
        return False
    strict = (a.t < b.t - EPS) or (a.K < b.K - EPS) or (a.W < b.W - EPS)
    return strict


def _filter_dominated_labels(labels):
    n = len(labels)
    dominated = [False] * n
    for i in range(n):
        if dominated[i]:
            continue
        for j in range(n):
            if i == j or dominated[j]:
                continue
            if _dominates_label(labels[j], labels[i]):
                dominated[i] = True
                break
            if _dominates_label(labels[i], labels[j]):
                dominated[j] = True
    return [labels[i] for i in range(n) if not dominated[i]]


# ---------------------------------------------------------------------------
# [BƯỚC MỚI - Testb_hull_final.md Sec2] hull filter sau Pareto filter, tại
# MỖI key (v,IV,Cd) riêng - dùng partial (K,W) tích lũy tới state hiện tại
# (chưa phải route hoàn chỉnh). supported-only theo Proposition Sec0.
# ---------------------------------------------------------------------------

def hull_filter_on_pareto(pareto_labels):
    """pareto_labels: list Label CUNG 1 key (v,IV,Cd), DA qua
    _filter_dominated_labels (Pareto-efficient). Tra subset chi gom supported
    points (tren lower convex hull cua (K,W) tich luy). Neu <=2 label, khong
    du diem de hull loai gi - tra nguyen."""
    if len(pareto_labels) <= 2:
        return pareto_labels
    pts = sorted(pareto_labels, key=lambda lab: (lab.K, lab.W))
    tagged = [(lab.K, lab.W, lab) for lab in pts]
    hull = lower_hull_on_pareto(tagged)
    return [lab for (_k, _w, lab) in hull]


def _tt_to_km(tt_min):
    return tt_min * G.SPEED_KMH / 60.0


def _try_pickup(travel_time, driver, pd, lab, j, B, compat_graph=None):
    if j in lab.IV or j in lab.Cd:
        return None
    if len(lab.IV) + len(lab.Cd) >= B:
        return None
    if compat_graph is not None:
        for m in lab.IV:
            if not _compat_lookup(compat_graph, j, m):
                return None
        for m in lab.Cd:
            if not _compat_lookup(compat_graph, j, m):
                return None
    p, d = pd[j]
    tt = travel_time(lab.v, p.id)
    A = lab.t + tt
    Bt = A if A > p.e else p.e
    if Bt > p.l + EPS:
        return None
    Dt = Bt + p.s
    K2 = lab.K + KAPPA * _tt_to_km(tt)
    W2 = Dt - driver["t0"]
    return Label(p.id, lab.IV | {j}, lab.Cd, Dt, K2, W2, parent=lab, action=("pickup", j))


def _compat_lookup(compat_graph, i, j):
    if callable(compat_graph):
        return compat_graph(i, j)
    return compat_graph.get(frozenset((i, j)), True)


def _try_delivery(travel_time, driver, pd, lab, j):
    if j not in lab.IV:
        return None
    p, d = pd[j]
    tt = travel_time(lab.v, d.id)
    A = lab.t + tt
    Bt = A if A > d.e else d.e
    if Bt > d.l + EPS:
        return None
    Dt = Bt + d.s
    K2 = lab.K + KAPPA * _tt_to_km(tt)
    W2 = Dt - driver["t0"]
    return Label(d.id, lab.IV - {j}, lab.Cd | {j}, Dt, K2, W2, parent=lab, action=("delivery", j))


def _try_home(travel_time, driver, home, lab):
    if lab.IV:
        return None
    tt = travel_time(lab.v, home.id)
    A = lab.t + tt
    Bt = A if A > home.e else home.e
    if Bt > home.l + EPS:
        return None
    Dt = Bt + home.s
    K2 = lab.K + KAPPA * _tt_to_km(tt)
    W2 = Dt - driver["t0"]
    return Label(home.id, lab.IV, lab.Cd, Dt, K2, W2, parent=lab, action=("home", None))


def finalize_KW(driver, lab):
    if driver["cls"] == "OD":
        direct_dist = driver["direct_time"] * G.SPEED_KMH / 60.0
        K_final = max(0.0, lab.K - KAPPA * direct_dist)
        W_final = max(0.0, (lab.W - driver["direct_time"]) / 60.0)
    else:
        K_final = lab.K
        W_final = lab.W / 60.0
    return K_final, W_final


def run_dp(travel_time, driver, orders, B, use_dominance=True, compat_graph=None,
          use_hull_filter=True):
    """Giong het t6_dp.run_dp(), CHI THEM tham so use_hull_filter (mac dinh
    True o ban nay - so sanh voi t6_dp.py goc de biet hieu qua hull). Khi
    use_hull_filter=False, ham nay tuong duong 100% t6_dp.run_dp() (dung de
    doi chieu/regression trong cung file, khong can import 2 module).

    Tra them 2 truong so voi t6_dp.py goc:
      frontier_sizes_before_hull : list (touched, so label SAU Pareto, TRUOC hull)
      frontier_sizes_after_hull  : list (touched, so label SAU hull filter)
    (t6_dp.py goc chi co 1 frontier_sizes = tuong duong before_hull khi
    use_hull_filter=False).
    """
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    n_created = 1
    lab0 = Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)

    complete_by_C = defaultdict(list)
    frontier_sizes = []
    frontier_sizes_before_hull = []
    frontier_sizes_after_hull = []
    n_states_total = 0            # [ADD 2026-09-16] so key (v,IV,Cd) distinct
                                  # da xu ly dominance/hull (moi vi tri trong
                                  # closure loop VA pickup loop) - dung de
                                  # kiem tra gia thuyet "tam thuong": state
                                  # trung gian co it label/group hon route
                                  # hoan chinh (Test A) hay khong.
    n_labels_before_hull_total = 0

    frontier = {0: [lab0]}

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue

        active = list(labs_here)
        closure_all = []
        while active:
            next_active = []
            for lab in active:
                closure_all.append(lab)
                for j in sorted(lab.IV):
                    new_lab = _try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        continue
                    n_created += 1
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1 and not has_home:
                        complete_by_C[new_lab.Cd].append(new_lab)
                if has_home and not lab.IV and len(lab.Cd) >= 1:
                    new_lab = _try_home(travel_time, driver, home, lab)
                    if new_lab is not None:
                        n_created += 1
                        complete_by_C[new_lab.Cd].append(new_lab)

            if use_dominance:
                by_key = defaultdict(list)
                for lab in next_active:
                    by_key[lab.key()].append(lab)
                next_active = []
                n_before_h = 0
                n_after_h = 0
                for k, labs in by_key.items():
                    pareto_labs = _filter_dominated_labels(labs)
                    n_before_h += len(pareto_labs)
                    n_states_total += 1
                    n_labels_before_hull_total += len(pareto_labs)
                    if use_hull_filter:
                        surviving = hull_filter_on_pareto(pareto_labs)
                    else:
                        surviving = pareto_labs
                    n_after_h += len(surviving)
                    next_active.extend(surviving)
            active = next_active

        frontier_sizes.append((touched, len(closure_all)))

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = _try_pickup(travel_time, driver, pd, lab, j, B,
                                          compat_graph=compat_graph)
                    if new_lab is None:
                        continue
                    n_created += 1
                    new_by_key[new_lab.key()].append(new_lab)

            next_frontier = []
            n_before_h2 = 0
            n_after_h2 = 0
            if use_dominance:
                for k, labs in new_by_key.items():
                    pareto_labs = _filter_dominated_labels(labs)
                    n_before_h2 += len(pareto_labs)
                    n_states_total += 1
                    n_labels_before_hull_total += len(pareto_labs)
                    if use_hull_filter:
                        surviving = hull_filter_on_pareto(pareto_labs)
                    else:
                        surviving = pareto_labs
                    n_after_h2 += len(surviving)
                    next_frontier.extend(surviving)
            else:
                for k, labs in new_by_key.items():
                    next_frontier.extend(labs)
                    n_before_h2 += len(labs)
                    n_after_h2 += len(labs)
            frontier[touched + 1] = next_frontier
            frontier_sizes_before_hull.append((touched + 1, n_before_h2))
            frontier_sizes_after_hull.append((touched + 1, n_after_h2))

    if use_dominance:
        for Cset, labs in list(complete_by_C.items()):
            by_v = defaultdict(list)
            for lab in labs:
                by_v[lab.v].append(lab)
            kept = []
            for v, labs_v in by_v.items():
                kept.extend(_filter_dominated_labels(labs_v))
            complete_by_C[Cset] = kept

    n_survived = sum(len(v) for v in frontier.values()) + sum(len(v) for v in complete_by_C.values())

    return dict(
        complete_by_C=dict(complete_by_C),
        n_labels_created=n_created,
        n_labels_survived=n_survived,
        frontier_sizes=frontier_sizes,
        frontier_sizes_before_hull=frontier_sizes_before_hull,
        frontier_sizes_after_hull=frontier_sizes_after_hull,
        n_states_total=n_states_total,
        n_labels_before_hull_total=n_labels_before_hull_total,
    )
