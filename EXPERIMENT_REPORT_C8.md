# EXPERIMENT_REPORT_C8: can Layer 3 (the FD-completion label rule) make C5 faster?

Question (author, 2026-10-07): C5 was the fastest variant of `EXPERIMENT_REPORT.md`, but it uses only
Layer 1 (label dominance) and Layer 2 (per-bundle Pareto), plus the frontier inside the loop. Layer 3
of the T4 note (the FD-completion label rule) discards partial routes early and provably leaves K\*
unchanged. Does C5 already contain Layer 3, and if not, does C5 + Layer 3 give a faster final
Algorithm A?

Code: `audit_fd_rule3/`. Raw logs: `audit_logs3/`. Theory: `T4_Proofs/T4_Combined_v2.pdf`, Section 2.7.

## Tóm tắt (tiếng Việt)

**Câu hỏi:** C5 đã có Layer 3 (luật FD-completion trên nhãn) chưa? Nếu chưa, ghép Layer 3 vào C5 có cho ra Algorithm A
nhanh nhất mà K\* vẫn y hệt không?

1. **C5 chưa có Layer 3.** C5 chỉ gồm: tầng theo số sự kiện, Layer 1 (dominance), Layer 2 (Pareto theo bundle), frontier tính
   ngay trong vòng lặp. C3 là Layer 3 trên vòng lặp cũ; C7 là C5 + "Idea 3" (FD-dominance giữa hai nhãn thật), không phải
   Layer 3. Layer 3 cũng không phải "ma trận cận dưới": nó giữ trạng thái shortcut cho từng đơn đã nhận. Biến thể dùng
   ma trận cận dưới tính sẵn thì an toàn nhưng không bao giờ kích hoạt (T4 note, mục 2.6), nên không thể làm nhanh hơn.
2. **C8 = C5 + Layer 3: K\* đúng (đã chứng minh + kiểm tra đầy đủ), nhưng chậm hơn C5.** Layer 3 giảm thêm 14-32% số lần
   mở rộng nhãn, nhưng thời gian chạy bằng 0.60-0.80× C5 (0.73-0.95× với bản cài đặt nhanh, quyết định giống hệt). Ở mẫu
   grid: hòa ở alignment 0.90, chậm hơn ở 0.50; ở n = 20: 0.82-0.89× (kiểu label) và 0.77-1.17× (grid alignment 0.90).
   Lý do: 95-99% số nhãn Layer 3 loại đã nhận đủ B đơn, chỉ còn vài bước giao hàng, trong khi luật phải kiểm mọi nhãn.
3. **Phát hiện mới, quan trọng hơn: ở C5, tài xế OD chiếm 50-62% công việc** vì ngân sách detour chỉ được kiểm khi về nhà
   (`_try_home`). Phép lọc "nhánh chết" (Mệnh đề 4 trong T4 note, có chứng minh): loại nhãn khi một đơn đang trên xe không
   còn kịp giao, hoặc tài xế OD không còn kịp về nhà. R và K\* giữ nguyên tuyệt đối (kiểm trên mọi instance, cộng kiểm tra
   độc lập: 12,182 nhãn bị loại, 0 nhãn có completion khả thi). **C5h = C5 + lọc nhánh chết nhanh hơn C5
   1.57-2.86× và nhanh hơn C1 (production) 1.92-3.90×** (tới 4.39× khi dùng bảng thời gian di chuyển
   tính sẵn). Layer 3 thêm lên C5h (C8h) không phải tăng tốc ổn định: 0.78-1.32× tùy instance (trung vị 0.92×,
   nhanh hơn ở 9/41 instance); nó chỉ có lời khi cắt được từ khoảng 40% công việc trở lên
   (một số instance grid alignment 0.90), mà điều này chỉ biết được sau khi chạy.
4. **Chốt Algorithm A bản cuối = C5h**: tầng theo số sự kiện + Layer 1 + lọc nhánh chết + Layer 2 theo bundle + frontier
   trong vòng lặp (+ bảng thời gian di chuyển tính sẵn, thêm 1.06-1.11×). Layer 3 giữ làm kết quả lý thuyết (Theorem 3:
   an toàn), không dùng trong bản chạy, và không được viết là "tăng tốc Algorithm A".
