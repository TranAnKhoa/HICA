"""Test6.2.md (theo yeu cau nguoi dung, tiep noi Test6.1 Viec2) - Case D:
phan vi du 2D THAT (khong phai truc so 1D nhu case A/B/C cua Test6.1), tai
tao dung co che "canh cheo re bat ngo" cua phan vi du goc dan toi Test6
(Route1/Route2/O3) - co che nay la HINH HOC 2D thuc su: hai route ket thuc
o CUNG mot node voi 4 con so tom tat GIONG NHAU (hoac gan giong), nhung mot
trong hai route co VI TRI TRUNG GIAN khac nhau khien mot canh cheo toi order
thu 3 RE o route nay nhung DAT o route kia - dung KHONG THE tai tao trong
1D (khoang cach tren truc so la tuyet doi |a-b|, khong co "duong tat" giau
duoc sau tom tat). Day chinh la co che da ha guc Pareto-dominance o Test3 va
D1 o Test4 - CHUA duoc test lai bang du lieu MOI, doc lap trong Test6.1
(ca 3 case A/B/C deu dung truc so 1D).

Thiet ke cu the: 2 diem P_start_A, P_start_B O GAN NHAU va gan mot diem goc
X - nhung mot cai lech theo huong X (toa do y duong) con cai kia lech theo
huong nguoc (toa do y am). O3 duoc dat o MOT BEN (y duong) - dung mot canh
CHEO (Pythagoras) tu diem cuoi cua Route A (nam ben y duong) toi P3 se RE
(khoang cach Euclid ngan), nhung tu diem cuoi cua Route B (nam ben y am) toi
P3 se DAT (phai "vong" qua truc x, khoang cach Euclid dai hon nhieu) - MAC
DU Route A va Route B co the co CUNG (K,W) tom tat neu chi nhin tong quang
duong/thoi gian tich luy (thiet ke sao cho gan bang nhau), do la diem
"nguy hiem" cho dominance: neu dominance chi nhin (K,W) tom tat ma khong
biet VI TRI THAT (node hien tai), no co the danh gia sai kha nang chen O3.

LUU Y QUAN TRONG: Label cua Test6 (Sec1, t6_dp.py) dominance yeu cau
v_a = v_b (CUNG node hien tai) truoc khi so (t,K,W) - nen VE MAT THIET KE,
day chinh la diem cot loi can kiem: neu Route A va Route B ket thuc o node
KHAC NHAU thi dominance KHONG duoc ap dung giua chung (an toan tam thuong).
Cai can kiem la: neu chung ket thuc o CUNG mot node (v_a=v_b) nhung den do
qua nhung con duong 2D khac nhau ve mat lich su, dominance van phai dung -
tuc la ngay ca khi v giong nhau, IV/C giong nhau, K/W gan giong nhau, DP
khong duoc bo sot kha nang chen O3 chi vi hinh hoc "an" duoi tom tat.

DUNG: Output/Test6/case_d_2d_report.csv
"""

import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_core as C
import t4_profile as P
import t6_dp as D

OUT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "Output", "Test6")
EPS = 1e-6


class DistTable2D(object):
    """travel_time(a,b) = Euclidean 2D that su tu toa do (x,y) - cho phep
    tai tao dung 'canh cheo' (Pythagoras) khong the co tren truc so 1D."""
    def __init__(self, coords):
        self.coords = dict(coords)

    def __call__(self, a, b):
        if a == b:
            return 0.0
        xa, ya = self.coords[a]
        xb, yb = self.coords[b]
        return math.hypot(xa - xb, ya - yb)


def make_driver_gw(start_node):
    return {"cls": "GW", "start_node": start_node, "t0": 0.0, "capacity": 4.0}


def order(pickup_node, delivery_node, ready_p, deadline_p, ready_d, deadline_d, service=0.0):
    return {"pickup_node": pickup_node, "delivery_node": delivery_node, "demand": 1.0,
            "ready_time_p": ready_p, "deadline_p": deadline_p,
            "ready_time_d": ready_d, "deadline_d": deadline_d, "service_time": service}


