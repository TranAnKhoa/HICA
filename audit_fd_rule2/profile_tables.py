"""Table E: cProfile on n12_s42, B=3. Usage: python profile_tables.py C1 C4 C6 ..."""
import sys, cProfile, pstats, io, json
from variants import *

def prof(nm, tt, drivers, orders, q, B, reps=3):
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(reps):
        pool, per = build_all(nm, tt, drivers, orders, q, B)
        if nm not in INLOOP:
            kstar_pool(pool, q)
    pr.disable()
    st = pstats.Stats(pr)
    rows = []
    for (fn, ln, name), (cc, nc, tt_, ct, callers) in st.stats.items():
        short = "%s:%d %s" % (fn.replace("\\", "/").split("/")[-1], ln, name)
        rows.append((ct / reps, tt_ / reps, nc / reps, short))
    rows.sort(reverse=True)
    return rows

drivers, orders, tt, q = label_instance(12, 5, 42, 3)
out = {}
for nm in sys.argv[1:]:
    rows = prof(nm, tt, drivers, orders, q, 3)
    out[nm] = rows[:14]
    print("== %s : top 8 by cumulative time (seconds per full run, n12_s42 B=3, profiler overhead included)" % nm)
    for ct, tot, nc, name in rows[:8]:
        print("  %7.3f cum  %7.3f self  %9d calls  %s" % (ct, tot, nc, name))
    if nm in ("C6", "C7"):
        d = dict((r[3].split(" ", 1)[1], r) for r in rows)
        fdc = [r for r in rows if "fd_dominated" in r[3]]
        ab = [r for r in rows if "_absorption_A" in r[3]]
        if fdc and ab:
            print("  FD-dominance: total %.3f s (fd_dominated cum), of which absorption A %.3f s; subset lookups+tests ~ %.3f s"
                  % (fdc[0][0], ab[0][0], fdc[0][0] - ab[0][0]))
        out[nm + "_fd"] = dict(fd_total=fdc[0][0] if fdc else None, A=ab[0][0] if ab else None)
    sys.stdout.flush()
json.dump(out, open("../audit_logs2/profile.json", "w"), indent=1)
