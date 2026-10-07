"""C5s = C5h with a stronger, still exact, dead-end filter: the on-board orders must be deliverable in SOME order.

C5h tests every on-board order separately (t + tau(v, d_j) <= l(d_j)) and, for an occasional driver, a lower
bound on the time home. C5s keeps that cheap test and, when it passes and at least two orders are on board,
also asks whether some sequence of the remaining deliveries (followed by home for an occasional driver) meets
every deadline, starting from (v, t). The search is a depth-first search over sequences, earliest deadline
first, that stops at the first feasible sequence and abandons a branch as soon as an undelivered order cannot be
reached in time.

Why it is exact. Take any feasible completion of the label. Its deliveries of the on-board orders, in the order
the completion makes them, form a sequence. Running that sequence directly (dropping the other stops) arrives
at each stop no later than the completion does: travel times are Euclidean (triangle inequality), service and
waiting are nonnegative, and the start of service max(arrival, e) is nondecreasing in the arrival. So that
sequence passes the test, and a label that fails has no feasible completion. The test is monotone in t, so if a
failing label dominates another label of the same key, that label fails too; removing failing labels therefore
never changes which live labels survive Layer 1, and R and K* are unchanged. A margin of 1e-6 minutes keeps
rounding from removing a feasible label.
"""
import paths  # noqa: F401

import variants_h as VH
import variants as V

CHEAP = VH.make_dead      # C5h's filter, captured before any patching

MARGIN = 1e-6


def make_dead_seq(tt, pd, home, cnt):
    cheap = CHEAP(tt, pd, home)
    deliveries = {j: pd[j][1] for j in pd}
    hid = home.id if home is not None else None
    hl = home.l if home is not None else None

    def feasible(v, t, rest):
        # rest: tuple of order ids sorted by deadline
        for j in rest:
            d = deliveries[j]
            if t + tt(v, d.id) > d.l + MARGIN:
                return False
        if len(rest) == 1:
            d = deliveries[rest[0]]
            a = t + tt(v, d.id)
            if hid is None:
                return True
            return (a if a > d.e else d.e) + d.s + tt(d.id, hid) <= hl + MARGIN
        for i, j in enumerate(rest):
            d = deliveries[j]
            a = t + tt(v, d.id)
            t2 = (a if a > d.e else d.e) + d.s
            if feasible(d.id, t2, rest[:i] + rest[i + 1:]):
                return True
        return False

    def dead(nl):
        if cheap(nl):
            return True
        if len(nl.IV) < 2:
            return False
        cnt["seq_tests"] += 1
        rest = tuple(sorted(nl.IV, key=lambda j: deliveries[j].l))
        if feasible(nl.v, nl.t, rest):
            return False
        cnt["killed_seq"] += 1
        return True
    return dead


def run_tier_s(tt, driver, orders, B, q=None, inloop=True, **kw):
    """C5h's engine with the sequence test plugged in as its dead-end filter."""
    box = {}
    orig = VH.make_dead
    assert orig is CHEAP

    def patched(tt_, pd, home):
        return make_dead_seq(tt_, pd, home, box["cnt"])
    # run_tier_h creates its counter before calling make_dead; give the filter a counter of its own
    box["cnt"] = {"seq_tests": 0, "killed_seq": 0}
    VH.make_dead = patched
    try:
        pool, cnt = VH.run_tier_h(tt, driver, orders, B, q=q, inloop=inloop)
    finally:
        VH.make_dead = orig
    cnt.update(box["cnt"])
    return pool, cnt


def run_c5s(tt, driver, orders, B, q=None, **kw):
    return run_tier_s(tt, driver, orders, B, q=q, inloop=True)


def run_c4s(tt, driver, orders, B, q=None, **kw):
    return run_tier_s(tt, driver, orders, B, q=q, inloop=False)


V.VARIANTS.update(C5s=run_c5s, C4s=run_c4s)
V.INLOOP.update({"C5s"})
build_all = V.build_all
