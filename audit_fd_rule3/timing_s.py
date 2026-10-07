"""Timing of C5s (= C5h + sequence dead-end test, variants_s.py) against C5h: label instances, shared travel-time table, 3 runs.
Writes nothing; output is saved to ../audit_logs3/timing_s.log."""
import sys, time, gc, statistics
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths  # noqa
import fastrule as FR
import variants_s as VS
from variants_s import build_all
from common import label_instance, sig, LABEL_INSTANCES
def tm(nm, f, d, o, q, B):
    gc.collect(); gc.disable(); t0 = time.perf_counter(); p, per = build_all(nm, f, d, o, q, B); x = time.perf_counter() - t0; gc.enable(); return p, per, x
for (n, nd, seed) in LABEL_INSTANCES:
    for B in (3, 4):
        d, o, tt, q = label_instance(n, nd, seed, B)
        TT, KK = FR.make_tables(tt, FR.node_ids(d, o)); f = FR.matrix_tt(TT)
        th, ts = [], []
        for r in range(3):
            ph, perh, x = tm("C5h", f, d, o, q, B); th.append(x)
            ps, pers, x = tm("C5s", f, d, o, q, B); ts.append(x)
        S = lambda per, k: sum(c.get(k, 0) for _, c in per.values())
        print("n%d_s%d B=%d C5h %.3f C5s %.3f x%.2f same=%s | ext %d -> %d | dead %d, seq tests %d kills %d" % (
            n, seed, B, statistics.median(th), statistics.median(ts), statistics.median(th)/statistics.median(ts), sig(ph)==sig(ps),
            S(perh,"ext_attempts"), S(pers,"ext_attempts"), S(perh,"killed_dead"), S(pers,"seq_tests"), S(pers,"killed_seq")), flush=True)
