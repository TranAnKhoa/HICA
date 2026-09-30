### Table A: work saved (label-rule instances; ext = calls to _try_pickup/_try_delivery/_try_home)

| instance | B | ext C1 | ext C2 | saved % | killed_layer3 | routes_layer2 C1 | routes_layer2 C2 | routes_kstar C1 / C2 (identical) |
|---|---|---|---|---|---|---|---|---|
| n12_s42 | 3 | 71870 | 52663 | 26.7 | 14594 | 879 | 450 | 28 / 28 (True) |
| n10_s1 | 3 | 51361 | 40147 | 21.8 | 10672 | 714 | 478 | 165 / 165 (True) |
| n15_s7 | 3 | 187895 | 118650 | 36.9 | 47465 | 1561 | 941 | 165 / 165 (True) |
| n12_s123 | 3 | 111944 | 78947 | 29.5 | 25682 | 1416 | 766 | 208 / 208 (True) |
| n10_s999 | 3 | 37800 | 29570 | 21.8 | 7935 | 510 | 324 | 77 / 77 (True) |
| n12_s42 | 4 | 658706 | 515705 | 21.7 | 111294 | 2648 | 1574 | 74 / 74 (True) |
| n10_s1 | 4 | 530486 | 438690 | 17.3 | 88146 | 1845 | 1155 | 416 / 416 (True) |
| n15_s7 | 4 | 2635861 | 1801521 | 31.7 | 677686 | 5401 | 3371 | 603 / 603 (True) |
| n12_s123 | 4 | 1208860 | 903056 | 25.3 | 270442 | 4199 | 2268 | 482 / 482 (True) |
| n10_s999 | 4 | 316079 | 269268 | 14.8 | 57459 | 1104 | 651 | 193 / 193 (True) |

### Table B: time (s, median of 10 alternating runs; t_total = t_A + t_F)

| instance | B | t_A C1 | t_A C2 | t_F C1 | t_F C2 | t_total C1 | t_total C2 | speed-up C1/C2 total [IQR] |
|---|---|---|---|---|---|---|---|---|
| n12_s42 | 3 | 0.536 | 0.858 | 0.0324 | 0.0160 | 0.566 | 0.874 | 0.61 [0.581-0.670] |
| n10_s1 | 3 | 0.485 | 0.764 | 0.0400 | 0.0249 | 0.525 | 0.791 | 0.68 [0.661-0.716] |
| n15_s7 | 3 | 1.704 | 2.214 | 0.0610 | 0.0409 | 1.767 | 2.254 | 0.80 [0.772-0.804] |
| n12_s123 | 3 | 1.004 | 1.414 | 0.0593 | 0.0350 | 1.070 | 1.448 | 0.73 [0.718-0.747] |
| n10_s999 | 3 | 0.315 | 0.518 | 0.0227 | 0.0164 | 0.337 | 0.534 | 0.61 [0.589-0.635] |
| n12_s42 | 4 | 4.457 | 8.841 | 0.3534 | 0.1862 | 4.855 | 9.023 | 0.52 [0.507-0.559] |
| n10_s1 | 4 | 4.135 | 7.622 | 0.3982 | 0.2822 | 4.557 | 7.909 | 0.52 [0.520-0.540] |
| n15_s7 | 4 | 22.280 | 38.741 | 0.8040 | 0.5086 | 23.100 | 39.316 | 0.58 [0.577-0.587] |
| n12_s123 | 4 | 9.767 | 18.362 | 0.6783 | 0.3639 | 10.430 | 18.725 | 0.56 [0.550-0.564] |
| n10_s999 | 4 | 2.427 | 5.266 | 0.1512 | 0.1065 | 2.578 | 5.370 | 0.48 [0.479-0.491] |

B=3: median per-instance speed-up 0.68; pooled total-time ratio (C1/C2) median 0.72

B=4: median per-instance speed-up 0.52; pooled total-time ratio (C1/C2) median 0.56

### Table C: equality C1 vs C2 (K* pools, 20 profiles: truthful + 19 uniform[18,25]; CPLEX 12.10)

| instance | B | K* identical? | max abs dV | max abs dV_-k | max abs dPayment | allocation identical? (ties?) |
|---|---|---|---|---|---|---|
| n12_s42 | 3 | True | 0.0e+00 | 2.8e-14 | 2.8e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n10_s1 | 3 | True | 0.0e+00 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n15_s7 | 3 | True | 2.8e-14 | 5.7e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n12_s123 | 3 | True | 2.8e-14 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n10_s999 | 3 | True | 2.8e-14 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n12_s42 | 4 | True | 2.8e-14 | 2.8e-14 | 2.8e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n10_s1 | 4 | True | 2.8e-14 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n15_s7 | 4 | True | 2.8e-14 | 5.7e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n12_s123 | 4 | True | 2.8e-14 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |
| n10_s999 | 4 | True | 2.8e-14 | 2.8e-14 | 5.7e-14 | yes (differs in 0 profiles, 0 of them equal-Z ties) |

### Table D: main-grid sample (n=15, supply (3,3), B=3, reps 0-9; sums over 10 instances)

| alignment | ext C1 | ext C2 | saved % | routes_L2 C1 | routes_L2 C2 | K* C1 / C2 | t_A C1 | t_A C2 | t_F C1 | t_F C2 | t_total C1 | t_total C2 | ratio C1/C2 | drivers with rule fired GW | OD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.90 | 2963369 | 1682227 | 43.2 | 26792 | 20750 | 4742 / 4742 | 29.01 | 33.83 | 1.277 | 0.874 | 30.29 | 34.72 | 0.87 | 30/30 | 30/30 |
| 0.50 | 1530283 | 1108065 | 27.6 | 29860 | 11491 | 12 / 12 | 11.19 | 17.08 | 1.256 | 0.436 | 12.47 | 17.54 | 0.71 | 30/30 | 30/30 |

K* identical on every one of the 20 grid instances: True