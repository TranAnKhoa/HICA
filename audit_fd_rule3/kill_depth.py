"""Where does Layer 3 fire inside C8?  For every rule kill we record |P(L)| = |IV|+|C| of the killed
label and whether L is already a complete route (IV empty). A kill at |P(L)| = B can only save the
remaining deliveries (and, for an occasional driver, the home leg), so it saves little work.
Writes ../audit_logs3/kill_depth.json and prints a table."""
import json
from collections import Counter

import paths  # noqa: F401
import variants3 as V3
from common import label_instance, LABEL_INSTANCES


def main():
    rows = []
    for B in (3, 4):
        for (n, nd, seed) in LABEL_INSTANCES:
            drivers, orders, tt, q = label_instance(n, nd, seed, B)
            by_depth = Counter()
            complete = 0
            tot = 0
            for dr in drivers:
                log = []
                V3.run_tier_rule(tt, dr, orders, B, q=q, rule=True, inloop=True, fire_log=log)
                for (l, j) in log:
                    tot += 1
                    by_depth[len(l.IV) + len(l.Cd)] += 1
                    if not l.IV:
                        complete += 1
            row = dict(tag="n%d_s%d" % (n, seed), B=B, kills=tot,
                       by_depth={str(k): v for k, v in sorted(by_depth.items())},
                       share_full=by_depth[B] / tot if tot else 0.0,
                       share_no_order_on_board=complete / tot if tot else 0.0)
            rows.append(row)
            print("%-9s B=%d kills=%7d  share at |P|=B: %5.1f%%  share with nothing on board: %5.1f%%  by |P|: %s"
                  % (row["tag"], B, tot, 100 * row["share_full"], 100 * row["share_no_order_on_board"],
                     row["by_depth"]))
    json.dump(rows, open("../audit_logs3/kill_depth.json", "w"), indent=1)


main()
