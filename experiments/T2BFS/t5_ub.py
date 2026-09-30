"""Test5.md Sec0 - UB1_R(d), UB2_R(d): can tren cho "R tu cuu duoc minh
bang cach chen du d order tu Rem(S)". Tai dung sigma_j(R) da co tu t4_profile
(KHONG viet lai). Hai can nay tra loi CAU HOI KHAC voi UB_R(T)=min_j sigma_j
o t4_run_viec54.py (do o do la can cho "chen 1 order BAT KY trong T", con o
day la can cho "chen DU d order CUNG LUC") - xem Test5.md Sec0, KHONG duoc
gop code hai dai luong nay.
"""

import itertools
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t4_profile as P


def UB1(gamma, rem_orders, d):
    """Tong d gia tri sigma_j(R) LON NHAT trong {sigma_j(R): j in rem_orders}.
    Neu so order co sigma_j > -inf (kha chen rieng le) < d, tra -inf (khong
    du order de chen, chac chan chet)."""
    sigmas = sorted((P.sigma_j(gamma.get(j, [])) for j in rem_orders), reverse=True)
    finite = [s for s in sigmas if s != float("-inf")]
    if len(finite) < d:
        return float("-inf")
    return sum(sigmas[:d])


def UB2(gamma, rem_orders, d):
    """max qua moi to hop {j1..jd} subset rem_orders, cua min_j sigma_j(R).
    O(C(m,d)). Neu khong du d order kha chen rieng le, tra -inf."""
    best = float("-inf")
    feas_js = [j for j in rem_orders if P.sigma_j(gamma.get(j, [])) != float("-inf")]
    if len(feas_js) < d:
        return float("-inf")
    for combo in itertools.combinations(rem_orders, d):
        vals = [P.sigma_j(gamma.get(j, [])) for j in combo]
        if any(v == float("-inf") for v in vals):
            continue
        m = min(vals)
        if m > best:
            best = m
    return best