5. **Lý thuyết đã khép kín:** frontier trong vòng lặp (Mệnh đề 3), lọc nhánh chết (Mệnh đề 4) và Idea 3 (Mệnh đề 5) giờ đều
   có chứng minh trong `T4_Proofs/T4_Combined_v2.pdf`, mục 2.7; báo cáo trước ghi hai điều đầu là "chưa chứng minh".

## 0. Summary

| variant | what | K\* exact? | extension attempts | time to K\* | verdict |
|---|---|---|---|---|---|
| C5 | tiers, Layer 1, Layer 2, frontier in the loop (no Layer 3) | yes (proved, T4 Prop. 3) | baseline | 1.18-1.48x faster than C1 | previous best |
| **C8** | **C5 + Layer 3** (same rule code as C3) | yes (Theorem 3 + Prop. 3; all gates) | 14-32% fewer than C5 | **0.60-0.80x of C5** | slower |
| C8f | C8 with a faster, decision-identical rule implementation | yes (identical to C8) | as C8 | 0.73-0.95x of C5 | slower |
| C8open | rule only on labels that can still pick up (exploratory) | yes | 3-8% fewer than C5 | 0.86-1.04x of C5 | no gain |
| **C5h** | **C5 + dead-end filter** (new; T4 Prop. 4) | yes, and R unchanged (all gates + completion audit) | 52-76% fewer than C5 (OD: 98.6-100.0% fewer) | **1.57-2.86x faster than C5, 1.92-3.90x faster than C1** | **final version** |
| C8h | C5h + Layer 3 | yes | 10-48% fewer than C5h | 0.78-1.32x of C5h (median 0.92x, faster on 9 of 41 instances) | no reliable gain |

On the main-grid sample (n=15, B=3) C5h is 2.07x (alignment 0.90) and 2.35x (alignment 0.50) faster than C1
in total time; at n=20 it is 1.74-2.10x faster than C5. Layer 3 on top of C5h gives 0.84-1.21x on the
grid sample and 0.82-1.32x at n=20. A precomputed travel-time table adds another 1.06-1.11x with identical output.

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

## 6. A larger, exact speed-up: removing dead ends (C5h)

### 6.1 Where the work goes

In C5 (and C1) occasional drivers account for 50-62% of all extension attempts on the label instances, although their
frontier holds 6-7 routes. `experiments/T2BFS/t6_dp.py` checks an occasional driver's detour budget only in `_try_home`
(home deadline = departure + direct time + budget), and a delivery's closing time only in `_try_delivery`. A prefix that can
no longer reach home in time, or that carries an order whose delivery can no longer be reached before it closes, is still
extended to the end. Section 3.1 shows the same effect from the other side: many Layer-3 firings have no feasible
completion at all, i.e. Layer 3 was largely removing such dead ends, at the price of testing every label.

### 6.2 The filter (`variants_h.py`; T4 note, Proposition 4)

A new label `L = (v, IV, C, t, K, W)` is discarded if (a) some order `j` on board has `t + tau(v, d_j) > l(d_j)`, or
(b) the driver is occasional and
`max( t + tau(v, home), max_j [ max(t + tau(v, d_j), e(d_j)) + s(d_j) + tau(d_j, home) ] ) > l(home)`.
Both left-hand sides are lower bounds on what any completion needs (triangle inequality, nonnegative waiting and service),
so a discarded label has no feasible completion. A label dominated by a label without feasible completion has none either,
so the labels that matter survive Layer 1 exactly as before: **R and K\* are unchanged** (proof in the T4 note). The
implementation adds a margin of 1e-6 minutes to every test, so that rounding can never remove a feasible label.

### 6.3 Gates (`gate_h.py`, `audit_logs3/gate_h.log`, `gate_h.json`)

