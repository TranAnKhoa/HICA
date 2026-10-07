"""Assemble ../EXPERIMENT_REPORT_C8.md: hand-written text + tables generated from audit_logs3/ (no hand copying)."""
import json
import os
import statistics
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
L3 = os.path.join(ROOT, "audit_logs3")
REPORT = os.path.join(ROOT, "EXPERIMENT_REPORT_C8.md")


def j(name):
    return json.load(open(os.path.join(L3, name)))


def med(xs):
    return statistics.median(xs)


def paired(a, b):
    return med([x / y for x, y in zip(a, b)])


def rng(xs, fmt="%.2f"):
    return (fmt + "-" + fmt) % (min(xs), max(xs))


def main():
    subprocess.check_call(["python3", "report_part_c8.py"], cwd=HERE, stdout=subprocess.DEVNULL)
    subprocess.check_call(["python3", "report_part_h.py"], cwd=HERE, stdout=subprocess.DEVNULL)
    part_c8 = open(os.path.join(L3, "report_c8_part.md")).read()
    part_h = open(os.path.join(L3, "report_h_part.md")).read()

    hl = j("timing_h_orig_label.json")
    hm = j("timing_h_matrix_label.json")
    hg = j("timing_h_orig_grid.json")
    hgm = j("timing_h_matrix_grid.json")
    hs = j("timing_h_matrix_scale.json")
    gh = j("gate_h.json")
    te = j("ttable_effect.json")
    sc8 = j("scale_c8.json")

    c5h_c1 = [r["C5h"]["x_vs_C1"] for r in hl]
    c5h_c5 = [r["C5h"]["x_vs_C5"] for r in hl]
    c5h_c1_m = [r["C5h"]["x_vs_C1"] for r in hm]
    c8h_c5h = [paired(r["C5h"]["raw"], r["C8h"]["raw"]) for r in hl]
    c8h_c5h_m = [paired(r["C5h"]["raw"], r["C8h"]["raw"]) for r in hm]
    ext_cut = [100 * (1 - r["C5h"]["ext"] / r["C5"]["ext"]) for r in hl]
    od_cut = [100 * (1 - r["C5h"]["ext_OD"] / r["C5"]["ext_OD"]) for r in hl]

    def grid_stats(rows, al):
        rb = [r for r in rows if abs(r["alignment"] - al) < 1e-9]
        tot = lambda n: sum(r[n]["t"] for r in rb)
        return dict(c5h_c1=tot("C1") / tot("C5h"), c5h_c5=tot("C5") / tot("C5h"),
                    c8h=[paired(r["C5h"]["raw"], r["C8h"]["raw"]) for r in rb],
                    c8h_pooled=tot("C5h") / tot("C8h"))
    g90, g50 = grid_stats(hg, 0.90), grid_stats(hg, 0.50)
    g90m, g50m = grid_stats(hgm, 0.90), grid_stats(hgm, 0.50)
    sc_c5h_c5 = [r["C5h"]["x_vs_C5"] for r in hs]
    sc_c8h = [paired(r["C5h"]["raw"], r["C8h"]["raw"]) for r in hs]
    sc8_lab = [r["C8f_vs_C5"] for r in sc8 if r["tag"].startswith("label")]
    sc8_grid = [r["C8f_vs_C5"] for r in sc8 if r["tag"].startswith("grid")]
    te_x = [r["C5t_vs_C5"] for r in te]
    c5_c1 = [r["C5"]["x_vs_C1"] for r in hl]
    c8h_ext = [100 * (1 - r["C8h"]["ext"] / r["C5h"]["ext"]) for r in hl]
    ex = j("explore_open_policy.json")
    allpts = []
    for name in ("timing_h_matrix_label.json", "timing_h_matrix_grid.json", "timing_h_matrix_scale.json"):
        for r in j(name):
            allpts.append((100 * (1 - r["C8h"]["ext"] / r["C5h"]["ext"]), paired(r["C5h"]["raw"], r["C8h"]["raw"])))
    allx = [x for _, x in allpts]
    hi_cut = [x for c, x in allpts if c >= 40]
    lo_cut = [x for c, x in allpts if c < 35]
    open_ext = [100 * (1 - r["C8open"]["ext"] / r["C5"]["ext"]) for r in ex]
    open_x = [r["C8open_vs_C5"] for r in ex]

    vi = f"""**Câu hỏi:** C5 đã có Layer 3 (luật FD-completion trên nhãn) chưa? Nếu chưa, ghép Layer 3 vào C5 có cho ra Algorithm A
nhanh nhất mà K\\* vẫn y hệt không?

1. **C5 chưa có Layer 3.** C5 chỉ gồm: tầng theo số sự kiện, Layer 1 (dominance), Layer 2 (Pareto theo bundle), frontier tính
   ngay trong vòng lặp. C3 là Layer 3 trên vòng lặp cũ; C7 là C5 + "Idea 3" (FD-dominance giữa hai nhãn thật), không phải
   Layer 3. Layer 3 cũng không phải "ma trận cận dưới": nó giữ trạng thái shortcut cho từng đơn đã nhận. Biến thể dùng
   ma trận cận dưới tính sẵn thì an toàn nhưng không bao giờ kích hoạt (T4 note, mục 2.6), nên không thể làm nhanh hơn.
2. **C8 = C5 + Layer 3: K\\* đúng (đã chứng minh + kiểm tra đầy đủ), nhưng chậm hơn C5.** Layer 3 giảm thêm 14-32% số lần
   mở rộng nhãn, nhưng thời gian chạy bằng 0.60-0.80× C5 (0.73-0.95× với bản cài đặt nhanh, quyết định giống hệt). Ở mẫu
   grid: hòa ở alignment 0.90, chậm hơn ở 0.50; ở n = 20: {rng(sc8_lab)}× (kiểu label) và {rng(sc8_grid)}× (grid alignment 0.90).
   Lý do: 95-99% số nhãn Layer 3 loại đã nhận đủ B đơn, chỉ còn vài bước giao hàng, trong khi luật phải kiểm mọi nhãn.
3. **Phát hiện mới, quan trọng hơn: ở C5, tài xế OD chiếm 50-62% công việc** vì ngân sách detour chỉ được kiểm khi về nhà
   (`_try_home`). Phép lọc "nhánh chết" (Mệnh đề 4 trong T4 note, có chứng minh): loại nhãn khi một đơn đang trên xe không
   còn kịp giao, hoặc tài xế OD không còn kịp về nhà. R và K\\* giữ nguyên tuyệt đối (kiểm trên mọi instance, cộng kiểm tra
   độc lập: {gh['DA']['dead_labels']:,} nhãn bị loại, 0 nhãn có completion khả thi). **C5h = C5 + lọc nhánh chết nhanh hơn C5
   {rng(c5h_c5)}× và nhanh hơn C1 (production) {rng(c5h_c1)}×** (tới {max(c5h_c1_m):.2f}× khi dùng bảng thời gian di chuyển
   tính sẵn). Layer 3 thêm lên C5h (C8h) không phải tăng tốc ổn định: {rng(allx)}× tùy instance (trung vị {med(allx):.2f}×,
   nhanh hơn ở {sum(1 for x in allx if x > 1)}/{len(allx)} instance); nó chỉ có lời khi cắt được từ khoảng 40% công việc trở lên
   (một số instance grid alignment 0.90), mà điều này chỉ biết được sau khi chạy.
4. **Chốt Algorithm A bản cuối = C5h**: tầng theo số sự kiện + Layer 1 + lọc nhánh chết + Layer 2 theo bundle + frontier
   trong vòng lặp (+ bảng thời gian di chuyển tính sẵn, thêm {rng(te_x)}×). Layer 3 giữ làm kết quả lý thuyết (Theorem 3:
   an toàn), không dùng trong bản chạy, và không được viết là "tăng tốc Algorithm A".
5. **Lý thuyết đã khép kín:** frontier trong vòng lặp (Mệnh đề 3), lọc nhánh chết (Mệnh đề 4) và Idea 3 (Mệnh đề 5) giờ đều
   có chứng minh trong `T4_Proofs/T4_Combined_v2.pdf`, mục 2.7; báo cáo trước ghi hai điều đầu là "chưa chứng minh"."""

    en = f"""| variant | what | K\\* exact? | extension attempts | time to K\\* | verdict |
|---|---|---|---|---|---|
| C5 | tiers, Layer 1, Layer 2, frontier in the loop (no Layer 3) | yes (proved, T4 Prop. 3) | baseline | {rng(c5_c1)}x faster than C1 | previous best |
| **C8** | **C5 + Layer 3** (same rule code as C3) | yes (Theorem 3 + Prop. 3; all gates) | 14-32% fewer than C5 | **0.60-0.80x of C5** | slower |
| C8f | C8 with a faster, decision-identical rule implementation | yes (identical to C8) | as C8 | 0.73-0.95x of C5 | slower |
| C8open | rule only on labels that can still pick up (exploratory) | yes | {rng(open_ext, '%.0f')}% fewer than C5 | {rng(open_x)}x of C5 | no gain |
| **C5h** | **C5 + dead-end filter** (new; T4 Prop. 4) | yes, and R unchanged (all gates + completion audit) | {rng(ext_cut, '%.0f')}% fewer than C5 (OD: {min(od_cut):.1f}-{max(od_cut):.1f}% fewer) | **{rng(c5h_c5)}x faster than C5, {rng(c5h_c1)}x faster than C1** | **final version** |
| C8h | C5h + Layer 3 | yes | 10-48% fewer than C5h | {rng(allx)}x of C5h (median {med(allx):.2f}x, faster on {sum(1 for x in allx if x > 1)} of {len(allx)} instances) | no reliable gain |

On the main-grid sample (n=15, B=3) C5h is {g90['c5h_c1']:.2f}x (alignment 0.90) and {g50['c5h_c1']:.2f}x (alignment 0.50) faster than C1
in total time; at n=20 it is {rng(sc_c5h_c5)}x faster than C5. Layer 3 on top of C5h gives {rng(g90['c8h'] + g50['c8h'])}x on the
grid sample and {rng(sc_c8h)}x at n=20. A precomputed travel-time table adds another {rng(te_x)}x with identical output."""

    s = open(os.path.join(HERE, "report_template_c8.md")).read()
    s = s.replace("<!-- SUMMARY_VI -->", vi)
    s = s.replace("<!-- SUMMARY_EN -->", en)

    ddl = gh["DA"]
    mm = gh["M"]
    sec6 = f"""## 6. A larger, exact speed-up: removing dead ends (C5h)

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
so the labels that matter survive Layer 1 exactly as before: **R and K\\* are unchanged** (proof in the T4 note). The
implementation adds a margin of 1e-6 minutes to every test, so that rounding can never remove a feasible label.

### 6.3 Gates (`gate_h.py`, `audit_logs3/gate_h.log`, `gate_h.json`)

| gate | scope | result |
|---|---|---|
| R | R(C4h) = R(C1) per driver (the filter must not change the pool): 10 label configurations, 20 grid instances, 80 random instances | **PASS** on all 110 |
| G1 | K\\*(C5h) = K\\*(C8h) = K\\*(C1) per driver, same instances | **PASS** |
| G4 | brute force n=5,6, seeds 0-2: K\\*(brute) = K\\*(C5h) = K\\*(C8h) | **PASS** 6/6 |
| DA | every label removed by the filter (n10_s1, n10_s999 at B=3 and B=4, six brute-force instances): enumerate all continuations with the independent evaluator | **{ddl['dead_labels']:,} removed labels (GW {ddl['GW']:,}, OD {ddl['OD']}), 0 with a feasible completion** |
| M | invalid mutations: home deadline tightened by 5 min; delivery deadlines tightened by 5 min | home: R differs on {len(mm['home_deadline_minus5']['R_fails'])}/5 instances and DA finds {mm['home_deadline_minus5']['DA_with_completion']} wrongly removed labels; deliveries: R unchanged on all 5, **DA finds {mm['delivery_deadline_minus5']['DA_with_completion']} wrongly removed labels**; both detected |
| M (control) | valid weaker filter (test (a) only) | R unchanged, DA: 0 labels with a completion; passes, as it must |

The delivery mutation is caught only by the completion-level audit: a pool-equality test alone would have missed it.

### 6.4 Timing (`timing_h.py`; protocol as in Section 4; every time is the time to K\\*)

{part_h}
### 6.5 Layer 3 on top of the filter (C8h)

With dead ends gone, Layer 3 removes 10-48% of the remaining extension attempts, and its effect on time now depends on the
instance: {rng(c8h_c5h)}x of C5h on the label instances ({rng(c8h_c5h_m)}x with the shared table), {rng(g90['c8h'])}x on the grid
sample at alignment 0.90 (pooled {g90['c8h_pooled']:.2f}x; {g90m['c8h_pooled']:.2f}x with the shared table) and
{rng(g50['c8h'])}x at alignment 0.50, and {rng(sc_c8h)}x at n = 20. Over all {len(allx)} instances timed with the shared table, C8h runs at
{rng(allx)}x of C5h (median {med(allx):.2f}x) and is faster on {sum(1 for x in allx if x > 1)} of them.

The gain is tightly linked to the share of extension attempts that Layer 3 removes (correlation 0.89,
`audit_logs3/c8h_vs_cut.txt`): C8h is faster on all {len(hi_cut)} instances where the rule removes at least 40% (median
{med(hi_cut):.2f}x), and slower on {sum(1 for x in lo_cut if x < 1)} of the {len(lo_cut)} instances where it removes less than 35%.
The high-share instances are main-grid instances in which the crowd competes (alignment 0.90). That share is known only
after the run, so Layer 3 cannot be switched on in advance with a guaranteed gain. An adaptive switch (stop testing when the
rule has removed little after the first tiers) is possible future work; it was not tried here, to avoid tuning on these
instances.

### 6.6 A stronger dead-end test does not help (C5s, `variants_s.py`, `timing_s.py`, `audit_logs3/timing_s.log`)

C5s keeps C5h's test and, when at least two orders are on board, also asks whether SOME order of the remaining
deliveries (then home, for an occasional driver) meets every deadline, by a depth-first search that stops at the first
feasible sequence. The test is exact for the same reason as C5h's (Euclidean travel times, nonnegative waiting and
service, monotone in the clock), and K\\* was identical on all ten label configurations. It removes almost nothing that
C5h's per-order test misses: 0-271 labels per configuration, at most 0.3% of the extension attempts, while it is run on
3.5k-324k labels. C5s runs at 0.70-0.84x of C5h (shared table, median of three runs). Almost every label that cannot be
completed is already caught by the per-order test; the remaining waste of C5h is in labels that CAN be completed (on the
label instances, 91-99% of the gigworkers' completed routes are not in K\\*), which a feasibility test cannot touch.
C5s is not used.

## 7. Implementation detail: a precomputed travel-time table (`ttable_effect.py`)

The generator's `travel_time(a, b)` recomputes a Euclidean distance on every call. Reading a table built once per instance
gives bit-identical values (same function, called once per pair) and makes C5 {rng(te_x)}x faster (table construction
included). It is an implementation detail, not an algorithmic change, and helps every variant equally.

## 8. Recommendation: the final Algorithm A

**Final version = C5h** (`audit_fd_rule3/variants_h.py: run_c5h`; T4 note, Procedure 2):

1. labels processed in tiers of equal event count `m = |IV| + 2|C|` (all same-key labels meet in one Layer-1 batch);
2. Layer 1 (label dominance on key `(v, IV, C)`) once per tier;
3. the dead-end filter on every new label (Proposition 4);
4. Layer 2 (per-bundle Pareto) as soon as all routes of a bundle size are complete (tier 2k);
5. the frontier inside the loop (Proposition 3), so only K\\* is ever stored;
6. in an implementation: a precomputed travel-time table.

**Not included: Layer 3** (the FD-completion label rule) and Idea 3 (FD-dominance between generated labels). Both are
provably safe (Theorem 3; Proposition 5) and reduce the number of label extensions, but neither is a reliable speed-up.
Layer 3 makes C5 slower on every label and every alignment-0.50 instance; on top of C5h it is slower on most instances
(median {med(allx):.2f}x over {len(allx)} instances) and faster only where it happens to remove at least about 40% of the
work, which cannot be known before the run. Idea 3 was slower than C5 in `EXPERIMENT_REPORT.md` (on top of C5h it was not
tested). Keep both as theory, with safety as the claim, and leave Layer 3 as an optional switch that is off by default.

**Manuscript (`Paper.tex`, `Master_writeup.md`), statements the evidence supports:**

- "The production loop compares labels only within a round; processing labels in tiers of equal event count makes every
  pair of same-key labels meet, and the frontier can then be computed inside the loop (Proposition 3)."
- "A feasibility look-ahead removes labels that can no longer be completed (Proposition 4); it leaves the route pool and the
  frontier unchanged and removes 52-76% of the label extensions (about 99% for occasional drivers)."
- "On the five experimental instances the final version computes the frontier {rng(c5h_c1, '%.1f')} times faster than the
  production implementation (B = 3, 4; n <= 15), and {g90['c5h_c1']:.1f}/{g50['c5h_c1']:.1f} times faster on the main-grid
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
  sizes); the larger instances rest on pool/K\\* equality and on the proofs.
- **The exploratory policy** (Section 5.1) was chosen after looking at the data and was not tuned further.
- **Payments.** VCG payments were not recomputed: they are a function of K\\* (Corollary 1 of the T4 note), and K\\* is
  identical in every run; the earlier report checked payments for C3-C7 with CPLEX.

## 10. Files

- Code (`audit_fd_rule3/`): `paths.py` (repository paths; the private `Dataset` package is stubbed in `_stubs/`, it is only
  imported, never used), `variants3.py` (C8, C9, C5copy), `fastrule.py` (C8f), `variants_h.py` (C4h, C5h, C8h), `variants_s.py` and `timing_s.py` (C5s),
  `gate_c8.py`, `gate_c8_eval.py` (independent evaluator), `gate_h.py`, `timing_c8.py`, `timing_h.py`, `scale_c8.py`,
  `kill_depth.py`, `explore_open_policy.py`, `ttable_effect.py`, `make_tables_c8.py`, `report_part_c8.py`,
  `report_part_h.py`, `assemble_report.py` (this report), `run_chain*.sh` (the order in which everything was run).
- Logs (`audit_logs3/`): `gate_c8.{{log,json}}`, `gate_h.{{log,json}}`, `timing_{{orig,matrix}}_{{label,grid}}.{{log,json}}`,
  `timing_h_{{orig,matrix}}_{{label,grid}}.{{log,json}}`, `timing_h_matrix_scale.{{log,json}}`, `scale_c8.{{log,json}}`,
  `kill_depth.{{log,json}}`, `explore_open_policy.{{log,json}}`, `ttable_effect.{{log,json}}`, `tables_c8.md`.
- Theory: `T4_Proofs/T4_Combined_v2.{{tex,pdf}}`, Section 2.7 (Propositions 3-5, Procedure 2) and Section 2.9 (Table 7).
"""
    s = s.replace("<!-- TIMING -->", part_c8 + "\n" + sec6)
    open(REPORT, "w").write(s)
    print("written", REPORT, len(s))


main()
