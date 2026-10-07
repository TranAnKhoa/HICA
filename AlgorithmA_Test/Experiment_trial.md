# EXPERIMENT: can Algorithm A be made faster by (A) event-count tiers + in-loop frontier, or (B) FD-dominance between real labels?

> **Cách dùng (Vietnamese):** đặt file này ở thư mục gốc repo (cùng chỗ với `AUDIT_REPORT.md`), mở Claude Code và gõ:
> `Đọc EXPERIMENT_TIERS_AND_FD_DOMINANCE.md và làm lần lượt từng phase. Dừng ở các điểm STOP để báo cáo.`
> Mục tiêu: so sánh thời gian chạy **Algorithm A** của các cách mới với cách cũ (C1), và chỉ báo "nhanh hơn" khi K\* giống hệt.

---

## 0. Context

The previous audit (`AUDIT_REPORT.md`) established:

- **C1** = production Algorithm A: Layer 1 (label dominance, key `(v, IV, C)`, compare `(t, K, W)`) + Layer 2 (per-bundle Pareto), then post-hoc `Frontier` -> `K*`.
- **C2** = rule `RuleFires` called on every newly created label (before it joins the queue), with per-label shortcut triples. It cut extensions by 15–43% but was **slower** (median total ratio C1/C2 = 0.68 at B=3, 0.52 at B=4); 66% of C2 time was in `accept()`.
- `K*` was identical in C1 and C2 everywhere tested. The C2 pool is **not** a subset of the C1 pool.
- `Frontier` (`t_F`) is only 3–6% of total time at n <= 15 (up to 15% at alignment 0.50).

This experiment tests **two new ideas and one variant of C2**. Everything is compared against **C1** (the old way).

### Terminology (do not mix up)
- **R** = pool after Layers 1+2. **K\*** = output of `Frontier` (exact). **U** = whatever pool a variant hands to `Frontier`; we want `K* subseteq U subseteq R`-like behaviour but U need **not** be a subset of R (see audit Section 4).
- `RuleFires` = approximate label-level test (T = {j} only). `Frontier` = exact route-level filter. They are different.
- "event" = one pickup or one delivery; for an occasional driver the final home leg is an extra event.

### The three ideas

**Idea 1 (variant of C2, "C3"): lazy rule.** Run `RuleFires` only on labels that **survived** `FilterDominated`. Shortcut triples are computed lazily at survival time from the parent's triples (the parent is always a survivor, because only survivors are expanded).

**Idea 2 (Method A): event-count tiers + in-loop frontier.**
- *2a ("C4")*: process labels in tiers by number of events `m = |IV| + 2|C|`. Two labels with the same key `(v, IV, C)` always have the same `m`, so every pair with the same key is compared in the **same** batch. (Conjecture to verify, Phase 1: in the current loop, labels with the same key can land in different batches, so some dominance comparisons are never made.)
- *2b ("C5")*: with tiers, all routes of bundle size `k` are complete when tier `2k` has been processed (for ODs, the home-leg step of tier `2k`). Then, per bundle: Pareto-filter, test frontier membership using only `K*` routes of **smaller** bundles (plus the empty route), keep only `K*`. Never store `R`. Output: `K*` directly.

**Idea 3 (Method B, "C6" / "C7"): FD-dominance between real labels.** Compare a label `L2` with an **already generated label** `L1` instead of with a virtual shortcut.

> Discard `L2` (and all its extensions) if there is a surviving label `L1` such that
> 1. `L1` and `L2` have the same node `v` and the same `IV`;
> 2. `C1` is a **proper subset** of `C2`; let `T = C2 \ C1`;
> 3. `t1 <= t2`;
> 4. `(K2 - K1) + theta_low * max(0, (t2 - t1) - A) / 60  >=  q(T)`,
>    where `A = max(0, max_{w in F(L2)} (e_w - t1 - tau(v, w)))`, `F(L2)` as in the manuscript (pickups reachable from `L2`, deliveries of orders on board, deliveries of orders whose pickups lie in `F`), `e_w` the opening time of stop `w`, `theta_low = 18`.

Proof sketch (**NOT proven; passing tests is not a proof, do not state it as a theorem anywhere**): every feasible continuation `sigma` of `L2` is also feasible after `L1` (same `v`, same `IV`, `t1 <= t2`, `|C1| < |C2|` so the bundle cap is respected, `T` is untouched in `L1` and never touched by `sigma`). `L1.sigma` serves the bundle minus `T`. By the absorption lemma applied from the same node (no junction term needed), `W(L2.sigma) - W(L1.sigma) >= max(0, (t2-t1) - A)/60`, and the distance difference is exactly `K2 - K1`. So `c(L2.sigma) >= c(L1.sigma) + q(T)` for every `theta >= theta_low`, hence every route through `L2` has a "subroute + FD" substitute and lies outside `K*`. `L1` may itself be dominated or discarded later; only feasibility of the prefix `L1` matters.

