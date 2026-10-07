## 4. Timing of C8 (Layer 3 added to C5)

Machine: Intel Xeon @ 2.10 GHz (cloud container, 4 cores, one used), Linux, Python 3.13.16. The ranking of
C1, C3, C4, C5 and C7 reproduces `EXPERIMENT_REPORT.md` (Ryzen, Windows, Python 3.7): e.g. C5 is 1.21-1.24x
faster than C1 at B=3 here (1.15-1.23x there) and 1.30-1.46x at B=4 (1.33-1.43x there). Protocol of
`audit_fd_rule2/timing.py`: one warm-up, 10 timed runs per variant in alternating order, gc disabled, medians
of the paired ratios. Every time is the time to K\* (C1 includes its post-hoc frontier).

### 4.1 Label instances (`timing_orig_label.json`, `timing_matrix_label.json`)

| instance | B | C1 (s) | C5 (s) | C8 = C5 + Layer 3 (s) | C8f, fast rule code (s) | C5 vs C1 | C8 vs C5 | C8f vs C5 | C8f vs C5, shared table |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| n12_s42 | 3 | 0.141 | 0.117 | 0.183 | 0.150 | 1.21x | 0.65x | 0.79x | 0.77x |
| n10_s1 | 3 | 0.125 | 0.102 | 0.155 | 0.134 | 1.22x | 0.66x | 0.77x | 0.76x |
| n15_s7 | 3 | 0.444 | 0.362 | 0.489 | 0.400 | 1.24x | 0.75x | 0.91x | 0.88x |
| n12_s123 | 3 | 0.261 | 0.213 | 0.309 | 0.244 | 1.23x | 0.69x | 0.88x | 0.83x |
| n10_s999 | 3 | 0.088 | 0.070 | 0.110 | 0.094 | 1.24x | 0.65x | 0.75x | 0.73x |
| n12_s42 | 4 | 1.387 | 0.981 | 1.596 | 1.251 | 1.44x | 0.60x | 0.77x | 0.74x |
| n10_s1 | 4 | 1.457 | 0.989 | 1.520 | 1.294 | 1.46x | 0.67x | 0.76x | 0.77x |
| n15_s7 | 4 | 7.353 | 5.622 | 7.020 | 5.805 | 1.30x | 0.80x | 0.95x | 0.89x |
| n12_s123 | 4 | 3.309 | 2.295 | 3.301 | 2.721 | 1.44x | 0.72x | 0.86x | 0.84x |
| n10_s999 | 4 | 0.738 | 0.507 | 0.807 | 0.668 | 1.43x | 0.65x | 0.77x | 0.73x |

Ratios are medians of paired per-run ratios; a value below 1 in the last three columns means **slower than C5**.
The last column is the fair setting in which every variant reads the same precomputed travel-time table.
C8 is never faster than C5: 0.60-0.80x. Even the fast implementation C8f stays below C5 on every one of the
10 configurations: 0.75-0.95x with the generator's travel-time function, 0.73-0.89x when all variants share the table.

### Work (extension attempts; sums over all drivers)

| instance | B | ext C1 | ext C3 | ext C4 | ext C5 | ext C7 | ext C8 | ext C8f | rule kills (C8) | A evaluations (C8) | ext saved C8 vs C5 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n12_s42 | 3 | 71870 | 52627 | 62875 | 62875 | 54895 | 48082 | 48082 | 8102 | 1498 | 23.5% |
| n10_s1 | 3 | 51361 | 40057 | 43548 | 43548 | 38090 | 35119 | 35119 | 4570 | 734 | 19.4% |
| n15_s7 | 3 | 187895 | 118506 | 156332 | 156332 | 126363 | 105949 | 105949 | 23908 | 2331 | 32.2% |
| n12_s123 | 3 | 111944 | 78879 | 94338 | 94338 | 81056 | 69937 | 69937 | 12390 | 1756 | 25.9% |
| n10_s999 | 3 | 37800 | 29553 | 32574 | 32574 | 28927 | 26302 | 26302 | 3715 | 677 | 19.3% |
| n12_s42 | 4 | 658706 | 512837 | 527545 | 527545 | 459607 | 425721 | 425721 | 39050 | 14984 | 19.3% |
| n10_s1 | 4 | 530486 | 436193 | 389497 | 389497 | 339916 | 327025 | 327025 | 19842 | 7591 | 16.0% |
| n15_s7 | 4 | 2635861 | 1783862 | 1893101 | 1893101 | 1539907 | 1360327 | 1360327 | 184532 | 38211 | 28.1% |
| n12_s123 | 4 | 1208860 | 896323 | 881938 | 881938 | 763227 | 682910 | 682910 | 73529 | 23210 | 22.6% |
| n10_s999 | 4 | 316079 | 267626 | 238575 | 238575 | 216584 | 204063 | 204063 | 13662 | 5852 | 14.5% |

Layer 3 does what it promises on work: 14.5-32.2% fewer extension attempts than C5 with K\* unchanged. The time
it costs to test every surviving label is larger than the time those extensions would have taken.