| gate | scope | result |
|---|---|---|
| R | R(C4h) = R(C1) per driver (the filter must not change the pool): 10 label configurations, 20 grid instances, 80 random instances | **PASS** on all 110 |
| G1 | K\*(C5h) = K\*(C8h) = K\*(C1) per driver, same instances | **PASS** |
| G4 | brute force n=5,6, seeds 0-2: K\*(brute) = K\*(C5h) = K\*(C8h) | **PASS** 6/6 |
| DA | every label removed by the filter (n10_s1, n10_s999 at B=3 and B=4, six brute-force instances): enumerate all continuations with the independent evaluator | **12,182 removed labels (GW 11,325, OD 857), 0 with a feasible completion** |
| M | invalid mutations: home deadline tightened by 5 min; delivery deadlines tightened by 5 min | home: R differs on 5/5 instances and DA finds 15 wrongly removed labels; deliveries: R unchanged on all 5, **DA finds 883 wrongly removed labels**; both detected |
| M (control) | valid weaker filter (test (a) only) | R unchanged, DA: 0 labels with a completion; passes, as it must |

The delivery mutation is caught only by the completion-level audit: a pool-equality test alone would have missed it.

### 6.4 Timing (`timing_h.py`; protocol as in Section 4; every time is the time to K\*)

#### Label instances, generator's travel-time function (`timing_h_orig_label.json`)

| instance | B | C1 (s) | C5 (s) | C5h (s) | C8h = C5h + Layer 3 (s) | C5 vs C1 | C5h vs C1 | C5h vs C5 | C8h vs C5h | ext C5 | ext C5h | OD ext C5 -> C5h |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| n12_s42 | 3 | 0.143 | 0.121 | 0.052 | 0.055 | 1.20x | 2.73x | 2.36x | 0.94x | 62875 | 18456 | 38641 -> 284 |
| n10_s1 | 3 | 0.131 | 0.108 | 0.068 | 0.080 | 1.23x | 1.92x | 1.57x | 0.84x | 43548 | 21034 | 22483 -> 176 |
| n15_s7 | 3 | 0.442 | 0.361 | 0.177 | 0.181 | 1.19x | 2.46x | 2.04x | 0.98x | 156332 | 54434 | 96827 -> 350 |
| n12_s123 | 3 | 0.274 | 0.221 | 0.137 | 0.142 | 1.24x | 1.97x | 1.60x | 0.98x | 94338 | 43429 | 48535 -> 338 |
| n10_s999 | 3 | 0.089 | 0.075 | 0.039 | 0.051 | 1.18x | 2.21x | 1.85x | 0.81x | 32574 | 13181 | 17473 -> 240 |
| n12_s42 | 4 | 1.391 | 1.025 | 0.349 | 0.389 | 1.38x | 3.90x | 2.86x | 0.90x | 527545 | 128785 | 320840 -> 284 |
| n10_s1 | 4 | 1.437 | 1.000 | 0.611 | 0.753 | 1.46x | 2.33x | 1.63x | 0.84x | 389497 | 188766 | 196087 -> 176 |
| n15_s7 | 4 | 7.455 | 5.521 | 2.503 | 2.445 | 1.34x | 3.00x | 2.25x | 1.03x | 1893101 | 645939 | 1168771 -> 350 |
| n12_s123 | 4 | 3.294 | 2.211 | 1.342 | 1.388 | 1.48x | 2.43x | 1.64x | 0.99x | 881938 | 408182 | 443833 -> 338 |
| n10_s999 | 4 | 0.758 | 0.531 | 0.275 | 0.334 | 1.43x | 2.77x | 1.90x | 0.83x | 238575 | 91029 | 128434 -> 240 |

B=3 (travel-time function): median per-instance speed-up C5h vs C1 2.21x, C5h vs C5 1.85x, C8h vs C5h 0.94x; pooled C5h vs C1 2.28x; extension attempts C5h vs C5 61% fewer.

B=4 (travel-time function): median per-instance speed-up C5h vs C1 2.77x, C5h vs C5 1.90x, C8h vs C5h 0.90x; pooled C5h vs C1 2.82x; extension attempts C5h vs C5 63% fewer.

K* identical in every run: True

#### Label instances, shared travel-time table (`timing_h_matrix_label.json`)

