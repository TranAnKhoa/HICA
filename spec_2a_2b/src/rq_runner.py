"""RQ_Master.md §9 buoc 4 - runner chung cho RQ2 / RQ3+RQ4 / RQ5, co resume
(bo qua key da ghi trong CSV) va shard (chia instance cho nhieu process).

  python rq_runner.py rq2  <shard> <n_shards>
  python rq_runner.py rq34 <shard> <n_shards>
  python rq_runner.py rq5  <shard> <n_shards>

Doc lai + kiem tra hash rq_all_locked_params.json truoc instance dau tien.
"""
import csv
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_T4AUDIT = os.path.join("K:" + os.sep, "Data Science", "Q1 Research", "T4_audit_scripts", "T4_audit")
if _T4AUDIT not in sys.path:
    sys.path.insert(0, _T4AUDIT)
import rq_common as C
from kstar_zstar_payment_check import prune_pool_by_kstar


def verify_lock():
    p = json.load(open(C.LOCKED_ALL))
    h = p["sha256_of_this_file"]["hash"]
    p["sha256_of_this_file"] = "PLACEHOLDER"
    assert hashlib.sha256(json.dumps(p, indent=2, sort_keys=True).encode()).hexdigest() == h, \
        "[STOP] rq_all_locked_params.json bi sua sau khi hash"
    return p


SUPPLY = [(2, 2), (3, 2), (2, 3), (3, 3)]


def jobs(which, P):
    if which == "rq2":
        g = P["rq2"]["grid"]
        return [(a, n, s[0], s[1], r) for a in g["alignment"] for n in g["n"]
                for s in g["supply"] for r in range(g["reps"])]
    if which == "rq34":
        g = P["rq3"]["grid"]
        return [(a, n, s[0], s[1], r) for a in g["alignment"] for n in g["n"]
                for s in g["supply"] for r in range(g["reps"])]
    if which == "rq5":
        out = []
        for v in C.RQ5_VARIANTS:
            sup = C.RQ5_SUPPLY_SCALE if v in ("V9_n25", "V10_n30") else C.RQ5_SUPPLY_BASE
            for (ng, no) in sup:
                for r in range(P["rq5"]["reps_per_supply"]):
                    out.append((v, ng, no, r))
        return out


def all_ok(statuses):
    return all(C.is_optimal(s) for s in statuses)


# ---------------------------------------------------------------------------

def run_rq2(job, P):
    a, n, ng, no, rep = job
    d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
    oids = list(o)
    p3, tA3 = C.build_pool(tt, d, o, 3)
    cf = C.true_cost_fn(th)
    blocks = C.heur_blocks(o, tt, C.TW_WIDTH)
    menus = [("B1", C.filter_pool(p3, 1), 0.0), ("B2", C.filter_pool(p3, 2), 0.0),
             ("B3", p3, tA3), ("HEUR", C.heur_pool(p3, blocks), 0.0)]
    if n in P["rq2"]["B4_only_n"]:
        d4, o4, tt4, _, _, _ = C.make_rq1_instance(a, n, ng, no, rep, B=4)
        p4, tA4 = C.build_pool(tt4, d4, o4, 4)
        menus.append(("B4", p4, tA4))
    rows = []
    for name, pool, tA in menus:
        r = C.solve(pool, cf, q, oids)
        st = C.alloc_stats(r, n)
        rows.append(dict(alignment=a, n=n, n_gw=ng, n_od=no, rep=rep, menu=name,
                         true_cost=r["z"], status=r["status"], fd_rate=st["fd_rate"],
                         mean_bundle=st["mean_bundle"], n_routes=st["n_routes"],
                         pool_size=C.pool_size(pool), t_A=tA, t_B=r["wall"],
                         n_heur_blocks=sum(1 for b in blocks if len(b) >= 2)))
    return rows


