"""Test4.md Viec 1 - Profile Gamma(R), dominance D1/D2/D3, filter_dominated.

K(R), W(R) theo dung Sec0.1:
  K(R) = kappa * total_distance(R)     (chi phi quang duong)
  W(R) = active_route_time(R) / 60     (gio)
  OD: tinh theo DETOUR (route_time - direct_time, tuong tu cho distance)
  GW: tinh tren TOAN TUYEN

kappa: khong duoc Test4.md khoa gia tri cu the. Vi D2/D3 CHI so sanh THU TU
(K(p') <= K(p)), va kappa la hang so DUONG nhan deu moi K - gia tri kappa
KHONG anh huong ket qua so sanh dominance nao ca. Chon kappa=1 (don vi: 1
cost-unit/km) - cong khai lua chon nay, khong phai quyet dinh rui ro vi no
bat bien doi voi moi ket luan dominance.

total_distance(R) suy tu travel_time (dataset dung travel_time_model=
euclidean, t2_gen.SPEED_KMH=20 co dinh): dist_km(a,b) = travel_time(a,b) *
SPEED_KMH / 60.
"""

import sys
import os
import itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G

KAPPA = 1.0
EPS = 1e-9


def route_distance_km(travel_time, walk):
    """Tong quang duong (km) cua walk, suy tu travel_time qua SPEED_KMH co dinh."""
    total_min = 0.0
    for i in range(1, len(walk)):
        total_min += travel_time(walk[i - 1].id, walk[i].id)
    return total_min * G.SPEED_KMH / 60.0


def _insert_distance_delta_km(travel_time, walk, a, b, p_id, d_id):
    """Chenh lech quang duong (km) khi chen p_id tai vi tri a, d_id tai vi
    tri b (a<b) vao walk, TINH TRUC TIEP tu 2-3 canh bi thay doi - KHONG
    duyet lai toan bo walk. Toi uu hoa quan trong nhat cua Viec 2/3 (profile
    cho thay route_distance_km/K_W_of_route chiem >60% thoi gian Viec 1/2
    ban dau do goi O(|R|) MOI insertion thay vi O(1))."""
    old_a_prev_id = walk[a - 1].id
    old_a_next_id = walk[a].id if a < len(walk) else None

    if b == a + 1:
        # canh cu bi xoa: (a-1 -> a). Canh moi: (a-1->P), (P->D), (D-> node
        # tai vi tri a cua walk GOC, neu con).
        removed = travel_time(old_a_prev_id, old_a_next_id) if old_a_next_id else 0.0
        added = travel_time(old_a_prev_id, p_id) + travel_time(p_id, d_id)
        if old_a_next_id:
            added += travel_time(d_id, old_a_next_id)
        delta_min = added - removed
    else:
        # 2 canh cu bi xoa rieng biet: (a-1->a) va (b-2->b-1) [chi so walk GOC]
        # (b-1 chinh la walk[b-1], node ngay sau doan giua, van con nguyen
        # trong walk GOC vi P,D KHONG chen giua no).
        old_b_prev_id = walk[b - 2].id
        old_b_next_id = walk[b - 1].id if (b - 1) < len(walk) else None

        removed = travel_time(old_a_prev_id, old_a_next_id)
        if old_b_next_id:
            removed += travel_time(old_b_prev_id, old_b_next_id)

        added = travel_time(old_a_prev_id, p_id) + travel_time(p_id, old_a_next_id)
        added += travel_time(old_b_prev_id, d_id)
        if old_b_next_id:
            added += travel_time(d_id, old_b_next_id)
        delta_min = added - removed

    return delta_min * G.SPEED_KMH / 60.0


def K_W_of_route(driver, travel_time, walk, schedule):
    """Tra (K, W) cho 1 route DA feasible (co schedule). Dung khi CAN tinh
    tren 1 walk DAY DU (khong co dist_base san) - vi du cho walk goc R (chua
    chen gi). Voi insertion, dung K_W_incremental (nhanh hon O(|R|) lan)."""
    dist_total = route_distance_km(travel_time, walk)
    active_time_min = schedule[-1][2] - driver["t0"]
    return _K_W_from_dist_time(driver, dist_total, active_time_min)


def _K_W_from_dist_time(driver, dist_total, active_time_min):
    if driver["cls"] == "OD":
        direct_dist = driver["direct_time"] * G.SPEED_KMH / 60.0
        detour_dist = dist_total - direct_dist
        detour_time = active_time_min - driver["direct_time"]
        K = KAPPA * detour_dist
        W = detour_time / 60.0
    else:
        K = KAPPA * dist_total
        W = active_time_min / 60.0
    return K, W


