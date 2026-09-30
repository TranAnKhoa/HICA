"""DEMO: cau truc constraints cua model CPLEX PDPTW lien khoi (monolithic,
arc-based) dung trong Compare_result.md - Phien ban A, nhanh 1.

File nay la ban RUT GON + CHU THICH cho MUC DICH TRINH BAY (giai thich cho
giang vien vi sao model bung no nhanh du n nho) - logic dung dung
test_compact_arc_milp.py (da chay that, da doi chieu Z* voi route-pool),
KHONG viet lai thuat toan, chi trich va gom nhom lai co giai thich.

===============================================================================
VI SAO n=4 (hoac n nho noi chung) VAN CO THE CHAM VOI MODEL NAY:
===============================================================================

Day KHONG phai "n=4 order thi bai toan nho" theo nghia thong thuong. So bien/
rang buoc KHONG scale theo n don gian - no scale theo (n x driver) VI MOI
DRIVER CO MOT BAN SAO RIENG cua toan bo do thi arc:

  - Voi 1 driver, n order: co 2n+1 node (1 start + n pickup + n delivery,
    cong 1 home neu la OD). So CAP node (a,b) toi da la O(n^2) -> so bien
    arc y[i,j,k] la O(n_drivers x n^2).
  - Vi du n=8, n_drivers=4: ~17 node/driver x 4 driver = 68 node, nhung so
    CAP (arc) la ~17*16 x 4 ~ 1,088 bien nhi phan CHI RIENG cho y - chua ke
    t[i,k] (continuous, cho time), load[i,k], served[i,k] (2 bien resource
    TACH RIENG - xem ghi chu duoi), end_of[i,k] (GW).
  - Rang buoc big-M (thoi gian, tai trong, so don da phuc vu) MOI CAP ARC
    can 2-3 dong rang buoc rieng (bat gia tri lien tuc khi arc active).

=> Voi bai toan set-partitioning/routing dang nay, SO BIEN NHI PHAN va SO
RANG BUOC BIG-M tang xap xi BAC 2 theo (n x n_drivers) - CPLEX B&B phai
kham pha khong gian nghiem lon hon rat nhieu so voi con so "n" gian di cho
thay, va cac rang buoc big-M noi tieng la lam LP-relaxation LONG LEO (bound
yeu), khien pruning trong B&B kem hieu qua di rat nhieu - day la ly do co
ban khien MILP dang arc-based/big-M cho VRP/PDPTW noi tieng la kho scale,
DU LA VAN DE CAU TRUC CUA DANG MODEL NAY (khong phai loi cai dat).

Doi chieu: Algorithm A + B (decomposed) TRANH duoc van de nay bang cach
KHONG dung bien arc/big-M nua - Algorithm A liet ke SAN cac route kha thi
(DP nhan tien, khong big-M) thanh mot "route pool" hop chat, roi Algorithm B
chi giai 1 set-partitioning THUAN TUY (khong con bien thoi gian/tai trong -
da "an" trong chi phi route) - day chinh la ly do decomposed nhanh hon
40,000-300,000 lan o cung instance (xem ket qua thuc te trong
spec_2a_2b/results/compare_monolithic_vs_decomposed.csv).
===============================================================================

Chay demo (in ra so bien/rang buoc that cho 1 instance nho, KHONG solve):
  "C:\\Users\\An Khoa\\AppData\\Local\\Programs\\Python\\Python37\\python.exe" \\
      spec_2a_2b\\src\\pdptw_monolithic_demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
_CPLEX_PATH = os.path.join("K:" + os.sep, "Programing Hardware", "Cplex", "cplex",
                           "python", "3.7", "x64_win64")
if _CPLEX_PATH not in sys.path:
    sys.path.insert(0, _CPLEX_PATH)

import instance_gen as IG
import test_compact_arc_milp as CM


# =============================================================================
# TOM TAT CAC NHOM CONSTRAINT (doc de hieu, khong phai code chay) - danh cho
# giang vien: day la cac nhom rang buoc CHINH trong build_compact_model()
# cua test_compact_arc_milp.py, theo dung thu tu trong ham do.
# =============================================================================
CONSTRAINT_GROUPS_EXPLAINED = """
BIEN (moi driver k, moi cap node (i,j) trong do thi RIENG cua driver do):
  y[i,j,k] in {0,1}   - driver k co di THANG tu node i sang node j khong
  t[i,k]   continuous - thoi diem driver k den node i (bi chan boi [e_i, l_i])
  load[i,k] continuous - tai trong TUC THOI tai node i (0..capacity)
  served[i,k] continuous - TONG SO DON da pickup TOI node i (0..B, khac load:
                            KHONG giam khi giao hang - day moi la B-cap that su)
  end_of[i,k] in {0,1} - (chi GW) danh dau node i la node KET THUC route
  z[o] in {0,1}        - order o bi tu choi, giao cho FD (freelance delivery)

