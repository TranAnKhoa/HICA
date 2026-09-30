"""Test4.md Viec 0 - Gate 0.1 (F tuong duong recompute) va Gate 0.2 (so muc
chat voi min-slack).

=== Ly thuyet dung (sau qua trinh debug, xem lich su hoi thoai) ===

t4_fwdslack.forward_slack tra ve CA F (forward slack GOC, Test4.md Sec0.2)
LAN Fp ("F prime"). Ly do can Fp:

F[i] = min_{i<=j<=N} { sum_{i<p<=j} W_p + (l_j-B_j) } GOM CA term j=i, tuc
BI RANG BUOC boi deadline cua CHINH node i. Dinh nghia nay dung cho cau hoi
"neu node i roi tre di 1 luong, ca no lan phan sau co con on khong" - nhung
KHONG dung cho insertion: khi chen node moi NGAY SAU vi tri i (walk goc),
node i KHONG bi delay gi ca (no van duoc phuc vu dung schedule cu, chi la
buoc di TIEP THEO khac di). Dung F[i] cho insertion se bi rang buoc SAI boi
deadline cua node i (khong lien quan) - da xac nhan bang phan vi du so (2
truong hop mau thuan nhau khi thu F[a] va F[a-1] rieng le, chi khop khi bo
han term j=i).

Fp[i] = W[i+1] + F[i+1]  (bo term j=i) = delay TOI DA co the xay ra tai
ARRIVAL cua node i+1 (node dau tien chiu anh huong khi chen sau vi tri i)
ma PHAN DUOI tu i+1 tro di van kha thi. Day la dai luong DUNG can dung.

=== Cong thuc insertion 2-diem (pickup tai a, delivery tai b, a<b) ===

Buoc 1 - chen P tai vi tri a (giua walk[a-1] va walk[a]):
  Tinh (B_p, D_p) binh thuong.
  Neu a < len(walk): push_p = A_new(walk[a]) - A_old(walk[a])
    (A_new tinh tu D_p + travel(P, walk[a]); A_old tinh tu schedule GOC)
    Neu push_p > 0: can push_p <= Fp[a-1].

Buoc 2a (b == a+1, D ngay sau P, khong node cu giua):
  Tinh (B_d, D_d) tu (P.id, D_p).
  Neu b < len(walk): push_total = A_new(walk[b]) - A_old(walk[b])
    (walk[b] = walk[a] = node ke tiep P trong walk GOC)
    Neu push_total > 0: can push_total <= Fp[a-1] (VAN dung Fp[a-1], KHONG
    phai Fp[a] hay F[a] - vi node bi anh huong dau tien VAN LA walk[a], va
    Fp[a-1] da la dai luong dung cho "phan duoi tu walk[a] tro di").

Buoc 2b (b > a+1, co node cu giua P,D): PHAI lan truyen delay qua tung node
  [a, b) (O(b-a) buoc, KHONG the rut gon them bang F/Fp don thuan vi delay
  bi thay doi boi tung node giua - waiting time co the hap thu 1 phan truoc
  khi toi b). Sau khi tinh duoc (B_d, D_d) qua vong lap nay, so push cuoi
  cung (tai walk[b]) VOI Fp[a-1] (van la vi tri goc a-1, ly do nhu tren:
  Fp[a-1] da gom TOAN BO phan duoi tu vi tri a tro di trong dinh nghia cua
  no, khong can tinh lai Fp cho tung buoc trung gian).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t4_fwdslack as FS

EPS = 1e-9


def _try_insert_at(travel_time, prev_id, D_prev, new_node):
    """Tinh (B_new, D_new) khi chen new_node ngay sau 1 node co (id, D).
    Tra None neu vi pham TW ngay tai new_node."""
    A_new = D_prev + travel_time(prev_id, new_node.id)
    B_new = A_new if A_new > new_node.e else new_node.e
    if B_new > new_node.l + EPS:
        return None
    D_new = B_new + new_node.s
    return B_new, D_new


def _arrival_old(travel_time, walk, schedule, idx):
    """Arrival time GOC (A_i, TRUOC khi max voi e_i) tai walk[idx], tinh tu
    node truoc no TRONG WALK GOC. idx phai >= 1."""
    D_prev = schedule[idx - 1][2]
    return D_prev + travel_time(walk[idx - 1].id, walk[idx].id)


def feasible_by_F_two_insert(travel_time, walk, schedule, Fp, new_p, new_d, a, b):
    """Kiem chen (new_p tai vi tri a, new_d tai vi tri b, a<b, 1<=a, b<=len(walk))
    vao walk, dung Fp cua walk GOC (khong goi is_feasible tu dau tu start,
    nhung CO lan truyen delay O(b-a) qua doan giua khi b>a+1).

    CHI kiem TW (Time Window) - capacity kiem RIENG o noi goi ham nay.

    Tra (ok, B_p, D_p, B_d, D_d). ok=False neu vi pham TW o bat ky buoc nao.
    """
    prev = walk[a - 1]
    D_prev = schedule[a - 1][2]
    res_p = _try_insert_at(travel_time, prev.id, D_prev, new_p)
    if res_p is None:
        return False, None, None, None, None
    B_p, D_p = res_p

    if a < len(walk):
        A_nxt_new = D_p + travel_time(new_p.id, walk[a].id)
        A_nxt_old = _arrival_old(travel_time, walk, schedule, a)
        push_p = A_nxt_new - A_nxt_old
        if push_p > EPS and push_p > Fp[a - 1] + EPS:
            return False, B_p, D_p, None, None

    if b == a + 1:
        res_d = _try_insert_at(travel_time, new_p.id, D_p, new_d)
        if res_d is None:
            return False, B_p, D_p, None, None
        B_d, D_d = res_d
        if b > len(walk):
            # b == len(walk)+1: D chen o CUOI walk moi (khong con node cu
            # nao phia sau ca P lan D) - luon kha thi neu qua TW cua D.
            return True, B_p, D_p, B_d, D_d
        # node ke tiep trong walk MOI o vi tri b la walk GOC[b-1] (=walk[a],
        # vi walk moi da chen 2 phan tu P,D truoc no) - KHONG PHAI walk[b].
        A_nxt2_new = D_d + travel_time(new_d.id, walk[b - 1].id)
        A_nxt2_old = _arrival_old(travel_time, walk, schedule, b - 1)
        push_total = A_nxt2_new - A_nxt2_old
        if push_total <= EPS:
            return True, B_p, D_p, B_d, D_d
        ok = push_total <= Fp[a - 1] + EPS
        return ok, B_p, D_p, B_d, D_d

    # b > a+1: lan truyen delay qua cac node CU trong [a, b-1] (walk[a]..walk[b-2])
    cur_id = new_p.id
    D_cur = D_p
    ok_mid = True
    for idx in range(a, b - 1):
        nd = walk[idx]
        A_nd = D_cur + travel_time(cur_id, nd.id)
        B_nd = A_nd if A_nd > nd.e else nd.e
        if B_nd > nd.l + EPS:
            ok_mid = False
            break
        D_nd = B_nd + nd.s
        cur_id = nd.id
        D_cur = D_nd
    if not ok_mid:
        return False, B_p, D_p, None, None

    res_d = _try_insert_at(travel_time, cur_id, D_cur, new_d)
    if res_d is None:
        return False, B_p, D_p, None, None
    B_d, D_d = res_d

    if b > len(walk):
        return True, B_p, D_p, B_d, D_d

    # node ke tiep trong walk GOC ma walk MOI chua "dung" la walk[b-1] (da
    # dung het walk[a..b-2] + 2 node moi P,D) - KHONG PHAI walk[b].
    A_nxt_new = D_d + travel_time(new_d.id, walk[b - 1].id)
    A_nxt_old = _arrival_old(travel_time, walk, schedule, b - 1)
    push = A_nxt_new - A_nxt_old
    if push <= EPS:
        return True, B_p, D_p, B_d, D_d
    # QUAN TRONG: dung Fp[b-2] (vi tri NGAY TRUOC walk[b-1] TRONG WALK GOC),
    # KHONG PHAI Fp[a-1]. Ly do (tim ra sau debug): push o day la delay TAI
    # CHINH walk[b-1], DA bi thay doi (thuong giam do waiting time hap thu)
    # so voi push_p ban dau tai walk[a] - Fp[a-1] chi dam bao delay tai CHINH
    # walk[a] (node dau tien) khong vuot qua, KHONG dam bao delay (da bien
    # doi qua nhieu node giua) tai walk[b-1] van nam trong gioi han cho toan
    # bo phan duoi TU walk[b-1] tro di - can Fp DUNG TAI VI TRI do (b-2, node
    # ngay truoc walk[b-1] trong walk goc).
    ok = push <= Fp[b - 2] + EPS
    return ok, B_p, D_p, B_d, D_d
