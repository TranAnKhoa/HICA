"""Figure.md §0.3 — sanity checks. A figure is saved only if all its checks pass; failures are
appended to figures/CHECK_FAILURES.md. Expected values are never edited to match data."""
import datetime
import os

from style import FIG_DIR

FAIL_PATH = os.path.join(FIG_DIR, "CHECK_FAILURES.md")
MISSING_PATH = os.path.join(FIG_DIR, "MISSING.md")


def reset_logs():
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(FAIL_PATH, "w", encoding="utf-8") as f:
        f.write("# CHECK_FAILURES\n\nRun %s. Empty list below = every sanity check passed.\n\n" % stamp)
    with open(MISSING_PATH, "w", encoding="utf-8") as f:
        f.write("# MISSING\n\nRun %s. Figures (or series) that could not be drawn from existing "
                "data without estimating, re-solving or reading excluded folders.\n\n" % stamp)


def missing(fig, what, looked_in, note=""):
    with open(MISSING_PATH, "a", encoding="utf-8") as f:
        f.write("## %s\n- Needs: %s\n- Looked in: %s\n%s\n" % (fig, what, looked_in,
                ("- Note: %s\n" % note) if note else ""))


class Checker:
    """close(): pass if |got-exp| is within the rounding of the printed expected value
    (0.5·10^-dec) or within the spec tolerance (0.01 points for %, 1% relative for times)."""

    def __init__(self, fig):
        self.fig, self.fails, self.n = fig, [], 0

    def close(self, name, got, exp, dec, kind="pct"):
        self.n += 1
        diff = abs(got - exp)
        ok = diff <= 0.5 * 10 ** (-dec) + 1e-12
        if not ok:
            ok = diff <= 0.01 + 1e-12 if kind == "pct" else diff <= 0.01 * abs(exp) + 1e-12
        if not ok:
            self.fails.append("%s: got %.6g, expected %s (dec=%d, kind=%s)" % (name, got, exp, dec, kind))
        return ok

    def true(self, name, cond, detail=""):
        self.n += 1
        if not cond:
            self.fails.append("%s: FALSE %s" % (name, detail))
        return cond

    def ok(self):
        if self.fails:
            with open(FAIL_PATH, "a", encoding="utf-8") as f:
                f.write("## %s\n" % self.fig + "".join("- %s\n" % m for m in self.fails) + "\n")
        return not self.fails

    def summary(self):
        return "%d/%d" % (self.n - len(self.fails), self.n)
