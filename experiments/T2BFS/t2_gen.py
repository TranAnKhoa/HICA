"""Test2.md Sec5 - sinh instance, KHOA GRID truoc khi chay.

Khac biet duy nhat so voi Sec5 goc: toa do node lay tu POOL DIEM THAT cua
Atlanta (Dataset da co san - D1, Sply+Req) thay vi random uniform trong hinh
vuong tong hop. Ly do: de tai su dung ha tang du lieu da co, va vi thu
nghiem nay kiem tra mot TINH CHAT THUAT TOAN (completeness cua BFS, do bung
no |Seq(S)|) - khong phai cau hoi ve dia ly, nen nguon toa do khong anh
huong ban chat cau hoi. Moi tham so con lai (n_orders, B, tw_width, tau,
seeds, area_km, speed, service) GIU NGUYEN dung Sec5, khoa truoc khi chay.

  travel_time(a,b) = euclid_km(a,b) / speed_kmh * 60      (phut)

Euclid thuan tuy (khong circuity) -> thoa bat dang thuc tam giac CHINH XAC
(khong xap xi), dung yeu cau [LOCK] Sec1.1.2. Assertion kiem tra ngay sau
khi sinh.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from Dataset import generate as hica_generate  # noqa: E402
from Dataset import loader as hica_loader       # noqa: E402

# ------------------------------------------------------------- KHOA GRID (Sec5)
N_ORDERS_SMALL = (4, 5, 6)                # gate correctness (brute force con chay noi)
N_ORDERS_BIG = (8, 10, 12, 15)            # do Q2 (chi BFS)
B_GRID = (2, 3, 4)
DRIVER_CLASS = ("OD", "GW")
TW_WIDTH_GRID = (30, 60, 120, 240)        # phut
TAU_GRID = (15, 30, 60)                   # phut, chi OD
AREA_KM = 10.0
SPEED_KMH = 20.0
SERVICE_MIN = 5.0
GW_AVAIL_MIN = 480.0
# Seeds: spec khoa 30/cell. Phien nay giam con SEEDS_PER_CELL vi ngan sach
# thoi gian - giam GIAM CONG KHAI, khong am tham (xem REPORT Sec "Deviations").
SEEDS_PER_CELL = 8
CAPACITY = None   # dat = B khi sinh (xem ghi chu duoi) -- demand=1/don, khong
# rang buoc trong Sec5; chon capacity=B de capacity KHONG BAO GIO la nut that
# (moi don demand=1, toi da B don/bundle -> tai toi da B), giu thi nghiem tap
# trung dung vao cau hoi TW/slack* ma grid nham do, khong tron voi cau hoi
# capacity rieng (spec khong khoa mot gia tri capacity nao).

# [PATCH Test3.md Viec1] Sau khi neo ready_time theo tau, feasibility_rate_k1
# cua OD van duoi 50% o tau=15/30 (3.9%/17.2%) - xac nhan bang chung "P/D sinh
# random toan vung, khong quanh corridor start->home" (xem chan doan thu cong
# trong hoi thoai: cac chang start->p, p->d, d->home deu lon xap xi bang chinh
# direct_time, du ready_time da dung luc). Sua: P/D cua OD duoc uu tien lay
# tu vung dem CORRIDOR_BUFFER_KM quanh doan thang start->home, ty le
# CORRIDOR_SHARE (con lai lay ngau nhien toan pool nhu cu). Day la MOT GIA
# DINH THIET KE (khong duoc Test2.md/Test3.md khoa gia tri) - cong khai trong
# report, khong am tham chinh cho dep so.
CORRIDOR_BUFFER_KM = 3.0
CORRIDOR_SHARE = 0.7

_POOL_CACHE = {}


def _atlanta_pool(session=3, network="ARC,Road"):
    """Tra list (lat, lon) tu Sply+Req cua 1 session D1 - nguon toa do that."""
    key = (session, network)
    if key in _POOL_CACHE:
        return _POOL_CACHE[key]
    sess = hica_generate.load_session(session, network)
    pts = sess["points"]
    xy = [(la, lo) for _, la, lo in pts["Sply"]] + [(la, lo) for _, la, lo in pts["Req"]]
    _POOL_CACHE[key] = xy
    return xy


def _project_km(anchor_latlon, latlon):
    """Flat equirectangular quanh anchor -> (x_km, y_km). Du chinh xac cho
    hop 10km. Dung cong thuc giong loader.haversine_km ve ban chat (Trai Dat
    ban kinh 6371km), chi khac la tra toa do phang (x,y) chu khong phai 1 so."""
    lat0, lon0 = anchor_latlon
    lat, lon = latlon
    dy = (lat - lat0) * 111.32
    dx = (lon - lon0) * 111.32 * math.cos(math.radians(lat0))
    return dx, dy


def _euclid_km(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _dist_point_to_segment(pt, a, b):
    """Khoang cach tu diem pt den doan thang a-b (km, toa do phang)."""
    ax, ay = a
    bx, by = b
    px, py = pt
    dx, dy = bx - ax, by - ay
    seg_len2 = dx * dx + dy * dy
    if seg_len2 < 1e-12:
        return _euclid_km(pt, a)
    t = ((px - ax) * dx + (py - ay) * dy) / seg_len2
    t = max(0.0, min(1.0, t))
    proj = (ax + t * dx, ay + t * dy)
    return _euclid_km(pt, proj)


def _sample_local_pool(rng, session, n_needed):
    """Bot anchor ngau nhien, lay cac diem trong hop AREA_KM x AREA_KM quanh
    no (chieu tu pool Atlanta that), chieu ve (x,y) km. Neu khong du diem
    (hiem, vung thua), mo rong dan bien do cho toi khi du hoac cham tran."""
    pool = _atlanta_pool(session)
    anchor = rng.choice(pool)
    half = AREA_KM / 2.0
    for _attempt in range(6):
        local = []
        for latlon in pool:
            x, y = _project_km(anchor, latlon)
            if abs(x) <= half and abs(y) <= half:
                local.append((x, y))
        if len(local) >= n_needed:
            return local
        half *= 1.6      # mo rong hop neu vung qua thua diem that
    return local          # tra ve nhung gi co, sinh se raise neu van thieu


def build_instance(rng, session, n_orders, driver_cls, tw_width, tau, B):
    """Sinh 1 instance dung Sec5 (tru nguon toa do). Tra (driver, orders,
    travel_time_fn, meta)."""
    n_pts_needed = 2 * n_orders + 2   # pickup+delivery/don + start (+home)
    pool = _sample_local_pool(rng, session, n_pts_needed)
    if len(pool) < n_pts_needed:
        raise SystemExit("khong du diem that trong hop %gkm cho n_orders=%d "
                         "(co %d, can %d) - thu session khac hoac giam n"
                         % (AREA_KM, n_orders, len(pool), n_pts_needed))

    node_xy = {}
    node_ctr = [0]
    used_pts = set()

    def new_node_at(xy):
        nid = "n%d" % node_ctr[0]
        node_ctr[0] += 1
        node_xy[nid] = xy
        used_pts.add(xy)
        return nid

    def _pop_random(candidates):
        # loai diem da dung, chon 1 diem con lai
        avail = [pt for pt in candidates if pt not in used_pts]
        return rng.choice(avail) if avail else None

    start_xy = _pop_random(pool)
    start_node = new_node_at(start_xy)
    t0 = 0.0

    def travel_time(a, b):
        if a == b:
            return 0.0
        return _euclid_km(node_xy[a], node_xy[b]) / SPEED_KMH * 60.0

    driver = {"cls": driver_cls, "start_node": start_node, "t0": t0,
              "capacity": float(B)}
    meta = {"session": session, "n_orders": n_orders, "B": B,
            "tw_width": tw_width, "driver_cls": driver_cls}

    corridor_pts = None   # danh sach diem trong buffer quanh start->home, OD only
    if driver_cls == "OD":
        # home phai duoc sinh TRUOC cac don (Test3.md Viec1): ready_time can
        # neo theo tau cua driver, chu khong phai U[0,120] tuyet doi.
        home_xy = _pop_random(pool)
        home_node = new_node_at(home_xy)
        direct_t = travel_time(start_node, home_node)
        driver["home_node"] = home_node
        driver["direct_time"] = direct_t
        driver["tau"] = tau
        meta["tau"] = tau

        # [PATCH Test3.md Viec1, phan 2] uu tien P/D trong buffer quanh
        # corridor start->home - xem ghi chu CORRIDOR_BUFFER_KM/CORRIDOR_SHARE
        # o dau file.
        corridor_pts = [pt for pt in pool
                        if _dist_point_to_segment(pt, start_xy, home_xy) <= CORRIDOR_BUFFER_KM]
        meta["corridor_share_target"] = CORRIDOR_SHARE
        meta["corridor_buffer_km"] = CORRIDOR_BUFFER_KM
        meta["corridor_pool_size"] = len(corridor_pts)
    else:
        driver["availability_min"] = GW_AVAIL_MIN   # ghi nhan, KHONG ep thanh
        # rang buoc feasibility rieng - Sec1.2 khong liet ke no

    def next_od_xy():
        """OD: CORRIDOR_SHARE tu vung dem quanh start->home, con lai tu pool
        toan vung. Neu vung dem qua thua diem chua dung, roi ve toan pool."""
        if corridor_pts and rng.random() < CORRIDOR_SHARE:
            pt = _pop_random(corridor_pts)
            if pt is not None:
                return pt
        return _pop_random(pool)

    orders = {}
    for i in range(n_orders):
        oid = "o%d" % i
        if driver_cls == "OD":
            p_xy = next_od_xy()
            d_xy = next_od_xy()
        else:
            p_xy = _pop_random(pool)
            d_xy = _pop_random(pool)
        if p_xy is None or d_xy is None:
            raise SystemExit("khong du diem that (da dung het pool) cho n_orders=%d" % n_orders)
        p_node = new_node_at(p_xy)
        d_node = new_node_at(d_xy)
        if driver_cls == "OD":
            # [PATCH Test3.md Viec1] neo ready_time theo tau, khong doc lap
            # tuyet doi nhu ban goc (bug: ready_p~U[0,120] doc lap voi
            # t0/tau -> pickup thuong san sang SAU khi deadline_home da troi
            # qua -> OD chet gan het ngay k=1). Cong thuc deadline giu nguyen.
            ready_p = t0 + rng.uniform(0, tau)
        else:
            ready_p = rng.uniform(0, 120)
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

    # [LOCK] assertion bat dang thuc tam giac (Sec1.1.2) tren MOI bo ba node
    # cua chinh instance nay (du, khong can toan bo pool).
    ids = list(node_xy.keys())
    for a in ids:
        for b in ids:
            if a == b:
                continue
            for c in ids:
                if c in (a, b):
                    continue
                if travel_time(a, c) > travel_time(a, b) + travel_time(b, c) + 1e-9:
                    raise AssertionError(
                        "triangle inequality violated: %s->%s->%s" % (a, b, c))

    return driver, orders, travel_time, meta
