"""Test2.md - loi thuat toan: feasibility, brute force, BFS level-wise.

Mo hinh (Test2.md Sec1.1): Order(id, pickup_node, delivery_node, demand),
Node(id, x, y, ready_time e, deadline l, service_time s),
Driver(id, cls in {OD,GW}, start_node, capacity, t0, home_node[OD], tau[OD]).

is_feasible() duoc viet MOT LAN DUY NHAT (Sec2 yeu cau), dung chung cho brute
force lan BFS. OD/GW dung CHUNG mot ham: detour budget cua OD duoc cai thanh
mot deadline tai node 'home' o cuoi walk (Sec1.2), nen ham feasibility chi
can duyet qua danh sach node voi (e,l,s,demand) - khong biet no la OD hay GW.
"""

import itertools

EPS = 1e-9


# ---------------------------------------------------------------- walk node
class WNode(object):
    """Mot node trong walk: id, e, l, s, demand, kind, order_id.

    demand duong = pickup (+tai), am = delivery (-tai), 0 = start/home.
    """
    __slots__ = ("id", "e", "l", "s", "demand", "kind", "order_id")

    def __init__(self, id_, e, l, s, demand, kind, order_id=None):
        self.id = id_
        self.e = e
        self.l = l
        self.s = s
        self.demand = demand
        self.kind = kind          # "start" | "pickup" | "delivery" | "home"
        self.order_id = order_id

    def __repr__(self):
        return "WNode(%s,%s)" % (self.id, self.kind)


def build_walk_nodes(driver, orders):
    """Tra ve (start_node, {order_id: (pickup_node, delivery_node)}, home_node|None)."""
    start = WNode(driver["start_node"], driver["t0"], float("inf"), 0.0, 0, "start")
    pd = {}
    for oid, o in orders.items():
        p = WNode(o["pickup_node"], o["ready_time_p"], o["deadline_p"],
                  o["service_time"], o["demand"], "pickup", oid)
        d = WNode(o["delivery_node"], o["ready_time_d"], o["deadline_d"],
                  o["service_time"], -o["demand"], "delivery", oid)
        pd[oid] = (p, d)
    home = None
    if driver["cls"] == "OD":
        deadline_home = driver["t0"] + driver["direct_time"] + driver["tau"]
        home = WNode(driver["home_node"], 0.0, deadline_home, 0.0, 0, "home")
    return start, pd, home


# ------------------------------------------------------------ feasibility
def is_feasible(travel_time, driver, walk):
    """walk = list [start_wnode, ...order wnodes theo thu tu..., home_wnode?].

    Tra (ok, slack, schedule). slack = min(l_i - B_i) tren MOI node co l_i
    huu han (bo start), theo Sec1.3.
    """
    cap = driver["capacity"]
    cur = walk[0]
    D_prev = driver["t0"]           # D_start = t0 (khoi hanh ngay, khong service)
    load = 0
    schedule = [(cur.id, driver["t0"], D_prev, load)]
    slack = float("inf")
    seen_pickup = set()
    for nd in walk[1:]:
        A_i = D_prev + travel_time(cur.id, nd.id)
        B_i = A_i if A_i > nd.e else nd.e
        if B_i > nd.l + EPS:
            return False, None, None
        if nd.kind == "pickup":
            load += nd.demand
            if load > cap + EPS:
                return False, None, None
            seen_pickup.add(nd.order_id)
        elif nd.kind == "delivery":
            if nd.order_id not in seen_pickup:
                return False, None, None       # precedence vi pham
            load += nd.demand                  # demand da am
            if load < -EPS:
                return False, None, None
        D_i = B_i + nd.s
        schedule.append((nd.id, B_i, D_i, load))
        if nd.l < float("inf"):
            gap = nd.l - B_i
            if gap < slack:
                slack = gap
        D_prev = D_i
        cur = nd
    return True, slack, schedule


def canonical(walk):
    return tuple((nd.id, nd.kind, nd.order_id) for nd in walk)


# --------------------------------------------------------- validate (Sec4.2)
def validate(travel_time, driver, walk):
    """Ham kiem tra doc lap - cai dat KHAC is_feasible(): tinh lai tu dau
    bang vong lap tho, gom loi vao list thay vi return som."""
    cap = driver["capacity"]
    t = driver["t0"]
    load = 0
    picked = set()
    errors = []
    prev_id = walk[0].id
    for idx in range(1, len(walk)):
        nd = walk[idx]
        travel = travel_time(prev_id, nd.id)
        arrival = t + travel
        begin = max(arrival, nd.e)
        if begin - nd.l > EPS:
            errors.append("TW violated at %s: begin=%.4f > l=%.4f" % (nd.id, begin, nd.l))
        if nd.kind == "pickup":
            picked.add(nd.order_id)
            load = load + nd.demand
            if load - cap > EPS:
                errors.append("capacity exceeded at %s: load=%.2f cap=%.2f" % (nd.id, load, cap))
        elif nd.kind == "delivery":
            if nd.order_id not in picked:
                errors.append("precedence violated: delivery %s before pickup" % nd.id)
            load = load + nd.demand
            if load < -EPS:
                errors.append("negative load at %s" % nd.id)
        t = begin + nd.s
        prev_id = nd.id
    return (len(errors) == 0), errors


