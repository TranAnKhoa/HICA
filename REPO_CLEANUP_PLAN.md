# REPO_CLEANUP_PLAN: plan for tidying the HICA repository (for Claude Code on the author's machine, which has CPLEX)

> **Read this whole file before doing anything.** Then read, in this order: `MASTER_SUMMARY.md` (context of the whole
> project), `BENCHMARK_GUIDE.md`, `EXPERIMENT_REPORT_C8.md` (Section 0), and `T4_Proofs/T4_Combined_v3.pdf`
> (Section 2.7).
>
> Items marked **[ASK]** must be put to the author, and you must wait for the answer before doing them.
> Do not decide them yourself.

Written on 2026-10-10 in a cloud session (session ID `session_01PQkHJAP2DvVMbHcNKDNJGY`, branch
`claude/charming-ramanujan-ppzinr`).

---

## 0. LOCKED decision: Algorithm A = **C5h** (not C5s)

- **C5h** = event tiers + Layer 1 (label dominance) + **exact dead-end filter** + Layer 2 (Pareto per bundle) +
  **frontier computed inside the loop**. It is the **fastest** variant: 1.9–3.9× faster than production C1, and
  1.6–2.9× faster than C5. K\* is identical everywhere, and correctness is proved (T4 v3, Props 2–3).
  - Code: `audit_fd_rule3/variants_h.py` → `run_tier_h(..., inloop=True, rule_tables=None)`, wrapped as `run_c5h`.
- **C5s** (C5h + "deliverable in some order" test) is **SLOWER**: 0.70–0.84× of C5h. It must **not** be used as
  Algorithm A. (The author once wrote "C5s is the fastest"; that is a slip. The data are in
  `audit_logs3/timing_s.log`.)
- **Layer 3 (label rule, C8/C8h) and FD-dominance (C6/C7) are NOT part of Algorithm A.** Keep them only as evidence
  for the negative result, in the archive.

Lock it in code: the final Algorithm A has exactly one public function, `generate_routes(driver, orders, B, q,
theta_range)`, with **no flag** to switch on Layer 3 or other variants.

---

## 1. How to give this session's context to Claude Code on your machine

**Option A — continue this very conversation (teleport).** Claude Code supports moving a cloud session to the local
CLI. It carries the conversation history (whatever remains after automatic summarisation) and checks out the
branch.

```bash
cd <path to the local HICA checkout>     # the same repo, not a fork
git status                              # must be clean (or let Claude stash)
claude auth login                       # the same claude.ai account as the web session (not an API key)
claude --teleport session_01PQkHJAP2DvVMbHcNKDNJGY
# or: claude --teleport  (choose from the list); or type /teleport inside the CLI
```

Docs: https://code.claude.com/docs/en/claude-code-on-the-web.md ("Continue a cloud session in your terminal").
The handoff is one-way: what you do locally does not go back to the cloud session.

**Option B — start a fresh session (recommended for the clean-up, because this conversation is very long).**
`CLAUDE.md` is loaded automatically and points to the three files below. The first prompt can be:

> Read CLAUDE.md, MASTER_SUMMARY.md, BENCHMARK_GUIDE.md and REPO_CLEANUP_PLAN.md. Carry out REPO_CLEANUP_PLAN.md in
> order, phase by phase, and stop to ask me at every [ASK] item and at the end of every phase.

---

## 2. Rules that must not be broken

1. **Delete nothing.** Every move uses `git mv` (history is kept). Files that are no longer needed go to the archive
   folder (Section 4).
2. **Work on a new branch.**
   1. Bring in the latest work from this session:
      ```bash
      git fetch origin
      git checkout claude/charming-ramanujan-ppzinr
      git pull
      ```
   2. Create a snapshot tag and a working branch:
      ```bash
      git tag pre-cleanup-2026-10
      git checkout -b repo-cleanup
      ```
   3. Do **not** merge into `main` until the author approves. **[ASK]** whether this branch should first be merged
      into `main` (it has not been yet).
3. **No result may change.**
   - Do not edit the raw result files (`spec_2a_2b/results/**`). They may be moved, but keep their content
     byte-for-byte.
   - Do not edit the **pre-registration file** `spec_2a_2b/results/rq_all/rq_all_locked_params.json`. Its SHA-256 is
     checked by `rq_runner.py`. If you move it, update the path and keep its content and hash unchanged.