RANG BUOC (nhom, dung so thu tu trong code):
  (1) Covering:      moi order duoc phuc vu DUNG 1 LAN - qua 1 driver DUY
                      NHAT, HOAC qua z_o=1 (FD). => Sum_k visited[pickup_o,k]
                      + z_o = 1.
  (2) PD-link:       pickup va delivery CUNG 1 order, CUNG driver phai
                      CUNG duoc tham hoac CUNG khong (visited bang nhau).
  (2b) Precedence:   t[delivery] >= t[pickup] + travel(pickup,delivery) -
                      dam bao thu tu pickup-truoc-delivery (KHONG the suy ra
                      tu flow conservation don thuan - da co bug thuc te ve
                      diem nay, xem chu thich dong 276-301 file goc).
  (3) Flow cons.:    tai moi node duoc tham: sum(arc vao) = visited,
                      sum(arc ra) <= visited (GW co the KET THUC tai bat
                      ky node nao, khong bat buoc quay ve).
  (4) Start/home:    OD bat buoc dung DUNG 1 arc ra tu start VA DUNG 1 arc
                      vao home. GW: <=1 arc ra tu start (co the route rong).
  (5) Time (big-M):  y[i,j,k]=1 => t[j,k] >= t[i,k] + travel(i,j) + service(i)
                      - dung Big-M (M = deadline lon nhat toan instance) de
                      "tat" rang buoc khi arc khong active - day la NGUON
                      CHINH cua LP-relaxation long leo (M lon => bound yeu).
  (6) Load (big-M):  tuong tu (5), nhung cho tai trong tuc thoi (+demand khi
                      pickup, -demand khi delivery).
  (6b) Served (big-M): tuong tu, nhung CHI TANG khi pickup (KHONG giam khi
                      giao hang) - day moi la B-cap DUNG (tong so don MOT
                      route tung phuc vu, khac tai trong tuc thoi).
  (7)/(7b) K_raw/W_raw: tich luy chi phi THO (khoang cach x kappa, thoi gian
                      active) qua CAC ARC DUOC DUNG - rieng W_raw can them
                      xu ly waiting time (khong nam tren arc nao ca).
  (8) K_final/W_final: OD tru di quang duong/thoi gian di THANG ve nha
                      (detour cost that su); GW giu nguyen (khong co "duong
                      thang" tham chieu).

=> Diem mau chot: nhom (5),(6),(6b) la RANG BUOC BIG-M, moi nhom co SO
LUONG RANG BUOC = O(so arc) = O(n_drivers x n^2). Day la NGUYEN NHAN CHINH
khien so rang buoc bung no nhanh hon nhieu so voi "n" don gian ma thay nhin
thay, VA la ly do LP-relaxation long leo (big-M luon danh doi giua "an toan"
va "chat", chon M an toan thi bound cang long).
"""


def demo_size(n, B, tw_width, n_drivers, seed):
    """Sinh 1 instance va dem so bien/rang buoc THAT SU se duoc tao ra,
    KHONG solve - chi de minh hoa toc do bung no."""
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B, B_od=B, tw_width=tw_width, n_drivers=n_drivers,
        seed=seed, tau=20.0, spatial_mode="dispersed")
    theta_by_driver = {d["id"]: 1.0 for d in (drivers if isinstance(drivers, list) else drivers.values())}
    q_o_by_order = {oid: 5.0 for oid in orders}

    c, meta2 = CM.build_compact_model(drivers, orders, q_o_by_order, tt, theta_by_driver)
    n_vars = c.variables.get_num()
    n_bin = c.variables.get_num_binary()
    n_cons = c.linear_constraints.get_num()
    c.end()
    return n_vars, n_bin, n_cons


def main():
    print(CONSTRAINT_GROUPS_EXPLAINED)
    print("=" * 90)
    print("So bien/rang buoc THAT SU sinh ra (khong solve) - minh hoa toc do bung no:")
    print("=" * 90)
    print("%6s %6s %10s %12s %12s %14s" % ("n", "B", "n_drivers", "n_vars", "n_binary", "n_constraints"))
    for (n, B, ndrv) in [(4, 2, 3), (8, 2, 4), (10, 3, 5), (15, 3, 6), (20, 3, 8)]:
        n_vars, n_bin, n_cons = demo_size(n, B, 120, ndrv, seed=0)
        print("%6d %6d %10d %12d %12d %14d" % (n, B, ndrv, n_vars, n_bin, n_cons))


if __name__ == "__main__":
    main()
