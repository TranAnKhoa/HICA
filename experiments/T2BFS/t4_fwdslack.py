"""Test4.md Viec 0 - Forward time slack F_i (Savelsbergh 1985/1992).

CANH BAO TEN: day la "Test4.md" (Guideline/Test4.md, representative-rule qua
lookahead-profile dominance) - KHONG lien quan "T4" trong Test1.md (MST
geometric lower-bound diagnostic, experiments/T4/). Trung ten tinh co.

F_i = min_{i<=j<=N} { sum_{i<p<=j} W_p + (l_j - B_j) }
    W_p = max(0, e_p - A_p)   (waiting time tai p, theo lich ASAP)

Y nghia: F_i = luong delay toi da co the chen NGAY SAU vi tri i ma route van
kha thi - vi delay o i co the duoc waiting time o cac node SAU do hap thu,
truoc khi cham deadline nao do. F_i[0] (tai start) = slack(R) toan tuyen
(truong hop dac biet j=N).

Tinh bang MOT luot quet NGUOC: F_N = l_N - B_N (node cuoi, khong con gi phia
sau). F_i = min(F_{i+1} + W_{i+1}, l_i - B_i) - nhung can can than: W_{i+1}
la waiting o node i+1, xay ra SAU vi tri i, nen no duoc CONG vao truoc khi
lay min voi (l_i - B_i) cua chinh node i.

Dung lai chinh xac cong thuc: dinh nghia lai chi so - i chay tren CAC VI TRI
walk (0..N, gom start), F_i noi ve "delay chen ngay SAU node tai vi tri i".
Quet nguoc tu N ve 0:
    F_N = l_N - B_N
    F_i = min(l_i - B_i, W_{i+1} + F_{i+1})    for i = N-1 .. 0
(voi quy uoc node "start" co l_0 = +inf, W_0 = 0 - deadline vo han, khong
gioi han gi tai chinh no, nhung F_0 van huu han vi lan truyen tu phia sau).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C

EPS = 1e-9


def forward_slack(travel_time, driver, walk):
    """Tra (ok, schedule, F, Fp).

    F[i]  = forward slack GOC tai vi tri i (Test4.md Sec0.2), GOM ca deadline
            cua chinh node i trong min.
    Fp[i] = bien the DUNG CHO INSERTION (xem ghi chu trong ham) - delay toi
            da co the xay ra tai ARRIVAL cua node i+1 (node dau tien bi anh
            huong khi chen sau vi tri i) ma phan duoi i+1..N van kha thi -
            KHONG rang buoc boi deadline cua chinh node i (i khong bi delay).

    Neu walk infeasible (theo dung is_feasible), tra (False, None, None, None).
    schedule: list [(node_id, B_i, D_i, load)] dung format cua is_feasible.
    """
    ok, slack, schedule = C.is_feasible(travel_time, driver, walk)
    if not ok:
        return False, None, None, None

    n = len(walk)
    # waiting time tai moi node (tru start): W_p = max(0, e_p - A_p)
    # A_p = D_{p-1} + travel(prev,p); B_p = max(A_p, e_p) da co trong schedule.
    # => W_p = B_p - A_p (vi B_p = max(A_p,e_p), W_p = B_p - A_p neu A_p<e_p else 0 - dung).
    W = [0.0] * n
    for i in range(1, n):
        D_prev = schedule[i - 1][2]
        A_i = D_prev + travel_time(walk[i - 1].id, walk[i].id)
        B_i = schedule[i][1]
        W[i] = B_i - A_i   # >= 0 theo dinh nghia B_i = max(A_i, e_i)

    F = [0.0] * n
    l_last = walk[n - 1].l
    B_last = schedule[n - 1][1]
    F[n - 1] = (l_last - B_last) if l_last < float("inf") else float("inf")
    for i in range(n - 2, -1, -1):
        l_i = walk[i].l
        term_here = (l_i - schedule[i][1]) if l_i < float("inf") else float("inf")
        term_fwd = W[i + 1] + F[i + 1]
        F[i] = term_here if term_here < term_fwd else term_fwd

    # Fp[i] ("F prime") = F_i NHUNG BO term j=i (deadline cua CHINH node i).
    # Can thiet cho insertion: khi chen node moi ngay SAU walk[i], node i
    # KHONG bi delay gi ca (no van duoc phuc vu dung schedule cu) - chi phan
    # DUOI (tu i+1 tro di) moi chiu anh huong. Dung F[i] (goc) cho muc dich
    # nay la SAI vi F[i] con bi rang buoc boi (l_i-B_i) cua chinh node i,
    # thu khong lien quan gi toi delay bat nguon TU SAU i.
    #   Fp[i] = W[i+1] + F[i+1]   (= F[i] neu term_fwd < term_here, nhung
    #   KHONG cat bot boi term_here khi term_here nho hon - Fp luon >= F).
    #   Fp[N] (khong co node sau) = +inf (chen sau node cuoi khong anh
    #   huong gi, walk ket thuc ngay do - N o day la node cuoi cung cua
    #   walk, thuong la home hoac delivery cuoi).
    Fp = [float("inf")] * n
    for i in range(n - 1):
        Fp[i] = W[i + 1] + F[i + 1]

    return True, schedule, F, Fp


# Logic day du de kiem 1 insertion 2-diem (pickup+delivery) bang F: xem
# t4_gate0.feasible_by_F_two_insert - F o day chi la building block.