def case_D_v2():
    """Phan vi du D - 'canh cheo re bat ngo' 2D that (Euclid), khac han truc
    so 1D cua case A/B/C (Test6.1). Diem mau chot de dominance-giua-chung
    (dung nghia hep Sec2.3: v_a=v_b, CUNG mot tap S) THAT SU duoc kiem: cho
    O1 (pickup P1) va O2 (pickup P2) CUNG GIAO ve MOT NODE VAT LY CHUNG
    "DSHARED" (hop le trong model - 2 don giao cung dia chi, 1 node co the
    la diem giao cua nhieu order khac nhau qua cac lan ghe). Sau khi hoan
    tat CA HAI order (theo BAT KY thu tu nao: O1 truoc hay O2 truoc), xe
    LUON ket thuc tai DUNG node DSHARED - nen 2 label (tu 2 thu tu chen
    khac nhau) THAT SU cung (v=DSHARED, IV=rong, C={O1,O2}) va dominance
    THAT SU ap dung giua chung, dung nghia hep Sec2.3.

    Hinh hoc: X=(0,0). P1=(10,15) "nhanh +y", P2=(10,-15) "nhanh -y" -
    DOI XUNG qua truc x nen quang duong X->P1 = X->P2 = hypot(10,15) va
    K/W cua ca 4 thu tu chen {O1,O2} (da kiem bang brute_force: 4/6 walk
    kha thi co K=22.019,W=1.101 GIONG HET NHAU, 2 walk con lai co K=24.037)
    - dung y de dominance PHAI dua vao (K,W) that, khong "an may" tu chenh
    lech ngau nhien.

    O3 (P3=(26,16), D3=(34,18)) dat GAN P1 (canh P1->P3 = hypot(16,1)=16.03)
    nhung RAT XA P2 (canh P2->P3 = hypot(16,31)=34.89, phai "vong qua" ca
    truc x) - day CHINH LA 'canh cheo re bat ngo' 2D: deadline O3=36 chi
    du cho nhanh DA GHE P1 SOM (truoc khi hoan tat ca {O1,O2}) tranh thu re
    sang O3, nhanh ghe P2 truoc thi khong kip. Da kiem brute_force: bundle
    {O1,O2,O3} kha thi (9 walk), va ca 9 walk deu bat dau bang pickup O1
    hoac pickup O3 - KHONG walk nao bat dau bang pickup O2 truoc, dung
    kha nang du doan."""
    coords = {
        "X": (0.0, 0.0),
        "P1": (10.0, 15.0), "P2": (10.0, -15.0),
        "DSHARED": (20.0, 0.0),   # O1 va O2 giao VE CUNG mot node vat ly (id giong het)
        "P3": (26.0, 16.0), "D3": (34.0, 18.0),
    }
    tt = DistTable2D(coords)
    driver = make_driver_gw("X")

    d_X_P1 = math.hypot(10, 15)
    d_X_P2 = math.hypot(10, -15)
    d_P1_P3 = math.hypot(16, 1)
    d_P2_P3 = math.hypot(16, 31)
    print("  [case D toa do] X->P1=%.3f X->P2=%.3f | P1->P3=%.3f P2->P3=%.3f (bat doi xung ro ret)"
          % (d_X_P1, d_X_P2, d_P1_P3, d_P2_P3))

    orders = {
        # O1, O2 CUNG giao ve node DSHARED (dominance THAT SU ap dung giua
        # cac thu tu chen O1-truoc vs O2-truoc, vi ket thuc CUNG mot v).
        "O1": order("P1", "DSHARED", ready_p=0.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0),
        "O2": order("P2", "DSHARED", ready_p=0.0, deadline_p=200.0, ready_d=0.0, deadline_d=200.0),
        # O3 deadline CHAT (36) - chi kha thi neu ghe P1 (canh CHEO gan, 16.03)
        # SOM, khong kip neu ghe P2 truoc (canh cheo xa, 34.89) do "vong qua"
        # phia doi dien truc x - dung ban chat "canh cheo re bat ngo" 2D.
        "O3": order("P3", "D3", ready_p=0.0, deadline_p=36.0, ready_d=0.0, deadline_d=50.0),
    }
    return tt, driver, orders, 3