### 4.2 Main-grid sample (n=15, supply (3,3), B=3, reps 0-9; 5 timed runs; `timing_*_grid.json`)

| setting | alignment | C5 vs C1 (pooled) | C8f vs C5 (pooled) | C8f vs C5 per instance: min / median / max | instances where C8f is faster | ext C5 -> C8f (sum) |
|---|---|---:|---:|---|---:|---|
| travel-time function | 0.90 | 1.27x | 1.00x | 0.80 / 1.07 / 1.23 | 6 of 10 | 2411163 -> 1513545 (-37%) |
| travel-time function | 0.50 | 1.19x | 0.80x | 0.75 / 0.79 / 0.85 | 0 of 10 | 1392547 -> 1049111 (-25%) |
| shared table | 0.90 | 1.25x | 0.97x | 0.78 / 1.02 / 1.13 | 5 of 10 | 2411163 -> 1513545 (-37%) |
| shared table | 0.50 | 1.21x | 0.76x | 0.72 / 0.76 / 0.81 | 0 of 10 | 1392547 -> 1049111 (-25%) |

Where the crowd competes (alignment 0.90), Layer 3 removes 23-47% of the extensions and C8f breaks even with C5
on aggregate (faster on about half of the instances, slower on the other half). Where the fixed fleet dominates
(alignment 0.50), it is slower on every instance. Full tables: `audit_logs3/tables_c8.md`.

## 5. Why Layer 3 does not pay: where it fires

For every label removed by Layer 3 in C8 we recorded |P(L)| = |IV| + |C| (`kill_depth.py`, `kill_depth.json`).

| instance | B | labels removed by Layer 3 | share with \|P(L)\| = B | share with nothing on board |
|---|---|---:|---:|---:|
| n12_s42 | 3 | 8102 | 98.7% | 18.1% |
| n10_s1 | 3 | 4570 | 97.7% | 19.2% |
| n15_s7 | 3 | 23908 | 98.1% | 13.6% |
| n12_s123 | 3 | 12390 | 98.0% | 16.1% |
| n10_s999 | 3 | 3715 | 97.5% | 18.3% |
| n12_s42 | 4 | 39050 | 96.9% | 10.5% |
| n10_s1 | 4 | 19842 | 94.8% | 8.8% |
| n15_s7 | 4 | 184532 | 97.1% | 6.7% |
| n12_s123 | 4 | 73529 | 96.8% | 9.2% |
| n10_s999 | 4 | 13662 | 94.7% | 8.5% |

94.7-98.7% of the labels that Layer 3 removes already carry B orders (|P(L)| = B: no further pickup is
possible). Such a label can only be followed by its remaining deliveries (and, for an occasional driver, the
home leg), so each removal saves a handful of extensions. The test, however, runs on every label that survives
Layer 1, and the shortcut states cost O(B) per label. The bound of Definition 3 becomes strong only late, when
the detour spent on an order is known, which is exactly where pruning is worth least. The decision-identical
fast implementation C8f narrows the gap but does not close it, so this is a property of the rule on these
instances rather than of one implementation.

### 5.1 Exploratory: test only labels that can still pick up an order (`explore_open_policy.py`)

Chosen **after** seeing the table above, so it is exploratory. Applying Layer 3 only when |P(L)| < B keeps K\*
(Theorem 3 allows the rule on any subset of labels), but it removes few labels (1-5% of those
that C8f removes) and is slower than C5 on 9 of the 10 configurations (0.86-0.96x; 1.04x on n10_s1 at B=3, within
run-to-run noise). Shared travel-time table, 5 runs:

| instance | B | C5 (s) | C8f (s) | C8open (s) | ext C5 | ext C8open | Layer-3 removals in C8open | C8open vs C5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| n12_s42 | 3 | 0.105 | 0.140 | 0.114 | 62875 | 60721 | 102 | 0.92x |
| n10_s1 | 3 | 0.111 | 0.131 | 0.102 | 43548 | 41963 | 106 | 1.04x |
| n15_s7 | 3 | 0.317 | 0.370 | 0.342 | 156332 | 144687 | 458 | 0.93x |
| n12_s123 | 3 | 0.195 | 0.238 | 0.202 | 94338 | 90385 | 248 | 0.96x |
| n10_s999 | 3 | 0.061 | 0.084 | 0.067 | 32574 | 31341 | 94 | 0.91x |
| n12_s42 | 4 | 0.852 | 1.152 | 0.965 | 527545 | 501937 | 1193 | 0.88x |
| n10_s1 | 4 | 0.876 | 1.140 | 0.977 | 389497 | 370053 | 1035 | 0.90x |
| n15_s7 | 4 | 4.975 | 5.575 | 5.410 | 1893101 | 1749970 | 5362 | 0.94x |
| n12_s123 | 4 | 2.065 | 2.434 | 2.230 | 881938 | 844444 | 2355 | 0.94x |
| n10_s999 | 4 | 0.455 | 0.599 | 0.532 | 238575 | 229265 | 718 | 0.86x |