Implementation hint for C6: do **not** scan a bucket. For each proper subset `C1` of `C2` (at most `2^B - 1` subsets), look up key `(v, IV, C1)` in a dict of **survivors from earlier tiers** and test its Pareto list. Run the test only on survivors of `FilterDominated` (this is the lazy idea again). Compute `A` only if the test passes with `A = 0`.

## 1. Ground rules (same as the previous audit, plus fairness)

1. Phases 1–2 are read-only on tracked files. All new code goes in `audit_fd_rule2/`, on a new branch `exp-tiers-fd-dominance` created from the `audit-fd-rule` branch. Never merge, never push.
2. `sha256sum` of both locked parameter files before and after; they must match. Do not touch results directories, the instance generator or seeds.
3. **Fairness rule:** every variant must reuse the **same** `_try_pickup / _try_delivery / _try_home`, the same data structures and the same dominance code as C1. Any micro-optimisation you make for a variant must also be applied to C1 (and the speed-ups of C1 reported separately). Otherwise the comparison is void.
4. **No claim of speed-up unless the equality gate (Phase 4) passes.** If the gate fails, stop and report the counterexample.
5. Do not fabricate. Every claim needs `path:line` or a saved log. Unknown = `UNKNOWN`.
6. Do not tune any parameter to improve a result. Do not run the full 1,500-instance grid.
7. Save all raw output to `audit_logs2/`.
8. Do not edit the `.tex` file.

## 2. Phase 1 — Structure of today's loop (read-only) and the ceiling

### 1.1 Describe `run_dp` (`spec_2a_2b/experiments/T2BFS/t6_dp.py`, `src/dp_labeling.py`)
Answer with `path:line`:
- What container holds pending labels (list, deque, heap, recursion/stack)? In which order are labels expanded: tier by tier, depth-first, or other?
- Where is dominance applied: **at insertion** into a per-key structure, or **in batches** (`FilterDominated` style)? What defines a batch?
- Can two labels with the same key `(v, IV, C)` be created in **different** batches? Give a concrete example sequence if yes (e.g. `p_b, d_a, d_j` vs `d_a, p_b, d_j`).
- Is a label that is expanded **later found dominated** by another label of the same key (expansion wasted)?
- Where are completed routes collected, and where is the per-bundle Pareto filter?

### 1.2 Hypothesis check: is it DFS?
The author believes the current generation behaves like DFS (expand one branch fully before backtracking), so a label in branch `X->P1` cannot be compared with a label in branch `X->P2` that does not exist yet. State clearly whether this is **true, false, or partially true** for `run_dp`, with evidence. If the code is batch/tier based, explain how far it differs.

### 1.3 Measure the ceiling (instrumentation only, no behaviour change)
For C1, record every created label with an id, creation order, key, `(t, K, W)`, and the number of children it generated. After the run, for each key compute the **final** Pareto set over **all** labels ever created for that key. Report:

| quantity | meaning |
|---|---|
| `wasted_labels` | labels that are strictly dominated by some label of the final set (they should never have been expanded) |
| `wasted_children` | children generated by `wasted_labels` |
| `wasted_share` | `wasted_children / ext_attempts` |
| `cross_batch_pairs` | pairs of same-key labels, one dominating the other, that were **never compared** because they were in different batches |

`wasted_share` is an **upper bound** on what any better ordering of Layer 1 can save. Compute it for the five label-rule instances (B=3, B=4).

### STOP 1
Print the answers to 1.1–1.2 and the table of 1.3. **If `wasted_share < 5%` on all instances, say so explicitly: Idea 2a cannot give a meaningful speed-up; continue only with Ideas 1, 2b and 3.**

## 3. Phase 2 — Implement the variants (branch `exp-tiers-fd-dominance`)

All in `audit_fd_rule2/`, each as a function with the same signature as `run_dp`, plus counters (`ext_attempts`, `labels_created`, `killed_layer1`, `killed_rule`, `complete_labels`, `routes_layer2` or `routes_kept`) and `perf_counter` timers (`t_A`, `t_F`, `t_total`).

