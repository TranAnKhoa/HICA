# EXPERIMENT_REPORT: can Algorithm A be made faster by event-count tiers, an in-loop frontier, or FD-dominance between real labels?

Written for: the thesis author (decides what Algorithm A looks like in Paper.tex and what may be claimed). Specification: `AlgorithmA_Test/Experiment_trial.md`. Raw logs: `audit_logs2/`; code: `audit_fd_rule2/`. Everything is compared against **C1** (production Algorithm A). A ratio above 1 means the variant is **faster** than C1.

## 0. Summary (read this first)

| Variant | What it is | Correct? (all gates) | Work (extension attempts vs C1) | Time vs C1 (t_total) | Verdict |
|---|---|---|---|---|---|
| **C3** | lazy rule (virtual shortcut) on FilterDominated survivors | yes | -15% to -37% | **0.64-0.79x (slower)** | keep C1 |
| **C4** | event-count tiers (`m = abs(IV) + 2 abs(C)`), rule off | yes, R identical to C1 | -12.5% to -16.8% (B=3), -19.9% to -28.2% (B=4) | **1.07-1.22x (B=3), 1.22-1.30x (B=4)** | **real speed-up** |
| **C5** | C4 + frontier inside the loop, outputs K* directly | yes (K* identical) | same as C4 | **1.15-1.23x (B=3), 1.33-1.43x (B=4)** | **best variant**; also never stores R |
| **C6** | C4 + FD-dominance between real labels (Idea 3) | yes, 0 violations in 6,239 completions | -23% to -42% | 0.81-0.90x (B=3), 0.86-1.01x (B=4) | fewer extensions, **not faster** |
| **C7** | C6 + frontier in the loop | yes | same as C6 | 0.86-0.94x (B=3), 0.88-1.05x (B=4) | not faster than C5 |

Three findings that matter for the manuscript:

1. **The production loop does leave dominance on the table, and tiering recovers all of it.** Same-key labels land in different Layer-1 batches in `run_dp`; 7.9-22.1% of its extension work is spent on labels that a same-key label already dominates. With tiers the measured waste is exactly 0 and the number of extensions saved equals the Phase 1 ceiling (Table C).
2. **The speed-up of Method A is real but modest (about 1.1-1.4x), and it grows with B.** It is not a 2-3x effect. It comes from doing less work, with all outputs unchanged (R for C4, K* for C5).

3. **FD-dominance between real labels (Idea 3) is safe in every test we ran but does not pay for itself in this implementation.** It removes 9-19% more extensions than C4, and the lookup over proper sub-bundles costs more than it saves (Table E: 82% of the FD-dominance time is subset lookups, 18% is the absorption term A). At the largest size run (n15_s7, B=4) it reaches about 1.0-1.05x versus C1, still well below C4/C5.

Status of the theory: Idea 3 and the in-loop frontier hypothesis are **conjectures validated by tests, not theorems.** Nothing here proves them.

## 1. Environment and sha256 check

- Branch `exp-tiers-fd-dominance`, created from `audit-fd-rule`. Not merged, not pushed. New files are untracked (`audit_fd_rule2/`, `audit_logs2/`); no tracked file was modified.
- AMD Ryzen AI 5 340 w/ Radeon 840M, Windows 11, **Python 3.7.7** (production interpreter), CPLEX 12.10 for G3, power plan **Balanced** (`audit_logs2/environment.txt`). Single thread; timing runs were executed alone on the machine.
- Locked parameter files, sha256 before = after (`audit_logs2/lock_sha256_before.txt`, `lock_sha256_after.txt`, `diff` empty):
  - `spec_2a_2b/results/rq1_locked_params.json` 638e3957...04e8
  - `spec_2a_2b/results/rq_all/rq_all_locked_params.json` 861378ba...f7be
- **Machine drift check.** The old audit's C1 (`audit_fd_rule/fdrule_dp`, rule off) was re-timed on the five label instances at B=3 and compared with `AUDIT_REPORT.md` Table B: first pass -3.8% to +19.3% (two instances above 10%), repeat -3.0% to +11.6% (one instance above 10%, the smallest, 0.35 s). Because the rule asks for a repeat when drift exceeds 10%, the whole B=3 label timing was repeated (`timing_label3.json`). The speed-up ratios replicate (max change 0.10 in the ratio, at the smallest instance; Section 6, replicate table), so the conclusions do not depend on the drift. All variants are timed interleaved in the same session, so absolute drift cancels in the ratios.

## 2. How the current loop works (Phase 1.1-1.2, evidence)