# ---------------------------------------------------------- brute force
def brute_force(travel_time, driver, orders, B):
    """Sec2. Tra (result, perm_stats).
    result: {frozenset(S): [(canonical_seq, slack, walk_objs), ...]}
    perm_stats: {frozenset(S): n_permutations_checked}   -- (2k)!  (khong /2^k,
    vi ta duyet TAT CA hoan vi 2k phan tu roi loc precedence, dung y Sec2).
    """
    start, pd, home = build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    result = {}
    stats = {}
    for k in range(1, B + 1):
        for S in itertools.combinations(order_ids, k):
            events = []
            for oid in S:
                events.append(pd[oid][0])
                events.append(pd[oid][1])
            n_perm_checked = 0
            feas = []
            for perm in itertools.permutations(events):
                n_perm_checked += 1
                seen_p = set()
                ok_prec = True
                for nd in perm:
                    if nd.kind == "pickup":
                        seen_p.add(nd.order_id)
                    else:
                        if nd.order_id not in seen_p:
                            ok_prec = False
                            break
                if not ok_prec:
                    continue
                walk = [start] + list(perm) + ([home] if home is not None else [])
                ok, slack, sched = is_feasible(travel_time, driver, walk)
                if ok:
                    feas.append((canonical(walk), slack, walk))
            result[frozenset(S)] = feas
            stats[frozenset(S)] = n_perm_checked
    return result, stats


# --------------------------------------------------------- BFS level-wise
def _insert_positions(walk, has_home):
    """Vi tri hop le de chen 1 node moi vao walk (khong truoc start, khong
    sau home). Tra list index i sao cho walk[:i]+[new]+walk[i:] hop le."""
    upper = len(walk) - 1 if has_home else len(walk)
    return range(1, upper + 1)


def bfs_generate(travel_time, driver, orders, B, use_filter=True):
    """Sec3.1. Tra (Seq, prune_counter, insertion_attempts, slack_star_table, pruned_sets).

    Seq: {frozenset(S): [(canonical_seq, slack, walk_objs), ...]}
    slack_star_table: {frozenset(S): float}  (-inf neu S khong co seq nao kha thi)
    parent choice: j = min(S) - tuy y theo Sec3.2 (da chung minh chon nao cung
    dung), chon deterministic de tai lap duoc.
    """
    start, pd, home = build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    Seq = {}
    slack_star = {}
    prune_counter = 0
    insertion_attempts = 0
    insertion_attempts_by_S = {}
    pruned_sets = set()

    # k = 1
    for oid in order_ids:
        p, d = pd[oid]
        walk = [start, p, d] + ([home] if has_home else [])
        ok, slack, sched = is_feasible(travel_time, driver, walk)
        S = frozenset([oid])
        insertion_attempts_by_S[S] = 0     # k=1 khong chen, sinh truc tiep
        if ok:
            Seq[S] = [(canonical(walk), slack, walk)]
            slack_star[S] = slack
        else:
            Seq[S] = []
            slack_star[S] = float("-inf")

    for k in range(2, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)

            if use_filter:
                bound = min(slack_star[frozenset(S - {j})] for j in S)
                if bound < -EPS:
                    Seq[S] = []
                    slack_star[S] = float("-inf")
                    insertion_attempts_by_S[S] = 0
                    prune_counter += 1
                    pruned_sets.add(S)
                    continue

            j = min(S)                      # chon parent: bo di order nho nhat
            P = S - {j}
            parent_entries = Seq.get(frozenset(P), [])
            if not parent_entries:
                Seq[S] = []
                slack_star[S] = float("-inf")
                insertion_attempts_by_S[S] = 0
                continue

            pj, dj = pd[j]
            out = []
            seen_canon = set()
            attempts_here = 0
            for _canon, _slack, R_objs in parent_entries:
                for a in _insert_positions(R_objs, has_home):
                    R1 = R_objs[:a] + [pj] + R_objs[a:]
                    for b in _insert_positions(R1, has_home):
                        if b <= a:
                            continue
                        R2 = R1[:b] + [dj] + R1[b:]
                        insertion_attempts += 1
                        attempts_here += 1
                        ok, slack, sched = is_feasible(travel_time, driver, R2)
                        if ok:
                            c = canonical(R2)
                            if c not in seen_canon:
                                seen_canon.add(c)
                                out.append((c, slack, R2))
            Seq[S] = out
            slack_star[S] = max((s for _, s, _ in out), default=float("-inf"))
            insertion_attempts_by_S[S] = attempts_here

    return Seq, prune_counter, insertion_attempts, slack_star, pruned_sets, insertion_attempts_by_S


