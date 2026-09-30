# MISSING

Run 2026-09-29 12:11. Figures (or series) that could not be drawn from existing data without estimating, re-solving or reading excluded folders.

## FIG 1 — fig01_pool_growth.pdf
- Needs: routes per driver split by class (GW / OD), menus B3 and B4, per instance and n
- Looked in: D3 `rq2_shard*.csv` (column `pool_size` = total over all drivers); D5 `rq34_shard*.csv` (`pool_full`, `pool_kstar` = totals); D7 has per-driver rows but only emptiness flags, no route counts
- Note: Partial alternative exists but was NOT used: `spec_2a_2b/results/rq1_pool_size_check.log` has mean *bundles* (not routes) per driver by class, B3 only, alignment 0.70/0.90 only. Obtaining per-class route counts needs re-running Algorithm A (forbidden by §0.1). Decision for the user: (i) re-run Algorithm A with a per-driver pool-size logger, or (ii) plot bundles/driver from the log with a caption saying so, or (iii) drop FIG 1.

## FIG A6 — figA6_synthetic_label_rule_fd_price.pdf
- Needs: per-seed (or per-driver) label-extension saving and wall-clock speed-up of the label rule at FD price scales 0.6 / 1.0 / 1.4 (synthetic instances)
- Looked in: New_t4/files/*.csv|*.json (only RQ1 timing files present); T4_Label_Rule.tex §'Work and time'; AUDIT_REPORT_LABEL_RULE.md §3.3
- Note: Only a summary table exists: ranges 73–76% / 27–30% / 7–9% and speed-ups 2.8–3.1× / '≈1.0×' / 0.75×. The middle speed-up is not a number, so plotting it would be an estimate. Raw output of the synthetic runs was not saved; regenerating it = re-running the enumerator (forbidden by §0.1). Option: cite the table in text instead of a figure.

## FIG A7 — figA7_single_parameter_menu.pdf
- Needs: bundle-menu (d(B), t(B)) points of a representative driver, angular deviation sigma_psi, welfare loss of the one-parameter projection
- Looked in: whole repo except `Not Using (dont reed this folder)`
- Note: The only files with sigma_psi / gap data (v9, v9_1 outputs) sit in `Not Using (dont reed this folder)`, which the user asked not to read. Not opened. If the user wants this figure, confirm that folder may be used as a data source.