Full answers: `audit_logs2/phase1_answers.md`. In short (`experiments/T2BFS/t6_dp.py`):

- Pending labels live in plain lists and a dict `frontier[touched]` (:227, :237-266); no heap, deque or recursion.
- Labels are expanded round by round on `touched = abs(IV) + abs(C)` (:229); inside a round a closure repeatedly expands deliveries/home (:239-266), then pickups go to the next round (:273-291).
- Dominance (`_filter_dominated_labels`) is applied **in batches**, not at insertion: each closure iteration (:258-266), each pickup round (:284-291), and at the end on complete labels per (C, v) (:293-308). A pair of labels is only compared if both are in the same batch.
- **Hypothesis "it is DFS": false.** It is a level-synchronous DP. The defect is that the batch boundary (round, closure iteration) does not coincide with the key `(v, IV, C)`. Example found in the data (n10_s999, B=3, gw0), key v=n11, IV={}, C={o0,o2): label `p0 d0 p2 d2` (batch: round 2, iteration 1, (t,K,W) = (71.16, 17.053, 71.16)) strictly dominates `p2 p0 d0 d2` (batch: round 2, iteration 2, (71.78, 17.259, 71.78)), they are never compared, and the dominated one is expanded.
- Complete routes: `complete_by_C` (:221, :250, :255), Layer 1 on complete labels per (C, v) (:293-308), Layer 2 `_pareto_front` per bundle in `spec_2a_2b/src/dp_labeling.py:28,82`.

## 3. Ceiling (Phase 1.3) and what tiering achieves

Instrumented C1 (behaviour unchanged; reproduces production on 48/48 drivers). `wasted_share` follows the spec (`wasted_children / ext_attempts`); `wasted_attempt_share` counts the extension *attempts* made by wasted labels, which is the quantity that actually becomes savings.

| B | instance | ext_attempts | wasted_labels | wasted_children | wasted_share | wasted_attempt_share | cross_batch_pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| 3 | n12_s42 | 71870 | 6469 | 5655 | 7.87% | 12.52% | 20788 |
| 3 | n10_s1 | 51361 | 6982 | 5073 | 9.88% | 15.21% | 24125 |
| 3 | n15_s7 | 187895 | 25416 | 21910 | 11.66% | 16.80% | 87486 |
| 3 | n12_s123 | 111944 | 14648 | 12471 | 11.14% | 15.73% | 50319 |
| 3 | n10_s999 | 37800 | 4266 | 3495 | 9.25% | 13.83% | 14826 |
| 4 | n12_s42 | 658706 | 48655 | 87766 | 13.32% | 19.91% | 350243 |
| 4 | n10_s1 | 530486 | 66594 | 95330 | 17.97% | 26.58% | 563277 |
| 4 | n15_s7 | 2635861 | 319501 | 581900 | 22.08% | 28.18% | 2792992 |
| 4 | n12_s123 | 1208860 | 138785 | 252387 | 20.88% | 27.04% | 1143059 |
| 4 | n10_s999 | 316079 | 32330 | 55854 | 17.67% | 24.52% | 288178 |

`wasted_share` is above the 5% threshold in all 10 configurations (7.9-11.7% at B=3, 13.3-22.1% at B=4), so Idea 2a was not dropped. About two thirds of the wasted labels have a dominating label that was created *earlier*.

**Reality check.** The extension savings of C4 over C1 (Table A, second block) are 12.5, 15.2, 16.8, 15.7, 13.8% at B=3 and 19.9, 26.6, 28.2, 27.0, 24.5% at B=4, which equal `wasted_attempt_share` to the printed precision. Tiering therefore reaches the ceiling exactly; the spec's `wasted_share` (children only) understates it by about a third.

## 4. Implementation summary and regression

Files in `audit_fd_rule2/`: `variants.py` (all engines), `phase1_ceiling.py`, `phase1_after_tier.py`, `regress.py`, `gate_equal.py`, `gate_wdp.py`, `gate_audit.py`, `timing.py`, `profile_tables.py`, `anchor.py`, `make_tables.py`, `run_chain*.sh`.

All variants re-use the same `_try_pickup/_try_delivery/_try_home`, `_filter_dominated_labels`, `finalize_KW`, `_pareto_front`, the same `Label` class and the same counters. Nothing was micro-optimised for one variant only. C3 re-uses the previous audit's `_next_sc/_rule_fires` unchanged.