def pareto_filter_kw(pts):
    n = len(pts)
    dominated = [False] * n
    for i in range(n):
        Ki, Wi = pts[i]
        for j in range(n):
            if i == j:
                continue
            Kj, Wj = pts[j]
            if Kj <= Ki + EPS and Wj <= Wi + EPS and (Kj < Ki - EPS or Wj < Wi - EPS):
                dominated[i] = True
                break
    return [pts[i] for i in range(n) if not dominated[i]]


def check_case(name, travel_time, driver, orders, B, note=""):
    bf, bf_stats = C.brute_force(travel_time, driver, orders, B)
    dp_result = D.run_dp(travel_time, driver, orders, B, use_dominance=True)
    dp_full = D.run_dp(travel_time, driver, orders, B, use_dominance=False)

    order_ids = sorted(orders.keys())
    all_ok = True
    detail_rows = []

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

            truth_pareto = pareto_filter_kw(truth_kw)
            dp_pareto = pareto_filter_kw(dp_kw)

            for (Kt, Wt) in truth_pareto:
                if not any(Kd <= Kt + EPS and Wd <= Wt + EPS for (Kd, Wd) in dp_pareto):
                    all_ok = False
                    detail_rows.append(dict(case=name, S=sorted(S), issue="TRUTH_MISSING_IN_DP",
                                             truth_point="(%.4f,%.4f)" % (Kt, Wt), dp_pareto=str(dp_pareto)))
            for (Kd, Wd) in dp_pareto:
                if not any(Kt <= Kd + EPS and Wt <= Wd + EPS for (Kt, Wt) in truth_pareto):
                    all_ok = False
                    detail_rows.append(dict(case=name, S=sorted(S), issue="DP_NOT_IN_TRUTH_PARETO",
                                             dp_point="(%.4f,%.4f)" % (Kd, Wd), truth_pareto=str(truth_pareto)))

    print("=== %s === %s" % (name, "PASS" if all_ok else "FAIL"))
    print("  ghi chu:", note)
    print("  DP_full labels created:", dp_full["n_labels_created"], "| DP_prune labels created:", dp_result["n_labels_created"])
    print("  bundles hoan chinh (DP):", sorted(str(sorted(c)) for c in dp_result["complete_by_C"].keys() if dp_result["complete_by_C"][c]))
    if not all_ok:
        for d in detail_rows:
            print("  VIOLATION:", d)
    return all_ok, detail_rows, dp_result, dp_full


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    tt, driver, orders, B = case_D_v2()
    ok, details, dp_result, dp_full = check_case(
        "D_diagonal_shortcut_2D", tt, driver, orders, B,
        note="Kiem co che 'canh cheo re bat ngo' 2D that (Euclid), khac han truc so 1D cua case A/B/C Test6.1 - "
             "O1,O2 CUNG giao ve 1 node vat ly DSHARED (dominance giua cac thu tu chen THAT SU ap dung, dung nghia hep "
             "Sec2.3: v_a=v_b=DSHARED), K/W cua da so thu tu GIONG HET NHAU (22.019,1.101), nhung O3 chi kha thi (deadline=36) "
             "neu nhanh da ghe P1 (canh P1->P3=16.03, gan) - nhanh ghe P2 truoc thi khong kip (canh P2->P3=34.89, xa gap doi).")

    import csv
    if details:
        fields = sorted(set(k for d in details for k in d.keys()))
        with open(os.path.join(OUT, "case_d_2d_report.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(details)
    else:
        with open(os.path.join(OUT, "case_d_2d_report.csv"), "w", newline="", encoding="utf-8") as f:
            f.write("no violations - case D (2D diagonal shortcut) passed\n")

    print("\n=== CASE D TONG KET ===")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
