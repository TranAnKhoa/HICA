"""FIG 1 [M] — pool growth per driver, GW vs OD. Requires route counts split by driver class,
which no stored file has: D3 (pool_size) and D5 (pool_full/pool_kstar) store the TOTAL pool per
instance only. Per Figure.md §0.2 the figure is not drawn and not approximated."""
from checks import missing

NAME = "fig01_pool_growth"


def run():
    missing(
        "FIG 1 — fig01_pool_growth.pdf",
        "routes per driver split by class (GW / OD), menus B3 and B4, per instance and n",
        "D3 `rq2_shard*.csv` (column `pool_size` = total over all drivers); "
        "D5 `rq34_shard*.csv` (`pool_full`, `pool_kstar` = totals); D7 has per-driver rows but "
        "only emptiness flags, no route counts",
        "Partial alternative exists but was NOT used: `spec_2a_2b/results/rq1_pool_size_check.log` "
        "has mean *bundles* (not routes) per driver by class, B3 only, alignment 0.70/0.90 only. "
        "Obtaining per-class route counts needs re-running Algorithm A (forbidden by §0.1). "
        "Decision for the user: (i) re-run Algorithm A with a per-driver pool-size logger, or "
        "(ii) plot bundles/driver from the log with a caption saying so, or (iii) drop FIG 1.")
    return "MISSING", None


if __name__ == "__main__":
    print(run()[0])