| instance | B | C1 (s) | C5 (s) | C5h (s) | C8h = C5h + Layer 3 (s) | C5 vs C1 | C5h vs C1 | C5h vs C5 | C8h vs C5h | ext C5 | ext C5h | OD ext C5 -> C5h |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| n12_s42 | 3 | 0.137 | 0.120 | 0.048 | 0.053 | 1.14x | 2.86x | 2.41x | 0.92x | 62875 | 18456 | 38641 -> 284 |
| n10_s1 | 3 | 0.122 | 0.096 | 0.060 | 0.075 | 1.23x | 2.03x | 1.64x | 0.80x | 43548 | 21034 | 22483 -> 176 |
| n15_s7 | 3 | 0.394 | 0.325 | 0.146 | 0.157 | 1.20x | 2.71x | 2.20x | 0.94x | 156332 | 54434 | 96827 -> 350 |
| n12_s123 | 3 | 0.257 | 0.211 | 0.125 | 0.139 | 1.22x | 2.04x | 1.66x | 0.90x | 94338 | 43429 | 48535 -> 338 |
| n10_s999 | 3 | 0.080 | 0.064 | 0.034 | 0.043 | 1.24x | 2.35x | 1.87x | 0.79x | 32574 | 13181 | 17473 -> 240 |
| n12_s42 | 4 | 1.289 | 0.981 | 0.297 | 0.343 | 1.37x | 4.39x | 3.09x | 0.86x | 527545 | 128785 | 320840 -> 284 |
| n10_s1 | 4 | 1.426 | 0.946 | 0.573 | 0.734 | 1.48x | 2.42x | 1.71x | 0.80x | 389497 | 188766 | 196087 -> 176 |
| n15_s7 | 4 | 6.949 | 5.130 | 2.135 | 2.213 | 1.36x | 3.23x | 2.45x | 0.96x | 1893101 | 645939 | 1168771 -> 350 |
| n12_s123 | 4 | 3.107 | 2.188 | 1.169 | 1.274 | 1.41x | 2.58x | 1.86x | 0.92x | 881938 | 408182 | 443833 -> 338 |
| n10_s999 | 4 | 0.701 | 0.486 | 0.231 | 0.292 | 1.46x | 3.04x | 2.09x | 0.80x | 238575 | 91029 | 128434 -> 240 |

B=3 (shared table): median per-instance speed-up C5h vs C1 2.35x, C5h vs C5 1.87x, C8h vs C5h 0.90x; pooled C5h vs C1 2.40x; extension attempts C5h vs C5 61% fewer.

B=4 (shared table): median per-instance speed-up C5h vs C1 3.04x, C5h vs C5 2.09x, C8h vs C5h 0.86x; pooled C5h vs C1 3.06x; extension attempts C5h vs C5 63% fewer.

K* identical in every run: True

#### Main-grid sample, n=15, supply (3,3), B=3, reps 0-9 (`timing_h_*_grid.json`)

| setting | alignment | C1 (s, sum) | C5 (s, sum) | C5h (s, sum) | C8h (s, sum) | C5 vs C1 | C5h vs C1 | C5h vs C5 | C8h vs C5h per instance: min / median / max | ext C5 -> C5h |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| travel-time function | 0.90 | 8.87 | 6.87 | 4.29 | 4.00 | 1.29x | 2.07x | 1.60x | 0.84 / 1.14 / 1.21 | 2411163 -> 1165324 |
| travel-time function | 0.50 | 3.29 | 2.73 | 1.40 | 1.52 | 1.20x | 2.35x | 1.95x | 0.86 / 0.91 / 0.95 | 1392547 -> 491947 |
| shared table | 0.90 | 7.92 | 6.33 | 3.77 | 3.73 | 1.25x | 2.10x | 1.68x | 0.78 / 1.07 / 1.15 | 2411163 -> 1165324 |
| shared table | 0.50 | 3.10 | 2.60 | 1.27 | 1.42 | 1.19x | 2.43x | 2.04x | 0.84 / 0.90 / 0.93 | 1392547 -> 491947 |

#### n = 20, shared travel-time table, 3 timed runs (`timing_h_matrix_scale.json`)