| id | tiering | Layer 1 | rule | Layer 2 | Frontier | output |
|---|---|---|---|---|---|---|
| **C1** | production | on | off | on | post-hoc | `K*` (baseline, old way) |
| **C3** | production | on | `RuleFires` on **survivors only** (lazy triples) | on | post-hoc | `K*` |
| **C4** | events `m = |IV|+2|C|` | on | off | on | post-hoc | `K*` |
| **C5** | events | on | off | per bundle, in loop | **in loop**, only `K*` kept | `K*` directly |
| **C6** | events | on | **FD-dominance between labels** (Idea 3) on survivors | on | post-hoc | `K*` |
| **C7** | events | on | FD-dominance (Idea 3) | per bundle, in loop | **in loop** | `K*` directly |

Notes:
- C4: tier `m` produces tier `m+1` only; `FilterDominated` runs once per tier over the whole tier, before expansion. For ODs, the home-leg completion is evaluated from labels with `IV = empty`, at the end of their tier.
- C5/C7 in-loop frontier: when tier `2k` is done, take all completed routes with `|bundle| = k`, apply the per-bundle Pareto filter, then keep a route `r` iff `max over b in [18,25] of (E_r(b) - c_r(b)) > 0`, where `E_r` is the lower envelope over `{K*-routes with bundle subseteq S_r, bundle != S_r or r' != r}` plus the empty route `0_i`, each with `+ q(S_r \ S_r')`. **Hypothesis to verify, not assume:** using only `K*` routes of smaller bundles (not all of `R`) gives the same `K*` as the exact `Frontier(R)`. The equality gate decides.
- C6/C7 FD-dominance: bucket survivors by exact key `(v, IV, C)`; for each new survivor `L2`, loop over proper subsets `C1` of `C2` and test the Pareto list of key `(v, IV, C1)`. Use the cheap test with `A = 0` first; compute `A` only if it passes. A discarded `L2` never enters the next tier.
- Do **not** optimise C3/C6 beyond what C1 gets (fairness rule).

### STOP 2
Print: file list, a 10-line description of each variant, and the results of the regression test below.

**Regression test before anything else:** C1 (instrumented) must reproduce production `dp_labeling.run_pool` exactly on all drivers of the five instances (canonical signature sets equal, as in `regression_rule_off.log`). C4 with the rule off must reproduce the **same R** as C1 (tier order may change which labels are expanded, never the final Pareto set per bundle). Report any difference.

## 4. Phase 3 — Equality gates (must pass before any timing claim)

Canonical signature of a route: `(driver, frozenset(bundle), round(K, 9), round(W, 9))`.

### 4.1 Instances
- The five label-rule instances: `n12_s42, n10_s1, n15_s7, n12_s123, n10_s999`, at B=3 and B=4.
- Main-grid sample: n=15, supply (3,3), alignment 0.90 and 0.50, reps 0–9, B=3.
- Brute force: n=5 and n=6, three seeds each (use the existing oracle).

### 4.2 Gates
| gate | requirement |
|---|---|
| G1 | `K*` of every variant equals `K*` of C1 (signature sets), for every driver of every instance |
| G2 | for C4: `R` equals `R` of C1 |
| G3 | on 20 report profiles per instance (truthful + 19 uniform draws in [18,25], fixed seed): `V`, every `V_{-k}`, every payment equal to C1's within `1e-9` (expected `~1e-13`) |
| G4 | brute force (n=5,6): `K*(brute) = K*(C1) = K*(variant)` |
| G5 | **completion-level audit of Idea 3** (C6/C7): for every discard `(L2 by L1, T)` on the n<=10 instances at B=3, enumerate **all** feasible completions `sigma` of `L2` and verify with an **independent route evaluator** (re-simulate the route from scratch, do not reuse label arithmetic) that `L1.sigma` is feasible and `c(L2.sigma) - c(L1.sigma) >= q(T) - 1e-9` at `theta = 18`. Report firings audited, completions checked, violations (must be 0) |
| G6 | **mutation test** for C6, three invalid mutations: (a) set `A = 0` (ignore absorption); (b) drop the `K2 - K1` term from condition 4; (c) relax condition 3 to `t1 <= t2 + 5`. Each mutation must **fail** G1 or G5 on at least one instance. One valid control: lower the threshold to `q(T) - 1.0` (a weaker test fires less), which must still pass. If an invalid mutation passes everything, the audit is too weak: say so |
| G7 | for C5/C7: compare the in-loop `K*` to `Frontier(R)` on every driver; report mismatches with a minimal counterexample (driver, route, which smaller-bundle route was missing from `K*`) |

### STOP 3
Print the gate table. **If G1, G4 or G5 fails for a variant, stop for that variant: save the smallest counterexample (instance, driver, labels `L1`, `L2`, `T`, both costs, `q(T)`) and do not time it.**

