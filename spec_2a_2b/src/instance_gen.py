"""Spec 2a+2b - instance generator.

Doc lap voi t2_gen (Atlanta pool) - o day dung hop khong gian tong hop
20x20 km theo dung Spec 2a, va tach n_drivers thanh THAM SO DOC LAP (khong
suy ra tu n_orders). Van tra ve driver/orders dict tuong thich voi
t2_core.build_walk_nodes / t6_dp.run_dp (KHONG sua 2 module do).

travel_time(a,b) = euclid_km(a,b) / SPEED_KMH * 60      (PHUT)
  -> giu dung quy uoc t2_gen (travel_time tra PHUT); t6_dp._tt_to_km va
     t4_profile deu quy doi qua SPEED_KMH/60 nen phai giu SPEED_KMH = 20.

Euclid thuan -> bat dang thuc tam giac chinh xac (yeu cau [LOCK] Test2 Sec1.1.2).
"""

import hashlib
import math
import random


def stable_seed(*args):
    """Seed on dinh xuyen tien trinh (thay hash() - bi randomize per-process
    tu Python 3.3, PYTHONHASHSEED, pha vo moi seed=hash(params) cu)."""
    s = "|".join(str(a) for a in args)
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) & 0x7FFFFFFF


AREA_KM = 8.0             # [PATCH new_01] GIA DINH THIET KE, khoa truoc:
#   Spec 2a goc dung 20x20km, nhung avg travel time giua 2 diem ngau nhien o
#   AREA=20 la ~31 phut (0.5214*AREA/SPEED*60) - lon hon han tau nho (10-20p)
#   ngay ca voi corridor bias (bias chi kiem soat HUONG, khong kiem soat
#   KHOANG CACH). feasibility_gate.py do duoc overall feasibility_rate_k1 =
#   15.3% (< nguong 0.5) voi AREA=20 + corridor bias - khong dat du sau khi
#   da ap dung ca 1.1 va 1.2. AREA=8.0 -> avg leg ~12.5 phut, cung do lon voi
#   dai tau {10..60} dang xet. Day la DIEU CHINH THAM SO INSTANCE CO CHU DICH
#   (khong phai bug), quyet dinh boi nguoi dung sau khi xem bang truoc/sau -
#   xem feasibility_gate_k1_by_tau.csv va report patch OD.
SPEED_KMH = 20.0          # PHAI khop t2_gen.SPEED_KMH (t6_dp/t4_profile quy doi qua no)
SERVICE_MIN = 5.0
DAY_MIN = 720.0           # khung ngay 12h de dat time window
GW_AVAIL_MIN = 600.0      # availability window GW "rong" (Spec 2a)

# clustered mode: pickup gom quanh vai diem co dinh (meal-delivery-like)
N_CLUSTERS = 4
CLUSTER_RADIUS_KM = 2.5

# ---- [PATCH new_01] OD corridor bias -----------------------------------
# Fix lai dung nhu t2_gen.py (Test2/Test3 "Viec 1"): OD co deadline_home =
# t0 + direct_time + tau rat chat -> pickup/delivery rai deu toan hop
# 20x20km khien >80% route OD vi pham deadline (do phat hien khi do speedup
# that bang CPLEX, xem report_2a_2b_real_wdp_check.md). GIA DINH THIET KE,
# khoa truoc, KHONG chinh cho toi khi feasibility_rate "dep":
CORRIDOR_SHARE = 0.7        # ty le order dat quanh corridor cua 1 OD duoc chon
CORRIDOR_BUFFER_KM = 3.0    # be rong vung dem quanh doan thang start->home


def _lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _offset_perp(base, a, b, offset_km):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return base
    px, py = -dy / length, dx / length
    x = min(AREA_KM, max(0.0, base[0] + px * offset_km))
    y = min(AREA_KM, max(0.0, base[1] + py * offset_km))
    return (x, y)


def _sample_corridor_pt(rng, start_xy, home_xy, buffer_km=CORRIDOR_BUFFER_KM):
    t = rng.uniform(0.0, 1.0)
    base = _lerp(start_xy, home_xy, t)
    perp = rng.uniform(-buffer_km, buffer_km)
    return _offset_perp(base, start_xy, home_xy, perp)