# ------------------------------------------------------- Pareto (Test3.md Viec 2)
def label_of(driver, walk, sched, slack):
    """Nhan Pareto (Test3.md Viec 2): (end_node, arrival_time, K, W).

    end_node, arrival_time: node CUOI CUNG duoc phuc vu THAT SU (khong tinh
    home, vi home la diem ket bat buoc chung cho moi sequence cua 1 OD - so
    sanh no khong phan biet gi giua cac sequence). arrival_time = B_i (begin
    service) tai node do.
    K = tai (load) tai cuoi walk THUC (truoc home neu co) - anh huong truc
    tiep kha nang chen them don o cac level sau (capacity).
    W = D_end - t0, "cong viec/thoi gian da dung" tinh den node cuoi walk
    thuc - anh huong truc tiep kha nang chen them don sau do (arrival cang
    tre, deadline con lai cang it). Day la GIA DINH THIET KE tu Test3.md
    khong dinh nghia K,W tuong minh - da chon theo dung 2 dai luong duy nhat
    anh huong tinh kha thi cua phan con lai cua walk (xem BFS_GENERATE
    insertion): tai (capacity) va thoi diem hien tai (deadline con lai).
    """
    has_home = walk[-1].kind == "home"
    end_idx = len(walk) - 2 if has_home else len(walk) - 1
    end_node = walk[end_idx].id
    arrival = sched[end_idx][1]     # B_i
    depart = sched[end_idx][2]      # D_i
    load = sched[end_idx][3]
    W = depart - driver["t0"]
    return (end_node, arrival, load, W)


def dominates(lab1, lab2):
    """label1 dominates label2 (Test3.md Viec 2)."""
    e1, a1, k1, w1 = lab1
    e2, a2, k2, w2 = lab2
    if e1 != e2:
        return False
    if not (a1 <= a2 + EPS and k1 <= k2 + EPS and w1 <= w2 + EPS):
        return False
    strict = (a1 < a2 - EPS) or (k1 < k2 - EPS) or (w1 < w2 - EPS)
    return strict


def filter_pareto_with_sched(entries_with_sched, driver):
    """entries_with_sched: [(canon, slack, walk, sched)]. Tra danh sach con
    khong bi dominate, giu nguyen tuple 4 phan tu."""
    labeled = [(c, s, w, sc, label_of(driver, w, sc, s)) for c, s, w, sc in entries_with_sched]
    kept = []
    for i, (c, s, w, sc, lab) in enumerate(labeled):
        dominated = False
        for j, (c2, s2, w2, sc2, lab2) in enumerate(labeled):
            if i == j:
                continue
            if dominates(lab2, lab):
                dominated = True
                break
        if not dominated:
            kept.append((c, s, w, sc, lab))
    return kept


def bfs_generate_pareto(travel_time, driver, orders, B, use_filter=True):
    """Test3.md Viec 2 - BFS_PARETO: giong bfs_generate, nhung Pareto[P] (khong
    phai Seq[P]) duoc dung lam nguon chen cho level sau.

    Tra (Seq, Pareto, slack_star, pruned_sets) voi:
      Seq[S]    = [(canon, slack, walk)]        - GIONG bfs_generate (day du)
      Pareto[S] = [(canon, slack, walk, label)] - tap con khong bi dominate
    """
    start, pd, home = build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    Seq = {}
    Pareto = {}
    slack_star = {}
    pruned_sets = set()

    for oid in order_ids:
        p, d = pd[oid]
        walk = [start, p, d] + ([home] if has_home else [])
        ok, slack, sched = is_feasible(travel_time, driver, walk)
        S = frozenset([oid])
        if ok:
            Seq[S] = [(canonical(walk), slack, walk)]
            slack_star[S] = slack
            Pareto[S] = filter_pareto_with_sched([(canonical(walk), slack, walk, sched)], driver)
        else:
            Seq[S] = []
            slack_star[S] = float("-inf")
            Pareto[S] = []

    for k in range(2, B + 1):
        for S_tuple in itertools.combinations(order_ids, k):
            S = frozenset(S_tuple)

            if use_filter:
                bound = min(slack_star[frozenset(S - {j})] for j in S)
                if bound < -EPS:
                    Seq[S] = []
                    Pareto[S] = []
                    slack_star[S] = float("-inf")
                    pruned_sets.add(S)
                    continue

            j = min(S)
            P = S - {j}
            parent_pareto = Pareto.get(frozenset(P), [])
            if not parent_pareto:
                Seq[S] = []
                Pareto[S] = []
                slack_star[S] = float("-inf")
                continue

            pj, dj = pd[j]
            out = []
            out_sched = []
            seen_canon = set()
            for _canon, _slack, R_objs, _sched, _lab in parent_pareto:
                for a in _insert_positions(R_objs, has_home):
                    R1 = R_objs[:a] + [pj] + R_objs[a:]
                    for b in _insert_positions(R1, has_home):
                        if b <= a:
                            continue
                        R2 = R1[:b] + [dj] + R1[b:]
                        ok, slack, sched = is_feasible(travel_time, driver, R2)
                        if ok:
                            c = canonical(R2)
                            if c not in seen_canon:
                                seen_canon.add(c)
                                out.append((c, slack, R2))
                                out_sched.append((c, slack, R2, sched))
            Seq[S] = out
            slack_star[S] = max((s for _, s, _ in out), default=float("-inf"))
            Pareto[S] = filter_pareto_with_sched(out_sched, driver)

    return Seq, Pareto, slack_star, pruned_sets
