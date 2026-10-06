# Phase 1 answers (STOP 1) — branch exp-tiers-fd-dominance

Evidence: experiments/T2BFS/t6_dp.py (read in full), audit_logs2/phase1_ceiling.log|json, audit_logs2/phase1_example.log.
Regression: instrumented C1 == production dp_labeling.run_pool on 48/48 drivers (5 instances x B=3,4); ext_attempts equal to audit_logs/regression_rule_off.log.

## 1.1 Structure of run_dp
- Containers: Python lists + dict `frontier[touched]` (t6_dp.py:227); `closure_all`, `active`, `next_active` lists (:237-266). No heap, no recursion, no deque.
- Order: ROUND by round on touched = |IV|+|C| (loop :229). Inside a round: a "closure" that repeatedly expands delivery/home labels (while-loop :239-266), THEN pickups from all closure labels to round touched+1 (:273-291).
- Dominance is applied IN BATCHES (not at insertion), via `_filter_dominated_labels` on a per-key dict:
  (i) each closure iteration: `next_active` grouped by key (:258-266);
  (ii) each pickup round: `new_by_key` (:284-291);
  (iii) at the end on complete labels per (C, v) (:293-308).
  A batch = one closure iteration of one round, or one pickup round. Comparisons never cross batches.
- Same key in different batches: YES. Key (v,IV,C) fixes the last stop v, but not how the label got there.
  Concrete (n10_s999, B=3, gw0), key v=n11 IV={} C={o0,o2}:
  a = [p0 d0 p2 d2] batch ('D', level 2, iteration 1), (t,K,W)=(71.16,17.053,71.16)
  b = [p2 p0 d0 d2] batch ('D', level 2, iteration 2), (t,K,W)=(71.78,17.259,71.78)
  a strictly dominates b, never compared, b is expanded (8 extension attempts).
- Wasted expansion: yes (table below).
- Complete routes: `complete_by_C` (:221, :250, :255), per-(C,v) Layer-1 filter at :293-308, per-bundle Pareto (Layer 2) in dp_labeling.py:run_pool `_pareto_front` (:82, def :28).

## 1.2 DFS hypothesis: FALSE
The loop is a breadth-style, level-synchronous DP, not DFS: no branch is expanded to the end before another starts.
The real defect is different: batches are defined by (round, closure-iteration), but labels with the same key
can arise at different closure iterations (because deliveries of a round start from pickup-created labels that
already carry a different number of delivered orders). Tiers by event count m=|IV|+2|C| would put all same-key labels in one batch.
