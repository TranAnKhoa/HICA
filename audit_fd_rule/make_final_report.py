import os
os.chdir(os.path.join("K:" + os.sep, "Data Science", "Q1 Research"))
tables = open("audit_logs/tables.md").read()
head = r"""# AUDIT_REPORT: is the FD-completion label rule running inside Algorithm A?

Written for: the thesis author (decides what to claim in Paper.tex). Raw logs are in `audit_logs/`; code in `audit_fd_rule/`.

## 1. Environment
- Base commit `0d6e69041964726d86a6b681c43789c5431bd13b` (snapshot taken at audit start; the folder was not a git repo before), branch `audit-fd-rule`. Not merged, not pushed.
- Python 3.7.7 (the production interpreter), CPLEX 12.10, CPU AMD Ryzen AI 5 340, single thread, Windows 11.
- Locked parameter files, sha256 before = after (`audit_logs/lock_sha256_before.txt`, `lock_sha256_after.txt`, `diff` empty):
  - `spec_2a_2b/results/rq1_locked_params.json` 638e3957...04e8
  - `spec_2a_2b/results/rq_all/rq_all_locked_params.json` 861378ba...f7be
- No tracked production file was modified. All new code is in `audit_fd_rule/`.

## 2. What runs today (Phase 1; evidence as path:line)
- Production Algorithm A = `spec_2a_2b/src/dp_labeling.py:100 build_route_pool` -> `:69` -> `experiments/T2BFS/t6_dp.py:191 run_dp`. It has **no call to any label rule** (Q1/Q2). Layer 1 key `(v,IV,C)` at `t6_dp.py:63`, dominance on `(t,K,W)` with one strict at `:76-81` (Q4). Coarser keys exist only in the test `spec_2a_2b/src/test_C_relaxed_key.py:139-148`.
- The rule exists only in `New_t4/files/dp_fast.py:17-115` (and `dp_rules.py:104-225`): a DFS enumerator with **no Layer 1 and no Layer 2**; `use_rule` default True at `:17` but every caller passes it; `LEGACY` flags default True (`:15`), timing scripts reset them to False (`repeat_timing.py:40-41`). The rule uses `lo=18` and singleton `T={j}` only, reads `orders[j].q`, never a bid (Q5).
- Q6: the Table 7 baseline ("without rule") is `dp_fast` with `use_rule=False` = **Layer 1 OFF** (`repeat_timing.py:53`); "extension" is counted at `dp_fast.py:33` for every candidate *before* feasibility. `t6_dp` counts only non-null labels. The two counts are not comparable.
- Q7: "pool removed" = `1 - pool_kstar/pool_full` (`rq_runner.py:93,125`); denominator = Layer-2 pool without the rule. Keep it so.
- Q3 (entry points): RQ1 main grid (`rq1_main_grid.py`, `rq1_treatments.py:49,57`), RQ2, RQ3/4, RQ5 (`rq_runner.py:62-151`), `compare_bc_runtime.py:47-50` and the gates all call `build_route_pool` (Layer 1 on, no rule flag exists). Frontier is applied post hoc only in RQ3/4 (`rq_runner.py:93`), `compare_bc_runtime.py:50`, `rq_gate.py:180` and the K* scripts; RQ1/RQ2/RQ5 use the full Layer-2 pool. Label-rule evaluation = `repeat_timing.py` / `audit_rq1_bounds.py` on `dp_fast` (Layer 1 off, no Layer 2, no Frontier).
- Consequence: Paper.tex Table `tab:label` (Paper.tex:1517-1540) is identical to the old `dp_fast` results (`New_t4/files/timing_medians_B3.json`, `Final_t4_Speedup_RESULTS.md`): it measures the rule against an enumerator **without Layer 1**, not against Algorithm A.

## 3. Measurements
Configurations: **C1** = Layer 1 on, rule off (= production); **C2** = Layer 1 on, rule on (`audit_fd_rule/fdrule_dp.py`, a port of the `dp_fast` rule into a copy of `t6_dp.run_dp`, re-using its `_try_*` and dominance code); **C0** = Layer 1 off, rule off. Regression: C1 (instrumented) equals production `dp_labeling.run_pool` on 48/48 drivers (`audit_logs/regression_rule_off.log`). Counters `ext_attempts`, `labels_created`, `killed_layer1`, `killed_layer3`, `complete_labels`, `routes_layer2` are in `audit_logs/timing_*.json`.
Instances: the five label-rule instances at B=3 and B=4, plus n=15, supply (3,3), alignment 0.90 and 0.50, reps 0-9, B=3 only. In the speed-up columns a value below 1 means C2 is slower than C1.

"""
tail = r"""

C0 (single run, B=3; `audit_logs/c0_and_profile.log`): pool identical to C1 on all 5 instances; Layer 1 alone cuts ext_attempts by 49-60% and time by 1.6-1.9x (C0/C1). Most of the work the rule "saved" in Table 7 is already removed by Layer 1.

Profile of C2 (n12_s42, B=3, cProfile): `accept()` (shortcut update + rule) = 1.00 s of 1.51 s (66%); the `_try_*` feasibility calls are about 0.26 s. t_F does fall by 35-65% on the smaller pool, but t_F is only 3-6% of the total at n<=15 (up to 15% at alignment 0.50), so it cannot pay for the slower generation.

## 4. Equality verdict
**K\* identical on 50 of 50 drivers** (label instances, B=3 and 4) **and on all 20 main-grid instances**; brute force n=5,6 (3 seeds each): K\*(brute) = K\*(C1) = K\*(C2) in 6/6 (the rule fired 375-1784 times per instance). Max deviations over 20 profiles per instance: |dV| <= 2.8e-14, |dV_-k| <= 5.7e-14, |dPayment| <= 5.7e-14; allocations identical in every profile (no ties needed). The C2 Layer-2 pool is smaller than C1 in size, but it is **not a subset**: it contains routes absent from C1 (53 of 450 at n12_s42 B=3, 517 of 3371 at n15_s7 B=4; `audit_logs/equality_label_instances.log`) because their dominators were removed by the rule; none of them is in K\*. A statement "the C2 pool is a subset of the C1 pool" would be false.

## 5. Interpretation (one row of the Phase 4 table)
**C2 K\* == C1 K\*, payments equal, but t_total is not lower.** Integration is safe but slower in pure Python: the per-instance median ratio C1/C2 is 0.68 (B=3) and 0.52 (B=4) on the label instances, and the grid sample gives 0.87 (alignment 0.90) and 0.71 (0.50) (only 2 of 20 grid instances reach about 1.0). The extra bookkeeping (O(B) shortcut states and absorption per extension; 66% of C2 time) outweighs a 15-43% cut in extensions.
Secondary finding: **the rule fires for OD drivers** (30/30 OD drivers in the grid sample), contradicting "never fired for occasional drivers" (Paper.tex:1520 area, Master_writeup.md 8.2). Likely cause (hypothesis, not tested): in `t6_dp` the OD detour budget is enforced only at the home leg, so OD prefixes exist that `dp_fast` already discarded with its detour filter; the rule then removes them. OD pools are tiny either way.
Does Frontier get faster on the smaller C2 pool? Yes, t_F drops 35-65%, but the gain is computational only and small in absolute terms.

## 6. What this does NOT show
- n=20 and above, and B=4 on the main grid, were not run. The share of extensions saved rises with n and B here, so a crossover at larger sizes cannot be excluded.
- Single machine, pure Python 3.7. My port of the rule is not optimised (label copy, repeated `travel_time`, dict states), so part of the overhead is implementation, not the rule.
- Equality was checked on K\* pools and on brute force for n<=6; it was not checked on the full C2 pool through B/C, nor on the 1,500-instance grid.
- The C0 comparison is one timing run per instance. The OD-firing explanation is unverified.
- The completion-level bound audit (0 violations / 5.65 M completions) was done on `dp_fast` and was not repeated on the `t6_dp` port; here safety rests on K\* equality.

## 7. Recommended manuscript edits (only what the evidence supports)
1. Table `tab:label` and the sentences at Paper.tex:81, 175 and 1517-1525 (35-76% fewer extensions; 1.48/2.19 median, 1.72/2.94 pooled): delete the speed-up claim, or state the baseline explicitly ("against plain enumeration without label dominance"). Against production Algorithm A (Layer 1 on) the measured result is a slowdown (median 0.52-0.68x on the label instances).
2. State that the production implementation uses Layers 1 and 2 followed by Frontier and that the rule is integrated only in an experimental build; present safety (K\* and payments unchanged, brute force, audit), not speed, as the contribution of the label-rule section. Measured part, suggested phrasing: "Integrated into a label-setting implementation with label dominance, the rule reduced label extensions by 15-43% and the pool entering the frontier by 40-60%, and left the frontier and all payments unchanged, but increased the running time of Algorithm A (median ratio 0.5-0.9)."
3. Remove "never fired for occasional drivers", or restrict it to the enumerator baseline; in the label-setting implementation it fired for every OD driver.
4. The 75-100% pool removal and the B+C speed-ups come from C1 + Frontier and stay valid as stated (the denominator is the rule-off pool).
5. Master_writeup.md (8.2, contribution 3, the 1.48x/2.19x figures) needs the same changes; the sentence at Paper.tex:1390 is accurate.
"""
open("AUDIT_REPORT.md", "w", encoding="utf-8").write(head + tables + tail)
print("written", len(head + tables + tail))
