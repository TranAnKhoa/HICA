"""Test6.1.md Viec 2 - tan cong bang phan vi du DUNG TAY (khong sinh ngau
nhien). Dung travel_time TRUC TIEP tu bang khoang cach tu dinh nghia (khong
qua toa do Euclid cua t2_gen) de kiem soat CHINH XAC tung con so, dung dinh
huong cua Test6.1.md Sec2.

GHI CHU TRUNG THUC (bat buoc cong khai): so lieu dung tay goc cua phan vi du
A/B (P1=10,D1=12,P2=30,D2=32, tau=11/22, slack=19/2) nam trong LICH SU HOI
THOAI TRUOC Test4, KHONG con trong context hien tai (da bi nen/compact) va
KHONG xuat hien trong bat ky file Guideline/*.md nao khac ngoai chinh mo ta
tom tat trong Test6.1.md. KHONG the doi chieu tung chu so voi ban goc.

Theo dung Sec2.2 diem 4 cua spec: "brute_force() moi la trong tai", khong
phai dap an tinh tay. Vi vay o day TU DUNG LAI mot instance cu the THEO DUNG
CAU TRUC mo ta (crisscross dau tuyen / nut that hai dau tuyen / 3 nen+1 chen)
bang travel_time suy tu TOA DO 1D (truc so) - dam bao TU DONG day du moi
cap canh VA thoa bat dang thuc tam giac tuyet doi (brute_force duyet MOI
hoan vi 2k phan tu, can du khoang cach cho MOI cap, khong chi cac cap "co y
nghia" - liet ke tay tung canh nhu ban dau da gay loi KeyError vi thieu
canh). Danh doi: 1D don gian hon hinh hoc 2D cua vi du goc, nhung du de tao
dung dung cau truc (khe ho dau tuyen, nut that hai dau, do sau 3) vi cau
truc do chi phu thuoc THU TU va KHOANG CACH tuong doi.

Dung brute_force() GOC lam trong tai duy nhat - dung dung tinh than doi
khang cua Test6.1: neu DP khop brute_force, KET LUAN DP DUNG cho instance
nay, bat ke co khop dap an tay cu (khong the doi chieu, vi transcript da bi
nen) hay khong. Ghi ro dieu nay trong report, KHONG gia vo day la ban sao
chinh xac cua vi du cu.

DUNG: Output/Test6/viec2_handbuilt_counterexamples.csv
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t4_profile as P
import t6_dp as D

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")
EPS = 1e-6


class DistTable(object):
    """travel_time(a,b) tra ve tu TOA DO 1D (truc so) cho MOI node - dam bao
    TU DONG day du (moi cap node deu co khoang cach) VA thoa bat dang thuc
    tam giac tuyet doi (|x_a - x_b|, metric chuan tren truc so) - AN TOAN HON
    liet ke tay tung cap canh (brute_force() duyet MOI hoan vi 2k phan tu,
    can du khoang cach cho MOI cap, khong chi cac cap "co y nghia").

    Danh doi: 1D khong the tao hinh hoc phang phuc tap nhu vi du dung tay
    goc (co the da dung 2D that su) - nhung DU de tao dung cau truc can kiem
    (khe ho dau tuyen, nut that hai dau, do sau 3) vi cau truc do CHI phu
    thuoc THU TU va KHOANG CACH tuong doi tren 1 truc thoi gian/khong gian,
    khong phu thuoc goc nhin 2D. Ghi ro trong report."""
    def __init__(self, coords):
        self.coords = dict(coords)

    def __call__(self, a, b):
        if a == b:
            return 0.0
        return abs(self.coords[a] - self.coords[b])


def make_driver_gw(start_node):
    return {"cls": "GW", "start_node": start_node, "t0": 0.0, "capacity": 4.0}


def order(pickup_node, delivery_node, ready_p, deadline_p, ready_d, deadline_d, service=5.0):
    return {"pickup_node": pickup_node, "delivery_node": delivery_node, "demand": 1.0,
            "ready_time_p": ready_p, "deadline_p": deadline_p,
            "ready_time_d": ready_d, "deadline_d": deadline_d, "service_time": service}


def check_case(name, travel_time, driver, orders, B, expected_note=""):
    """Chay brute_force + DP, so Pareto front, in ket qua. Tra True neu khop."""
    bf, bf_stats = C.brute_force(travel_time, driver, orders, B)
    dp_result = D.run_dp(travel_time, driver, orders, B, use_dominance=True)

    order_ids = sorted(orders.keys())
    all_ok = True
    detail_rows = []

    import itertools
    for k in range(1, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)
            truth_entries = bf.get(S, [])
            truth_exists = len(truth_entries) > 0
            dp_labels = dp_result["complete_by_C"].get(S, [])
            dp_exists = len(dp_labels) > 0

            if truth_exists != dp_exists:
                all_ok = False
                detail_rows.append(dict(case=name, S=sorted(S), issue="EXISTENCE_MISMATCH",
                                         truth_exists=truth_exists, dp_exists=dp_exists))
                continue
            if not truth_exists:
                continue

            truth_kw = []
            for canon, slack, walk in truth_entries:
                ok, slack2, sched = C.is_feasible(travel_time, driver, walk)
                K, W = P.K_W_of_route(driver, travel_time, walk, sched)
                truth_kw.append((K, W))
            dp_kw = [D.finalize_KW(driver, lab) for lab in dp_labels]

            def pareto(pts):
                keep = []
                for i, (K, W) in enumerate(pts):
                    dominated = False
                    for j, (K2, W2) in enumerate(pts):
                        if i == j:
                            continue
                        if K2 <= K + EPS and W2 <= W + EPS and (K2 < K - EPS or W2 < W - EPS):
                            dominated = True
                            break
                    if not dominated:
                        keep.append((K, W))
                return keep

            truth_pareto = pareto(truth_kw)
            dp_pareto = pareto(dp_kw)

            for (Kt, Wt) in truth_pareto:
                found = any(Kd <= Kt + EPS and Wd <= Wt + EPS for (Kd, Wd) in dp_pareto)
                if not found:
                    all_ok = False
                    detail_rows.append(dict(case=name, S=sorted(S), issue="TRUTH_POINT_MISSING_IN_DP",
                                             truth_point="(%.4f,%.4f)" % (Kt, Wt), dp_pareto=str(dp_pareto)))
            for (Kd, Wd) in dp_pareto:
                found = any(Kt <= Kd + EPS and Wt <= Wd + EPS for (Kt, Wt) in truth_pareto)
                if not found:
                    all_ok = False
                    detail_rows.append(dict(case=name, S=sorted(S), issue="DP_POINT_NOT_IN_TRUTH_PARETO",
                                             dp_point="(%.4f,%.4f)" % (Kd, Wd), truth_pareto=str(truth_pareto)))

    print("=== %s === %s" % (name, "PASS" if all_ok else "FAIL"))
    print("  ghi chu:", expected_note)
    print("  bundles hoan chinh tim duoc (DP):", sorted(str(sorted(c)) for c in dp_result["complete_by_C"].keys() if dp_result["complete_by_C"][c]))
    if not all_ok:
        for d in detail_rows:
            print("  VIOLATION:", d)
    return all_ok, detail_rows


def case_A_crisscross():
    """Phan vi du A - crisscross dau tuyen (1D): truc so, X=0. O1(P1=10,D1=12),
    O2(P2=30,D2=32) la 2 order 'nen' - route GON X-P1-D1-P2-D2 di THANG mot
    chieu tren truc, KHONG co khe ho. O3,O4 dat o toa do AM (truoc X tren
    truc) - de tham duoc PHAI di NGUOC (tao 'khe ho'/detour dau tuyen) truoc
    khi quay lai huong P1. Deadline O3/O4 CHAT (chi kha thi neu ghe NGAY dau
    tien, truoc khi di ve huong P1) - buoc DP phai chon nhanh 'ghe O3/O4
    truoc' tu buoc dau tien, dung dinh nghia 'khe ho dau tuyen' cua spec."""
    coords = {
        "X": 0.0,
        "P1": 10.0, "D1": 12.0, "P2": 30.0, "D2": 32.0,
        "P3": -1.0, "D3": -2.0,
        "P4": -1.5, "D4": -2.5,
    }
    tt = DistTable(coords)
    driver = make_driver_gw("X")
    orders = {
        "O1": order("P1", "D1", ready_p=10.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        "O2": order("P2", "D2", ready_p=30.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        "O3": order("P3", "D3", ready_p=0.0, deadline_p=1.5, ready_d=0.0, deadline_d=3.0, service=0.0),
        "O4": order("P4", "D4", ready_p=0.0, deadline_p=2.0, ready_d=0.0, deadline_d=3.5, service=0.0),
    }
    return tt, driver, orders, 4


def case_B_two_ended_knot():
    """Phan vi du B - nut that hai dau tuyen (1D): X=0, P1=10,D1=12, P2=30,
    D2=32 tren CUNG truc (nhu case A, nhung KHONG co O3/O4 o toa do am).
    Route A (X-P1-D1-P2-D2) va Route B (X-P2-D2-P1-D1, di NGUOC truc truoc
    roi ve) deu kha thi rieng cho {O1,O2} (deadline O1/O2 rong, deadline_d
    =200). O3,O4 dat GAN P2 (toa do 29,29.2) voi deadline CHAT quanh khu vuc
    do - chi kha thi neu duoc ghe SOM (ngay sau khi den gan P2), tuc chi
    Route B (ghe P2/D2 truoc) moi co the "tranh thu" ghe O3/O4 ngay khi con
    o gan do, con Route A (den P2/D2 sau cung, da qua deadline O3/O4 tu lau)
    thi khong the."""
    coords = {
        "X": 0.0,
        "P1": 10.0, "D1": 12.0, "P2": 30.0, "D2": 32.0,
        "P3": 29.0, "D3": 29.2,
        "P4": 29.5, "D4": 29.7,
    }
    tt = DistTable(coords)
    driver = make_driver_gw("X")
    orders = {
        "O1": order("P1", "D1", ready_p=10.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        "O2": order("P2", "D2", ready_p=30.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        # O3,O4 chi kha thi neu ghe truoc thoi diem ~30 (tuc PHAI la nhanh
        # ghe P2 vung SOM trong hanh trinh, khong phai sau khi da di qua
        # P1/D1 truoc - buoc DP kiem ca 2 thu tu O1/O2 that su, khong chi 1)
        "O3": order("P3", "D3", ready_p=0.0, deadline_p=31.0, ready_d=0.0, deadline_d=31.5, service=0.0),
        "O4": order("P4", "D4", ready_p=0.0, deadline_p=31.5, ready_d=0.0, deadline_d=32.0, service=0.0),
    }
    return tt, driver, orders, 4


def case_C_three_base_one_insert():
    """Phan vi du C (tu thiet ke, theo yeu cau Sec2.1 muc C, 1D) - 3 order
    "nen" O1,O2,O3 tren truc so tang dan (chuoi X-P1-D1-P2-D2-P3-D3), B=4
    nen chi chen them DUNG 1 order nua. O4 dat GAN khu vuc D1/P2 (giua
    chuoi) voi deadline CHAT - chi kha thi neu duoc ghe DUNG LUC di ngang
    qua do (sau khi giao O1, truoc khi lay O2) - kiem dominance o do SAU 3
    (touched=3: da pickup+deliver O1, da pickup O2 hoac tuong duong) truoc
    khi cho phep hoan tat O2,O3."""
    coords = {
        "X": 0.0,
        "P1": 5.0, "D1": 10.0, "P2": 15.0, "D2": 20.0, "P3": 25.0, "D3": 30.0,
        "P4": 10.5, "D4": 11.0,
    }
    tt = DistTable(coords)
    driver = make_driver_gw("X")
    orders = {
        "O1": order("P1", "D1", ready_p=5.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        "O2": order("P2", "D2", ready_p=0.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        "O3": order("P3", "D3", ready_p=0.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0, service=0.0),
        # O4 chi kha thi neu ghe P4/D4 NGAY SAU D1 (thoi diem ~10), truoc khi
        # tiep tuc ve huong P2 (~15) - deadline chat quanh 10.5-11.0
        "O4": order("P4", "D4", ready_p=0.0, deadline_p=11.0, ready_d=0.0, deadline_d=11.6, service=0.0),
    }
    return tt, driver, orders, 4


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    cases = [
        ("A_crisscross_dau_tuyen", case_A_crisscross,
         "Ky vong: DP tim duoc bundle {O1,O2,O3,O4} qua nhanh dung khe ho dau tuyen"),
        ("B_nut_that_hai_dau", case_B_two_ended_knot,
         "Ky vong: DP tim duoc {O1,O2,O3,O4} it nhat qua 1 duong (giong Route B), khong de dominance giua chung xoa mat duong do"),
        ("C_ba_nen_mot_chen", case_C_three_base_one_insert,
         "Ky vong: DP tim duoc {O1,O2,O3,O4} qua dung khe ho hep giua D1-P2 (do sau 3)"),
    ]

    all_pass = True
    all_details = []
    for name, builder, note in cases:
        tt, driver, orders, B = builder()
        ok, details = check_case(name, tt, driver, orders, B, expected_note=note)
        all_pass = all_pass and ok
        all_details.extend(details)
        print()

    print("=== VIEC2 TONG KET ===")
    print("TAT CA PASS" if all_pass else "CO VIOLATION - xem chi tiet o tren")

    import csv
    if all_details:
        fields = sorted(set(k for d in all_details for k in d.keys()))
        with open(os.path.join(OUT, "viec2_handbuilt_counterexamples.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(all_details)
    else:
        with open(os.path.join(OUT, "viec2_handbuilt_counterexamples.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("no violations - all 3 hand-built cases passed\n")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