def _euclid_km(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _rand_pt(rng):
    return (rng.uniform(0.0, AREA_KM), rng.uniform(0.0, AREA_KM))


def _rand_pt_near(rng, center, radius):
    # diem ngau nhien trong dia tron ban kinh 'radius' quanh center, kep trong hop
    ang = rng.uniform(0.0, 2 * math.pi)
    r = radius * math.sqrt(rng.random())
    x = min(AREA_KM, max(0.0, center[0] + r * math.cos(ang)))
    y = min(AREA_KM, max(0.0, center[1] + r * math.sin(ang)))
    return (x, y)


def generate_instance(n, B_gw, B_od, tw_width, n_drivers, seed,
                      tau=20.0, spatial_mode="dispersed", gw_od_ratio=0.5,
                      corridor_share=None, corridor_buffer_km=None):
    """Sinh 1 instance.

    [PATCH rq1] corridor_share, corridor_buffer_km (optional, mac dinh None):
    neu truyen, GHI DE hang so global CORRIDOR_SHARE=0.7 / CORRIDOR_BUFFER_KM=
    3.0 CHI cho lan goi nay - dung cho Rq1.md Sec3 (calibration curve alignment
    target). None (mac dinh) = dung dung 2 hang so cu nhu truoc gio, KHONG doi
    hanh vi cho 2a/2b hay bat ky caller nao khac khong truyen tham so nay - day
    la CONG TUY CHINH MOI, KHONG phai doi default (Rq1.md Sec2: "khong doi bat
    ky default nao ngoai hai truc duoc kiem soat o Sec4"). corridor_buffer_km
    them SAU corridor_share (2026-09-16): calibration curve 1 chieu voi chi
    corridor_share KHONG du manh de phu target range {0.10,...,0.90} - buffer
    co dinh 3.0km qua rong so voi r0~1.36km khien alignment "sai" ngay ca khi
    tat corridor bias hoan toan (corridor_share=0 van cho alignment~0.43) -
    can them chieu dieu khien thu 2.

    [PATCH new_03] B tach thanh B_gw/B_od (xem new03.md Viec 1) - GW va OD la
    HAI THAM SO DOC LAP, khong con dung chung 1 gia tri B. Ly do: OD da bi
    gioi han chat boi tau (detour budget) nen bundle OD lon it co y nghia; GW
    khong co rang buoc tau nen B_gw la truc can khao sat rong. Day la
    QUYET DINH THIET KE (khong phai gioi han ky thuat) - khong anh huong
    DSIC/VCG: B (chung hay tach lop) van la route range cong bo truoc,
    bid-independent (dieu kien song con #2 cua de cuong goc).

    n           : so order
    B_gw        : bound bundle size cho driver GW (dat capacity = B_gw)
    B_od        : bound bundle size cho driver OD (dat capacity = B_od)
    tw_width    : do rong time window (phut)
    n_drivers   : so driver (THAM SO DOC LAP - khong suy tu n)
    seed        : seed tai tao
    tau         : detour budget OD (phut) - 2a co dinh, 2b quet
    spatial_mode: "dispersed" | "clustered"
    gw_od_ratio : ty le GW trong tong driver (0.5 = 50:50)

    Tra (drivers, orders, travel_time_fn, meta).
      drivers : list dict, moi dict tuong thich t2_core.build_walk_nodes
      orders  : {oid: {...}} tuong thich t2_core.build_walk_nodes
      travel_time(a, b) -> PHUT
    """
    rng = random.Random(seed)

    node_xy = {}
    ctr = [0]

    def new_node(xy):
        nid = "n%d" % ctr[0]
        ctr[0] += 1
        node_xy[nid] = xy
        return nid

    def travel_time(a, b):
        if a == b:
            return 0.0
        return _euclid_km(node_xy[a], node_xy[b]) / SPEED_KMH * 60.0

    # ---- cluster centers (chi dung khi clustered) --------------------------
    centers = [_rand_pt(rng) for _ in range(N_CLUSTERS)]

    # ---- drivers (sinh TRUOC orders - can start/home cua OD de corridor bias) --
    n_gw = int(round(n_drivers * gw_od_ratio))
    n_od = n_drivers - n_gw
    drivers = []

    for gi in range(n_gw):
        s_xy = _rand_pt(rng)
        s_node = new_node(s_xy)
        drivers.append({
            "id": "gw%d" % gi, "cls": "GW",
            "start_node": s_node, "t0": 0.0,
            "capacity": float(B_gw),
            "availability_min": GW_AVAIL_MIN,
        })

    od_xy = []  # (start_xy, home_xy) - dung cho corridor bias khi sinh orders
    for oi in range(n_od):
        o_xy = _rand_pt(rng)
        h_xy = _rand_pt(rng)
        o_node = new_node(o_xy)
        h_node = new_node(h_xy)
        direct_t = travel_time(o_node, h_node)
        od_xy.append((o_xy, h_xy))
        drivers.append({
            "id": "od%d" % oi, "cls": "OD",
            "start_node": o_node, "t0": 0.0,
            "capacity": float(B_od),
            "home_node": h_node, "direct_time": direct_t, "tau": float(tau),
        })

    # ---- orders -----------------------------------------------------------
    # [PATCH new_01] Viec 1.1 + 1.2: OD co deadline_home = t0+direct_time+tau
    # rat chat -> neu pickup/delivery rai deu toan hop 20x20km, hau het route
    # OD vi pham deadline (fix cu o t2_gen.py, chua duoc mang sang generator
    # nay). Ap dung corridor bias: voi xac suat CORRIDOR_SHARE, chon ngau
    # nhien 1 driver OD trong instance, dat pickup+delivery quanh doan thang
    # start->home cua driver do (bang CORRIDOR_BUFFER_KM); nguoc lai giu
    # nguyen cach sinh cu (rai deu / clustered). Order van "chung" cho ca GW
    # lan OD - khong gan cung driver nao, chi thien vi VI TRI de it nhat vai
    # OD co route kha thi.
    eff_corridor_share = CORRIDOR_SHARE if corridor_share is None else corridor_share
    eff_corridor_buffer_km = CORRIDOR_BUFFER_KM if corridor_buffer_km is None else corridor_buffer_km
    orders = {}
    for i in range(n):
        oid = "o%d" % i
        use_corridor = bool(od_xy) and rng.random() < eff_corridor_share
        if use_corridor:
            s_xy, h_xy = rng.choice(od_xy)
            p_xy = _sample_corridor_pt(rng, s_xy, h_xy, buffer_km=eff_corridor_buffer_km)
            d_xy = _sample_corridor_pt(rng, s_xy, h_xy, buffer_km=eff_corridor_buffer_km)
        elif spatial_mode == "clustered":
            # pickup gom quanh 1 cluster center; delivery rai ngau nhien
            c = rng.choice(centers)
            p_xy = _rand_pt_near(rng, c, CLUSTER_RADIUS_KM)
            d_xy = _rand_pt(rng)
        elif spatial_mode == "dispersed":
            p_xy = _rand_pt(rng)
            d_xy = _rand_pt(rng)
        else:
            raise ValueError("spatial_mode phai la 'dispersed' | 'clustered'")

        p_node = new_node(p_xy)
        d_node = new_node(d_xy)

        # time window: rong tw_width. [PATCH new_01 Sec1.1] neo ready_time
        # theo tau khi order duoc dat qua corridor bias (de trung binh nam
        # trong cua so ma it nhat 1 OD reachable co the chinh phuc); giu
        # cach sinh cu (rai deu khung ngay) khi khong dung corridor.
        if use_corridor:
            ready_p = rng.uniform(0.0, max(1.0, tau))
        else:
            ready_p = rng.uniform(0.0, max(1.0, DAY_MIN - tw_width))
        deadline_p = ready_p + tw_width
        ready_d = ready_p
        deadline_d = deadline_p + tw_width
        orders[oid] = {
            "pickup_node": p_node, "delivery_node": d_node,
            "demand": 1.0,
            "ready_time_p": ready_p, "deadline_p": deadline_p,
            "ready_time_d": ready_d, "deadline_d": deadline_d,
            "service_time": SERVICE_MIN,
        }

    # ---- [LOCK] bat dang thuc tam giac (Test2 Sec1.1.2) --------------------
    # travel_time = euclid_km / speed: metric Euclid THOA bat dang thuc tam
    # giac CHINH XAC (khong xap xi) theo dai so - khong phu thuoc toa do cu
    # the. O n<=15 (Test2-6) assertion O(n^3) day du con re; o n=100 (~215
    # node) no ton ~13s/instance va KHONG the that bai (Euclid). Giu 1 mau
    # ngau nhien O(n) lam sanity-check, khong duyet toan bo O(n^3).
    ids = list(node_xy.keys())
    if len(ids) >= 3:
        _rng_chk = random.Random(stable_seed(seed, "trichk"))
        for _ in range(min(2000, len(ids) * 5)):
            a, b, cc = _rng_chk.sample(ids, 3)
            if travel_time(a, cc) > travel_time(a, b) + travel_time(b, cc) + 1e-9:
                raise AssertionError("triangle inequality violated: %s->%s->%s" % (a, b, cc))

    meta = {
        "n": n, "B_gw": B_gw, "B_od": B_od, "tw_width": tw_width, "n_drivers": n_drivers,
        "seed": seed, "tau": tau, "spatial_mode": spatial_mode,
        "gw_od_ratio": gw_od_ratio, "n_gw": n_gw, "n_od": n_od,
        "n_nodes": len(node_xy),
        "corridor_share": eff_corridor_share, "corridor_buffer_km": eff_corridor_buffer_km,
        "node_xy": dict(node_xy),   # [PATCH rq1] them de Rq1.md Sec3 (alignment
                                    # metric) tinh khoang cach diem-den-doan
                                    # CHINH XAC - khong doi field nao khac,
                                    # thuan tuy BO SUNG thong tin da co san
                                    # trong closure, khong anh huong bat ky
                                    # logic nao dang doc meta hien co (chi
                                    # doc key co san, them key moi khong pha
                                    # vo code cu).
    }
    return drivers, orders, travel_time, meta


# --------------------------------------------------------------------------
# [PATCH new_03] Viec 2 - Pairwise Compatibility Filter (PCF): precompute
# compat_graph[i][j] MOT LAN cho ca instance (khong phu thuoc driver cu the -
# chi phu thuoc vi tri/time-window cua order), dung lai cho MOI driver khi
# chay DP. Xem new03.md Sec2.2 "BUOC 0".
# --------------------------------------------------------------------------

def _pair_feasible_one_order(travel_time, seq):
    """seq: list (node_id, e, l, s) THEO DUNG THU TU can kiem tra (khong gom
    driver start - goi tu build_compat_graph, start la node dau tien cua seq).
    Tra True neu di het seq (lien tuc tu diem dau) khong vi pham time window
    tai bat ky diem nao. CHI xet time window + travel (bo qua capacity/driver
    cu the - day la precompute CHUNG cho moi driver, dung "diem xuat phat gia
    dinh" la pickup dau tien cua cap, khong phai driver that)."""
    if not seq:
        return True
    cur_node, cur_t = seq[0][0], seq[0][1]
    for (nid, e, l, s) in seq[1:]:
        tt = travel_time(cur_node, nid)
        A = cur_t + tt
        Bt = A if A > e else e
        if Bt > l + 1e-9:
            return False
        cur_t = Bt + s
        cur_node = nid
    return True


def _order_events(oid, o):
    p = (o["pickup_node"], o["ready_time_p"], o["deadline_p"], o["service_time"])
    d = (o["delivery_node"], o["ready_time_d"], o["deadline_d"], o["service_time"])
    return p, d


def _pair_has_feasible_order(travel_time, oi, oj):
    """Thu ca 6 thu tu hop le (precedence: pickup truoc delivery cung don) cho
    cap (oi, oj). Diem xuat phat gia dinh = pickup som nhat trong 2 don (dung
    ready_time_p lam moc t0 gia dinh, KHONG phu thuoc driver cu the - day la
    tinh CHUNG cho ca instance). Tra True neu >=1 trong 6 thu tu kha thi."""
    Pi, Di = _order_events(*oi)
    Pj, Dj = _order_events(*oj)
    # 6 thu tu hop le cua {Pi,Di,Pj,Dj} voi rang buoc Pi<Di, Pj<Dj:
    #   Pi Di Pj Dj | Pj Dj Pi Di | Pi Pj Di Dj | Pi Pj Dj Di | Pj Pi Di Dj | Pj Pi Dj Di
    orders6 = [
        [Pi, Di, Pj, Dj], [Pj, Dj, Pi, Di],
        [Pi, Pj, Di, Dj], [Pi, Pj, Dj, Di],
        [Pj, Pi, Di, Dj], [Pj, Pi, Dj, Di],
    ]
    t0_guess = min(Pi[1], Pj[1])
    start = (orders6[0][0][0], t0_guess, t0_guess, 0.0)   # node cua diem dau, t0 gia dinh
    for seq in orders6:
        full = [start] + [(nid, e, l, s) for (nid, e, l, s) in seq]
        if _pair_feasible_one_order(travel_time, full):
            return True
    return False


def build_compat_graph(travel_time, orders):
    """[PATCH new_03] precompute compat_graph = {frozenset({i,j}): bool} cho
    MOI cap order trong instance. Dung lai (khong tinh lai) cho tat ca driver
    khi chay DP - xem new03.md Sec2.2 BUOC 0. Chi xet time window + travel
    (bo capacity/driver rieng) - la dieu kien CAN cho tuong thich, khong DU."""
    oids = sorted(orders.keys())
    graph = {}
    for a in range(len(oids)):
        for b in range(a + 1, len(oids)):
            i, j = oids[a], oids[b]
            oi = (i, orders[i])
            oj = (j, orders[j])
            graph[frozenset((i, j))] = _pair_has_feasible_order(travel_time, oi, oj)
    return graph