- **C1**: production round structure with counters (identical to `t6_dp.run_dp` + `dp_labeling.run_pool`).
- **C3**: C1, but the rule runs only on labels that survived FilterDominated; shortcut triples computed at that moment from the parent's triples.
- **C4**: tiers by `m = abs(IV) + 2 abs(C)`; FilterDominated once per tier over the whole tier before expansion; Layer 2 per bundle as soon as tier `2k` is done.
- **C5**: C4 + after tier `2k`: Pareto per bundle, then keep a route iff its margin is positive against the empty route, the other routes of the same bundle and the **K\* routes of smaller bundles**; only K\* is stored.
- **C6**: C4 + FD-dominance (Idea 3): for each FilterDominated survivor L2 with non-empty C, loop over the proper subsets C1 of C2 (including the empty set), look up key (v, IV, C1) among the FilterDominated survivors of earlier tiers, cheap test with A=0 first, absorption A only if that passes.
- **C7**: C6 + in-loop frontier.

Design choices to know about: (i) the survivors dictionary for FD-dominance contains every FilterDominated survivor, also those later discarded by FD-dominance itself (the proof sketch says only the feasibility of the prefix L1 matters); (ii) the in-loop frontier test also uses the other Pareto routes of the *same* bundle (they are part of D(r)); the spec only listed smaller bundles and the empty route; (iii) A uses the manuscript's F(L2) (pickups reachable from L2, deliveries of orders on board, deliveries of those pickups' orders).

**Regression (STOP 2).** `audit_logs2/regression.log` and, after a small refactor (absorption term moved into its own function so it can be profiled), `regression_after_refactor.log`: C1 == production `dp_labeling.run_pool` on all drivers of the 10 label configurations: **PASS**; C4 reproduces the same R as C1: **PASS**. G5/G6 results were identical before and after the refactor.

## 5. Gate table

| gate | scope | result |
|---|---|---|
| **G1** K* equal to C1 | 10 label configurations (B=3,4) + 20 main-grid instances (n=15, align 0.90/0.50, reps 0-9, B=3), every driver, variants C3-C7 | **PASS**, 0 mismatches |
| **G2** R(C4) = R(C1) | same 30 instances | **PASS** |
| **G3** V, V_-k, payments within 1e-9, 20 profiles | 10 label configurations, C3-C7 vs C1 (CPLEX 12.10) | **PASS**; max deviation 5.7e-14 (C3 5.7e-14, C4 2.8e-14, C5 2.8e-14, C6 5.7e-14, C7 5.7e-14); no profile with a different winner set |
| **G4** brute force n=5,6, 3 seeds each | K*(brute) = K*(C1) = K*(variant), all 5 variants | **PASS** (6/6 instances) |
| **G5** completion-level audit of Idea 3 (n10_s1, n10_s999 at B=3 + six n=5,6 instances) | independent evaluator (re-simulates a route from its stop sequence). Evaluator validated first: **2,811 complete labels, 0 mismatches** against `finalize_KW` | **9,517 discards audited (GW 4,557, OD 4,960), 6,239 completions checked, 0 violations**; smallest margin `c(L2.sigma) - c(L1.sigma) - q(T)` = +0.0030 at theta = 18 |
| **G6** mutations of C6 (G1 on 5 label configurations at B=3 + n10_s999 at B=4; G5 as above) | see below | all invalid mutations detected, control passes |
| **G7** in-loop K* = Frontier(R) | C5, C7 on the same 30 instances; **plus** a counterexample hunt: 80 random instances (n=6..9, B=3, 4 drivers, seeds 100-119) = 960 drivers, C5/C6/C7 vs Frontier(R_C1) | **PASS**, 0 mismatches |

G6 detail (`audit_logs2/gate_audit.log`):

| mutation | G1 fails on | G5 violations / completions | detected? |
|---|---|---:|---|
| (a) A = 0 (ignore absorption) | n15_s7, n10_s999, n10_s999 (B=4) | 1,186 / 11,154 | yes (G1 and G5) |
| (b) drop `K2-K1` | none | 4 / 1,839 | yes, **only by G5** |
| (c) `t1 <= t2 + 5` | none | 2 / 6,241 | yes, **only by G5** |
| extra: threshold `q(T) - 1.0` | all 6 | 820 / 7,183 | yes (G1 and G5) |
| control (valid): threshold `q(T) + 1.0` | none | 0 / 5,424, min margin +1.002 | passes, as it must |

