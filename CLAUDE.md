# Instructions for Claude Code in this repository

- Benchmarks: read `BENCHMARK_GUIDE.md` first. Part A (the C5h scalability study) may be run as specified there.
  **Do not build, code or run any comparison benchmark in Part B (comparisons with other methods or papers) on your
  own initiative.** Before writing any code, ask the author in detail every question in section B.5 of that file and
  wait for the answers; then propose a short spec for approval.
- The final Algorithm A is C5h (`audit_fd_rule3/variants_h.py`); the label rule ("Layer 3") is not part of it
  (`T4_Proofs/T4_Combined_v3.pdf`).
- Repository clean-up: follow `REPO_CLEANUP_PLAN.md` phase by phase and stop at every **[ASK]** item. Algorithm A is
  locked to **C5h** (not C5s, which is slower). Project context: `MASTER_SUMMARY.md`.
