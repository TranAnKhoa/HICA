"""Test6.md - Unified Forward Label-Setting DP.

Label = (v, IV, C, t, K, W):
  v  = node hien tai
  IV = frozenset order dang mang tren xe (da pickup, chua delivery)
  C  = frozenset order da giao xong (ca pickup lan delivery)
  t  = thoi diem hien tai (SAU service_time tai v)
  K  = kappa * quang duong TICH LUY THO (chua tru direct cho OD - xem Sec1.3)
  W  = thoi luong TICH LUY THO (active_time = t - t0; voi OD, detour = W - direct_time
       CHI tinh MOT LAN khi label hoan chinh, KHONG tru dan tung buoc - Sec1.3)

Rang buoc: |IV|+|C| <= B tai moi thoi diem (dung capacity=B, moi order demand=1,
xem t2_gen.build_instance - capacity=float(B)).

GW: label hoan chinh khi IV=rong va 1<=|C|<=B (khong co home).
OD: phai ghe home sau khi IV=rong; hoan chinh khi v=home va IV=rong.

Do thi trang thai la DAG theo |IV|+|C| (KHONG GIAM qua transition pickup/
delivery, LUON TANG qua home vi home la nut la) - nen ta xu ly THEO ROUND
tang dan |IV|+|C| = 0,1,2,...,B. Tai moi round, dominance (neu bat) duoc ap
dung NGAY tren tap label VUA sinh cua round do, TRUOC KHI dung lam nguon cho
round sau - dung "xuyen suot" theo dung nghia Sec1.2/Sec2.3, khong phai loc
mot lan o cuoi.

Dung khong doc bid o bat ky dau - regression: chi dung e/l/s/demand cong khai
tu WNode, giong t2_core.

[PATCH new_03] B trong module nay la CAP HIEU LUC cho 1 lan goi run_dp (co the
la B_gw hoac B_od tuy driver["cls"] - caller (dp_labeling.py) chiu trach nhiem
chon dung gia tri truoc khi goi, module nay KHONG tu doc driver["cls"] de
chon B). Them tham so tuy chon `compat_graph` cho run_dp/_try_pickup: bo loc
tuong thich cap (Pairwise Compatibility Filter - PCF, xem new03.md Sec2) -
CAN nhung KHONG DU, chi cat nhanh SOM cac tap chan chan infeasible, khong thay
the feasibility check hien co.
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t2_gen as G
import t4_profile as P

EPS = 1e-9
KAPPA = P.KAPPA   # =1.0, dung CHUNG voi t4_profile - khong dinh nghia lai


class Label(object):
    __slots__ = ("v", "IV", "Cd", "t", "K", "W", "parent", "action")

    def __init__(self, v, IV, Cd, t, K, W, parent=None, action=None):
        self.v = v
        self.IV = IV      # frozenset order id dang mang
        self.Cd = Cd       # frozenset order id da giao xong
        self.t = t
        self.K = K
        self.W = W
        self.parent = parent     # label truoc (truy vet, dung cho phan vi du)
        self.action = action     # ("pickup"|"delivery"|"home", order_id|None)

    def key(self):
        return (self.v, self.IV, self.Cd)

    def path(self):
        """Truy nguoc tu label nay ve goc, tra list (action, order_id, v, t, K, W)."""
        out = []
        cur = self
        while cur is not None:
            out.append((cur.action, cur.v, cur.t, cur.K, cur.W))
            cur = cur.parent
        return list(reversed(out))


def _dominates_label(a, b):
    """a preempts b: cung (v,IV,C), t_a<=t_b, K_a<=K_b, W_a<=W_b, it nhat 1 strict."""
    if a.t > b.t + EPS or a.K > b.K + EPS or a.W > b.W + EPS:
        return False
    strict = (a.t < b.t - EPS) or (a.K < b.K - EPS) or (a.W < b.W - EPS)
    return strict


def _filter_dominated_labels(labels):
    """labels: list Label CUNG mot key (v,IV,C). Tra list con khong bi dominate
    lan nhau (antichain theo (t,K,W), tat ca minimize)."""
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


def _tt_to_km(tt_min):
    """travel_time() tra PHUT (t2_gen quy uoc) - K phai tich luy theo KM,
    dung CHUNG he so quy doi voi t4_profile.route_distance_km (SPEED_KMH/60).
    Thieu buoc nay la BUG: cong don K theo don vi phut se sai gap SPEED_KMH/60
    lan (o day 20/60=1/3, tuc K bi tinh gap 3x qua thuc te - phat hien bang
    Gate 1.C khi doi chieu voi K_W_of_route that)."""
    return tt_min * G.SPEED_KMH / 60.0


def _try_pickup(travel_time, driver, pd, lab, j, B, compat_graph=None):
    """[PATCH new_03] compat_graph (tuy chon): dict {frozenset({i,k}): bool}
    hoac callable(i,k)->bool. Neu duoc truyen, THEM dieu kien CAN (khong DU -
    xem new03.md Sec2.1): moi order m dang trong IV hoac da o C cua label PHAI
    tuong thich (compat=True) voi j truoc khi cho phep pickup j. Day la BO LOC
    CAT NHANH (Pairwise Compatibility Filter - PCF), khong thay the feasibility
    check ben duoi - chi loai SOM cac nhanh chac chan hong."""
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
    """compat_graph: dict {frozenset({i,j}): bool} hoac callable(i,j)->bool."""
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
    """Tra (K_final, W_final) cho 1 label HOAN CHINH, ap dung tru direct MOT
    LAN DUY NHAT cho OD (Sec1.3) - K/W tich luy trong lab.K/lab.W la THO."""
    if driver["cls"] == "OD":
        direct_dist = driver["direct_time"] * G.SPEED_KMH / 60.0
        K_final = max(0.0, lab.K - KAPPA * direct_dist)
        W_final = max(0.0, (lab.W - driver["direct_time"]) / 60.0)
    else:
        K_final = lab.K
        W_final = lab.W / 60.0
    return K_final, W_final


def run_dp(travel_time, driver, orders, B, use_dominance=True, compat_graph=None):
    """Chay DP forward label-setting toi B, XU LY THEO ROUND tang dan
    |IV|+|C| = 0..B. Dominance (neu use_dominance) ap dung NGAY sau moi round
    tren cac label MOI cua round do (xuyen suot, dung Sec1.2/Sec2.3) - KHONG
    phai loc 1 lan cuoi cung.

    Delivery labels (KHONG lam tang |IV|+|C|) va home labels duoc xu ly xen
    ke trong CUNG round voi round cua |IV|+|C| hien tai cua label nguon (vi
    delivery giu nguyen touched=|IV|+|C|), dung mot vong lap con "sub-round"
    lap lai delivery/home cho toi khi khong con gi moi sinh trong round do
    (delivery co the noi tiep delivery ngay lap tuc trong 1 don vi thoi gian
    round vi khong doi touched).

    Tra dict:
      complete_by_C     : {frozenset(C): [Label,...]} (SAU dominance neu bat,
                           label hoan chinh - GW: IV rong sau delivery cuoi;
                           OD: da ve home)
      n_labels_created   : tong so label da tao (truoc dominance)
      n_labels_survived  : tong so label con song SAU dominance (neu bat,
                           nguoc lai = n_labels_created)
      frontier_sizes     : list (touched_level -> so label frontier sau
                           dominance tai level do, TRUOC khi tach delivery/home)
    """
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None

    n_created = 1
    lab0 = Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)

    complete_by_C = defaultdict(list)
    frontier_sizes = []

    # frontier[touched] = list label CHUA duoc "dong bo" delivery/home het,
    # nhung ta xu ly delivery/home lap tuc bang closure trong CUNG touched-
    # level (khong lam tang touched), roi moi pickup SANG touched+1.
    frontier = {0: [lab0]}

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue

        # --- closure: lap lai delivery/home cho toi khi bao hoa (touched
        # khong doi qua delivery/home, nen closure nay LUON dung - moi
        # order chi giao 1 lan, IV giam dan, closure huu han).
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
                        # home la nut la, KHONG dua vao next_active (khong mo rong tiep)

            if use_dominance:
                # gom theo key, loc dominance NGAY trong closure - xuyen suot
                by_key = defaultdict(list)
                for lab in next_active:
                    by_key[lab.key()].append(lab)
                next_active = []
                for k, labs in by_key.items():
                    next_active.extend(_filter_dominated_labels(labs))
            active = next_active

        frontier_sizes.append((touched, len(closure_all)))

        # --- pickup: sinh sang touched+1, TU MOI label trong closure (bao
        # gom ca label goc cua round nay LAN moi label sinh tu delivery-
        # closure, vi delivery khong doi touched nen van o round nay).
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
            if use_dominance:
                for k, labs in new_by_key.items():
                    next_frontier.extend(_filter_dominated_labels(labs))
            else:
                for k, labs in new_by_key.items():
                    next_frontier.extend(labs)
            frontier[touched + 1] = next_frontier

    if use_dominance:
        # dominance CUNG da ap dung tren complete_by_C? KHONG - hoan chinh
        # sinh tu delivery/home trong closure CO THE trung key (v,IV,C) voi
        # nhau (VI DU 2 label hoan chinh khac t/K/W cung mot C) - loc lai o
        # day theo dung dinh nghia dominance (Sec1.2), CHI so sanh trong
        # CUNG mot C (khong can v/IV vi hoan chinh la IV=rong, v co the khac
        # nhau giua GW (v=node giao cuoi) nhung dominance yeu cau v_a=v_b -
        # GIU DUNG dinh nghia Sec1.2: chi loc cac label CUNG v).
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
    )
