
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

(`build_all`/`run_cN` wrapper rows omitted; full output in `audit_logs2/profile.log`.) Cost inside C6's FD-dominance: **0.323 s total, of which the absorption term A is 0.057 s (18%) and the sub-bundle lookups and tests are 0.266 s (82%).** The tier engine itself (C4 vs C1) adds little bookkeeping: the same functions dominate and `_filter_dominated_labels` is called on fewer labels (18,539 vs 23,334 calls) because of the larger batches.

## 7. Interpretation (one row per variant)

| Variant | Observation (evidence) | Meaning | What to do |
|---|---|---|---|
| Ceiling / Idea 2a | `wasted_share` 7.9-22.1% (above 5%); after tiering 0.00% and 0 cross-batch pairs on all 10 configurations (Table C) | The production loop wastes work that is entirely recoverable by batching per event count | Idea 2a is **not** dropped; C4 captures the whole ceiling |
| **C4** | Passes G1-G4; R identical to C1; ext -12.5% to -28.2%; time 1.07-1.30x on the label instances, 1.16x (align 0.90) and 1.07x (align 0.50) on the grid | **A real speed-up of Algorithm A**, modest, growing with B (median 1.14x at B=3, 1.28x at B=4) | Report with the exact conditions (n <= 15, B = 3, 4); do not extrapolate to n = 20 |
| **C5** | Passes G1-G4, G7 (K* identical, 960 random drivers without a counterexample); time 1.15-1.43x on the label instances, 1.19x/1.14x on the grid; stores only K* (about 8x fewer routes than R on label instances at B=3; 5.65x fewer at align 0.90; Table "closeness") | Removes the post-hoc pass (`t_F` is 4-11% of C1's total) **and** the speed-up of C4. The additional gain of C5 over C4 is about `t_F`, as expected | Report as "outputs K* directly; the extra gain over C4 is the post-hoc pass". Memory saving is implied by the route counts but **was not measured** |
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
