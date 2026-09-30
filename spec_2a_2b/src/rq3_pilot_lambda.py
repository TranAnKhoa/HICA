"""RQ_Master.md §4.3 - pilot khoa lambda cho POSTED (instance rieng, tag
'rq3_pilot_lambda', KHONG trung instance main). Chon lambda co mean payout nho
nhat. Kem kiem tra G1a o n lon (loc pool B3 == sinh truc tiep B=1,2)."""
import json
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instance_gen as IG
import rq1_cost_gen as RC
import rq_common as C
from rq_gate import pools_equal

LAMS = [round(0.40 + 0.05 * k, 2) for k in range(13)]


def inst(align, n, n_gw, n_od, rep, B=3):
    cs, cb = C.corridor_for(align)
    gs = IG.stable_seed(n, n_gw, n_od, align, rep, "rq3_pilot_lambda")
    nd = n_gw + n_od
    d, o, tt, m = IG.generate_instance(n=n, B_gw=B, B_od=B, tw_width=C.TW_WIDTH, n_drivers=nd,
                                       seed=gs, tau=C.TAU, spatial_mode="dispersed",
                                       corridor_share=cs, corridor_buffer_km=cb,
                                       gw_od_ratio=n_gw / float(nd))
    th = RC.assign_theta(random.Random(gs + 1), d)
    return d, o, tt, th, RC.assign_q_o(o, tt)


def main():
    os.makedirs(C.OUT_DIR, exist_ok=True)
    payouts = {l: [] for l in LAMS}
    g1a_checks = g1a_fail = 0
    for align in [0.50, 0.90]:
        for n in [10, 15, 20]:
            for (ng, no) in [(2, 2), (3, 2), (2, 3), (3, 3)]:
                for rep in range(5):
                    d, o, tt, th, q = inst(align, n, ng, no, rep)
                    pool, _ = C.build_pool(tt, d, o, 3)
                    oids = list(o)
                    for l in LAMS:
                        payouts[l].append(C.posted(pool, th, q, oids, l)["payout"])
                    if rep == 0 and n >= 15:
                        for B in [1, 2]:
                            dB, oB, ttB, _, _ = inst(align, n, ng, no, rep, B)
                            pB, _ = C.build_pool(ttB, dB, oB, B)
                            g1a_checks += 1
                            if not pools_equal(C.filter_pool(pool, B), C.filter_pool(pB, B)):
                                g1a_fail += 1
            print("align=%.2f done" % align if n == 20 else "", end="")
            sys.stdout.flush()
    means = {l: statistics.mean(v) for l, v in payouts.items()}
    best = min(LAMS, key=lambda l: (means[l], l))
    print("\nlambda -> mean payout (120 pilot instance)")
    for l in LAMS:
        print("  %.2f  %.4f%s" % (l, means[l], "  <== chon" if l == best else ""))
    print("G1a (n>=15): %d fail / %d check" % (g1a_fail, g1a_checks))
    with open(os.path.join(C.OUT_DIR, "rq3_pilot_lambda.json"), "w") as f:
        json.dump(dict(lambda_grid=LAMS, mean_payout=means, chosen_lambda=best,
                       n_pilot_instances=len(payouts[LAMS[0]]),
                       g1a_large_n=dict(checks=g1a_checks, fails=g1a_fail)), f, indent=2)


if __name__ == "__main__":
    main()
