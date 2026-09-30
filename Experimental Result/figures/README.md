# Figures — HICA-S results (C&OR submission)

Built from `Experimental Result/Figure.md` by the scripts in `Experimental Result/plots/`.
Reproduce: `..\.venv-plots\Scripts\python.exe plots\make_all.py` (from `Experimental Result/`; the venv lives in the
repository root, versions pinned in `requirements-plots.txt`). `make_all.py` deletes old outputs first, so a figure
whose checks fail can never leave a stale file behind.

Nothing here re-solves, regenerates or interpolates: every point is read from the files listed in
`DATA_MANIFEST.md` (with SHA-256). Every figure recomputes its key numbers and compares them with the values in the
Master Write-up (`plots/expected.py`); a figure is written only if all its checks pass.

## Provenance and status

| Fig | File | Script | Data (codes in DATA_MANIFEST.md) | Checks | Status |
|---|---|---|---|---|---|
| C1 | `fig_c1_frontier_intuition` | `fig_c1.py` | none (Example 11, analytic) | 5/5 | OK |
| 1 | `fig01_pool_growth` | `fig01.py` | — | — | **MISSING**: no per-class route counts stored |
| 2 | `fig02_runtime_breakdown` | `fig02.py` | D5 (+ D3 for `t_B`) | 16/16 | OK |
| 3 | `fig03_payment_speedup` | `fig03.py` | D5 | 16/16 | OK |
| 4 | `fig04_label_rule` | `fig04.py` | D9 (timing JSON) | 15/15 | OK |
| 5 | `fig05_rq1_complementarity` | `fig05.py` | D1 (cross-check D2) | 32/32 | OK |
| 5b | `fig05b_sequential` | `fig05.py` | D1 (cross-check D1b) | 125/125 | OK (optional) |
| 6 | `fig06_rq2_bundling` | `fig06.py` | D3 | 17/17 | OK |
| 7 | `fig07_rq3_mechanisms` | `fig07.py` | D4 | 12/12 | OK |
| 8 | `fig08_regimes_certificate` | `fig08.py` | D3 (FD rate), D7, D12 | 23/23 | OK |
| 9 | `fig09_rq5_forest` | `fig09.py` | D6 | 10/10 | OK |
| A1 | `figA1_kstar_build_vs_pool` | `figA.py` | D5, D8 | 4/5 | **CHECK_FAIL**, see CHECK_FAILURES.md |
| A2 | `figA2_pool_compression` | `figA.py` | D5 | 4/4 | OK |
| A3 | `figA3_t5_components` | `figA.py` | D11 | 4/4 | OK |
| A4 | `figA4_synthetic_price_of_locality` | `figA.py` | D13 (audit log) | 9/9 | OK (synthetic) |
| A5 | `figA5_pipeline_scaling` | `figA.py` | D6 | 6/6 | OK |
| A6 | `figA6_synthetic_label_rule_fd_price` | `figA.py` | — | — | **MISSING**: only a range table, with "≈1.0×" |
| A7 | `figA7_single_parameter_menu` | `figA.py` | — | — | **MISSING**: data only in the excluded folder |

LaTeX blocks with the design widths: `captions.tex`. Lines marked `% CHANGED` differ from the draft captions in
Figure.md and say why.

## Deviations from Figure.md (and why)

- **Bootstrap seed for the checks.** Figures use `seed=20260929`. The checks that compare a CI with the Master
  Write-up rerun the same bootstrap with the seed the Write-up used (20260928 for RQ1, 20260927 for RQ2/3/5), in the
  same instance order. This reproduces the published CIs exactly and does not change any plotted number.
- **Instance order.** A fixed-seed bootstrap depends on row order; wide tables are built in file order (not with
  `pivot_table`, which reorders). Found when the first FIG 6 CI check failed; fixed in code, expected values untouched.
- **FIG 2.** No separate WDP time exists in the RQ4 files. `t_B` is the base WDP solve of the same instance from the
  RQ2 run. The draft caption said payments "never exceed 0.66 s at n=20". That is the median; the maximum is 1.15 s,
  so the caption was corrected.
- **FIG 3.** The diamond is the mean of log10(speed-up), i.e. a geometric mean. This is stated in the legend and caption.
- **FIG 4.** Only per-instance medians and IQRs over repeated runs were stored, not the raw repeats, so no strip is
  drawn. For B=3, instance n10 s999 uses the N=20 rerun, as in the Write-up.
- **FIG 8(a) and tick labels.** D1 has no FD-rate column. It is read from D3 menu B3, which is the same JOINT
  allocation on the same instances (check X1: max |Δ| = 1.1e-13).
- **FIG 9.** Filled markers mean the 95% CI excludes zero. Variant θ∼U[15,30] is described per Write-up §2.3: RQ5
  never restricts reports to Θ.
- **Environment.** SciencePlots with `no-latex`, so fonts do not match the paper exactly. If LaTeX is available,
  switch `style.py` to `["science"]`.

## Open items for the author

1. **FIG A1.** One check failed. µs/route for the RQ4 sample is 48.1–54.5; Figure.md expects 48–54. 36.96 ms / 678
   routes = 54.51 µs, so the spec range was probably truncated rather than rounded. Expected values were not edited
   (§0.3). If you accept 48–55, change `expected.FIGA1["us_RQ4"]` yourself and rerun.
2. **FIG 1.** Needs per-class (GW/OD) route counts. Options are in MISSING.md.
3. **FIG A6, A7.** See MISSING.md.

## TODO — diagrams in TikZ (not matplotlib, Figure.md §4)

- Pipeline overview (Master Write-up §19.2, "Fig 1" of the paper). A starting point exists in
  `New_t4/files/T4_Algorithm_Overview.tex`.
- Twin instances of Example 11 ($I_0$ vs $I_1$).
- Construction of Theorem 10.

## QA checklist (Figure.md §7)

- [x] Every main figure passes its checks; CHECK_FAILURES.md lists only A1 (appendix).
- [x] Grayscale previews are in `_gray/`. Series stay distinguishable by marker, line style or position.
- [x] Fonts are 7–8 pt at design width. No text is clipped (checked visually).
- [x] Every log axis says "log scale".
- [x] Units are on every axis (s, %, ×, pp, routes).
- [x] No titles inside figures. Panel labels (a)(b)(c) are bold, top left.
- [x] No "mean of cell medians" anywhere.
- [x] Synthetic figure: "synthetic" appears in the file name and caption (A4).
- [x] Alignment ticks carry the FD-rate row. "Neutral" is not used.
- [x] The FIG 3 caption states the single-auction figure (1.06×).
- [x] The FIG 7 caption says PAB-BR is not an equilibrium.
- [x] DATA_MANIFEST.md has SHA-256 hashes. This README has the provenance table.