## 5. Phase 4 — Timing (only variants that passed all gates)

Protocol (identical to the previous audit):
- single thread, nothing else running; record CPU model, Python version, power plan;
- warm-up run discarded; then **10 timed runs per configuration, alternating order** (C1, C3, C4, C5, C6, C7, C1, ...). For runs longer than 20 s you may use 5 runs; say so;
- report median and IQR of `t_A`, `t_F`, `t_total` per instance; pooled ratio of totals; also per-instance ratio `t_total(C1) / t_total(variant)` (values > 1 mean the variant is **faster**);
- also report C1's time against the C1 time in `AUDIT_REPORT.md` Table B: a difference above 10% means machine drift, and the comparison must be repeated;
- for C5/C7, `t_F = 0` by construction; their `t_total` must include the in-loop frontier cost, counted inside `t_A`.

### Tables to produce

**Table A: work.**
| instance | B | ext C1 | ext C3 | ext C4 | ext C6 | labels killed by FD-dominance (C6) | labels killed by Layer 1 (C1 vs C4) | routes kept (R for C1/C4/C6, K* for C5/C7) |
|---|---|---|---|---|---|---|---|---|

**Table B: time (median of runs, seconds).**
| instance | B | C1 t_A | C1 t_F | C1 total | C3 total | C4 total | C5 total | C6 total | C7 total | speed-up vs C1 (each) |
|---|---|---|---|---|---|---|---|---|---|---|

**Table C: ceiling vs reality.** For C4: `wasted_share` before (Phase 1.3) and after (re-measure) tiering; expected after is `~0` for same-key comparisons.

**Table D: main-grid sample** (alignment 0.90 and 0.50, 10 reps each): `ext`, `t_A`, `t_F`, `t_total`, ratio vs C1, for the variants that passed. Report also the share of drivers for which FD-dominance fired, split GW / OD.

**Table E: where the time goes** (cProfile or `line_profiler` on n12_s42, B=3, for C1 and for the best variant): top 8 functions by cumulative time, and for C6 the cost of the subset lookups and of the `A` computation separately.

### STOP 4
Print Tables A–E.

## 6. Phase 5 — Interpretation (pick one row per variant; quote evidence)

| Observation | Meaning | What to do |
|---|---|---|
| Gate fails (G1/G4/G5/G7) | Theory or implementation is wrong | Stop, save counterexample. Do **not** report timing. Tell the author the claim is unproven |
| Passes, `wasted_share < 5%` | Tiering cannot help | Drop Idea 2a |
| C4 passes, not faster | Tier bookkeeping costs more than it saves | Report Table E; keep C1 |
| C5/C7 passes, `t_total` lower than C1 by about `t_F` only | In-loop frontier removes the post-hoc pass but cannot speed up generation (t_F is 3–6% of total) | Report as "outputs K* directly, saves memory, small time gain" |
| C6 passes all gates, `ext` and `t_total` both below C1 | **Method B is a real speed-up of Algorithm A** | Report with the exact conditions (n, B, alignment); do not extrapolate beyond the sizes run; the author must still prove the claim |
| C6 passes, `ext` lower but `t_total` not lower | Lookup and `A` cost dominate | Report Table E; try only the optimisations that C1 also receives |
| C3 faster than C2 but slower than C1 | Lazy evaluation helps but the rule is still not worth it | Keep C1 |
| Fires for OD drivers | Contradicts the old claim "never fires for OD" | Report counts |

Also answer with numbers: **does a variant get closer to `K*`?** Report `|routes kept| / |K*|` for C1, C3, C6 (C5 and C7 are `1` by construction).

## 7. Final deliverable: `EXPERIMENT_REPORT.md`

Sections: (1) Environment and sha256 check; (2) How the current loop works (1.1–1.2) with evidence; (3) Ceiling (Table of 1.3); (4) Implementation summary and regression result; (5) Gate table; (6) Tables A–E; (7) Interpretation (one row per variant); (8) **What this does NOT show** (n=20, B=4 on the main grid, other machines, pure-Python implementation effects, proof status of Idea 3 and of the in-loop frontier hypothesis); (9) Recommended manuscript statements, only those the evidence supports.

## 8. Do NOT

- Do not state that Idea 3 or the in-loop frontier is "proved". They are conjectures validated by tests.
- Do not change a variant's thresholds after seeing the results.
- Do not report a speed-up for a variant that failed a gate.
- Do not compare a tuned variant against an untuned C1.
- Do not merge the branch, push, or edit the manuscript.