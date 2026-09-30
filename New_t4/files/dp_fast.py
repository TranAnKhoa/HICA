"""
dp_fast.py -- incremental implementation of the LB2 label rule (singleton T), for timing.
Each label carries, for every picked order j, the state (D', v', r') of its own shortcut
(the same path with j's stops removed). Extending a label updates each state in O(1):
  - the new stop belongs to j  -> j's shortcut skips it (state unchanged)
  - otherwise                  -> shortcut travels to the new stop like the real path.
Rule check for j (valid for ALL completions, proof in the note):
  dK = kappa * (D - D' - d(v', v))          dW = max(0, (r - r' - tau(v', v)) - A) / 60
  prune label + subtree if dK + lo*dW >= q_j.     A computed only if the rule could fire with A=0.
"""
from hica_core import dist, tt, SERVICE, simulate

MUT = set()   # audit mutation switches: {"no_absorb", "no_junction"}
# Tam thoi giu hanh vi cu cua 2 cho nghi loi de do suc bat loi cua audit; tat ca = False sau khi sua.
LEGACY = {"exclude_own_delivery": True, "shortcut_ignores_e_d": True}

def enumerate_fast(dr, orders, B, lo, use_rule=True, tol=1e-9, log=None):
    stats = {"ext": 0, "fired": 0, "A_evals": 0}
    out = []
    kappa = dr.kappa
    oids = list(orders)
    max_e = max([o.e_p for o in orders.values()] +
               [o.e_d for o in orders.values() if o.e_d != float("-inf")])

    def rec(seq, pos, r, D, load, picked, delivered, sc):
        onboard = [j for j in picked if j not in delivered]
        nexts = [(j, 'D') for j in onboard]
        if len(picked) < B:
            nexts += [(j, 'P') for j in oids if j not in picked]
        for s in nexts:
            oid, kind = s
            o = orders[oid]
            stats["ext"] += 1
            pt = o.p if kind == 'P' else o.d
            nD = D + dist(pos, pt)
            arr = r + tt(pos, pt)
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
            nr = a + SERVICE
            if nr > dr.t1 + 1e-9: continue
            if dr.cls == 'OD' and (nr + tt(pt, dr.dest) - dr.t0) - tt(dr.start, dr.dest) > dr.tau + 1e-9:
                continue
            # ---- incremental shortcut states
            nsc = {}
            if kind == 'P':
                e_s = o.e_p
            else:
                e_s = float('-inf') if LEGACY["shortcut_ignores_e_d"] else o.e_d
            for j, (Dj, vj, rj) in sc.items():
                if j == oid:
                    nsc[j] = (Dj, vj, rj)
                else:
                    nsc[j] = (Dj + dist(vj, pt), pt, max(rj + tt(vj, pt), e_s) + SERVICE)
            if kind == 'P':
                nsc[oid] = (D, pos, r)                 # shortcut without oid = parent path
            # ---- rule
            if use_rule:
                fired = False
                for j, (Dj, vj, rj) in nsc.items():
                    qj = orders[j].q
                    jd = 0.0 if "no_junction" in MUT else dist(vj, pt)
                    jt = 0.0 if "no_junction" in MUT else tt(vj, pt)
                    dK = kappa * (nD - Dj - jd)
                    delta0 = nr - rj - jt
                    if dK + lo * max(0.0, delta0) / 60.0 < qj + tol:
                        continue                         # cannot fire even with A = 0
                    A = 0.0
                    # F(L) (Remark 'Delivery time windows with an opening time'): deliveries of every
                    # order on board at the end of L -- INCLUDING j, whose delivery stays in the
                    # continuation of pi = (L \ {j}) . sigma -- plus future pickups/deliveries.
                    if LEGACY["exclude_own_delivery"]:
                        onboard_j = [w for w in npk if w not in ndl and w != j]
                    else:
                        onboard_j = [w for w in npk if w not in ndl]
                    for w in onboard_j:
                        ow = orders[w]
                        if ow.e_d == float("-inf"): continue
                        A = max(A, ow.e_d - (rj + tt(vj, ow.d)))
                    if len(npk) < B and rj < max_e:
                        stats["A_evals"] += 1
                        for w in oids:
                            if w in npk: continue
                            ow = orders[w]
                            if nr + tt(pt, ow.p) <= ow.l_p + 1e-9:
                                A = max(A, ow.e_p - (rj + tt(vj, ow.p)))
                            if ow.e_d != float("-inf") and nr + tt(pt, ow.d) <= ow.l_d + 1e-9:
                                A = max(A, ow.e_d - (rj + tt(vj, ow.d)))
                    if "no_absorb" in MUT:
                        A = 0.0
                    dW = max(0.0, delta0 - A) / 60.0
                    if dK + lo * dW >= qj + tol:
                        fired = True
                        if log is not None:
                            log.append((seq + (s,), j, dK, dW, qj))
                        break
                if fired:
                    stats["fired"] += 1
                    continue
            nseq = seq + (s,)
            if len(ndl) == len(npk):
                kw = simulate(dr, orders, nseq)
                if kw is not None: out.append((nseq, kw[0], kw[1]))
            rec(nseq, pt, nr, nD, nload, npk, ndl, nsc)

    rec((), dr.start, dr.t0, 0.0, 0, frozenset(), frozenset(), {})
    return out, stats
