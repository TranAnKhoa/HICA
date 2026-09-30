"""kstar_gridcheck.py -- doc lap voi kstar_rule.py, theo dung khuyen nghi Add_test.md
Sec1.2 ("cach de lam nhat, ton it cong nhat ma van that su doc lap").

kstar_rule.py tinh margin bang CACH: dung cac duong thang affine (a, w) trong
dominator_lines(), tim envelope NHO NHAT qua MIN cua toan bo duong, roi lay MAX
tren cac diem kink + hai dau mut (dua vao tinh LOM cua mu_r = E_r - c_r de
chi can kiem diem kink, khong can quet het [lo,hi]).

File nay tinh margin bang CACH KHAC VE CAU TRUC: grid brute-force tho, KHONG
gia dinh gi ve loi/lom, KHONG dung diem kink -- chi chia [lo,hi] thanh n_grid
diem DEU NHAU, tai MOI diem tinh truc tiep:
    E_r(b) = min_{r' in D(r)} (K_{r'} + b*W_{r'})    (duyet toan bo D(r), khong
                                                        rut gon ve danh sach
                                                        (a,w) truoc)
    c_r(b) = K_r + b*W_r
    mu_r(b) = E_r(b) - c_r(b)
roi lay max qua toan bo grid. Neu max > tol -> r in K*.

Khong import/goi bat ky ham nao trong kstar_rule.py -- tu viet lai D(r), E_r,
c_r tu du lieu tho (rid, bundle, K, W) + q. Muc dich: neu ca hai cach tinh
(kink-based vs grid-based) cho CUNG mot tap kept tren nhieu instance, do la
bang chung kiem chung doc lap that su (khac duong tinh toan, khong chi khac
ten bien/code).
"""
import itertools


def _dominators(routes, q, rid, bundle):
    """D(r): moi route r' (rid2 != rid) co bundle S' la TAP CON THAT SU/BANG
    cua S=bundle, CONG voi 'route rong' (khong dung driver nao, moi order
    con lai di FD). Tra list (a, w) voi cost tai b la a + b*w.
    Tu viet lai tu dau, KHONG goi kstar_rule.dominator_lines()."""
    S = frozenset(bundle)
    qS = sum(q[o] for o in S)
    lines = [(qS, 0.0)]  # route rong: toan bo S di FD, khong phu thuoc b
    for (rid2, S2, K2, W2) in routes:
        if rid2 == rid:
            continue
        S2 = frozenset(S2)
        if not S2 <= S:
            continue
        qrest = qS - sum(q[o] for o in S2)  # phan con lai cua S ngoai S2, di FD
        lines.append((K2 + qrest, W2))
    return lines


def grid_margin(routes, q, rid, bundle, K, W, lo, hi, n_grid):
    """max_{b in grid deu tren [lo,hi], n_grid diem} (E_r(b) - c_r(b)).
    Grid THO, khong dung kink -- neu n_grid qua nho co the bo sot dinh that
    (mu_r la ham lom nen dinh that CHI o kink, khong chac trung diem grid) --
    day la ly do can tang n_grid khi nghi ngo lech o bien (Add_test.md Sec1.3)."""
    lines = _dominators(routes, q, rid, bundle)
    best = float("-inf")
    for k in range(n_grid):
        b = lo + (hi - lo) * k / (n_grid - 1)
        Er = min(a + b * w for (a, w) in lines)
        cr = K + b * W
        mu = Er - cr
        if mu > best:
            best = mu
    return best


def kstar_gridcheck(routes, q, lo, hi, n_grid=5000, tol=1e-9):
    """routes: list of (rid, bundle, K, W) CUNG mot driver (giong dinh dang
    kstar_rule.local_frontier nhan). Tra (kept: list[rid], margin: dict).
    Hoan toan doc lap: khong import kstar_rule, khong dung dominator_lines/
    envelope/candidate_points cua kstar_rule.py."""
    kept, margin = [], {}
    for (rid, bundle, K, W) in routes:
        m = grid_margin(routes, q, rid, bundle, K, W, lo, hi, n_grid)
        margin[rid] = m
        if m > tol:
            kept.append(rid)
    return kept, margin