| instance | B | C1 (s) | C5 (s) | C5h (s) | C8h (s) | C5h vs C5 | C5h vs C1 | C8h vs C5h | ext C5 | ext C5h |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| label n20_s42 | 3 | 1.06 | 0.82 | 0.45 | 0.47 | 1.80x | 2.25x | 0.96x | 379029 | 154377 |
| label n20_s7 | 3 | 1.70 | 1.43 | 0.79 | 0.86 | 1.77x | 2.20x | 0.89x | 520212 | 236739 |
| label n20_s123 | 3 | 1.10 | 0.86 | 0.44 | 0.47 | 1.85x | 2.48x | 0.95x | 377939 | 160551 |
| label n20_s42 | 4 | - | 14.70 | 7.16 | 7.91 | 2.10x | - | 0.90x | 5860609 | 2202082 |
| label n20_s7 | 4 | - | 31.13 | 16.77 | 18.05 | 1.84x | - | 0.92x | 9605160 | 4372843 |
| label n20_s123 | 4 | - | 14.59 | 7.64 | 7.46 | 1.91x | - | 1.02x | 5730924 | 2335542 |
| grid a0.90_n20_rep0 | 3 | 2.11 | 1.92 | 1.03 | 0.78 | 1.86x | 2.03x | 1.32x | 589169 | 278657 |
| grid a0.90_n20_rep1 | 3 | 2.50 | 2.10 | 1.12 | 1.33 | 1.81x | 2.20x | 0.82x | 620552 | 295825 |
| grid a0.90_n20_rep2 | 3 | 2.19 | 1.89 | 1.07 | 1.06 | 1.77x | 2.07x | 0.99x | 612531 | 286547 |
| grid a0.90_n20_rep3 | 3 | 2.40 | 2.10 | 1.13 | 1.45 | 1.81x | 2.06x | 0.82x | 627411 | 296505 |
| grid a0.90_n20_rep4 | 3 | 2.13 | 1.94 | 1.08 | 0.92 | 1.74x | 1.97x | 1.18x | 595897 | 286646 |

K* identical in every run: True

### 6.5 Layer 3 on top of the filter (C8h)

With dead ends gone, Layer 3 removes 10-48% of the remaining extension attempts, and its effect on time now depends on the
instance: 0.81-1.03x of C5h on the label instances (0.79-0.96x with the shared table), 0.84-1.21x on the grid
sample at alignment 0.90 (pooled 1.08x; 1.01x with the shared table) and
0.86-0.95x at alignment 0.50, and 0.82-1.32x at n = 20. Over all 41 instances timed with the shared table, C8h runs at
0.78-1.32x of C5h (median 0.92x) and is faster on 9 of them.

The gain is tightly linked to the share of extension attempts that Layer 3 removes (correlation 0.89,
`audit_logs3/c8h_vs_cut.txt`): C8h is faster on all 7 instances where the rule removes at least 40% (median
1.14x), and slower on 31 of the 32 instances where it removes less than 35%.
The high-share instances are main-grid instances in which the crowd competes (alignment 0.90). That share is known only
after the run, so Layer 3 cannot be switched on in advance with a guaranteed gain. An adaptive switch (stop testing when the
rule has removed little after the first tiers) is possible future work; it was not tried here, to avoid tuning on these
instances.

## 7. Implementation detail: a precomputed travel-time table (`ttable_effect.py`)

The generator's `travel_time(a, b)` recomputes a Euclidean distance on every call. Reading a table built once per instance
gives bit-identical values (same function, called once per pair) and makes C5 1.06-1.11x faster (table construction
included). It is an implementation detail, not an algorithmic change, and helps every variant equally.

## 8. Recommendation: the final Algorithm A

**Final version = C5h** (`audit_fd_rule3/variants_h.py: run_c5h`; T4 note, Procedure 2):

1. labels processed in tiers of equal event count `m = |IV| + 2|C|` (all same-key labels meet in one Layer-1 batch);
2. Layer 1 (label dominance on key `(v, IV, C)`) once per tier;
3. the dead-end filter on every new label (Proposition 4);
4. Layer 2 (per-bundle Pareto) as soon as all routes of a bundle size are complete (tier 2k);
5. the frontier inside the loop (Proposition 3), so only K\* is ever stored;
6. in an implementation: a precomputed travel-time table.

**Not included: Layer 3** (the FD-completion label rule) and Idea 3 (FD-dominance between generated labels). Both are
provably safe (Theorem 3; Proposition 5) and reduce the number of label extensions, but neither is a reliable speed-up.
Layer 3 makes C5 slower on every label and every alignment-0.50 instance; on top of C5h it is slower on most instances
(median 0.92x over 41 instances) and faster only where it happens to remove at least about 40% of the
work, which cannot be known before the run. Idea 3 was slower than C5 in `EXPERIMENT_REPORT.md` (on top of C5h it was not
tested). Keep both as theory, with safety as the claim, and leave Layer 3 as an optional switch that is off by default.

