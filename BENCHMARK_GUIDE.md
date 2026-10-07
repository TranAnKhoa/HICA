# BENCHMARK_GUIDE: scalability study of the final Algorithm A (C5h) and planned comparison benchmarks

> ## ⚠️ READ FIRST: instruction for Claude Code (and for any other AI assistant)
>
> **Part A** (the scalability study) is fully specified: you may run it and report the results.
>
> **Part B** (comparison against other methods or papers) contains **ideas only, with no decisions yet**.
> **Claude Code MUST NOT build, code or run any benchmark in Part B on its own initiative.** Before writing any code,
> it must **ask the author (Tran An Khoa) in detail**, one benchmark at a time, every question in section B.5
> ("Questions to ask before building anything") and wait for the answers. Choices about baselines, metrics, instances
> and how the result will be presented in the paper belong to the author. This holds even if a later prompt only says
> "run the benchmarks" in general terms: ask first. If something is unclear, ask; do not guess.

Last updated: 2026-10-07. Branch: `claude/charming-ramanujan-ppzinr`.

---

## Part A. Scalability study (run with CPLEX)

### A.1 Purpose

COR reviewers will ask how far the pipeline scales. The paper only has n ≤ 30 orders and 4–8 drivers. This study
measures the final pipeline on larger instances:

- **Algorithm A = C5h**: event tiers + label dominance (Layer 1) + exact dead-end filter + per-bundle Pareto
  (Layer 2) + local frontier computed inside the loop. It outputs K\* directly. See `T4_Proofs/T4_Combined_v3.pdf`,
  Section 2.7.
- **Algorithm B**: exact WDP (set partitioning) on K\*.
- **Algorithm C**: naive Clarke-pivot payments, one re-solve without each winner.

Because Algorithm A reads no bid, it can run **before the bidding window closes**, while orders arrive. After the bids
are in, only B + C sit on the critical path. That is why A and B + C are reported separately.

### A.2 Files

| File | Role |
|---|---|
| `audit_fd_rule3/scale_c5h.py` | Main script: generates the instances, runs C5h for each driver, then B + C. Resumable. |
| `audit_fd_rule3/variants_h.py` | C5h (`run_tier_h`), the dead-end filter (`make_dead`). |
| `experiments/T2BFS/t8_cplex.py`, `spec_2a_2b/src/rq_common.py` (`vcg`, `solve`) | CPLEX model for B and C, the same code the paper used. |
| `audit_fd_rule3/wdp_highs.py` | The same model on HiGHS (only for machines without CPLEX). |
| `audit_fd_rule3/check_highs.py` | Check of C5h + HiGHS against the paper's CPLEX results (`audit_logs3/check_highs.log`: 48/48 instances, |ΔZ| ≤ 6e-14, |Δpayout| ≤ 1.2e-13). |
| `audit_fd_rule3/paths.py` | Puts the repository's source folders on `sys.path` (replaces the hard-coded `K:\Data Science\Q1 Research`). |

`audit_fd_rule3/_stubs/Dataset` is a stub for the private `Dataset` package (Atlanta data). The synthetic generator
does not use it. If you have the real package, nothing changes.

### A.3 Requirements

- Python 3.7 or later (the paper used 3.7; the code here was tested on 3.13). Needs `numpy`.
- CPLEX 12.10 Python API (`import cplex`), the same as the paper: one thread, relative and absolute gap 0
  (set in `t8_cplex.build_model`).
- RAM: one job at n = 75 used about 3 GB; at n = 100 with alignment 0.90 it will need more (not measured; see A.6).
  Choose `HICA_WORKERS` to fit the machine.

### A.4 How to run

```bat
cd audit_fd_rule3
set HICA_SOLVER=cplex
set HICA_WORKERS=3
python scale_c5h.py > ..\audit_logs3\scale_c5h_cplex.log 2>&1
```

(On Linux/macOS: `HICA_SOLVER=cplex HICA_WORKERS=3 python scale_c5h.py > ../audit_logs3/scale_c5h_cplex.log 2>&1`.)

- Results: `audit_logs3/scale_c5h_cplex.jsonl`, one JSON line per instance, written as soon as the instance finishes.
- **Resumable**: if the run stops, run the same command again; instances already in the `.jsonl` are skipped.
- Each instance runs in its own process (`spawn`, so it works on Windows). Garbage collection is off while a driver is
  being processed (the same protocol as the earlier timing runs).