Notes: (1) mutations (b) and (c) pass G1 (K* is unchanged on these instances) and are caught only by the completion-level audit G5. A K*-equality test alone would not have exposed them; that is the reason G5 exists. (2) The spec says the valid control should "lower the threshold to `q(T) - 1.0` (a weaker test fires less)". Lowering the threshold makes the test fire *more*; I therefore used `q(T) + 1.0` as the valid control (fires less), and ran `q(T) - 1.0` as an additional invalid mutation.


## 6. Tables A-E (Phase 4; label instances: 10 timed runs, 5 for n15_s7 at B=4; grid: 5 timed runs)

Table A-D are produced by `audit_fd_rule2/make_tables.py` from the saved JSON. Speed-up columns are medians of paired per-repetition ratios `t_total(C1)/t_total(variant)` with IQR in brackets.

### Table A: work (label-rule instances; sums over all drivers of the instance)

| instance | B | ext C1 | ext C3 | ext C4 | ext C6 | killed by FD-dominance (C6) | killed by Layer 1 C1 | killed by Layer 1 C4 | routes kept R: C1 / C4 / C6 | K* (C5=C7=C1) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| n12_s42 | 3 | 71870 | 52627 | 62875 | 54895 | 5377 | 16937 | 17751 | 879 / 879 / 708 | 28 |
| n10_s1 | 3 | 51361 | 40057 | 43548 | 38090 | 4356 | 15079 | 16988 | 714 / 714 / 657 | 165 |
| n15_s7 | 3 | 187895 | 118506 | 156332 | 126363 | 19429 | 63402 | 66908 | 1561 / 1561 / 1121 | 165 |
| n12_s123 | 3 | 111944 | 78879 | 94338 | 81056 | 9752 | 35512 | 37689 | 1416 / 1416 / 1183 | 208 |
| n10_s999 | 3 | 37800 | 29553 | 32574 | 28927 | 2750 | 10661 | 11432 | 510 / 510 / 471 | 77 |
| n12_s42 | 4 | 658706 | 512837 | 527545 | 459607 | 29551 | 198297 | 159186 | 2648 / 2648 / 2249 | 74 |
| n10_s1 | 4 | 530486 | 436193 | 389497 | 339916 | 24248 | 212727 | 183991 | 1845 / 1845 / 1708 | 416 |
| n15_s7 | 4 | 2635861 | 1783862 | 1893101 | 1539907 | 152749 | 1261511 | 999112 | 5401 / 5401 / 4396 | 603 |
| n12_s123 | 4 | 1208860 | 896323 | 881938 | 763227 | 62731 | 537534 | 423932 | 4199 / 4199 / 3704 | 482 |
| n10_s999 | 4 | 316079 | 267626 | 238575 | 216584 | 11029 | 125889 | 102365 | 1104 / 1104 / 1041 | 193 |

Extension savings vs C1 (percent): 

| instance | B | C3 | C4 | C6 |
|---|---|---:|---:|---:|
| n12_s42 | 3 | 26.8 | 12.5 | 23.6 |
| n10_s1 | 3 | 22.0 | 15.2 | 25.8 |
| n15_s7 | 3 | 36.9 | 16.8 | 32.7 |
| n12_s123 | 3 | 29.5 | 15.7 | 27.6 |
| n10_s999 | 3 | 21.8 | 13.8 | 23.5 |
| n12_s42 | 4 | 22.1 | 19.9 | 30.2 |
| n10_s1 | 4 | 17.8 | 26.6 | 35.9 |
| n15_s7 | 4 | 32.3 | 28.2 | 41.6 |
| n12_s123 | 4 | 25.9 | 27.0 | 36.9 |
| n10_s999 | 4 | 15.3 | 24.5 | 31.5 |

### Table B: time (s, median of the timed runs; t_total = t_A + t_F; speed-up = median of paired t_total(C1)/t_total(variant), >1 = variant faster)

