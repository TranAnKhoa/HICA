# EXPERIMENT_REPORT_C8: can Layer 3 (the FD-completion label rule) make C5 faster?

Question (author, 2026-10-07): C5 was the fastest variant of `EXPERIMENT_REPORT.md`, but it uses only
Layer 1 (label dominance) and Layer 2 (per-bundle Pareto), plus the frontier inside the loop. Layer 3
of the T4 note (the FD-completion label rule) discards partial routes early and provably leaves K\*
unchanged. Does C5 already contain Layer 3, and if not, does C5 + Layer 3 give a faster final
Algorithm A?

Code: `audit_fd_rule3/`. Raw logs: `audit_logs3/`. Theory: `T4_Proofs/T4_Combined_v2.pdf`, Section 2.7.

## Tóm tắt (tiếng Việt)

<!-- SUMMARY_VI -->

## 0. Summary

<!-- SUMMARY_EN -->

## 1. Does C5 contain Layer 3?

No. C5 is `run_tier(..., fd_dom=False, inloop=True)` in `audit_fd_rule2/variants.py`: event-count tiers,
Layer 1 once per tier, Layer 2 per bundle, frontier inside the loop. It calls no label rule. Of the
variants of `EXPERIMENT_REPORT.md`, two touch label rules, and neither is "C5 + Layer 3":

| variant | engine | label rule | frontier |
|---|---|---|---|
| C3 | production rounds (C1) | Layer 3 (`RuleFires`, virtual shortcut), lazily on Layer-1 survivors | post-hoc |
| C7 | tiers (as C5) | Idea 3 (FD-dominance between two *generated* labels), not Layer 3 | in the loop |

So the combination asked for had not been run. It is variant **C8** below.

A remark on the "lower-bound matrix". Layer 3 is not a matrix: it keeps, for every picked order `j`,
the state of the shortcut that skips `j` (three numbers per order, updated in O(1) per extension) and
evaluates the bound `beta(L, {j})` of Definition 3 after every extension. A rule based on a precomputed
lower-bound matrix (decide before visiting a pickup, using the cheapest possible next stop) also exists
and is safe, but it never fired on the synthetic instances (T4 note, Section 2.6, "A negative result"):
its distance credit was 0.5-0.75 against FD prices of 15-21. A rule that never fires removes nothing and
cannot make Algorithm A faster, so it was not run again.

## 2. Variants and fairness

| id | what | code |
|---|---|---|
| C1 | production Algorithm A (rounds, Layer 1, Layer 2), post-hoc frontier | `variants.run_c1` (unchanged) |
| C4 | tiers, Layer 1, Layer 2, post-hoc frontier | `variants.run_c4` (unchanged) |
| C5 | tiers, Layer 1, Layer 2, frontier in the loop | `variants.run_c5` (unchanged) |
| C3, C7 | as in `EXPERIMENT_REPORT.md` (re-timed for continuity) | unchanged |
| **C8** | **C5 + Layer 3**: after the Layer-1 filter of each tier, every survivor goes through `RuleFires`; a label that fires is dropped with all its extensions | `variants3.run_tier_rule(rule=True)` |
| **C8f** | C8 with a faster implementation of the *same* rule: travel times and distance terms read from a table built once per instance, no `travel_time` calls inside the rule, same loops, same test order | `fastrule.py` |
| C5copy | `run_tier_rule` with the rule switched off (checks that the new code path equals C5) | `variants3.run_c5copy` |

Fairness, as in the earlier protocol: C8 re-uses unchanged the `_try_*` feasibility functions, Layer 1,
Layer 2, the in-loop frontier test and the rule functions `_next_sc` / `_rule_fires` of C3. C8f changes
only the rule's own code; its decisions are identical to C8 (checked: same pools and the same value of
every counter on every instance). Because C8f reads a travel-time table, a second timing setting gives
the **same table to every variant** (C1, C4, C5 read it through the travel-time function), so that no
variant profits alone from it.