def compute_gamma(driver, travel_time, walk, schedule, pd, rem_orders):
    """Tinh Gamma(R) = {j: A_j(R)} cho R=walk, voi rem_orders = Rem(S).

    A_j(R) = list cac (K, W, slack) cho MOI vi tri chen (a,b) hop le cua j.
    Tra dict {j: [(K,W,slack), ...]} (rong neu khong chen duoc).

    Toi uu: dist_base (quang duong walk GOC) tinh MOT LAN, moi insertion
    chi tinh DELTA quang duong (O(1) thay vi O(|R|)) - giam ~3-5x thoi gian
    tren cac route dai (do bang cProfile: route_distance_km O(|R|)/insertion
    chiem phan lon thoi gian Viec 1/2). Dung t2_core.is_feasible TRUC TIEP
    (khong dung F/Fp - Viec 1 uu tien DUNG hon nhanh tuyet doi; F/Fp la toi
    uu RIENG cho feasibility check, khong lam ham nay).
    """
    has_home = walk[-1].kind == "home"
    upper_a = len(walk) - 1 if has_home else len(walk)
    upper_b = len(walk) if has_home else len(walk) + 1

    dist_base = route_distance_km(travel_time, walk)

    gamma = {}
    for j in rem_orders:
        p, d = pd[j]
        pts = []
        for a in range(1, upper_a + 1):
            R1 = walk[:a] + [p] + walk[a:]
            for b in range(a + 1, upper_b + 1):
                R2 = R1[:b] + [d] + R1[b:]
                ok, slack, sched2 = C.is_feasible(travel_time, driver, R2)
                if ok:
                    delta_km = _insert_distance_delta_km(travel_time, walk, a, b, p.id, d.id)
                    dist_total = dist_base + delta_km
                    active_time_min = sched2[-1][2] - driver["t0"]
                    K, W = _K_W_from_dist_time(driver, dist_total, active_time_min)
                    pts.append((K, W, slack))
        gamma[j] = pts
    return gamma


def reachable_orders(driver, travel_time, pd, order_ids):
    """Test4.md Sec0.3: danh sach order kha thi DON LE (k=1) cho driver nay -
    KHONG doc bid, deterministic. Dung is_feasible truc tiep tren walk 1-don."""
    start, _, home = C.build_walk_nodes(driver, {})
    has_home = home is not None
    out = []
    for oid in order_ids:
        p, d = pd[oid]
        walk = [start, p, d] + ([home] if has_home else [])
        ok, slack, sched = C.is_feasible(travel_time, driver, walk)
        if ok:
            out.append(oid)
    return out


def sigma_j(pts):
    """sigma_j(R) = max slack trong A_j(R), -inf neu rong."""
    if not pts:
        return float("-inf")
    return max(s for _, _, s in pts)


# ------------------------------------------------------------ dominance
def feas_set(gamma, rem_orders):
    return frozenset(j for j in rem_orders if gamma[j])


def dominates_D1(gamma_a, gamma_b, rem_orders):
    """Feas(R_b) subset Feas(R_a)."""
    fa = feas_set(gamma_a, rem_orders)
    fb = feas_set(gamma_b, rem_orders)
    return fb.issubset(fa)


def dominates_D2(gamma_a, gamma_b, rem_orders):
    """forall j, forall p in A_j(Rb), exists p' in A_j(Ra): K'<=K and W'<=W."""
    for j in rem_orders:
        pts_b = gamma_b[j]
        if not pts_b:
            continue
        pts_a = gamma_a[j]
        for (K, W, _s) in pts_b:
            found = False
            for (Kp, Wp, _sp) in pts_a:
                if Kp <= K + EPS and Wp <= W + EPS:
                    found = True
                    break
            if not found:
                return False
    return True


def dominates_D3(gamma_a, gamma_b, rem_orders):
    """Nhu D2 nhung them slack' >= slack."""
    for j in rem_orders:
        pts_b = gamma_b[j]
        if not pts_b:
            continue
        pts_a = gamma_a[j]
        for (K, W, s) in pts_b:
            found = False
            for (Kp, Wp, sp) in pts_a:
                if Kp <= K + EPS and Wp <= W + EPS and sp >= s - EPS:
                    found = True
                    break
            if not found:
                return False
    return True


DOMINATES = {"D1": dominates_D1, "D2": dominates_D2, "D3": dominates_D3}


def filter_dominated(entries_with_gamma, rem_orders, variant):
    """entries_with_gamma: [(canon, walk, schedule, gamma)]. Tra list con
    (antichain) khong bi dominate, theo variant in {D1,D2,D3}.

    Tie-break: R_a preferred over R_b (giu R co canonical() nho hon) khi ca
    hai chieu dominate lan nhau."""
    dom_fn = DOMINATES[variant]
    n = len(entries_with_gamma)
    dominated = [False] * n
    for i in range(n):
        if dominated[i]:
            continue
        ci, _, _, gi = entries_with_gamma[i]
        for jx in range(n):
            if i == jx or dominated[jx]:
                continue
            cj, _, _, gj = entries_with_gamma[jx]
            i_dom_j = dom_fn(gi, gj, rem_orders)
            j_dom_i = dom_fn(gj, gi, rem_orders)
            if i_dom_j and j_dom_i:
                # tie: giu canonical nho hon
                if cj < ci:
                    dominated[i] = True
                    break
                else:
                    dominated[jx] = True
            elif j_dom_i:
                dominated[i] = True
                break
    return [entries_with_gamma[i] for i in range(n) if not dominated[i]]
