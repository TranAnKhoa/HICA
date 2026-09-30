"""
Test8 §1 — Sinh instance tong hop co kiem soat cau truc component.

KHONG dung lai Test2-7. Moi component la 1 khoi doc lap tuyet doi: driver/order/route
cua component nay khong dung order cua component khac. make_instance ghep n_components
khoi lai, KHONG them route/canh nao noi giua cac khoi -> instance co dung n_components
connected component (dung lam oracle kiem build_conflict_graph).
"""

import random


def make_component(component_id, n_drivers, n_routes_per_driver, n_orders, seed):
    """
    1 component DOC LAP. driver id / order id co prefix "C{component_id}_" de khong
    trung khi ghep. Route phu 1-2 order ngau nhien trong dung n_orders order cua
    component nay. Cost = base + offset random (tao canh tranh that). fd_cost moi
    order: ~50% co hoi THAP hon route re nhat phu no (FD tham gia that vao loi giai,
    theo bai hoc Case C Test7 — khong luon thua, khong luon thang).
    """
    rng = random.Random(seed * 100003 + component_id)
    pfx = f"C{component_id}_"
    orders = [f"{pfx}o{j}" for j in range(1, n_orders + 1)]

    drivers = {}
    # gom route theo order de tinh route re nhat phu tung order (cho fd_cost)
    cheapest_route_for_order = {o: float("inf") for o in orders}

    for d in range(n_drivers):
        did = f"{pfx}D{d}"
        routes = []
        seen_sig = set()
        attempts = 0
        while len(routes) < n_routes_per_driver and attempts < 200:
            attempts += 1
            k = rng.choice([1, 1, 2])          # thien ve 1-order route
            covered = frozenset(rng.sample(orders, k))
            sig = covered
            if sig in seen_sig:
                continue
            seen_sig.add(sig)
            base = 8.0 + 4.0 * len(covered)
            cost = round(base + rng.uniform(-3.0, 8.0), 3)
            if cost <= 0:
                cost = round(base, 3)
            rid = f"{pfx}D{d}r{len(routes)}"
            routes.append((rid, covered, cost))
            for o in covered:
                cheapest_route_for_order[o] = min(cheapest_route_for_order[o], cost)
        drivers[did] = {"routes": routes}

    fd_cost = {}
    for o in orders:
        base = cheapest_route_for_order[o]
        if base == float("inf"):
            base = 12.0
        if rng.random() < 0.5:
            fd_cost[o] = round(base * rng.uniform(0.55, 0.95), 3)   # FD re hon
        else:
            fd_cost[o] = round(base * rng.uniform(1.15, 2.2), 3)    # FD dat hon
    return {"drivers": drivers, "orders": orders, "fd_cost": fd_cost}


def make_instance(n_components, n_drivers_per_component=4, n_routes_per_driver=3,
                  n_orders_per_component=4, seed=0):
    """
    Goi make_component n_components lan (seed + component_id), gop toan bo. KHONG
    them bat ky route/canh nao noi giua cac component. Tra ve:
      {'drivers': {...}, 'orders': [...], 'fd_cost': {...},
       'n_components_designed': n_components,
       'component_of': {driver_id -> component_id}}  # ground truth
    """
    all_drivers, all_orders, all_fd = {}, [], {}
    component_of = {}
    for cid in range(n_components):
        comp = make_component(cid, n_drivers_per_component, n_routes_per_driver,
                              n_orders_per_component, seed)
        for did, dv in comp["drivers"].items():
            all_drivers[did] = dv
            component_of[did] = cid
        all_orders.extend(comp["orders"])
        all_fd.update(comp["fd_cost"])
    return {
        "drivers": all_drivers,
        "orders": all_orders,
        "fd_cost": all_fd,
        "n_components_designed": n_components,
        "component_of": component_of,
    }


if __name__ == "__main__":
    inst = make_instance(2, seed=0)
    print("drivers:", list(inst["drivers"]))
    print("orders :", inst["orders"])
    print("fd_cost:", inst["fd_cost"])
    print("designed components:", inst["n_components_designed"])
