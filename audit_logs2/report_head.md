# EXPERIMENT_REPORT: can Algorithm A be made faster by event-count tiers, an in-loop frontier, or FD-dominance between real labels?

Written for: the thesis author (decides what Algorithm A looks like in Paper.tex and what may be claimed). Specification: `AlgorithmA_Test/Experiment_trial.md`. Raw logs: `audit_logs2/`; code: `audit_fd_rule2/`. Everything is compared against **C1** (production Algorithm A). A ratio above 1 means the variant is **faster** than C1.

## 0. Summary (read this first)

| Variant | What it is | Correct? (all gates) | Work (extension attempts vs C1) | Time vs C1 (t_total) | Verdict |
|---|---|---|---|---|---|
| **C3** | lazy rule (virtual shortcut) on FilterDominated survivors | yes | -16% to -37% | **0.64-0.79x (slower)** | keep C1 |
| **C4** | event-count tiers (`m = abs(IV) + 2 abs(C)`), rule off | yes, R identical to C1 | -12.5% to -16.8% (B=3), -19.9% to -28.2% (B=4) | **1.07-1.22x (B=3), 1.22-1.30x (B=4)** | **real speed-up** |
| **C5** | C4 + frontier inside the loop, outputs K* directly | yes (K* identical) | same as C4 | **1.15-1.23x (B=3), 1.33-1.43x (B=4)** | **best variant**; also never stores R |
| **C6** | C4 + FD-dominance between real labels (Idea 3) | yes, 0 violations in 6,239 completions | -24% to -42% | 0.81-0.90x (B=3), 0.86-1.01x (B=4) | fewer extensions, **not faster** |
| **C7** | C6 + frontier in the loop | yes | same as C6 | 0.86-0.94x (B=3), 0.88-1.05x (B=4) | not faster than C5 |

Three findings that matter for the manuscript:

1. **The production loop does leave dominance on the table, and tiering recovers all of it.** Same-key labels land in different Layer-1 batches in `run_dp`; 7.9-22.1% of its extension work is spent on labels that a same-key label already dominates. With tiers the measured waste is exactly 0 and the number of extensions saved equals the Phase 1 ceiling (Table C).
2. **The speed-up of Method A is real but modest (about 1.1-1.4x), and it grows with B.** It is not a 2-3x effect. It comes from doing less work, with all outputs unchanged (R for C4, K* for C5).
3. **FD-dominance between real labels (Idea 3) is safe in every test we ran but does not pay for itself in this implementation.** It removes 13-19% more extensions than C4, and the lookup over proper sub-bundles costs more than it saves (Table E: 82% of the FD-dominance time is subset lookups, 18% is the absorption term A). At the largest size run (n15_s7, B=4) it reaches about 1.0-1.05x versus C1, still well below C4/C5.

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

