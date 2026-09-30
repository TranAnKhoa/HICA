"""Xac dinh co che chinh xac khien key_drop_C mat route hop le.
Gia thuyet: bo C khoi key khien 2 label cung (v, IV) nhung khac t (do thu
tu giao hang khac nhau) bi so dominance CHI theo (K,W), bo qua t - trong
khi t khac nhau anh huong truc tiep kha nang giao kip deadline cua cac
order con lai trong IV o tuong lai. Mot label (K,W) tot hon nhung t muon
hon co the loai nham 1 label (K,W) kem hon nhung t som hon - ma chinh label
t som hon moi la duong duy nhat con kha thi tiep."""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG

_T2BFS = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "experiments", "T2BFS")
if _T2BFS not in sys.path:
    sys.path.insert(0, _T2BFS)
import t6_dp as D
import t2_core as C

TAU = 20.0
SPATIAL = "dispersed"


def main():
    n, B_gw, tw, sd = 3, 2, 60, 2
    gen_seed = IG.stable_seed(n, B_gw, 2, tw, 4, sd, "testC_gate_key_drop_C")
    drivers, orders, tt, meta = IG.generate_instance(
        n=n, B_gw=B_gw, B_od=2, tw_width=tw, n_drivers=4,
        seed=gen_seed, tau=TAU, spatial_mode=SPATIAL)
    drv = [d for d in drivers if d["id"] == "gw0"][0]
    print("driver:", drv["id"], "cls:", drv["cls"])
    print("orders:", sorted(orders.keys()))
    for oid, o in sorted(orders.items()):
        print("  %s: pickup=%s e=%.3f l=%.3f  delivery=%s e=%.3f l=%.3f" %
              (oid, o["pickup_node"], o["ready_time_p"], o["deadline_p"],
               o["delivery_node"], o["ready_time_d"], o["deadline_d"]))

    start, pd, home = C.build_walk_nodes(drv, orders)
    print("\nstart:", start.id, "t0:", drv["t0"])

    # Chay DP goc (key_full) VA ghi lai toan bo label hoan chinh cho bundle {o0,o2}
    order_ids = sorted(orders.keys())
    lab0 = D.Label(start.id, frozenset(), frozenset(), drv["t0"], 0.0, 0.0)
    frontier = {0: [lab0]}
    complete_by_C = defaultdict(list)
    B = B_gw
    all_labels_by_key = defaultdict(list)  # key_full -> list of label (truoc dominance cuoi)

    for touched in range(0, B + 1):
        labs_here = frontier.get(touched, [])
        if not labs_here:
            continue
        active = list(labs_here)
        closure_all = []
        while active:
            next_active = []
            for lab in active:
                closure_all.append(lab)
                for j in sorted(lab.IV):
                    new_lab = D._try_delivery(tt, drv, pd, lab, j)
                    if new_lab is None:
                        continue
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1:
                        complete_by_C[new_lab.Cd].append(new_lab)
                        all_labels_by_key[(new_lab.v, new_lab.IV, new_lab.Cd)].append(new_lab)
            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
                all_labels_by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(D._filter_dominated_labels(labs))
            active = filtered

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(tt, drv, pd, lab, j, B)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
                    all_labels_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    target = frozenset({"o0", "o2"})
    print("\n=== Toan bo label (bat ky IV/C nao) co the lien quan bundle {o0,o2} ===")
    for key, labs in sorted(all_labels_by_key.items(), key=lambda kv: str(kv[0])):
        v, IV, Cd = key
        if Cd == target or (Cd < target and IV <= target):
            for lab in labs:
                K, W = D.finalize_KW(drv, lab)
                print("  v=%s IV=%s Cd=%s  t=%.6f K=%.6f W=%.6f  finalK=%.6f finalW=%.6f"
                      % (v, sorted(IV), sorted(Cd), lab.t, lab.K, lab.W, K, W))


if __name__ == "__main__":
    main()