## 3. Correctness: gates and proofs

### 3.1 Gates (`audit_fd_rule3/gate_c8.py`, `audit_logs3/gate_c8.log`, `gate_c8.json`)

| gate | scope | result |
|---|---|---|
| R0 regression | C5copy = C5 (pools); C8f = C8 (pools and every counter: extensions, labels killed by the rule, A evaluations, routes) | **PASS** on all 30 instances |
| G1 K\* equal to C1 | per driver; 10 label configurations (B=3,4) + 20 main-grid instances (n=15, (3,3), alignment 0.90/0.50, reps 0-9, B=3); variants C5, C8, C8f | **PASS**, 0 mismatches |
| G4 brute force | n=5,6, seeds 0-2: K\*(brute) = K\*(C8) | **PASS** 6/6 |
| H hunt | 80 random instances (n=6..9, seeds 100-119, B=3, 320 drivers): K\*(C8) = Frontier(R of C1) | **PASS**, 0 mismatches |
| G5 completion-level audit of Layer 3 inside C8 | every rule firing on n10_s1, n10_s999 (B=3) and the six brute-force instances; all feasible completions enumerated and re-simulated with an independent evaluator; check that L.sigma without j is feasible and `c(L.sigma) - c(L.sigma minus j) >= q_j` at theta = 18 | **11,238 firings (GW 5,419, OD 5,819), 8,589 completions, 0 violations**; smallest margin +0.0096 |
| G6 mutations | (a) A = 0 (credit the whole time saving); (b) no junction terms | (a) G1 fails on 5/5 instances, G5 2,331 violations; (b) G1 fails on 4/5, G5 813 violations: **both detected** |

Many firings have no feasible completion at all (11,238 firings, 8,589 completions): the rule also
removes dead-end prefixes, in particular occasional-driver prefixes that can no longer reach home within
the detour budget (that budget is checked only at the home leg in `t6_dp`).

### 3.2 Proofs

Everything C5 and C8 do is now proved; nothing rests on tests alone.

* **Layer 3 is safe** (Theorem 3 of the T4 note): discarding some or all labels that satisfy the rule
  leaves K\* unchanged. The proof uses only that every label is filtered by Layer 1 in exactly one batch
  and that its extensions are filtered in later batches (Lemma P3), which holds for the tiers of C5.
* **The in-loop frontier of C5 is exact** (new, T4 note, Proposition 3). `EXPERIMENT_REPORT.md` called it
  a hypothesis validated by tests. Proof, by induction on the bundle size: let `r` have bundle `S`, and
  suppose the routes accepted for smaller bundles are exactly the frontier routes of those bundles. The
  restricted substitutes used in the loop (idle route, accepted routes of proper sub-bundles, other Pareto
  routes of `S`) are a subset of `D(r)`, so the restricted margin is at least the true margin; hence
  every frontier route is accepted. If `r` is not in the frontier, Lemma 1 of the T4 note gives, for
  every report `b`, a substitute `u` in the frontier (or the idle route) with `S_u` a subset of `S` and
  `c_u(b) + q(S \ S_u) <= c_r(b)`; such a `u` is always among the restricted substitutes (by the induction
  hypothesis if `S_u` is smaller, as a route of the same bundle otherwise), so the restricted margin is
  `<= 0` everywhere and `r` is rejected. The argument needs only "no duplicate pairs", so it also holds
  for the smaller pool generated with Layer 3; therefore **C8 outputs exactly K\*** as well.
* **Idea 3 (FD-dominance between generated labels, C6/C7) is also safe** (new, T4 note, Proposition 5):
  every continuation of `L2` is feasible after `L1` (same stop, same load, earlier clock, fewer orders);
  the distance difference is exactly `K2 - K1`; Lemma 3 (absorption) bounds the time difference by
  `max(0, t2 - t1 - A)`; so every route through `L2` costs at least `q(T)` more than a feasible route
  serving `T` fewer orders, and the proof of Theorem 3 applies.

<!-- TIMING -->