**Manuscript (`Paper.tex`, `Master_writeup.md`), statements the evidence supports:**

- "The production loop compares labels only within a round; processing labels in tiers of equal event count makes every
  pair of same-key labels meet, and the frontier can then be computed inside the loop (Proposition 3)."
- "A feasibility look-ahead removes labels that can no longer be completed (Proposition 4); it leaves the route pool and the
  frontier unchanged and removes 52-76% of the label extensions (about 99% for occasional drivers)."
- "On the five experimental instances the final version computes the frontier 1.9-3.9 times faster than the
  production implementation (B = 3, 4; n <= 15), and 2.1/2.3 times faster on the main-grid
  sample (alignment 0.90/0.50, n = 15, B = 3)."
- "The FD-completion label rule is safe (Theorem 3) and removes a further 14-32% of the extensions, but in our
  implementation it does not reliably reduce running time: almost all labels it removes already carry B orders, so each
  removal saves little, while every label must be tested. It pays only on instances where it removes a large share of the
  work (about 40% or more), which occurred on some main-grid instances where the crowd competes."
- Remove or qualify the label-rule speed-ups 1.48x / 2.19x (Table `tab:label` of Paper.tex): they compare the rule with an
  enumerator **without** label dominance (see `AUDIT_REPORT.md`, section 7).
- Remove "the rule never fires for occasional drivers": in the label-setting implementation it fires for every occasional
  driver of the grid sample, mostly on dead ends.

## 9. What this does NOT show

- **Sizes.** Label instances n <= 15 (B = 3, 4), grid sample n = 15 (B = 3), and a small n = 20 check (3 label-style
  instances at B = 3 and 4, 5 grid instances at alignment 0.90, 3 timed runs). The full 1,500-instance grid was not run.
- **One machine, pure Python.** Intel Xeon 2.1 GHz cloud container, Python 3.13.16; the earlier reports used Python 3.7.7 on
  a Ryzen laptop. The ranking C1 < C4 < C5 reproduced closely, but absolute times differ. A compiled implementation could
  change the cost balance of Layer 3 (its test is cheap arithmetic, its savings are label creations); this was not tested.
- **Statistical depth.** Medians of 10 paired runs (5 on the grid, 3 at n = 20); no confidence intervals.
- **The completion audits** (G5 for Layer 3, DA for the dead-end filter) were run on instances with n <= 10 (and brute-force
  sizes); the larger instances rest on pool/K\* equality and on the proofs.
- **The exploratory policy** (Section 5.1) was chosen after looking at the data and was not tuned further.
- **Payments.** VCG payments were not recomputed: they are a function of K\* (Corollary 1 of the T4 note), and K\* is
  identical in every run; the earlier report checked payments for C3-C7 with CPLEX.

## 10. Files

- Code (`audit_fd_rule3/`): `paths.py` (repository paths; the private `Dataset` package is stubbed in `_stubs/`, it is only
  imported, never used), `variants3.py` (C8, C9, C5copy), `fastrule.py` (C8f), `variants_h.py` (C4h, C5h, C8h),
  `gate_c8.py`, `gate_c8_eval.py` (independent evaluator), `gate_h.py`, `timing_c8.py`, `timing_h.py`, `scale_c8.py`,
  `kill_depth.py`, `explore_open_policy.py`, `ttable_effect.py`, `make_tables_c8.py`, `report_part_c8.py`,
  `report_part_h.py`, `assemble_report.py` (this report), `run_chain*.sh` (the order in which everything was run).
- Logs (`audit_logs3/`): `gate_c8.{log,json}`, `gate_h.{log,json}`, `timing_{orig,matrix}_{label,grid}.{log,json}`,
  `timing_h_{orig,matrix}_{label,grid}.{log,json}`, `timing_h_matrix_scale.{log,json}`, `scale_c8.{log,json}`,
  `kill_depth.{log,json}`, `explore_open_policy.{log,json}`, `ttable_effect.{log,json}`, `tables_c8.md`.
- Theory: `T4_Proofs/T4_Combined_v2.{tex,pdf}`, Section 2.7 (Propositions 3-5, Procedure 2) and Section 2.9 (Table 7).

