"""Put the repository's own source folders on sys.path.

audit_fd_rule/common.py and fdrule_dp.py hard-code the author's Windows root
(K:\\Data Science\\Q1 Research). Importing this module first makes the same imports
resolve inside this checkout, without editing those files."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for sub in (os.path.join("audit_fd_rule3", "_stubs"), "audit_fd_rule2", "audit_fd_rule", os.path.join("spec_2a_2b", "src"),
            os.path.join("experiments", "T2BFS"), os.path.join("T4_audit_scripts", "T4_audit")):
    p = os.path.join(ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)