4. **Do not refactor without an equivalence test.** See Phase 4.
5. **Python version:** the paper used **Python 3.7 + CPLEX 12.10**. Code must stay 3.7-compatible: no `:=`, no
   `list[int]` / `dict[str, int]` types, no `match`.
   - **[ASK]** Does the author want to move to a newer Python and CPLEX? If yes, all timings must be re-run.
6. **Local-only folders** (git-ignored; they exist only on the author's machine): `Dataset/`, `Output/`,
   `Src_Cplex/`, `Sharing Economy Logistics/`, `Not Using (dont reed this folder)/`, `.venv-plots/`, `.paper_text/`.
   **Do not move or delete them without asking [ASK].**
7. Do not build comparison benchmarks (`BENCHMARK_GUIDE.md`, Part B) without asking first.
8. Commit after each phase with a clear message. Do not push unless the author says so **[ASK]**.

---

## 3. Target structure (proposal; **[ASK]** the author to approve it before Phase 3)

```
HICA/
├── README.md                     # for reviewers: install, how to reproduce each table/figure, expected times
├── CLAUDE.md                     # instructions for Claude Code (short)
├── requirements.txt              # numpy, pyyaml, matplotlib, ... (+ notes on CPLEX 12.10)
├── hica/                         # the main package; the paper's code lives here only
│   ├── config.py                 # constants (speed, kappa, Theta, TW, tau) + CPLEX path from environment variables
│   ├── data/
│   │   ├── instance_gen.py       # synthetic generator (from spec_2a_2b/src/instance_gen.py)
│   │   ├── cost_gen.py           # theta, q_o (from rq1_cost_gen.py)
│   │   └── rq_instances.py       # make_rq1_instance, make_rq5_instance (from rq_common.py)
│   ├── algorithm_a/              # = C5h, the ONLY version
│   │   ├── labels.py             # Label, try_pickup / try_delivery / try_home, finalize_KW (from t6_dp.py, t2_core.build_walk_nodes)
│   │   ├── dominance.py          # Layer 1 (_filter_dominated_labels, _dominates_label)
│   │   ├── dead_end.py           # dead-end filter (make_dead, variants_h.py)
│   │   ├── frontier.py           # Layer 2 (_bundle_front) + local frontier (post-hoc Procedure 1 and in-loop Prop 2)
│   │   └── generate.py           # generate_routes = run_tier_h(inloop=True), no variant flags
│   ├── algorithm_b/
│   │   └── wdp.py                # set-partitioning WDP: CPLEX (from t8_cplex.build_model/solve) + optional HiGHS backend
│   ├── algorithm_c/
│   │   ├── vcg.py                # naive Clarke pivots (from rq_common.vcg)
│   │   └── decomposition.py      # component decomposition (T5) - [ASK] keep in the package or move to archive
│   └── mechanisms/               # posted price, pay-as-bid best response (RQ3, from rq_common.py)
├── experiments/
│   ├── configs/                  # locked params (rq_all_locked_params.json, grid_*.yaml), UNCHANGED
│   ├── run_rq.py                 # = rq_runner.py (rq1, rq2, rq34, rq5)
│   ├── run_scale_study.py        # = audit_fd_rule3/scale_c5h.py
│   └── README.md
├── results/                      # raw results of the main runs (moved from spec_2a_2b/results/rq_all, content unchanged)
├── analysis/
│   ├── rq_analysis_all.py        # tables
│   └── plots/                    # = "Experimental Result/plots" (make_all.py → figures/)
├── figures/                      # generated figures
├── verification/                 # every correctness check for the proofs and the implementation (read-only for reviewers)
│   ├── README.md                 # check ↔ statement in the paper ↔ how to run ↔ expected result
│   ├── brute_force.py
│   ├── gates_algorithm_a.py      # merge gate_h.py + the useful part of gate_c8.py: K*(C5h) = K*(C1+frontier), R unchanged, hunt, brute force
│   ├── dead_end_audit.py         # no removed label has a feasible completion
│   ├── t4_synthetic_audit/       # audit of Theorems 1-2 (from T4_audit_scripts/T4_audit, only what Table "synthetic audit" needs)
│   ├── solver_crosscheck.py      # CPLEX vs HiGHS (check_highs.py)
│   └── logs/                     # logs of the audits cited in the paper (audit_logs3 gate_*.log, ...)
├── paper/
│   ├── Paper.tex
│   ├── T4_Proofs/                # T4_Combined_v3.tex/.pdf (v2 → archive)
│   └── thesis/                   # Thesis_IU_format - [ASK]
├── docs/                         # MASTER_SUMMARY.md, BENCHMARK_GUIDE.md, EXPERIMENT_REPORT*.md, Algorithm_A_Description.md, ...
└── _archive/                     # everything else (DO NOT READ). Keep the original folder structure inside it.
```

**[ASK] about the archive folder:** `.gitignore` already has `Not Using (dont reed this folder)/`, but that folder is
**ignored by git**: moving files there takes them out of the repo. The proposal is a **tracked** folder `_archive/`
plus one line in `CLAUDE.md` saying "do not read `_archive/`". Ask the author which they prefer.

---

## 4. Classification of the current folders (proposal; check every item against the actual imports)

| Current | Destination | Note |
|---|---|---|
| `spec_2a_2b/src/instance_gen.py`, `rq1_cost_gen.py`, `rq_common.py` (instance part) | `hica/data/` | generators used by the paper |
| `spec_2a_2b/src/rq_common.py` (solve, vcg, posted, pab_br) | `hica/algorithm_b/`, `hica/algorithm_c/`, `hica/mechanisms/` | split by role |
| `spec_2a_2b/src/dp_labeling.py` | `hica/algorithm_a/` (Layer 2 `_pareto_front`) + archive | the production wrapper (C1) is no longer the final version; keep a C1 copy in `verification/` for comparison |
| `experiments/T2BFS/t6_dp.py`, `t2_core.py`, `t4_profile.py` (only the parts used) | `hica/algorithm_a/labels.py` | **remove the dependency `t6_dp → t2_gen → Dataset`** (only the constant `SPEED_KMH` is needed) |
| `experiments/T2BFS/t8_cplex.py` (build_model, solve_model, solve_wdp) | `hica/algorithm_b/wdp.py` | **remove the hard-coded path `K:\Programing Hardware\Cplex...`** → environment variable `CPLEX_PYTHON_PATH` |
| `audit_fd_rule2/variants.py` (`_bundle_front`, `_kstar_filter_bundle`) + `audit_fd_rule3/variants_h.py` (`run_tier_h`, `make_dead`) | `hica/algorithm_a/` | the heart of C5h |
| `spec_2a_2b/src/kstar_zstar_payment_check.py` (`prune_pool_by_kstar`), `T4_audit_scripts/T4_audit/kstar_rule.py` | `hica/algorithm_a/frontier.py` (post-hoc procedure) | check which file the main runs actually import |
| `spec_2a_2b/src/rq_runner.py`, `rq_gate.py`, `rq_analysis_all.py`, `rq1_*.py` (those still used) | `experiments/`, `analysis/` | |
| `spec_2a_2b/config/`, `spec_2a_2b/results/rq_all/rq_all_locked_params.json` | `experiments/configs/` | **content unchanged** |
| `spec_2a_2b/results/rq_all/*.csv` | `results/rq_all/` | raw data of the paper |
| `spec_2a_2b/results_prepatch_od_bug/` (14 MB) | `_archive/` | results before the OD bug fix |
| `spec_2a_2b/src/test_*.py`, `debug_*.py`, `research_*.py`, `convex_hull_*.py`, `viec*_*.py`, `run_2a*.py`, `run_2b*.py`, `probe_scaling.py`, ... | `_archive/` (or `verification/` if a check is cited in the paper) | **[ASK]** for anything unclear |
| `spec_2a_2b/src/brute_force.py`, `feasibility_gate.py`, `kstar_gridcheck_rq1.py`, `kstar_rq1_crosscheck.py`, `q1_solver_crosscheck.py` | `verification/` | checks that support the paper |
| `audit_fd_rule/`, `audit_fd_rule2/`, `audit_fd_rule3/` | split: the C5h core → `hica/`; `gate_h.py`, `gate_c8.py` (K\* part), `check_highs.py`, `brute_force` → `verification/`; `scale_c5h.py` → `experiments/`; `wdp_highs.py` → `hica/algorithm_b/` (backend); the rest (C3, C6–C8, C8f, C5s, timing/profile scripts) → `_archive/` | keep the timing scripts behind the C5h vs C1 table **[ASK]**: `verification/` or `experiments/timing/` |
| `audit_logs/`, `audit_logs2/`, `audit_logs3/` | the logs cited in the paper/report → `verification/logs/`; the rest → `_archive/` | |
| `T4_audit_scripts/T4_audit/` (many raw outputs, scripts) | the parts behind the "Synthetic audit" table → `verification/t4_synthetic_audit/`; the rest → `_archive/` | |
| `experiments/T2BFS/` (t3_*, t4_run_*, t5_*, t61_*, t62_*, t7_*, t8_run/gen/core, csv), `experiments/T4/` | `_archive/` (except the files moved into `hica/`) | |
| `Experimental Result/plots/` | `analysis/plots/` | update `discover.py` / `data.py` to the new paths |
| `Experimental Result/figures/` | `figures/` | `fig04_label_rule.*` → `_archive/` (Layer 3 is gone) |
| `Paper.tex`, `T4_Proofs/T4_Combined_v3.*` | `paper/` | `T4_Combined_v2.*` → `_archive/` |
| `Thesis_IU_format/` | `paper/thesis/` **[ASK]** | |
| `MASTER_SUMMARY.md`, `BENCHMARK_GUIDE.md`, `EXPERIMENT_REPORT*.md`, `Algorithm_A_Description.md` | `docs/` | update the paths inside these files |
| `Guideline*/`, `Test_EJOR_direction/`, `New_t4/`, `AlgorithmA_Test/`, `Master_Thesis_Q1.md`, `Master_writeup.md`, `Audit.md`, `AUDIT_REPORT.md`, `Compare_result.md`, `HICA_Crosscheck_Comments.md`, `Timeline_and_Results_so_far.md`, `guideline_paper_summarize.md`, `main_guideline.md` | `_archive/notes/` **[ASK]** | working notes and old specs; reviewers do not need them |

---

## 5. Phases

### Phase 1 — Survey (do not edit anything)

1. `git fetch && git checkout claude/charming-ramanujan-ppzinr && git pull`; tag and create the branch (Rule 2).
2. Check the environment:
   ```bash
   python --version
   python -c "import cplex; print(cplex.__version__)"
   ```
   Check numpy, and that `Dataset/` exists locally.
3. **Build the actual import graph** for the code paths used by the paper:
   - `rq_runner.py` (rq1/rq2/rq34/rq5);
   - `Experimental Result/plots/make_all.py`;
   - `audit_fd_rule3/variants_h.py`, `scale_c5h.py`, `gate_h.py`.

   Use static analysis (for example `python -X importtime`, or a script that walks `import` statements). Write
   `docs/IMPORT_MAP.md`: which file is used by which entry point, and which file is used by none (an archive
   candidate).
4. Compare with the table in Section 4, and report the differences to the author. **Stop and [ASK]** for the target
   structure to be approved.

### Phase 2 — Reference snapshot (before any refactor)

Run the old code and save the reference results to `verification/reference/` (JSON):

- K\* per driver of **C5h** (old code) for:
  - the 5 label instances × B=3,4;
  - 20 main-grid instances (n=15, (3,3), alignment 0.90/0.50, reps 0–9);
  - 80 random instances (n=6..9, seeds 100–119);
  - brute force n=5,6, seeds 0–2.
- Z and the total payout (CPLEX) on the 48 instances of `audit_fd_rule3/check_highs.py` (rq34 reps 0–1). They must
  match `spec_2a_2b/results/rq_all/rq34_shard*.csv` to within 1e-9.
- (Optional) Time C1 and C5h on the 10 label configurations, to compare with the paper's table.

### Phase 3 — Move files (no logic changes)

1. `git mv` following the approved structure. Update imports and paths.
2. Remove every `sys.path.insert` that hard-codes a Windows path. Use package imports (`from hica.algorithm_a import
   ...`) and a simple `pyproject.toml` / `setup.py` (`pip install -e .`).
3. Move the CPLEX path into an environment variable (`CPLEX_PYTHON_PATH`) and describe it in the README.
4. After this phase: re-run Phase 2 → it must be **identical** to the reference. Commit.

### Phase 4 — Clean up Algorithm A (= C5h) into its own module

1. Write `hica/algorithm_a/generate.py::generate_routes` from `run_tier_h` (inloop=True, no rule), keeping the logic
   exactly: event tiers, Layer 1 per tier, `try_delivery` → dead-end check (except a GW label with nothing on board),
   `try_home` for OD, `try_pickup` if |IV|+|C|<B → dead-end check, Layer 2 + in-loop frontier when m is even and ≥2.
2. Remove the counters used only for experiments (or keep them behind a `stats=None` parameter).
3. Keep the old C1 (production) code in `verification/` for comparison (it does not need to be cleaned).
4. **Equivalence test:** `verification/test_equivalence_algorithm_a.py` must show that the new `generate_routes` gives
   K\* (bundle, K, W) **identical** to the Phase 2 reference on every instance listed there. Bit-identical is
   expected; if not, the tolerance is 1e-12 and you must report why.
5. Re-run Z/payout on the 48 instances with CPLEX. They must be identical. Commit.

### Phase 5 — Format the code

1. **[ASK]** Choose the tool: `ruff format` + `ruff check` (recommended) or `black`. Line length (100?).
2. Standardise:
   - module docstrings in English (what the file does, which proposition/table of the paper it serves);
   - remove dead code and commented-out code;
   - clear names.

   **[ASK]** Should the Vietnamese comments be translated into English?
3. Formatting must not change the results: re-run the equivalence test after formatting.

### Phase 6 — Documentation for reviewers

1. **`README.md`:**
   - installation (Python 3.7, CPLEX 12.10, `pip install -e .`);
   - folder structure;
   - **a table mapping each table/figure in the paper → command → result file → expected time**;
   - how to run the checks (`verification/README.md`);
   - the scale study (`BENCHMARK_GUIDE.md`, Part A).
2. **`verification/README.md`:** each check → which statement of the paper it supports (Theorem 1(a)(b), Theorem 2,
   Prop 2 in-loop frontier, Prop 3 dead ends, Corollary 1 VCG) → command → expected result (for example "0
   mismatches", "1,157/1,157").
3. Update `CLAUDE.md` (short, under 60 lines): new structure, "Algorithm A = C5h, locked", "do not read `_archive/`",
   "ask before building Part B benchmarks", and point to `docs/MASTER_SUMMARY.md`.
4. Update the paths in `docs/MASTER_SUMMARY.md` and `docs/BENCHMARK_GUIDE.md`.

### Phase 7 — Final check

1. In a **brand-new clone** (`git clone` into another folder): install, then run the quick checks
   (`verification/` brute force + equivalence on the 5 label instances, a few minutes), then reproduce one paper table
   (for example the 10-row C5h vs C1 table), then `analysis/plots/make_all.py` on the existing results.
2. Report to the author:
   - the summary tree;
   - the list of files moved into `_archive/`;
   - the results of the equivalence tests;
   - the [ASK] items still open.

---

## 6. Points to watch (things that are easy to get wrong)

- `t6_dp.py` imports `t2_gen` → `Dataset` (the private Atlanta package). In the cloud this was worked around with a
  stub (`audit_fd_rule3/_stubs/Dataset`). Once cleaned, Algorithm A **must not depend on `Dataset`**. If the Atlanta
  data are used for the paper, keep them in `hica/data/` as an optional loader **[ASK]**.
- `audit_fd_rule/common.py` and `fdrule_dp.py` hard-code `K:\Data Science\Q1 Research`. They belong to Layer 3 →
  archive.
- `rq_runner.py` imports `kstar_zstar_payment_check.prune_pool_by_kstar` from `T4_audit_scripts/T4_audit` (through a
  `sys.path` hack). Check which file actually contains the function used in the main runs.
- The figure `fig04_label_rule` and `tab:label` in `Paper.tex` belong to Layer 3. They are listed in
  `MASTER_SUMMARY.md`, Section 12 (the checklist for editing the paper). **Editing `Paper.tex` is a separate task.**
  Do not edit it in this clean-up unless the author asks.
- The main paper runs used **production Algorithm A (C1)**, not C5h. K\* is identical, so the economic results do not
  change. **[ASK]** Should the RQs be re-run with C5h to update the times, or should the C1 times stay plus a C5h vs
  C1 table?
- Do not commit `__pycache__`, `.venv*`, or large outputs. Check `.gitignore`.
