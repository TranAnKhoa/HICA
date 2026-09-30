"""
dp_rules.py -- label-extension enumerator for ONE driver with two new bid-independent
label-elimination rules based on the FD price (FD-completion label rules).

  FW  (forward, "before visiting o"): at label L (last stop v, ready time t), do not extend to
      pickup p_o if every completion that contains o provably pays more for o than q_o.
  LB  (look-back, "after serving T"): at label L whose last stop is not a stop of T (T = set of
      orders already fully served in L), prune L and its whole subtree if removing T from any
      completion provably saves at least q(T).

Both rules only compare a route with ITS OWN shortcut (same driver) + FD for the removed orders,
uniformly over b in [lo, hi]. Every flagged route therefore lies outside K* (see note), which is
what makes the rules safe. Lower bounds used:

  distance saving  >= exact prefix saving (LB)  |  min_x [d(v,p)+d(p,x)-d(v,x)]           (FW)
  time saving      >= max(0, delta0 - A)        where A = max_w (e_w - T_w)^+ bounds the part of
                                                 the saving that later waiting can absorb.
"""
import itertools, math
from hica_core import dist, tt, SERVICE, simulate

INF = float("inf")
MUT = set()   # mutation switches for audit power tests: {"no_absorb", "no_junction"}

def stop_point(orders, s):
    oid, kind = s
    return orders[oid].p if kind == 'P' else orders[oid].d

def stop_e(orders, s):
    """[Remark 'Delivery time windows with an opening time', T4_Label_Rule.tex]
    Doc e_d neu Order co field do (RQ1 instance THAT co ready_time_d != -inf -
    xem instance_gen.py dong 228: ready_d = ready_p). getattr(..., -INF) giu
    tuong thich nguoc voi hica_core.Order goc (chi co e_p, khong co e_d -> coi
    nhu delivery khong co opening time, DUNG hanh vi cu)."""
    oid, kind = s
    if kind == 'P':
        return orders[oid].e_p
    return getattr(orders[oid], "e_d", -INF)

def path_cost(dr, orders, seq):
    """(K, W) of a stop sequence treated as a PATH (no feasibility checks) -- used for audits."""
    pos, t, dsum = dr.start, dr.t0, 0.0
    for s in seq:
        nxt = stop_point(orders, s)
        dsum += dist(pos, nxt); t += tt(pos, nxt); pos = nxt
        t = max(t, stop_e(orders, s)) + SERVICE
    if dr.cls == 'GW':
        return dr.kappa * dsum, (t - dr.t0) / 60.0
    dsum += dist(pos, dr.dest); t += tt(pos, dr.dest)
    return (dr.kappa * max(0.0, dsum - dist(dr.start, dr.dest)),
            max(0.0, (t - dr.t0) - tt(dr.start, dr.dest)) / 60.0)

def prefix_schedule(dr, orders, seq):
    """distance so far and service-start time at the last stop of a path prefix."""
    pos, t, dsum, a = dr.start, dr.t0, 0.0, dr.t0
    for s in seq:
        nxt = stop_point(orders, s)
        dsum += dist(pos, nxt); t += tt(pos, nxt); pos = nxt
        a = max(t, stop_e(orders, s)); t = a + SERVICE
    return dsum, a

def future_pickups(orders, picked, B):
    if len(picked) >= B: return []
    return [o for o in orders if o not in picked]

def future_stops(orders, picked, delivered, B):
    """[Remark 'Delivery time windows with an opening time', T4_Label_Rule.tex]
    F(L) mo rong: deliveries cua don DANG TREN XE (co the co e_d), CONG voi
    future pickups (neu chua dat B) VA deliveries cua chinh cac don do (mot
    don moi pickup roi cung co the can giao voi opening time). Tra list stop
    (oid, kind) thay vi chi order-id, de absorption() dung dung stop_e() cho
    ca P lan D (khong con gia dinh D luon co e=-inf)."""
    onboard = [o for o in picked if o not in delivered]
    stops = [(o, 'D') for o in onboard]
    if len(picked) < B:
        for o in orders:
            if o in picked:
                continue
            stops.append((o, 'P'))
            stops.append((o, 'D'))   # don moi pickup cung se can giao sau
    return stops