| instance | B | reps | C1 t_A | C1 t_F | C1 total | C3 total | C4 total | C5 total | C6 total | C7 total | C3 x | C4 x | C5 x | C6 x | C7 x |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| n12_s42 | 3 | 10 | 0.604 | 0.0405 | 0.644 | 0.967 | 0.556 | 0.539 | 0.779 | 0.748 | 0.65 [0.63-0.71] | 1.12 [1.08-1.23] | 1.15 [1.04-1.29] | 0.81 [0.75-0.97] | 0.86 [0.83-0.89] |
| n10_s1 | 3 | 10 | 0.533 | 0.0549 | 0.592 | 0.830 | 0.498 | 0.486 | 0.696 | 0.693 | 0.69 [0.66-0.73] | 1.14 [1.11-1.28] | 1.20 [1.12-1.27] | 0.84 [0.75-0.94] | 0.86 [0.76-0.92] |
| n15_s7 | 3 | 10 | 1.879 | 0.0827 | 1.957 | 2.479 | 1.689 | 1.612 | 2.234 | 1.979 | 0.79 [0.78-0.84] | 1.15 [1.11-1.18] | 1.18 [1.14-1.30] | 0.90 [0.86-0.95] | 0.94 [0.92-1.02] |
| n12_s123 | 3 | 10 | 1.099 | 0.0664 | 1.165 | 1.604 | 1.016 | 0.988 | 1.413 | 1.288 | 0.74 [0.71-0.82] | 1.22 [1.04-1.29] | 1.23 [1.14-1.31] | 0.88 [0.80-0.92] | 0.94 [0.88-0.98] |
| n10_s999 | 3 | 10 | 0.315 | 0.0252 | 0.340 | 0.541 | 0.314 | 0.278 | 0.396 | 0.395 | 0.64 [0.61-0.67] | 1.07 [1.07-1.08] | 1.23 [1.10-1.35] | 0.83 [0.76-0.96] | 0.90 [0.81-1.04] |
| n12_s42 | 4 | 10 | 4.557 | 0.3853 | 4.971 | 7.346 | 3.941 | 3.720 | 5.760 | 5.500 | 0.69 [0.67-0.69] | 1.22 [1.13-1.29] | 1.33 [1.24-1.42] | 0.86 [0.85-0.88] | 0.88 [0.86-0.92] |
| n10_s1 | 4 | 10 | 4.409 | 0.5079 | 4.896 | 7.104 | 3.773 | 3.421 | 5.338 | 4.915 | 0.69 [0.68-0.71] | 1.29 [1.24-1.37] | 1.43 [1.38-1.54] | 0.93 [0.90-0.96] | 1.00 [0.97-1.01] |
| n15_s7 | 4 | 5 | 21.702 | 0.8320 | 22.530 | 29.167 | 17.220 | 16.620 | 22.304 | 21.764 | 0.78 [0.76-0.78] | 1.28 [1.26-1.33] | 1.35 [1.32-1.39] | 1.01 [0.99-1.03] | 1.05 [0.99-1.06] |
| n12_s123 | 4 | 10 | 9.764 | 0.6799 | 10.414 | 13.818 | 8.194 | 7.522 | 10.943 | 10.561 | 0.75 [0.74-0.76] | 1.28 [1.24-1.31] | 1.38 [1.37-1.42] | 0.95 [0.94-1.00] | 0.99 [0.95-1.02] |
| n10_s999 | 4 | 10 | 2.383 | 0.1521 | 2.526 | 3.905 | 1.964 | 1.834 | 2.837 | 2.683 | 0.66 [0.65-0.66] | 1.30 [1.26-1.31] | 1.38 [1.33-1.41] | 0.90 [0.86-0.92] | 0.94 [0.93-0.98] |

B=3: median per-instance speed-up C3 0.69, C4 1.14, C5 1.20, C6 0.84, C7 0.90 ; pooled ratio of total times C3 0.73, C4 1.15, C5 1.20, C6 0.85, C7 0.92
B=4: median per-instance speed-up C3 0.69, C4 1.28, C5 1.38, C6 0.93, C7 0.99 ; pooled ratio of total times C3 0.74, C4 1.29, C5 1.37, C6 0.96, C7 1.00

### Table C: ceiling vs reality (wasted_share = wasted_children / ext_attempts)

| B | instance | wasted_share C1 (Phase 1.3) | wasted_share after tiering (C4) | cross-batch pairs C1 | after tiering | duplicates expanded after |
|---|---|---:|---:|---:|---:|---:|
| 3 | n12_s42 | 7.87% | 0.00% | 20788 | 0 | 0 |
| 3 | n10_s1 | 9.88% | 0.00% | 24125 | 0 | 0 |
| 3 | n15_s7 | 11.66% | 0.00% | 87486 | 0 | 0 |
| 3 | n12_s123 | 11.14% | 0.00% | 50319 | 0 | 0 |
| 3 | n10_s999 | 9.25% | 0.00% | 14826 | 0 | 0 |
| 4 | n12_s42 | 13.32% | 0.00% | 350243 | 0 | 0 |
| 4 | n10_s1 | 17.97% | 0.00% | 563277 | 0 | 0 |
| 4 | n15_s7 | 22.08% | 0.00% | 2792992 | 0 | 3 |
| 4 | n12_s123 | 20.88% | 0.00% | 1143059 | 0 | 0 |
| 4 | n10_s999 | 17.67% | 0.00% | 288178 | 0 | 0 |

