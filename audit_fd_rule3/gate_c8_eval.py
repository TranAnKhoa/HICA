"""Independent route evaluator (re-simulation from the stop sequence), shared by the audits.
Identical to the functions in gate_c8.py, which in turn copy audit_fd_rule2/gate_audit.py
(that file runs its main() at import time, so it cannot be imported)."""
import paths  # noqa: F401
import variants as V
import t2_gen as G

D = V.D
SPEED = G.SPEED_KMH


# ------------------------------------------------ independent evaluator (copied from audit_fd_rule2/gate_audit.py,
# which cannot be imported because it runs its main() at import time)
def simulate(tt, driver, orders, seq, B):
    t = driver["t0"]
    node = driver["start_node"]
    dist = 0.0
    load, done = set(), set()
    for kind, oid in seq:
        o = orders[oid]
        if kind == "p":
            if oid in load or oid in done or len(load) + len(done) >= B:
                return None
            nid, e, l = o["pickup_node"], o["ready_time_p"], o["deadline_p"]
        else:
            if oid not in load:
                return None
            nid, e, l = o["delivery_node"], o["ready_time_d"], o["deadline_d"]
        tr = tt(node, nid)
        dist += tr * SPEED / 60.0
        arr = t + tr
        st = arr if arr > e else e
        if st > l + 1e-9:
            return None
        t = st + o["service_time"]
        node = nid
        if kind == "p":
            load.add(oid)
        else:
            load.discard(oid)
            done.add(oid)
    return (t, node, dist, frozenset(load), frozenset(done))


def finish(tt, driver, state):
    t, node, dist, load, done = state
    if load:
        return None
    if not done:
        return (0.0, 0.0)
    if driver["cls"] == "OD":
        tr = tt(node, driver["home_node"])
        dist += tr * SPEED / 60.0
        arr = t + tr
        st = arr if arr > 0.0 else 0.0
        if st > driver["t0"] + driver["direct_time"] + driver["tau"] + 1e-9:
            return None
        t = st
        K = D.KAPPA * max(0.0, dist - driver["direct_time"] * SPEED / 60.0)
        W = max(0.0, (t - driver["t0"] - driver["direct_time"]) / 60.0)
    else:
        K = D.KAPPA * dist
        W = (t - driver["t0"]) / 60.0
    return (K, W)


def seq_of(label):
    out = []
    for act, v, t, K, W in label.path():
        if act is None or act[0] == "home":
            continue
        out.append(("p" if act[0] == "pickup" else "d", act[1]))
    return out


def completions(tt, driver, orders, base_seq, B):
    ids = sorted(orders.keys())
    out = []

    def rec(sigma):
        st = simulate(tt, driver, orders, base_seq + sigma, B)
        if st is None:
            return
        t, node, dist, load, done = st
        if not load and done and finish(tt, driver, st) is not None:
            out.append(list(sigma))
        if len(load) + len(done) < B:
            for j in ids:
                if j not in load and j not in done:
                    rec(sigma + [("p", j)])
        for j in sorted(load):
            rec(sigma + [("d", j)])
    rec([])
    return out