def absorption(orders, v_point, t_ready, stops):
    """A = max over possible future stops s=(oid,kind) of
    (e_s - (t_ready + tt(v, point(s))))^+. stops: list (oid, kind) tra ve boi
    future_stops() (bao gom ca P lan D, khop dung Remark cua .tex ve
    delivery time windows co opening time) - hoac list order-id (tuong thich
    nguoc, coi la pickup, GIU NGUYEN hanh vi cu khi khong co e_d trong du
    lieu goc cua hica_core.Order)."""
    A = 0.0
    for s in stops:
        if isinstance(s, tuple):
            oid, kind = s
            pt = stop_point(orders, s)
            e = stop_e(orders, s)
        else:
            oid, kind, pt, e = s, 'P', orders[s].p, orders[s].e_p
        if e == -INF:
            continue
        A = max(A, e - (t_ready + tt(v_point, pt)))
    return A

# --------------------------------------------------------------------------------------------
def enumerate_dp(dr, orders, B, q, lo, rules=(), log=None, subsets=True, tol=1e-9):
    """Return list of (seq, K, W) for all feasible complete routes not eliminated by `rules`.
    rules subset of {'FW','LB'}. `log` (list) receives one record per rule firing for auditing.
    stats['ext'] counts label extensions attempted (the work measure)."""
    stats = {"ext": 0, "labels": 0, "fw": 0, "lb": 0}
    out = []
    kappa = dr.kappa

    def rec(seq, pos, t_ready, dsum, load, picked, delivered):
        # candidate next stops
        onboard = [o for o in picked if o not in delivered]
        nexts = [(o, 'D') for o in onboard]
        if len(picked) < B:
            nexts += [(o, 'P') for o in orders if o not in picked]
        for s in nexts:
            oid, kind = s
            o = orders[oid]
            # ---------------- FW rule: before visiting p_o
            if kind == 'P' and 'FW' in rules:
                xs = [(oid, 'D')] + [(j, 'D') for j in onboard]
                if len(picked) + 1 < B:
                    xs += [(j, 'P') for j in orders if j not in picked and j != oid]
                p = o.p
                dd = min(dist(pos, p) + dist(p, stop_point(orders, x)) - dist(pos, stop_point(orders, x)) for x in xs)
                dt = min(tt(pos, p) + SERVICE + tt(p, stop_point(orders, x)) - tt(pos, stop_point(orders, x)) for x in xs)
                # F(L) sau khi (gia dinh) da pickup oid: onboard = cac don dang
                # mang (chua giao) CONG oid, + future stops con lai (Remark
                # delivery opening time cua .tex).
                onboard_after = [j for j in picked if j not in delivered] + [oid]
                fut = [(j, 'D') for j in onboard_after]
                if len(picked) + 1 < B:
                    for j in orders:
                        if j in picked or j == oid:
                            continue
                        fut.append((j, 'P')); fut.append((j, 'D'))
                A = absorption(orders, pos, t_ready, fut)
                dW = max(0.0, dt - A) / 60.0
                bound = kappa * dd + lo * dW
                if bound >= o.q + tol:
                    stats["fw"] += 1
                    if log is not None:
                        log.append(("FW", seq, oid, kappa * dd, dW, o.q))
                    continue
            stats["ext"] += 1
            nxt = o.p if kind == 'P' else o.d
            nd = dsum + dist(pos, nxt)
            arr = t_ready + tt(pos, nxt)
            if kind == 'P':
                a = max(arr, o.e_p)
                if a > o.l_p + 1e-9: continue
                nload = load + 1
                if nload > dr.cap: continue
                npk, ndl = picked | {oid}, delivered
            else:
                a = max(arr, o.e_d)
                if a > o.l_d + 1e-9: continue
                nload = load - 1
                npk, ndl = picked, delivered | {oid}
            nt = a + SERVICE
            if nt > dr.t1 + 1e-9: continue
            if dr.cls == 'OD':                       # necessary condition for any completion
                if (nt + tt(nxt, dr.dest) - dr.t0) - tt(dr.start, dr.dest) > dr.tau + 1e-9: continue
            nseq = seq + (s,)
            stats["labels"] += 1
            # ---------------- LB2 rule: generic junction bound, T any subset of PICKED orders
            if 'LB2' in rules:
                fired = False
                pk = sorted(npk)
                for k in range(1, len(pk) + 1):
                    for T in itertools.combinations(pk, k):
                        T = frozenset(T)
                        qT = sum(orders[j].q for j in T)
                        short = tuple(x for x in nseq if x[0] not in T)
                        if short:
                            d2, a2 = prefix_schedule(dr, orders, short)
                            vprime, rprime = stop_point(orders, short[-1]), a2 + SERVICE
                        else:
                            d2, vprime, rprime = 0.0, dr.start, dr.t0
                        jd = 0.0 if 'no_junction' in MUT else dist(vprime, nxt)
                        jt = 0.0 if 'no_junction' in MUT else tt(vprime, nxt)
                        dK = kappa * (nd - d2 - jd)
                        delta0 = nt - rprime - jt
                        # F(L): deliveries cua don dang mang (Remark delivery
                        # opening time cua .tex) + future pickups/deliveries
                        # con reachable (loc feasibility nhu code goc, ap dung
                        # dung deadline tuong ung P/D).
                        fut = []
                        for (w, wkind) in future_stops(orders, npk, ndl, B):
                            wl = orders[w].l_p if wkind == 'P' else orders[w].l_d
                            wpt = stop_point(orders, (w, wkind))
                            if nt + tt(nxt, wpt) <= wl + 1e-9:
                                fut.append((w, wkind))
                        A = 0.0 if 'no_absorb' in MUT else absorption(orders, vprime, rprime, fut)
                        dW = max(0.0, delta0 - A) / 60.0
                        if dK + lo * dW >= qT + tol:
                            stats["lb"] += 1
                            if log is not None:
                                log.append(("LB", nseq, T, dK, dW, qT))
                            fired = True
                            break
                    if fired: break
                if fired:
                    continue
            # ---------------- LB rule: after serving T, last stop not in T
            if 'LB' in rules:
                served = [j for j in ndl if j != oid]          # fully served, last stop not theirs
                Ts = []
                if subsets:
                    for k in range(1, len(served) + 1):
                        Ts += [frozenset(c) for c in itertools.combinations(sorted(served), k)]
                else:
                    Ts = [frozenset([j]) for j in served]
                fired = False
                for T in Ts:
                    qT = sum(orders[j].q for j in T)
                    short = tuple(x for x in nseq if x[0] not in T)
                    d2, a2 = prefix_schedule(dr, orders, short)
                    dK = kappa * (nd - d2)
                    fut = future_stops(orders, npk, ndl, B)
                    A = absorption(orders, nxt, a2 + SERVICE, fut)
                    dW = max(0.0, (a - a2) - A) / 60.0
                    if dK + lo * dW >= qT + tol:
                        stats["lb"] += 1
                        if log is not None:
                            log.append(("LB", nseq, T, dK, dW, qT))
                        fired = True
                        break
                if fired:
                    continue
            if len(ndl) == len(npk):                     # complete route
                kw = simulate(dr, orders, nseq)
                if kw is not None:
                    out.append((nseq, kw[0], kw[1]))
            rec(nseq, nxt, nt, nd, nload, npk, ndl)

    rec((), dr.start, dr.t0, 0.0, 0, frozenset(), frozenset())
    return out, stats