### Table D: main-grid sample (n=15, supply (3,3), B=3, reps 0-9; sums over 10 instances per alignment)

| alignment | variant | ext | t_A | t_F | t_total | ratio C1/variant (pooled) | median per-instance ratio | routes kept | K* equal on all | FD fired GW drivers | FD fired OD drivers |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0.90 | C1 | 2963369 | 29.16 | 1.340 | 30.62 | 1.00 | 1.00 | 26792 | True | - | - |
| 0.90 | C3 | 1679529 | 34.15 | 0.945 | 35.19 | 0.87 | 0.91 | 20741 | True | 30/30 | 30/30 |
| 0.90 | C4 | 2411163 | 24.83 | 1.387 | 26.29 | 1.16 | 1.15 | 26792 | True | - | - |
| 0.90 | C5 | 2411163 | 25.69 | 0.000 | 25.69 | 1.19 | 1.19 | 4742 | True | - | - |
| 0.90 | C6 | 1824917 | 30.18 | 0.800 | 30.94 | 0.99 | 1.00 | 17921 | True | 30/30 | 30/30 |
| 0.90 | C7 | 1824917 | 30.25 | 0.000 | 30.25 | 1.01 | 1.02 | 4742 | True | 30/30 | 30/30 |
| 0.50 | C1 | 1530283 | 11.05 | 1.318 | 12.36 | 1.00 | 1.00 | 29860 | True | - | - |
| 0.50 | C3 | 1107420 | 17.68 | 0.476 | 18.17 | 0.68 | 0.67 | 11420 | True | 30/30 | 30/30 |
| 0.50 | C4 | 1392547 | 10.25 | 1.287 | 11.57 | 1.07 | 1.04 | 29860 | True | - | - |
| 0.50 | C5 | 1392547 | 10.88 | 0.000 | 10.88 | 1.14 | 1.14 | 12 | True | - | - |
| 0.50 | C6 | 1254429 | 15.57 | 0.998 | 16.60 | 0.74 | 0.75 | 25157 | True | 30/30 | 30/30 |
| 0.50 | C7 | 1254429 | 15.51 | 0.000 | 15.51 | 0.80 | 0.79 | 12 | True | 30/30 | 30/30 |

### Closeness to K*: |routes kept| / |K*|

| set | C1 | C3 | C6 | C5 / C7 |
|---|---:|---:|---:|---|
| label instances B=3 (pooled) | 7.90 | 4.60 | 6.44 | 1 |
| label instances B=4 (pooled) | 8.60 | 5.06 | 7.41 | 1 |
| grid alignment 0.90 (pooled) | 5.65 | 4.37 | 3.78 | 1 |
| grid alignment 0.50 (pooled) | 2488.33 | 951.67 | 2096.42 | 1 |

### Replicate of the B=3 label timing (machine-drift protocol)

Speed-up vs C1, run 1 (10 repetitions) / run 2 (repeat, 10 repetitions). Raw: `timing_label.json`, `timing_label3.json`.

| instance | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|
| n12_s42 | 0.65 / 0.67 | 1.12 / 1.18 | 1.15 / 1.19 | 0.81 / 0.88 | 0.86 / 0.85 |
| n10_s1 | 0.69 / 0.66 | 1.14 / 1.11 | 1.20 / 1.19 | 0.84 / 0.85 | 0.86 / 0.89 |
| n15_s7 | 0.79 / 0.78 | 1.15 / 1.18 | 1.18 / 1.16 | 0.90 / 0.93 | 0.94 / 0.96 |
| n12_s123 | 0.74 / 0.77 | 1.22 / 1.22 | 1.23 / 1.25 | 0.88 / 0.95 | 0.94 / 0.96 |
| n10_s999 | 0.64 / 0.67 | 1.07 / 1.17 | 1.23 / 1.34 | 0.83 / 0.90 | 0.90 / 0.90 |

The ordering of the variants is the same in both runs on every instance. The largest change in a ratio is 0.11 (C5 on the smallest instance, 0.3 s per run).

### Table E: where the time goes (cProfile, n12_s42, B=3, seconds per full run of all five drivers, profiler overhead included)