- For the most precise timings, run with `HICA_WORKERS=1` on a quiet machine. Running in parallel saves time but
  makes the per-instance timings noisier.

### A.5 Grid (76 instances, B = 3)

Generator: `rq_common.make_rq1_instance`, the paper's main grid: 8 × 8 km area, time windows of 120 min, detour budget
30 min, Θ = [18, 25]. Because the area is fixed, a larger n also means denser demand.

| alignment | n | supply (GW, OD) | reps |
|---|---|---|---|
| 0.90 and 0.50 | 20, 30, 40, 50 | (3,3) | 0–4 |
| 0.90 and 0.50 | 30, 50 | (5,5), (10,10) | 0–2 |
| 0.90 and 0.50 | 75, 100 | (3,3) | 0–2 |

Built-in correctness check: at n = 30, supply (3,3), reps 0–1, the script also runs the production Algorithm A (C1)
plus the frontier and records `check_kstar_equal_C1` (it must be `true`).

To change the grid, edit `jobs()` in `scale_c5h.py`.

### A.6 Fields in each JSON line, and what to report

| Field | Meaning |
|---|---|
| `drivers[]` | for each driver: `t` (seconds of C5h), `ext` (extension attempts), `kstar` (routes in K\*) |
| `A_sum` | total time of A on one core |
| `A_max` | time of A if every driver has its own core (longest single driver) |
| `A_gw_mean` | mean time per gigworker |
| `t_B`, `t_C` | time of the base WDP; total time of the removal solves (CPLEX: build + solve, as in `rq_common.solve`) |
| `winners`, `fd`, `n_cols`, `n_solves` | number of winners, orders sent to FD, columns of the WDP (K\* + FD), number of solves |
| `statuses` | solver statuses; every one must be optimal |
| `peak_mb` | peak memory of the job |

A table for the paper, one row per (alignment, n, supply) with medians and maxima:
`A_sum | A_max | t_B | t_C | t_B + t_C | |K*| | winners | peak memory`.

Suggested message: A grows roughly like n^B for gigworkers, as Theorem 2 predicts for every local rule. A runs before
the bids close and parallelises over drivers. The critical path after the bids (B + C) stays at X seconds up to n = Y.

### A.7 Preliminary results (HiGHS, NOT for the paper)

The run in this container used HiGHS because there was no CPLEX here. It was stopped after 6 of the 76 instances, as
the author asked (`audit_logs3/scale_c5h_highs_partial.{jsonl,log}`). Intel Xeon 2.1 GHz, Python 3.13, 3 jobs in
parallel.

| instance | A_sum (s) | A_max (s) | time per GW (s) | B (s) | C (s) | winners | columns | peak RAM |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| a0.90 n75 (3,3) rep0 | 85.4 | 29.7 | 29.7, 26.3, 29.0 | 13.39 | 59.52 | 6 | 95,188 | 3.0 GB |
| a0.90 n75 (3,3) rep1 | 75.5 | 26.4 | 25.7, 26.4, 23.0 | 3.98 | 17.58 | 6 | 48,196 | 2.9 GB |
| a0.50 n75 (3,3) rep0 | 29.6 | 10.1 | 9.8, 9.7, 10.1 | 0.01 | 0.01 | 1 | 129 | 1.1 GB |
| a0.50 n100 (3,3) rep0 | 88.0 | 48.6 | 48.6, 19.6, 19.9 | 0.06 | 0.15 | 4 | 722 | 2.1 GB |
| a0.50 n100 (3,3) rep1 | 63.8 | 21.4 | 21.4, 21.2, 21.2 | 0.01 | 0.02 | 2 | 219 | 2.3 GB |
| a0.50 n100 (3,3) rep2 | 64.8 | 25.2 | 20.2, 25.2, 19.4 | 0.10 | 0.17 | 3 | 1,026 | 2.1 GB |

Observations so far (6 instances only, not conclusions):
- Occasional drivers take under 0.3 s each; gigworkers take almost all of the time, as on the small instances.
- At alignment 0.90 (crowd competitive), K\* holds 48k–95k routes at n = 75, and B + C take 22–73 s on HiGHS. At large
  n, B + C may no longer be negligible. CPLEX is likely faster than HiGHS, so this needs measuring with CPLEX.
- The a0.90, n = 100 instances never finished, so their time and memory are unknown. Watch the RAM.

