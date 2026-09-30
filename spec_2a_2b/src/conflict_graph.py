"""Spec 2b - conflict graph tren route pool THAT (toan bo pool, khong chi alloc*).

node = driver. canh (i,k) neu ton tai route trong pool[i] va route trong
pool[k] chia se >= 1 order (nhin toan bo route pool - dinh nghia T5 Sec2.2).
FD KHONG la node/canh.
"""


def _order_universe(pool):
    """pool: {frozenset(order_ids): [(K,W)]}. Tra set tat ca order xuat hien
    trong BAT KY bundle nao cua driver do."""
    u = set()
    for Cset in pool:
        u |= set(Cset)
    return u


def build_conflict_graph(pool_by_driver):
    """pool_by_driver: {driver_id: {frozenset(order_ids): [(K,W)]}}.

    Tra (nodes, edges) voi nodes = list driver_id, edges = set frozenset({i,k}).
    """
    driver_ids = list(pool_by_driver.keys())
    universe = {d: _order_universe(pool_by_driver[d]) for d in driver_ids}
    edges = set()
    for a in range(len(driver_ids)):
        for b in range(a + 1, len(driver_ids)):
            i, k = driver_ids[a], driver_ids[b]
            if universe[i] & universe[k]:
                edges.add(frozenset((i, k)))
    return driver_ids, edges


def connected_components(nodes, edges):
    """Tra list set driver_id, moi set la 1 component (ke ca singleton)."""
    adj = {n: set() for n in nodes}
    for e in edges:
        i, k = tuple(e)
        adj[i].add(k)
        adj[k].add(i)
    seen = set()
    comps = []
    for n in nodes:
        if n in seen:
            continue
        stack = [n]
        comp = set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            seen.add(x)
            for y in adj[x]:
                if y not in comp:
                    stack.append(y)
        comps.append(comp)
    return comps


def component_stats(nodes, edges):
    comps = connected_components(nodes, edges)
    sizes = sorted((len(c) for c in comps), reverse=True)
    n_drivers = len(nodes)
    return dict(
        n_components=len(comps),
        component_sizes=sizes,
        largest_component_fraction=(max(sizes) / n_drivers) if n_drivers else 0.0,
        n_singleton_components=sum(1 for s in sizes if s == 1),
        median_component_size=_median(sizes),
    )


def _median(xs):
    if not xs:
        return 0.0
    ys = sorted(xs)
    m = len(ys)
    if m % 2:
        return float(ys[m // 2])
    return (ys[m // 2 - 1] + ys[m // 2]) / 2.0