| rank | C1 | C4 | C6 |
|---|---|---|---|
| 1 | `run_round` 0.625 | `run_tier` 0.716 | `run_tier` 0.993 |
| 2 | `_try_delivery` 0.182 (34,827 calls) | `_try_delivery` 0.207 | **`fd_dominated` 0.323 (19,553 calls)** |
| 3 | `_try_pickup` 0.125 (32,724) | `_try_pickup` 0.147 | `_try_delivery` 0.159 |
| 4 | `_filter_dominated_labels` 0.106 (23,334) | `_filter_dominated_labels` 0.113 (18,539) | `_try_pickup` 0.138 |
| 5 | `travel_time` 0.073 | `travel_time` 0.082 | `travel_time` 0.096 |
| 6 | `kstar_pool` 0.058 | `kstar_pool` 0.066 | `_filter_dominated_labels` 0.095 (17,962) |

(`build_all`/`run_cN` wrapper rows omitted; full output in `audit_logs2/profile.log`.) Cost inside C6's FD-dominance: **0.323 s total, of which the absorption term A is 0.057 s (18%) and the sub-bundle lookups and tests are 0.266 s (82%).** The tier engine itself (C4 vs C1) adds little bookkeeping: the same functions dominate and `_filter_dominated_labels` is called fewer times (18,539 vs 23,334 key groups) because of the larger batches.

## 7. Interpretation (one row per variant)