def run_rq34(job, P):
    a, n, ng, no, rep = job
    d, o, tt, meta, th, q = C.make_rq1_instance(a, n, ng, no, rep, B=3)
    oids = list(o)
    pool, tA = C.build_pool(tt, d, o, 3)
    t0 = time.perf_counter()
    pk = prune_pool_by_kstar(pool, q, C.THETA_LO, C.THETA_HI)
    t_k = time.perf_counter() - t0
    if rep % 2 == 0:
        vn = C.vcg(pool, th, q, oids)
        va = C.vcg(pk, th, q, oids)
    else:
        va = C.vcg(pk, th, q, oids)
        vn = C.vcg(pool, th, q, oids)
    winners = set(vn["pay"]) | set(va["pay"])
    pay_err = max([abs(vn["pay"].get(w, 0.0) - va["pay"].get(w, 0.0)) for w in winners] or [0.0])
    lam = P["rq3"]["posted_lambda"]
    ps = C.posted(pool, th, q, oids, lam)
    t0 = time.perf_counter()
    pb = C.pab_br(pool, th, q, oids, hi=C.THETA_HI, step=P["rq3"]["pab_br"]["grid_step"])
    t_pab = time.perf_counter() - t0
    cls = {x["id"]: x["cls"] for x in d}
    wc = sum(vn["cost"].values())
    return [dict(
        alignment=a, n=n, n_gw=ng, n_od=no, rep=rep,
        Z=vn["Z"], fd_cost_in_Z=sum(q[x] for x in vn["full"]["fd_orders"]),
        fd_rate=len(vn["full"]["fd_orders"]) / float(n), n_winners=len(vn["pay"]),
        winner_true_cost=wc, vcg_rent=sum(vn["rent"].values()),
        vcg_rent_gw=sum(v for k, v in vn["rent"].items() if cls[k] == "GW"),
        vcg_rent_od=sum(v for k, v in vn["rent"].items() if cls[k] == "OD"),
        vcg_payout=vn["payout"],
        posted_lambda=lam, posted_payout=ps["payout"], posted_true_cost=ps["true_cost"],
        posted_fd_rate=len(ps["res"]["fd_orders"]) / float(n), posted_status=ps["res"]["status"],
        pab_payout=pb["payout"], pab_true_cost=pb["true_cost"], pab_rent=pb["rent"],
        pab_fd_rate=len(pb["res"]["fd_orders"]) / float(n), pab_status=pb["res"]["status"],
        pab_mean_markup=sum(pb["bids"][k] - th[k] for k in pb["bids"]) / len(pb["bids"]),
        t_pab=t_pab,
        # RQ4
        pool_full=C.pool_size(pool), pool_kstar=C.pool_size(pk), t_A=tA, t_kstar=t_k,
        t_C_naive=vn["wall"], t_C_accel=va["wall"],
        n_solves=len(vn["statuses"]), z_err=abs(vn["Z"] - va["Z"]), pay_err=pay_err,
        all_optimal=all_ok(vn["statuses"] + va["statuses"] + [ps["res"]["status"], pb["res"]["status"]]),
    )]


def run_rq5(job, P):
    v, ng, no, rep = job
    t_start = time.perf_counter()
    d, o, tt, meta, th, q, tw = C.make_rq5_instance(v, ng, no, rep, B=3)
    n = len(o)
    oids = list(o)
    pool, tA = C.build_pool(tt, d, o, 3)
    cf = C.true_cost_fn(th)
    vc = C.vcg(pool, th, q, oids)
    gw = C.solve(C.restrict_pool(pool, [x["id"] for x in d if x["cls"] == "GW"]), cf, q, oids)
    od = C.solve(C.restrict_pool(pool, [x["id"] for x in d if x["cls"] == "OD"]), cf, q, oids)
    b1 = C.solve(C.filter_pool(pool, 1), cf, q, oids)
    statuses = vc["statuses"] + [gw["status"], od["status"], b1["status"]]
    total = time.perf_counter() - t_start
    wc = sum(vc["cost"].values())
    return [dict(variant=v, n=n, n_gw=ng, n_od=no, rep=rep, Z=vc["Z"], C_gw_only=gw["z"],
                 C_od_only=od["z"], C_B1=b1["z"], fd_rate=len(vc["full"]["fd_orders"]) / float(n),
                 vcg_rent=sum(vc["rent"].values()), winner_true_cost=wc, vcg_payout=vc["payout"],
                 pool_size=C.pool_size(pool), t_A=tA, t_C=vc["wall"], t_total=total,
                 n_solves=len(statuses), n_optimal=sum(1 for s in statuses if C.is_optimal(s)))]


RUNNERS = {"rq2": run_rq2, "rq34": run_rq34, "rq5": run_rq5}
KEYS = {"rq2": ("alignment", "n", "n_gw", "n_od", "rep"),
        "rq34": ("alignment", "n", "n_gw", "n_od", "rep"),
        "rq5": ("variant", "n_gw", "n_od", "rep")}


def main():
    which, shard, nsh = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    P = verify_lock()
    all_jobs = jobs(which, P)
    mine = [j for i, j in enumerate(all_jobs) if i % nsh == shard]
    out = os.path.join(C.OUT_DIR, "%s_shard%d.csv" % (which, shard))
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                done.add(tuple(str(r[k]) for k in KEYS[which]))
    fn = RUNNERS[which]
    writer, fh = None, None
    t0 = time.time()
    k = 0
    for j in mine:
        key = tuple(str(x) for x in j)
        if which == "rq5":
            key = (j[0], str(j[1]), str(j[2]), str(j[3]))
        if key in done:
            continue
        rows = fn(j, P)
        if fh is None:
            new = not os.path.exists(out)
            fh = open(out, "a", newline="", encoding="utf-8")
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            if new:
                writer.writeheader()
        writer.writerows(rows)
        fh.flush()
        k += 1
        if k % 10 == 0:
            print("[%s shard %d] %d/%d new done, %.1f min" % (which, shard, k, len(mine) - len(done),
                                                             (time.time() - t0) / 60.0))
            sys.stdout.flush()
    print("[%s shard %d] FINISHED %d jobs in %.1f min" % (which, shard, k, (time.time() - t0) / 60.0))


if __name__ == "__main__":
    main()