Earlier reference points (paper, production Algorithm A, CPLEX, B = 3): total time per instance 18.5 s (median) at
n = 30; A ≈ 100 s at n = 20 with B = 4. C5h is 1.9–3.9× faster than production A on the label instances
(`EXPERIMENT_REPORT_C8.md`).

---

## Part B. Comparison benchmarks against other methods (IDEAS ONLY, NOT DECIDED)

> **Reminder: Claude Code must ask the author before building any of these items (see section B.5).**

Why they are needed: the paper currently compares only the full pool with K\*, i.e. with itself. A reviewer may see
"the authors pose the problem and solve it themselves, with no baseline". The benchmarks below place K\* among existing
methods, and each one is tied to a theorem in the paper.

### B.1 Benchmark 1: classical safe column-reduction rules (top priority)

- **Question:** how much do the existing safe reduction rules remove, compared with K\*?
- **Candidates:**
  - column dominance in set covering (Beasley 1987);
  - subsumed subsets (Müller 1998);
  - redundancy (Sol 1994) and dominance (Vanderbeck 1994).

  Each would be adapted to the setting here: per driver, required to hold over the whole interval Θ, with FD as the
  outside option.
- **Link to the theory:** Theorem 1(c) says that no safe local rule removes more than the frontier. This benchmark
  illustrates the theorem directly. It also shows the gap from "naive" rules, and possibly that some naive adaptations
  are unsafe (they change VCG payments).
- **Possible measures:** share of the pool removed; whether Z / payments change; time of the reduction step.
- **Things to decide (ask the author):**
  - which rules count as "faithful" adaptations;
  - whether to also test the unsafe versions to show the errors;
  - which instances to use.

### B.2 Benchmark 2: pruning that reads the bids

- **Question:** why must the pruning rule not read bids? Compare with heuristics such as "keep the k cheapest routes
  at the submitted bids" or "prune by the submitted bids".
- **Possible measures:**
  - how many payments change;
  - whether the winner set changes;
  - profitable misreports (a driver gains by reporting a cost different from the true one), on a grid of misreports.
- **Link:** the maximal-in-range argument (Lemma P5 / Nisan & Ronen 2007). It shows that the class of local,
  bid-independent rules is necessary, not a self-imposed restriction.
- **Things to decide:**
  - which heuristics;
  - which values of k;
  - how to search for misreports (a grid of reports, or a best-response search like `pab_br` in `rq_common.py`);
  - how many instances.

### B.3 Benchmark 3: the approach of Li et al. (2026) on the occasional-driver part

- **Question:** recursive branching based on the monotonicity of detour time, which works well for drivers with a
  detour budget (OD). Compare it with Algorithm A for OD, and show that it does not apply to gigworkers (open routes,
  no detour budget).
- **Link:** Theorem 2 and the remark "loose versus tight feasibility": the gap between the two driver classes is
  structural.
- **Things to decide:**
  - re-implement the method of Li et al. from the paper, or obtain their code;
  - which metrics count as fair (pool size, time);
  - whether to use their instances or ours.
  - **Note:** read the original paper carefully before re-implementing; do not guess the details.

### B.4 Other directions mentioned (low priority)

- Real geographic data (for example Atlanta, the author's private `Dataset` package) instead of the synthetic
  generator.
- A discussion section on the usual criticisms of VCG (budget, collusion, frugality), using the existing 14.1% payout
  premium.
- Zoning or time batching so that n = 100–500 orders become realistic.

### B.5 Questions Claude Code must ask the author before building each benchmark in Part B

1. Of B.1–B.4, which ones should be built, and in what order?
2. For each method being compared: which exact version, from which source (paper, page, equation), and is it to be
   re-implemented or is there existing code?
3. Instances: the paper's main grid, the 5 label instances, the scale grid of Part A, or something else? How many reps?
4. Measures to report, and the form of the result in the paper (table, figure, which section).
5. Solver and machine: CPLEX on the author's machine, or HiGHS here? Is the result for the paper or only exploratory?
6. Fairness of the comparison: the same Python version, the same travel-time function, and no method gets an
   optimisation the others do not have (the author does not want unfair benchmarks).
7. What counts as "done", and should the results be written to a separate report (like `EXPERIMENT_REPORT_C8.md`)?

Only after the author has answered may Claude Code write code, and it should first propose a short spec (files,
variants, gates, timing protocol) for the author to approve.