| Variant | Observation (evidence) | Meaning | What to do |
|---|---|---|---|
| Ceiling / Idea 2a | `wasted_share` 7.9-22.1% (above 5%); after tiering 0.00% and 0 cross-batch pairs on all 10 configurations (Table C) | The production loop wastes work that is entirely recoverable by batching per event count | Idea 2a is **not** dropped; C4 captures the whole ceiling |
| **C4** | Passes G1-G4; R identical to C1; ext -12.5% to -28.2%; time 1.07-1.30x on the label instances, 1.16x (align 0.90) and 1.07x (align 0.50) on the grid | **A real speed-up of Algorithm A**, modest, growing with B (median 1.14x at B=3, 1.28x at B=4) | Report with the exact conditions (n <= 15, B = 3, 4); do not extrapolate to n = 20 |
| **C5** | Passes G1-G4, G7 (K* identical, 960 random drivers without a counterexample); time 1.15-1.43x on the label instances, 1.19x/1.14x on the grid; stores only K* (about 8x fewer routes than R on label instances at B=3; 5.65x fewer at align 0.90; Table "closeness") | Removes the post-hoc pass (`t_F` is 4-11% of C1's total) **and** the speed-up of C4. The additional gain of C5 over C4 is close to or below `t_F`, as expected | Report as "outputs K* directly; the extra gain over C4 is the post-hoc pass". Memory saving is implied by the route counts but **was not measured** |
| **C6** | Passes G1-G6 (0 violations in 6,239 completions, mutations caught); ext -23% to -42% vs C1 (-9% to -19% vs C4), but time 0.81-0.90x (B=3) and 0.86-1.01x (B=4) vs C1, 0.99x/0.74x on the grid | Fewer extensions, **no speed-up**: the lookup over proper sub-bundles (82% of the FD cost) and the A term cost more than the extensions they remove | Do not claim a speed-up. Possible later work: faster lookup (e.g. precomputed sub-bundle index); any such optimisation must also be offered to C1/C4 |
| **C7** | Same safety as C6 plus in-loop frontier; time 0.86-1.05x vs C1 | Combining C6 with the in-loop frontier does not beat C5 (1.15-1.43x) | C5 is the better candidate for the production Algorithm A |
| **C3** | ext -15% to -37% (similar to the previous C2); time 0.64-0.79x vs C1 | Lazy evaluation of the rule helps relative to the earlier C2 (which was 0.48-0.80x in `AUDIT_REPORT.md`, different implementation, not re-run here) but is still slower than C1 | Keep C1 as the baseline; the virtual-shortcut rule is not worth it in this implementation |
| **FD rule fires for OD drivers** | G5: 4,960 of 9,517 audited discards are OD drivers; grid: fired for 30/30 GW and 30/30 OD drivers at both alignments (C3, C6, C7) | Contradicts the old statement "never fires for occasional drivers" for these label-setting implementations | State the counts if the statement is kept at all |

**Does a variant get closer to K\*?** `|routes kept| / |K*|` (pooled; 1 = exactly K\*):

| set | C1 | C3 | C6 | C5, C7 |
|---|---:|---:|---:|---:|
| label instances, B=3 | 7.90 | 4.60 | 6.44 | 1 (by construction, verified by G1/G7) |
| label instances, B=4 | 8.60 | 5.06 | 7.41 | 1 |
| grid, alignment 0.90 | 5.65 | 4.37 | 3.78 | 1 |
| grid, alignment 0.50 | 2488 | 952 | 2096 | 1 (K\* is tiny there: 12 routes over 10 instances, so the ratio is not meaningful as such) |

C3 and C6 move closer to K\* than C1 but stay far from it; only the in-loop frontier reaches K\* exactly. (C4 keeps R exactly as C1.)

## 8. What this does NOT show

- **n = 20 and above, and B = 4 on the main grid.** B=4 was run only on the five label instances (n <= 15). The speed-ups of C4/C5 grow with B in our data (median 1.14x -> 1.28x for C4), so larger sizes could behave differently in either direction.
- **Other machines, other Python builds.** Everything is pure Python 3.7.7 on one machine with the Balanced power plan. The relative cost of dictionary lookups (which hurts C6) and of larger batches (which helps C4) may differ elsewhere.
- **No optimisation of the variants.** C6's lookup was not optimised, and the spec forbids optimising a variant without giving the same optimisation to C1. A tuned FD-dominance could change the verdict; this experiment cannot say.
- **Machine drift.** The anchor showed up to +19% on one instance in the first pass and +11.6% on the smallest instance in the repeat. Ratios replicate on B=3 (Section 6), but B=4 and the grid (5 repetitions) were measured once.
- **Statistical depth.** Medians of 10 paired runs (5 for runs above 20 s and for the grid); IQRs are given, but no confidence intervals.
- **Proof status.** Idea 3 (FD-dominance between real labels) and the in-loop frontier hypothesis ("K\* of smaller bundles is enough") are **unproven**. Evidence: 6,239 completions checked with an independent evaluator (B=3, n <= 10), equality of K\* on 30 instances, 960 random drivers (n=6..9, B=3), brute force for n=5,6, and mutation tests. G5 covers B=3 only; G7's random hunt covers B=3 only; G3 uses 20 profiles per instance.
- **Memory.** The memory saving of the in-loop frontier is inferred from route counts, not measured.
- **Allocation ties.** G3 compared winner sets, values and payments; ties between equal-cost allocations were not separately analysed (no profile differed).
- **Duplicates.** Three exactly equal-(t,K,W) same-key labels were expanded twice on n15_s7 at B=4 under tiering (Table C). Irrelevant for correctness, noted for completeness.

## 9. Recommended manuscript statements (only what the evidence supports)

1. *Algorithm A (processing by event count).* "Processing labels in tiers of equal event count `m = abs(IV) + 2 abs(C)` puts all labels with the same key `(v, IV, C)` into one dominance batch. On the five experimental instances this removed 12.5-16.8% (B=3) and 19.9-28.2% (B=4) of the extension attempts, left the route pool and the frontier unchanged, and reduced running time by a median factor of 1.14 (B=3) and 1.28 (B=4) in our pure-Python implementation." State that the production loop compares labels only within a round/closure iteration.
2. *Frontier inside the loop.* "Testing frontier membership as soon as all routes of a bundle size are complete outputs the frontier directly and stores no other route; median speed-ups 1.20 (B=3) and 1.38 (B=4) relative to the baseline." Add that this was validated empirically, not proved.
3. *FD-dominance between generated labels.* "Safe in all tests (0 violations in 6,239 completions checked against an independent evaluator; mutations detected) and reduces extensions by a further 9-19% but did not reduce running time (0.8-1.05x)." Do **not** call it a speed-up and do not call it proved.
4. *Virtual-shortcut rule.* Keep the conclusion of the earlier audit: it removes extensions but is slower than the baseline (here 0.64-0.79x even when evaluated lazily).
5. The statement "never fires for occasional drivers" should be dropped or qualified (it fires for every occasional driver in the grid sample).
6. Never write "K\* speeds up the pipeline" without conditions; the speed-ups above are for Algorithm A only, not for B/C.

## Appendix: files

`audit_logs2/`: `phase1_answers.md`, `phase1_ceiling.{log,json}`, `phase1_example.log`, `phase1_after_tier.{log,json}`, `regression*.log`, `gate_equal.{log,json}`, `gate_wdp.{log,json}`, `gate_audit.{log,json}`, `gate_audit_after_refactor.log`, `timing_label.{log,json}`, `timing_label3.json`, `timing_label3_rerun.log`, `timing_grid.{log,json}`, `anchor*.log`, `profile.{log,json}`, `tables.md`, `environment.txt`, `lock_sha256_{before,mid,after}.txt`.
