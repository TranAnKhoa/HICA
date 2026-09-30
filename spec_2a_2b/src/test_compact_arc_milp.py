"""Compact Resource-Constrained MILP (arc-based) - de xuat 2026-09-16.

Y tuong: bo han Algorithm A (enumerate route pool). Thay bang bien arc
y[i,j,k] in {0,1} = driver i di THANG tu node j sang k. Route la AN, chi hien
ra tu tap arc duoc chon. Day la lan thu KHAC LOAI hoan toan so voi 4 huong
pruning da REJECTED (Report_ActivationRate.md) - khong loc pool, ne han viec
liet ke. Cau hoi doc lap: "kien truc enumerate-roi-chon co phai nguyen nhan
cham, hay ban than bai toan cham du giai cach nao?"

QUYET DINH THIET KE (khac vai diem so voi mo ta goc, sau khi doi chieu voi
t2_core.py/t4_profile.py/t6_dp.py - nguon su that hien tai):

1. Detour resource cua OD KHONG can track rieng qua big-M - t2_core.py da
   cai tau THANG vao deadline tai node home (deadline_home = t0 + direct_time
   + tau). Chi can propagate thoi gian t[i,k] binh thuong qua moi node KE CA
   home, deadline o home tu dong enforce tau. Giam 1 bo bien/rang buoc so
   voi mo ta goc.

2. "u[i,j]" (dem so dung) va "B cap" la CUNG MOT resource, khong phai 2 cai
   rieng - moi order co demand=1.0 CO DINH (instance_gen.py dong 232), va
   capacity=B (dong 166/181). Load tich luy = so order dang mang = tu dong
   <= B. Chi can 1 bien load[i,j], khong can u[i,j] rieng.

3. K,W cua OD la DETOUR (tong dist/time TOAN route TRU DI direct_dist/
   direct_time CUA CHINH driver do, tru DUNG 1 LAN o cuoi - t4_profile.py
   _K_W_from_dist_time, t6_dp.py finalize_KW dung max(0, ...)). KHONG duoc
   tru direct_dist phan bo tren tung arc (se sai objective). Model dung 2
   bien tich luy THO (dist_raw[i], time_raw[i] - tong theo km/phut, CHUA tru
   direct) roi tinh K_final/W_final qua 1 cap rang buoc "K_final >= K_raw -
   kappa*direct_dist" + "K_final >= 0" (tuong duong max(0,...) trong bai
   toan MINIMIZE - chinh la ly do "max" hoat dong dung trong objective toi
   thieu hoa, khong can bien nhi phan indicator).

4. Precedence pickup-truoc-delivery: dung MTZ-style tren bien t[i,j] (thoi
   gian toi j) - vi thoi gian LUON tang doc route (moi node co service_time
   >=0), t[i,pickup(o)] < t[i,delivery(o)] tu dong dam bao neu CA HAI node
   deu duoc tham (deu la 1 phan cua route) - KHONG can rang buoc precedence
   rieng biet, chi can dam bao 2 node CUNG duoc chon (cover) va lien thong
   qua flow.

Model xay dung TREN MOI driver rieng biet (drivers khong chia se node/arc -
moi driver co node "start_i" rieng, cac node pickup/delivery CHUNG cho moi
driver nhung "duoc tham boi driver i" la bien rieng cua i) + 1 lop covering
constraint chung (moi order duoc phu boi DUNG 1 driver HOAC FD).

Dung Big-M cho time propagation (chuan MTZ/arc-based VRP formulation) - M
chon la deadline lon nhat cua toan instance (an toan, khong can tinh chat che
hon vi day la test-so-sanh Z*, khong phai production).
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
import t4_profile as P  # noqa: E402 - lay KAPPA/SPEED_KMH tu nguon goc

KAPPA = P.KAPPA
EPS = 1e-6


def _sanitize(s):
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in s)


def build_nodes_for_driver(driver, orders):
    """Tra list node dict {id, e, l, s, demand, kind} CHO RIENG driver nay
    (start rieng, home rieng neu OD - GIONG t2_core.build_walk_nodes nhung
    tra ve dang list phang de tien build MILP)."""
    nodes = []
    nodes.append(dict(id=driver["start_node"], e=driver["t0"], l=float("inf"),
                      s=0.0, demand=0.0, kind="start", order_id=None))
    for oid, o in orders.items():
        nodes.append(dict(id=o["pickup_node"], e=o["ready_time_p"], l=o["deadline_p"],
                          s=o["service_time"], demand=o["demand"], kind="pickup", order_id=oid))
        nodes.append(dict(id=o["delivery_node"], e=o["ready_time_d"], l=o["deadline_d"],
                          s=o["service_time"], demand=-o["demand"], kind="delivery", order_id=oid))
    if driver["cls"] == "OD":
        deadline_home = driver["t0"] + driver["direct_time"] + driver["tau"]
        nodes.append(dict(id=driver["home_node"], e=0.0, l=deadline_home, s=0.0,
                          demand=0.0, kind="home", order_id=None))
    return nodes


def build_compact_model(drivers, orders, fd_cost, travel_time, theta_by_driver,
                        excluded_driver=None):
    """Xay MILP arc-based. Tra (c, meta) voi meta chua thong tin de doc lai
    solution (ten bien y/t/load/K_final/W_final theo driver, z theo order)."""
    import cplex  # noqa: E402

    c = cplex.Cplex()
    c.set_results_stream(None)
    c.set_log_stream(None)
    c.set_warning_stream(None)
    c.set_error_stream(None)
    c.parameters.threads.set(1)
    c.parameters.mip.tolerances.mipgap.set(0.0)
    c.parameters.mip.tolerances.absmipgap.set(0.0)
    c.objective.set_sense(c.objective.sense.minimize)

    order_ids = sorted(orders.keys())
    all_l = [o["deadline_p"] for o in orders.values()] + [o["deadline_d"] for o in orders.values()]
    driver_list = drivers if isinstance(drivers, list) else list(drivers.values())
    for d in driver_list:
        if d["cls"] == "OD":
            all_l.append(d["t0"] + d["direct_time"] + d["tau"])
    BIG_M = max(all_l) + 1000.0   # an toan, du lon cho time propagation (5)
    # [BUG DA SUA 2026-09-16] BIG_M_W rieng cho wrawL/wrawU: PHAI >= can bac
    # THAT SU cua bien W_raw (KHONG chi >= deadline lon nhat nhu BIG_M) - neu
    # W_raw co ub qua lon (vd 1e6 mac dinh) trong khi BIG_M nho hon nhieu,
    # rang buoc "M*(1-end_of)" khong con VO HIEU HOA dung khi end_of=0, gay
    # infeasible SAI cho MOI node khong phai diem ket thuc (phat hien qua
    # Buoc dau tien: Z*_compact khong khop Z*_pool, truy nguyen bang cach fix
    # cung dung route da biet toi uu roi thay van infeasible - loi kinh dien
    # "BIG_M phai lon hon can bac CUA CHINH BIEN lien quan, khong chi lon hon
    # 1 dai luong khac trong bai toan"). W_raw toi da thuc te <= BIG_M (deadline
    # lon nhat) + 1 chut margin - GIOI HAN LAI ub cua W_raw/K_raw ve BIG_M
    # thay vi 1e6 tuy y, dam bao nhat quan voi BIG_M dung trong (5)/(7b).
    W_RAW_UB = BIG_M   # an toan: khong route nao co active_time vuot BIG_M

    var_names, var_obj, var_lb, var_ub, var_types = [], [], [], [], []

    def add_var(name, obj=0.0, lb=0.0, ub=1.0, vtype="C"):
        var_names.append(name); var_obj.append(obj)
        var_lb.append(lb); var_ub.append(ub); var_types.append(vtype)

    per_driver = {}   # did -> dict(nodes, y_of, t_of, load_of, K_raw_name, W_raw_name, K_final_name, W_final_name)

    for d in driver_list:
        did = d["id"]
        if did == excluded_driver:
            continue
        theta_i = theta_by_driver[did]
        nodes = build_nodes_for_driver(d, orders)
        node_ids = [nd["id"] for nd in nodes]
        by_id = {nd["id"]: nd for nd in nodes}

        # [BUG DA SUA 2026-09-16] BAN DAU tao arc cho MOI cap (a,b) voi a!=b,
        # KE CA arc di RA tu home hoac arc di VAO start - khong co gi cam
        # dieu nay, dan toi node graph co the "phinh to" thanh nhieu nhanh
        # tu home (home khong con la diem KET THUC tuyet doi) - phat hien qua
        # kiem toan bo model (4 driver): 1 driver phuc vu CA 6 order (vuot
        # capacity=2) voi 4 arc ra CUNG LUC tu node home. Sua: LOAI TRU arc
        # co nguon=home (home la node KET THUC, khong di tiep) va arc co
        # dich=start (khong ai quay lai start) NGAY TU luc tao bien - khong
        # chi dua vao rang buoc (an toan hon, giam so bien khong can thiet).
        start_id = d["start_node"]
        home_id_for_arcs = d["home_node"] if d["cls"] == "OD" else None
        y_of = {}
        for a in node_ids:
            if a == home_id_for_arcs:
                continue   # home khong co arc ra
            for b in node_ids:
                if a == b or b == start_id:
                    continue   # khong ai quay lai start
                vname = "y_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b))
                y_of[(a, b)] = vname
                add_var(vname, obj=0.0, lb=0.0, ub=1.0, vtype="B")

        t_of = {}
        for nid in node_ids:
            vname = "t_%s_%s" % (_sanitize(did), _sanitize(nid))
            t_of[nid] = vname
            nd = by_id[nid]
            add_var(vname, obj=0.0, lb=nd["e"], ub=min(nd["l"], BIG_M), vtype="C")

        load_of = {}
        for nid in node_ids:
            vname = "load_%s_%s" % (_sanitize(did), _sanitize(nid))
            load_of[nid] = vname
            add_var(vname, obj=0.0, lb=0.0, ub=d["capacity"], vtype="C")

        # served_of: [BUG DA SUA 2026-09-16] "capacity"=B trong t2_core.py/
        # dp_labeling.py KHONG PHAI tai tuc thoi (moi luc <=B) - no la TONG
        # SO ORDER DA PICKUP TRONG TOAN ROUTE (dang mang HOAC da giao xong),
        # kiem tra qua len(IV)+len(Cd)>=B truoc khi cho pickup them (t6_dp.py
        # dong 121). "load_of" (bien da co) chi track TAI TUC THOI (tang khi
        # pickup, GIAM khi delivery) - la 1 RESOURCE KHAC, khong the dung
        # thay cho B-cap. Phat hien qua kiem thuc te: model tim duoc route 4
        # order cho driver B_gw=3 (tai tuc thoi luon <=1 vi giao xong roi moi
        # lay don tiep, nhung TONG so don phuc vu = 4 > 3). Them bien rieng
        # served_of (TANG khi pickup, KHONG GIAM khi delivery), rang buoc
        # served_of <= B (capacity).
        served_of = {}
        for nid in node_ids:
            vname = "served_%s_%s" % (_sanitize(did), _sanitize(nid))
            served_of[nid] = vname
            add_var(vname, obj=0.0, lb=0.0, ub=d["capacity"], vtype="C")

        visited_of = {}
        for nid in node_ids:
            nd = by_id[nid]
            if nd["kind"] in ("pickup", "delivery"):
                vname = "vis_%s_%s" % (_sanitize(did), _sanitize(nid))
                visited_of[nid] = vname
                add_var(vname, obj=0.0, lb=0.0, ub=1.0, vtype="B")

        k_raw_name = "Kraw_%s" % _sanitize(did)
        w_raw_name = "Wraw_%s" % _sanitize(did)
        add_var(k_raw_name, obj=0.0, lb=0.0, ub=W_RAW_UB, vtype="C")
        add_var(w_raw_name, obj=0.0, lb=0.0, ub=W_RAW_UB, vtype="C")

        k_final_name = "Kfin_%s" % _sanitize(did)
        w_final_name = "Wfin_%s" % _sanitize(did)
        add_var(k_final_name, obj=1.0, lb=0.0, ub=1e6, vtype="C")
        add_var(w_final_name, obj=theta_i, lb=0.0, ub=1e6, vtype="C")

        # end_of[node]: CHI can cho GW (khong home co dinh) - khai bao O DAY
        # (TRUOC c.variables.add()), khong phai trong vong lap rang buoc phia
        # duoi, de tranh loi "Invalid name" (bien dung trong constraint phai
        # da duoc them vao model truoc khi linear_constraints.add() chay).
        end_of = {}
        if d["cls"] != "OD":
            for nid in node_ids:
                nd = by_id[nid]
                if nd["kind"] not in ("pickup", "delivery"):
                    continue
                vname_end = "end_%s_%s" % (_sanitize(did), _sanitize(nid))
                end_of[nid] = vname_end
                add_var(vname_end, obj=0.0, lb=0.0, ub=1.0, vtype="B")

        per_driver[did] = dict(driver=d, nodes=nodes, node_ids=node_ids, by_id=by_id,
                               y_of=y_of, t_of=t_of, load_of=load_of, served_of=served_of,
                               visited_of=visited_of,
                               k_raw=k_raw_name, w_raw=w_raw_name,
                               k_final=k_final_name, w_final=w_final_name, end_of=end_of)

    z_of = {}
    for o in order_ids:
        vname = "z_" + _sanitize(o)
        z_of[o] = vname
        add_var(vname, obj=float(fd_cost[o]), lb=0.0, ub=1.0, vtype="B")

    c.variables.add(obj=var_obj, lb=var_lb, ub=var_ub, types=var_types, names=var_names)

    rows, senses, rhs, rnames = [], [], [], []

    # --- (1) Covering: moi order duoc phu DUNG 1 lan (pickup cua no duoc tham
    #     boi DUNG 1 driver, HOAC z_o=1) ---
    for o in order_ids:
        terms, coefs = [], []
        p_node = orders[o]["pickup_node"]
        for did, pd in per_driver.items():
            if p_node in pd["visited_of"]:
                terms.append(pd["visited_of"][p_node]); coefs.append(1.0)
        terms.append(z_of[o]); coefs.append(1.0)
        rows.append([terms, coefs]); senses.append("E"); rhs.append(1.0)
        rnames.append("cov_" + _sanitize(o))

    for did, pd in per_driver.items():
        nodes, node_ids, by_id = pd["nodes"], pd["node_ids"], pd["by_id"]
        y_of, t_of, load_of, visited_of = pd["y_of"], pd["t_of"], pd["load_of"], pd["visited_of"]
        served_of = pd["served_of"]
        d = pd["driver"]
        has_home = d["cls"] == "OD"
        home_id = d["home_node"] if has_home else None
        start_id = d["start_node"]

        # --- (2) pickup/delivery cua CUNG 1 order, CUNG driver: visited bang
        #     nhau (ca 2 deu duoc tham, hoac ca 2 deu khong). ---
        for oid in orders:
            p_node = orders[oid]["pickup_node"]
            d_node = orders[oid]["delivery_node"]
            rows.append([[visited_of[p_node], visited_of[d_node]], [1.0, -1.0]])
            senses.append("E"); rhs.append(0.0)
            rnames.append("pd_link_%s_%s" % (_sanitize(did), _sanitize(oid)))

            # --- (2b) [BUG DA SUA 2026-09-16] Precedence pickup-TRUOC-delivery
            #     CUA CUNG 1 order: docstring goc cua file nay (muc 4 dau file)
            #     KHANG DINH SAI rang "thoi gian tang doc route tu dong dam
            #     bao precedence neu ca 2 node deu duoc tham" - SAI, vi flow
            #     conservation CHI dam bao local balance tai tung node, KHONG
            #     dam bao pickup va delivery CUNG order nam theo DUNG thu tu
            #     tren chuoi arc (co the co route hop le ve mat flow nhung
            #     "delivery truoc, pickup sau" cua CUNG 1 order - phat hien
            #     qua kiem thuc te: model tim duoc route re hon Z*_pool that,
            #     giai ma ra thu tu n8(pickup o1)->n17(delivery o5)->n16
            #     (pickup o5) - giao nhau sai thu tu o5). Them RANG BUOC
            #     TUONG MINH: t[delivery] >= t[pickup] + travel(pickup,
            #     delivery) - AN TOAN (khong can big-M) vi (2) da dam bao ca
            #     2 node CUNG active hoac CUNG khong (neu khong active, bound
            #     cua t khong lien quan gi toi nhau qua rang buoc nay theo
            #     nghia dung - nhung vi day la rang buoc CUNG tinh (khong co
            #     bien y), no AP DUNG VO DIEU KIEN, kha nang duy nhat de no
            #     vo hai khi khong active la 2 bien t VAN nam trong khoang
            #     [e,l] rieng cua tung node va PHAI thoa man BAT KE active
            #     hay khong - dieu nay AN TOAN vi neu ca 2 node khong active,
            #     gia tri t cua chung khong anh huong obj/route that, CPLEX
            #     tu do chon t[delivery]=l[delivery] (max) de luon thoa). ---
            trav_pd = travel_time(p_node, d_node)
            rows.append([[t_of[d_node], t_of[p_node]], [1.0, -1.0]])
            senses.append("G"); rhs.append(trav_pd)
            rnames.append("prec_%s_%s" % (_sanitize(did), _sanitize(oid)))

        # --- (3) Flow conservation tai moi node pickup/delivery: vao=ra=visited ---
        for nid in node_ids:
            nd = by_id[nid]
            if nd["kind"] not in ("pickup", "delivery"):
                continue
            in_arcs = [y_of[(a, nid)] for a in node_ids if (a, nid) in y_of]
            out_arcs = [y_of[(nid, b)] for b in node_ids if (nid, b) in y_of]
            # in-flow: node duoc tham PHAI co DUNG 1 arc vao (Sum in = visited)
            rows.append([in_arcs + [visited_of[nid]], [1.0] * len(in_arcs) + [-1.0]])
            senses.append("E"); rhs.append(0.0)
            rnames.append("flow_in_%s_%s" % (_sanitize(did), _sanitize(nid)))
            # out-flow: node duoc tham co THE co 0 HOAC 1 arc ra (KHONG bat
            # buoc =1 - BUG DA SUA 2026-09-16: dung "=" o day buoc MOI node
            # duoc tham phai co dung 1 arc ra, mau thuan voi co chế end_of
            # (Buoc 7b) cho GW - GW khong co home co dinh nen node CUOI CUNG
            # cua route hop le co 0 arc ra trong khi van duoc tham (visited=1).
            # Phat hien qua bisect nhi phan tren toan bo nhom constraint, xac
            # nhan xoa nhom "flow_out" (ten cu) lam model tro lai feasible.
            rows.append([out_arcs + [visited_of[nid]], [1.0] * len(out_arcs) + [-1.0]])
            senses.append("L"); rhs.append(0.0)
            rnames.append("flow_out_%s_%s" % (_sanitize(did), _sanitize(nid)))

        # --- (4) start/home: OD LUON di start->home (truc tiep hoac qua order),
        #     dung DUNG 1 arc ra tu start, DUNG 1 arc vao home (bao gom ca
        #     arc start->home truc tiep cho truong hop khong phuc vu order
        #     nao - can them arc nay vao do thi neu chua co). GW: start co
        #     0 hoac 1 arc ra (khong bat buoc dung home, khong co home). ---
        start_out = [y_of[(start_id, b)] for b in node_ids if (start_id, b) in y_of]
        if has_home:
            home_in = [y_of[(a, home_id)] for a in node_ids if (a, home_id) in y_of]
            rows.append([start_out, [1.0] * len(start_out)])
            senses.append("E"); rhs.append(1.0)
            rnames.append("start_out_%s" % _sanitize(did))
            rows.append([home_in, [1.0] * len(home_in)])
            senses.append("E"); rhs.append(1.0)
            rnames.append("home_in_%s" % _sanitize(did))
            # home KHONG co arc ra, start KHONG co arc vao (khong can rang buoc them,
            # cau truc bien y da loai a==b va start/home la node dac biet)
        else:
            # GW: khong bat buoc dung home. cho phep start co 0 hoac 1 arc ra
            # (0 arc ra = route rong, khong phuc vu order nao) - dung "<=1"
            rows.append([start_out, [1.0] * len(start_out)])
            senses.append("L"); rhs.append(1.0)
            rnames.append("start_out_%s" % _sanitize(did))

        # --- (5) Time propagation (big-M, MTZ-style): y[a,b]=1 => t[b] >= t[a]+travel(a,b)+s(a) ---
        for (a, b), vname in y_of.items():
            travel_ab = travel_time(a, b)
            s_a = by_id[a]["s"]
            rows.append([[t_of[b], t_of[a], vname], [1.0, -1.0, -BIG_M]])
            senses.append("G"); rhs.append(travel_ab + s_a - BIG_M)
            rnames.append("time_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b)))

        # --- (6) Load propagation (big-M): y[a,b]=1 => load[b] = load[a] + demand(b) ---
        for (a, b), vname in y_of.items():
            demand_b = by_id[b]["demand"]
            # load[b] <= load[a] + demand_b + M*(1-y)   VA   load[b] >= load[a] + demand_b - M*(1-y)
            rows.append([[load_of[b], load_of[a], vname], [1.0, -1.0, BIG_M]])
            senses.append("L"); rhs.append(demand_b + BIG_M)
            rnames.append("loadU_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b)))
            rows.append([[load_of[b], load_of[a], vname], [1.0, -1.0, -BIG_M]])
            senses.append("G"); rhs.append(demand_b - BIG_M)
            rnames.append("loadL_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b)))
        # load tai start = 0
        rows.append([[load_of[start_id]], [1.0]])
        senses.append("E"); rhs.append(0.0)
        rnames.append("load_start_%s" % _sanitize(did))

        # --- (6b) Served-count propagation (B-cap that su, xem ghi chu o
        #     khai bao served_of o tren): y[a,b]=1 => served[b] = served[a] +
        #     1[b la pickup] (KHONG giam khi b la delivery - khac load). ---
        for (a, b), vname in y_of.items():
            inc_b = 1.0 if by_id[b]["kind"] == "pickup" else 0.0
            rows.append([[served_of[b], served_of[a], vname], [1.0, -1.0, BIG_M]])
            senses.append("L"); rhs.append(inc_b + BIG_M)
            rnames.append("servedU_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b)))
            rows.append([[served_of[b], served_of[a], vname], [1.0, -1.0, -BIG_M]])
            senses.append("G"); rhs.append(inc_b - BIG_M)
            rnames.append("servedL_%s_%s_%s" % (_sanitize(did), _sanitize(a), _sanitize(b)))
        rows.append([[served_of[start_id]], [1.0]])
        senses.append("E"); rhs.append(0.0)
        rnames.append("served_start_%s" % _sanitize(did))

        # --- (7) K_raw tich luy: bang tong kappa*dist(a,b) tren cac arc duoc
        #     dung - K KHONG chua waiting time nen tong theo arc la dung. ---
        k_terms, k_coefs = [], []
        for (a, b), vname in y_of.items():
            dist_ab_km = travel_time(a, b) * P.G.SPEED_KMH / 60.0 if hasattr(P, "G") else None
            k_terms.append(vname); k_coefs.append(KAPPA * dist_ab_km)
        rows.append([[pd["k_raw"]] + k_terms, [1.0] + [-c_ for c_ in k_coefs]])
        senses.append("E"); rhs.append(0.0)
        rnames.append("kraw_%s" % _sanitize(did))

        # --- (7b) W_raw KHONG the tinh bang tong travel_time tren arc (BUG
        #     DA TIM RA 2026-09-16: bo sot WAITING TIME - neu xe den 1 node
        #     som hon ready_time e, phai CHO toi e, phan cho nay la mot phan
        #     cua active_time nhung khong nam tren BAT KY arc nao, chi xuat
        #     hien qua chenh lech t[node] (da duoc rang buoc dung boi lb=e
        #     o (5)) so voi thoi diem den thuc te. Phat hien qua so sanh
        #     Z*_compact (74.376, roi 81.220 sau khi sua thieu service_time)
        #     != Z*_pool (81.636) - truy nguyen bang brute_force.py walk that
        #     (od1/{o5}: cho 10.19 phut tai pickup vi den som hon ready_time).
        #
        #     SUA DUNG: dung TRUC TIEP bien thoi gian t[node] (da bao gom
        #     waiting qua rang buoc lb=e va (5)) thay vi tong lai tu travel
        #     time tinh. OD: node cuoi LUON la home (deadline_home da enforce
        #     tau) => W_raw = t[home] - t0 (home s=0, khong can cong them).
        #     GW: KHONG co node ket thuc co dinh - node cuoi la 1 trong cac
        #     node duoc tham CO 0 arc ra (trong so cac node duoc tham). Dung
        #     bien nhi phan end_of[node] + rang buoc de xac dinh dung 1 node
        #     ket thuc, roi W_raw = Sum (t[node]+s[node])*end_of[node] - t0.
        # ---
        if has_home:
            rows.append([[pd["w_raw"], t_of[home_id]], [1.0, -1.0]])
            senses.append("E"); rhs.append(-d["t0"])
            rnames.append("wraw_%s" % _sanitize(did))
        else:
            end_of = pd["end_of"]   # da khai bao TRUOC c.variables.add() o tren
            for nid in end_of:
                vname_end = end_of[nid]
                # end_of[node] <= visited[node] (chi node duoc tham moi co
                # the la node ket thuc)
                rows.append([[vname_end, visited_of[nid]], [1.0, -1.0]])
                senses.append("L"); rhs.append(0.0)
                rnames.append("endle_%s_%s" % (_sanitize(did), _sanitize(nid)))
                # end_of[node] = 1 <=> node nay duoc tham VA khong co arc ra
                # nao active. Dung: end_of >= visited - Sum(out_arcs)
                out_arcs = [y_of[(nid, b2)] for b2 in node_ids if (nid, b2) in y_of]
                rows.append([[vname_end, visited_of[nid]] + out_arcs,
                            [1.0, -1.0] + [1.0] * len(out_arcs)])
                senses.append("G"); rhs.append(0.0)
                rnames.append("endge_%s_%s" % (_sanitize(did), _sanitize(nid)))
            # dung DUNG 1 node ket thuc NEU co it nhat 1 node duoc tham
            # (start_out=1) - tong end_of = start_out (0 hoac 1)
            rows.append([list(end_of.values()) + start_out,
                        [1.0] * len(end_of) + [-1.0] * len(start_out)])
            senses.append("E"); rhs.append(0.0)
            rnames.append("end_count_%s" % _sanitize(did))

            # W_raw = Sum_{node} end_of[node]*(t[node]+s[node]) - t0
            #   = Sum end_of[node]*t[node] + Sum end_of[node]*s[node] - t0
            # Sum end_of[node]*t[node] la SONG TUYEN TINH (tich 2 bien) - can
            # linearize. Vi CHI DUNG 1 end_of=1, dung Big-M: W_raw >= t[node]
            # + s[node] - t0 - M*(1-end_of[node]) cho MOI node, va W_raw <=
            # t[node]+s[node]-t0 + M*(1-end_of[node]) (2 chieu, vi day la
            # dang thuc khi end_of=1).
            # BIG_M2 (KHAC BIG_M cua (5)): phai >= bien do lon LON NHAT co
            # the co trong |W_raw - t[nid]| khi end_of=0, tuc >= W_RAW_UB +
            # (ub cua t[nid]) - dung BIG_M (da >= moi deadline, tuc >= moi
            # ub cua t) CONG THEM W_RAW_UB de chac chan du lon (xem ghi chu
            # BIG_M o dau ham - bug da sua 2026-09-16).
            BIG_M2 = BIG_M + W_RAW_UB
            for nid in end_of:
                s_n = by_id[nid]["s"]
                rows.append([[pd["w_raw"], t_of[nid], end_of[nid]], [1.0, -1.0, -BIG_M2]])
                senses.append("G"); rhs.append(s_n - d["t0"] - BIG_M2)
                rnames.append("wrawL_%s_%s" % (_sanitize(did), _sanitize(nid)))
                rows.append([[pd["w_raw"], t_of[nid], end_of[nid]], [1.0, -1.0, BIG_M2]])
                senses.append("L"); rhs.append(s_n - d["t0"] + BIG_M2)
                rnames.append("wrawU_%s_%s" % (_sanitize(did), _sanitize(nid)))
            # route rong (khong dung node nao): khong co end_of nao active,
            # cac rang buoc wrawL/wrawU o tren khong ep gi (M du lon) - w_raw
            # tu do trong [0, 1e6], nhung obj toi thieu hoa se tu chon 0 (he
            # so obj cua Wfin la theta_i>0, Wfin lien quan Wraw qua (8) chieu
            # cung dau) - KHONG can rang buoc rieng, da an toan qua minimize.

        # --- (8) K_final/W_final: GW = raw. OD = max(0, raw - direct).
        #     Don vi: K_raw = kappa*km (dong nhat K_final). W_raw = PHUT
        #     (travel_time tra ve phut), W_final = GIO (khop finalize_KW:
        #     W_final=(lab.W-direct_time)/60, direct_time_min cung PHUT) =>
        #     60*W_final >= W_raw - direct_time_min. ---
        if has_home:
            direct_dist_km = d["direct_time"] * (P.G.SPEED_KMH if hasattr(P, "G") else 20.0) / 60.0
            direct_time_min = d["direct_time"]
            # K_final >= K_raw - kappa*direct_dist   (K_final>=0 da co qua lb=0)
            rows.append([[pd["k_final"], pd["k_raw"]], [1.0, -1.0]])
            senses.append("G"); rhs.append(-KAPPA * direct_dist_km)
            rnames.append("kfin_%s" % _sanitize(did))
            rows.append([[pd["w_final"], pd["w_raw"]], [60.0, -1.0]])
            senses.append("G"); rhs.append(-direct_time_min)
            rnames.append("wfin_%s" % _sanitize(did))
        else:
            rows.append([[pd["k_final"], pd["k_raw"]], [1.0, -1.0]])
            senses.append("E"); rhs.append(0.0)
            rnames.append("kfin_%s" % _sanitize(did))
            rows.append([[pd["w_final"], pd["w_raw"]], [60.0, -1.0]])
            senses.append("E"); rhs.append(0.0)
            rnames.append("wfin_%s" % _sanitize(did))

    c.linear_constraints.add(lin_expr=rows, senses=senses, rhs=rhs, names=rnames)

    return c, dict(per_driver=per_driver, z_of=z_of, order_ids=order_ids)


def solve_compact(drivers, orders, fd_cost, travel_time, theta_by_driver, excluded_driver=None):
    c, meta = build_compact_model(drivers, orders, fd_cost, travel_time, theta_by_driver,
                                  excluded_driver=excluded_driver)
    c.solve()
    st = c.solution.get_status_string()
    obj = None
    if c.solution.is_primal_feasible():
        obj = c.solution.get_objective_value()
    c.end()
    return obj, st


if __name__ == "__main__":
    import random
    import rq1_cost_gen as RC

    drivers, orders, tt, meta = IG.generate_instance(
        n=6, B_gw=3, B_od=2, tw_width=120, n_drivers=4, seed=123,
        tau=30.0, spatial_mode="dispersed")

    rng = random.Random(7)
    theta_by_driver = RC.assign_theta(rng, drivers)
    q_o_by_order = RC.assign_q_o(orders, tt)

    print("Solving compact arc-based MILP...")
    obj, st = solve_compact(drivers, orders, q_o_by_order, tt, theta_by_driver)
    print("Z*_compact =", obj, "status=", st)
    print("Z*_pool (known) = 81.63562562519047")
    if obj is not None:
        print("Khop?", abs(obj - 81.63562562519047) < 1e-3)
