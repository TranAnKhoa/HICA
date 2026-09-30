"""Gia thuyet: closure 'chet' (survivors=0) trong Test A khong phai vi khong
co duong giao het IV - ma vi label sinh ra (IV rong, hoan chinh) bi
_filter_dominated_labels LOAI vi bi 1 label KHAC (tu closure root khac,
CUNG key (v,IV,Cd) tai thoi diem do) dominate. Day la hanh vi DUNG cua thuat
toan (khong mat optimality o muc route_pool cuoi cung), nhung lam cho
dinh nghia 'survivor' trong Test A/patch A2 KHONG PHAN ANH DUNG 'co duong
kha thi hay khong o muc closure rieng le' - closure van co duong kha thi,
chi la ket qua bi 1 nhanh khac (tot hon) lan at trong buoc loc dominance
chung. Day la ly do 0 label bi cat: patch A2 KHONG THE va KHONG NEN cat cac
truong hop nay, vi chinh DP goc (khong patch) van tao ra label do (dung),
chi la no bi dominance loai sau - dung hanh vi, khong phai bug."""

import itertools
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

N, B_GW, TW, SEED, NDRV = 20, 4, 240, 0, 10
TAU = 20.0
SPATIAL = "dispersed"


def iv_completion_feasible(travel_time, pd, lab):
    iv_list = list(lab.IV)
    if not iv_list:
        return True
    if len(iv_list) > 7:
        return True
    for perm in itertools.permutations(iv_list):
        t = lab.t
        v = lab.v
        ok = True
        for oid in perm:
            _, d = pd[oid]
            tt = travel_time(v, d.id)
            A = t + tt
            Bt = A if A > d.e else d.e
            if Bt > d.l + 1e-9:
                ok = False
                break
            t = Bt + d.s
            v = d.id
        if ok:
            return True
    return False


def run_dp_with_predom_tracking(travel_time, driver, orders, B, compat_graph=None):
    """Nhu Test A, NHUNG dem 'survivor' theo 2 dinh nghia:
    (1) post_dominance: nhu Test A goc (sau khi loc dominance) - IV rong that
        su con lai trong route_pool cuoi.
    (2) pre_dominance: co it nhat 1 lan _try_delivery lien tiep SINH RA label
        IV rong TRUOC KHI bi dominance loc di (bat ke sau co bi loai khong)."""
    start, pd, home = C.build_walk_nodes(driver, orders)
    order_ids = sorted(orders.keys())
    has_home = home is not None
    assert not has_home  # GW only trong test nay

    lab0 = D.Label(start.id, frozenset(), frozenset(), driver["t0"], 0.0, 0.0)
    complete_by_C = defaultdict(list)
    frontier = {0: [lab0]}
    closure_root = {id(lab0): id(lab0)}

    survivors_pre = defaultdict(int)    # sinh ra IV rong, TRUOC dominance
    survivors_post = defaultdict(int)   # con lai SAU dominance (that su vao complete_by_C)
    root_iv_feasible = {}

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
                root = closure_root.get(id(lab), id(lab))
                for j in sorted(lab.IV):
                    new_lab = D._try_delivery(travel_time, driver, pd, lab, j)
                    if new_lab is None:
                        continue
                    closure_root[id(new_lab)] = root
                    next_active.append(new_lab)
                    if not new_lab.IV and len(new_lab.Cd) >= 1:
                        survivors_pre[root] += 1   # SINH RA, truoc dominance

            by_key = defaultdict(list)
            for lab in next_active:
                by_key[lab.key()].append(lab)
            filtered = []
            for k, labs in by_key.items():
                filtered.extend(D._filter_dominated_labels(labs))
            active = filtered

            # sau khi loc dominance, kiem lai xem con label IV rong nao SONG SOT khong
            for lab in filtered:
                if not lab.IV and len(lab.Cd) >= 1:
                    root = closure_root.get(id(lab), id(lab))
                    survivors_post[root] += 1
                    complete_by_C[lab.Cd].append(lab)

        if touched < B:
            new_by_key = defaultdict(list)
            for lab in closure_all:
                for j in order_ids:
                    new_lab = D._try_pickup(travel_time, driver, pd, lab, j, B,
                                            compat_graph=compat_graph)
                    if new_lab is None:
                        continue
                    new_by_key[new_lab.key()].append(new_lab)
            next_frontier = []
            for k, labs in new_by_key.items():
                kept = D._filter_dominated_labels(labs)
                for lb in kept:
                    rid = id(lb)
                    closure_root[rid] = rid
                    root_iv_feasible[rid] = iv_completion_feasible(travel_time, pd, lb)
                next_frontier.extend(kept)
            frontier[touched + 1] = next_frontier

    return survivors_pre, survivors_post, root_iv_feasible


def main():
    gen_seed = IG.stable_seed(N, B_GW, 2, TW, NDRV, SEED, "research_case12")
    drivers, orders, tt, meta = IG.generate_instance(
        n=N, B_gw=B_GW, B_od=2, tw_width=TW, n_drivers=NDRV, seed=gen_seed,
        tau=TAU, spatial_mode=SPATIAL)
    gw_drivers = [d for d in drivers if d["cls"] == "GW"]
    drv = gw_drivers[2]  # gw2, giong vi du mismatch truoc
    print("driver:", drv["id"])

    sp, spost, rif = run_dp_with_predom_tracking(tt, drv, orders, B_GW)

    all_roots = set(sp.keys()) | set(rif.keys())
    # closure chet theo POST (nhu Test A goc)
    dead_post = [k for k in all_roots if spost.get(k, 0) == 0]
    # trong so do, bao nhieu cai CO sinh ra IV rong pre-dominance (tuc co duong kha thi that)
    # nhung bi dominance loai
    dead_post_but_had_pre = [k for k in dead_post if sp.get(k, 0) > 0]
    dead_post_and_no_pre = [k for k in dead_post if sp.get(k, 0) == 0]

    print("Tong so closure root (co iv_feasible ghi nhan):", len(rif))
    print("Closure 'chet' theo POST-dominance (nhu Test A):", len(dead_post))
    print("  - trong do CO sinh IV-rong nhung bi dominance loai (khong phai chet that):", len(dead_post_but_had_pre))
    print("  - trong do KHONG BAO GIO sinh duoc IV-rong (chet that su):", len(dead_post_and_no_pre))

    # doi chieu voi iv_completion_feasible cho nhom 'chet that su'
    mism = [k for k in dead_post_and_no_pre if rif.get(k, True) == True]
    print("  Trong nhom 'chet that su', so mismatch voi iv_completion_feasible (tra True sai):", len(mism))

    return mism, drv, orders, tt, closure_root


if __name__ == "__main__":
    main()
