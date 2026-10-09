# MASTER_SUMMARY: overview of Algorithm A, T4 v3 and what to check before the paper

Last updated: 2026-10-09. Branch: `claude/charming-ramanujan-ppzinr`.
Companion file: `BENCHMARK_GUIDE.md` (scale study with CPLEX, and the comparison benchmarks that still have to be
agreed with the author).

> **Rule for Claude Code** (see also `CLAUDE.md`): do not build any comparison benchmark (Part B of
> `BENCHMARK_GUIDE.md`) on your own initiative. Ask the author in detail first.

---

## Contents

1. [Decisions taken](#1-decisions-taken)
2. [The files that matter](#2-the-files-that-matter)
3. [Algorithm A: all variants tested and the numbers](#3-algorithm-a-all-variants-tested-and-the-numbers)
4. [The final Algorithm A = C5h: how it works](#4-the-final-algorithm-a--c5h-how-it-works)
5. [The dead-end filter in plain words](#5-the-dead-end-filter-in-plain-words)
6. [Why Layer 3 makes Algorithm A slower](#6-why-layer-3-makes-algorithm-a-slower)
7. [The bottleneck of C5h and the extra tests](#7-the-bottleneck-of-c5h-and-the-extra-tests)
8. [Running time of A + B + C, and scalability](#8-running-time-of-a--b--c-and-scalability)
9. [T4_Combined_v3: what changed and how it is organised](#9-t4_combined_v3-what-changed-and-how-it-is-organised)
10. [Assessment of the contribution and the reviewer risks](#10-assessment-of-the-contribution-and-the-reviewer-risks)
11. [Preliminary literature search: positioning](#11-preliminary-literature-search-positioning)
12. [Checklist before bringing T4 v3 into Paper.tex](#12-checklist-before-bringing-t4-v3-into-papertex)
13. [Open questions and next steps](#13-open-questions-and-next-steps)
14. [Commits on the branch](#14-commits-on-the-branch)

---

## 1. Decisions taken

| # | Decision | Reason |
|---|---|---|
| D1 | **The final Algorithm A = C5h** = event tiers + Layer 1 (dominance) + **dead-end filter** + Layer 2 (Pareto per bundle) + **frontier computed inside the loop**. It outputs K\* directly and never stores R. | Fastest of all variants (1.9–3.9× faster than production C1, 1.6–2.9× faster than C5). K\* is identical on every instance, and the result is proved. |
| D2 | **Layer 3 (the FD-completion label rule) is removed from Algorithm A and from the T4 proofs** (it is no longer Theorem 3). | Safe (proved and audited) but makes the run slower: 0.60–0.80× on C5, median 0.92× on C5h. |
| D3 | Of Layer 3, only a **short remark** is kept: rollback pruning cannot be transferred directly (unsafe, with a counterexample); the corrected version is safe but fires too late, so it does not speed things up. | A useful negative result; it answers the question "why not prune during the enumeration?". |
| D4 | The stronger dead-end test (C5s), the FD-dominance between labels (C6/C7) and switching the dead-end filter off for GW are **not used**. | C5s: 0.70–0.84×; C6/C7: 0.81–1.01×; GW without the filter: 0.79–1.14× (no clear gain). |
| D5 | The scale study with HiGHS was **stopped** (6/76 instances); the author will run it with CPLEX. | The paper uses CPLEX 12.10, which is not available in this container. |
| D6 | Comparison benchmarks against other methods/papers: **ideas only**; Claude Code must ask the author before building them. | The author's request. |

---

## 2. The files that matter

### 2.1 Theory

| File | Content |
|---|---|
| `T4_Proofs/T4_Combined_v3.tex` / `.pdf` | **Latest version (21 pages).** Two main theorems; the final Algorithm A; the rollback remark. |
| `T4_Proofs/T4_Combined_v2.tex` / `.pdf` | Previous version (28 pages), which still has Theorem 3 = Layer 3. Kept for reference. |
| `Paper.tex` | The paper manuscript (COR). **Not yet updated** to match T4 v3 (see Section 12). |

### 2.2 Code for the final Algorithm A and its audits

| File | Content |
|---|---|
| `audit_fd_rule3/variants_h.py` | **C5h** (`run_tier_h`, `run_c5h`), the dead-end filter (`make_dead`), C4h, C8h. |
| `audit_fd_rule2/variants.py` | Base engines: `run_round` (C1, C3), `run_tier` (C4–C7), `_kstar_filter_bundle` (in-loop frontier), `_bundle_front` (Layer 2). |
| `experiments/T2BFS/t6_dp.py` | `_try_pickup`, `_try_delivery`, `_try_home`, `_filter_dominated_labels` (Layer 1). Shared by every variant, unchanged. |
| `audit_fd_rule3/variants3.py`, `fastrule.py` | C8 and C8f (Layer 3 on top of C5). Kept to reproduce the negative result. |
| `audit_fd_rule3/variants_s.py`, `timing_s.py` | C5s (stronger dead-end test). Negative result. |
| `audit_fd_rule3/gate_c8.py`, `gate_h.py` | Correctness gates (K\*, brute force, hunt, completion audit, mutations). |
| `audit_fd_rule3/timing_c8.py`, `timing_h.py`, `scale_c8.py` | Timing protocols. |
| `audit_fd_rule3/kill_depth.py`, `explore_open_policy.py`, `ttable_effect.py` | Analysis of why Layer 3 is slow; effect of the precomputed travel-time table. |
| `audit_fd_rule3/wdp_highs.py`, `check_highs.py` | Algorithms B and C with HiGHS; check against CPLEX (48/48 match). |
| `audit_fd_rule3/scale_c5h.py` | The scale study (CPLEX by default). See `BENCHMARK_GUIDE.md`. |
| `audit_fd_rule3/paths.py`, `_stubs/Dataset` | Path setup (replaces `K:\Data Science\...`), stub for the private package. |

### 2.3 Reports and logs

| File | Content |
|---|---|
| `EXPERIMENT_REPORT.md` | Report on C1–C7 (tiers, in-loop frontier, FD-dominance). |
| `EXPERIMENT_REPORT_C8.md` | Report on C8 / C8f / C8h / **C5h** / C5s, with full tables and a Vietnamese summary. Built by `audit_fd_rule3/assemble_report.py`. |
| `audit_logs3/*.json`, `*.log` | All raw data: `gate_c8`, `gate_h`, `timing_*`, `timing_h_*`, `scale_c8`, `kill_depth`, `explore_open_policy`, `ttable_effect`, `timing_s`, `check_highs`, `scale_c5h_highs_partial`. |
| `BENCHMARK_GUIDE.md` | How to run the scale study with CPLEX, and ideas for comparison benchmarks. |

---

## 3. Algorithm A: all variants tested and the numbers

### 3.1 The variants

| ID | Description | K\* exact? | Extension attempts | Speed | Verdict |
|---|---|---|---|---|---|
| **C1** | Production Algorithm A: rounds on \|IV\|+\|C\|, closures over deliveries; Layer 1, Layer 2; frontier computed afterwards | baseline | baseline | baseline | old |
| C3 | C1 + Layer 3 (applied lazily to Layer-1 survivors) | yes | fewer | slower than C1 (0.69×) | rejected |
| C4 | Event tiers m = \|IV\|+2\|C\|; Layer 1 once per tier; Layer 2 per bundle; frontier afterwards | yes | 7.9–22.1% fewer than C1 | 1.14–1.28× of C1 | intermediate |
| **C5** | C4 + frontier inside the loop (stores only K\*) | yes (Prop 3) | as C4 | **1.18–1.48× faster than C1** | previous best |
| C6 / C7 | C4 / C5 + FD-dominance between generated labels ("Idea 3") | yes | 23–42% fewer | 0.81–1.01× | slower |
| C8 | C5 + Layer 3 | yes | 14–32% fewer than C5 | **0.60–0.80× of C5** | slower |
| C8f | C8 with a faster rule implementation (same decisions) | yes | as C8 | 0.73–0.95× of C5 | slower |
| C8open | Layer 3 only while the label can still pick up an order (\|P\|<B) | yes | 3–8% fewer than C5 | 0.86–1.04× | no gain |
| **C5h** | **C5 + dead-end filter** | **yes, and R is unchanged too** | **52–76% fewer than C5 (OD: 98.6–100% fewer)** | **1.57–2.86× faster than C5; 1.92–3.90× faster than C1** | **FINAL** |
| C8h | C5h + Layer 3 | yes | 10–48% fewer than C5h | 0.78–1.32× of C5h (median 0.92×; faster on 9/41 instances) | not stable |
| C5s | C5h + "deliverable in some order" test | yes | ≤0.3% fewer | 0.70–0.84× of C5h | slower |

### 3.2 Detailed numbers for C5h (label instances, 10 timed runs, Python 3.13, one core of a 2.1 GHz Xeon)

| Instance | B | C1 (s) | C5 (s) | C5h (s) | C5h vs C1 | C5h vs C5 |
|---|---|---:|---:|---:|---:|---:|
| n=12, seed 42 | 3 | 0.143 | 0.121 | 0.052 | 2.73× | 2.36× |
| n=10, seed 1 | 3 | 0.131 | 0.108 | 0.068 | 1.92× | 1.57× |
| n=15, seed 7 | 3 | 0.442 | 0.361 | 0.177 | 2.46× | 2.04× |
| n=12, seed 123 | 3 | 0.274 | 0.221 | 0.137 | 1.97× | 1.60× |
| n=10, seed 999 | 3 | 0.089 | 0.075 | 0.039 | 2.21× | 1.85× |
| n=12, seed 42 | 4 | 1.391 | 1.025 | 0.349 | 3.90× | 2.86× |
| n=10, seed 1 | 4 | 1.437 | 1.000 | 0.611 | 2.33× | 1.63× |
| n=15, seed 7 | 4 | 7.455 | 5.521 | 2.503 | 3.00× | 2.25× |
| n=12, seed 123 | 4 | 3.294 | 2.211 | 1.342 | 2.43× | 1.64× |
| n=10, seed 999 | 4 | 0.758 | 0.531 | 0.275 | 2.77× | 1.90× |

- Main-grid sample (n=15, (3,3), B=3, reps 0–9): C5h is **2.07×** (alignment 0.90) and **2.35×** (alignment 0.50)
  faster than C1 in total time.
- At n=20: C5h is 1.74–2.10× faster than C5, and 1.97–2.48× faster than C1 (shared travel-time table).
- A precomputed travel-time table gives another **1.06–1.11×** with identical output (up to 4.39× vs C1 with the table).

### 3.3 Correctness gates (all PASS)

- **R(C4h) = R(C1)** per driver: 10 label configurations (B=3,4), 20 main-grid instances, and an 80-instance hunt
  (n=6..9).
- **K\*(C5h) = K\*(C8h) = K\*(C1)** on the same instances.
- **Brute force**, n=5,6, seeds 0–2: K\*(brute) = K\*(C5h) = K\*(C8h), 6/6.
- **Dead-end audit:** 12,182 removed labels, **none of them has a feasible completion** (checked with an independent
  evaluator).
- **Mutations** (home deadline −5, delivery deadline −5) were detected; the valid control passes.
- C8 / Layer 3: 11,238 firings, 8,589 completions, 0 violations; mutations "A=0" and "no junction" detected.
- **HiGHS vs CPLEX:** C5h + HiGHS reproduces exactly Z and the total payout recorded by the paper (production A +
  CPLEX) on **48/48** instances (|ΔZ| ≤ 5.7e-14, |Δpayout| ≤ 1.1e-13).

---

## 4. The final Algorithm A = C5h: how it works

For each driver (drivers are independent, so they can run in parallel):

1. **Start** with the label (start point, nothing on board, nothing delivered, t0, K=0, W=0). A *label* is a partial
   route `(v, IV, C, t, K, W)`: current stop, orders on board, orders delivered, clock, distance cost, working time.
2. **Tiers** m = |IV| + 2|C| = 0, 1, 2, …: every extension (pickup or delivery) adds exactly one event, so labels
   with the same key `(v, IV, C)` always fall in the same tier.
3. In each tier:
   - **Layer 1 (dominance):** among labels with the same key, remove a label if another one arrives no later and
     has K and W no larger (one strictly smaller). Because of the tiers, every pair of same-key labels is compared
     (C1 missed 7.9–22.1% of the cases).
   - **Extensions:** deliver an order on board (`_try_delivery`); pick up a new order if |IV|+|C| < B
     (`_try_pickup`); for an occasional driver, go home once nothing is on board (`_try_home`).
   - **Dead-end filter:** every new label is checked at once and dropped if it can no longer be completed
     (Section 5).
   - **Completed routes:** when m = 2k (every route with k orders is complete), for each bundle S with |S| = k:
     **Layer 2** keeps the Pareto front on (K, W); then the **in-loop frontier** keeps the routes whose margin
     μ'_r(b) > 0 for some b ∈ Θ, computed against the idle route + the routes already accepted for smaller bundles
     + the other routes of the same bundle.
4. Output K\*_i directly. The full R_i is never stored.

**Proofs** (T4 v3, Section 2.7):
- **Prop 2** (in-loop frontier): the accepted routes are exactly K\*. Induction on the bundle size, using Lemma 1
  ("a kept substitute exists").
- **Prop 3** (dead ends): removing every dead label leaves R and K\* unchanged.

---

## 5. The dead-end filter in plain words

A **dead end** is a partial route that **cannot be completed validly, whatever happens next**.

**Why it used to be missed:** the production code checks
- the delivery deadline of order j only when j is actually delivered, and
- the home deadline (detour budget) of an occasional driver only at the final home leg.

A partial route that is already too late is therefore still extended through every delivery order before it is
rejected at the end. All that work is wasted.

**What the filter asks**, as soon as a label is created:
1. For every order on board: driving there directly right now, is the delivery deadline met?
2. Occasional driver: the earliest possible time back home (directly, or after delivering each order on board) —
   is it before the home deadline?

If the answer to either is no, the label is dropped.

**Why it is exact:** both checks use the *earliest possible* time. Detours are longer (triangle inequality), and
waiting and service are nonnegative, so a real route can only arrive later. Only labels that are certainly dead are
removed; R and K\* do not change at all. If a label that fails dominates another label with the same key, that label
fails too, so Layer 1 keeps exactly the same live labels.

**Effect:** in C5, occasional drivers took 50–62% of all extension attempts while their K\* held only a handful of
routes. With the filter they take under 1% (for example 350 out of 54k attempts on n15_s7, B=3).

**Picture:** before turning into an alley, look at the map; if the alley certainly has no exit, do not go in. The
old code walked to the end of the alley before turning back.

---

## 6. Why Layer 3 makes Algorithm A slower

### 6.1 What Layer 3 does

For every picked order j, the label keeps a "shadow": the same path without j, stored as `(D'_j, v'_j, r'_j)`. It
computes the distance spent on j, ΔD = D − D' − d(v', v_m), and the time spent on j,
δ = r − r' − τ(v', v_m), minus the waiting A that later stops can absorb. Then
β = κΔD + 18·max(0, δ − A)/60. **If β ≥ q_j**, sending j to FD is always cheaper, so the label and its whole
subtree are discarded.

### 6.2 Pinpointing the cause: cost on every label, savings only near the end

**Profile on n15_s7, B=3:**

| | C5 | C8 (= C5 + Layer 3) |
|---|---:|---:|
| Total time | 1.08 s | 1.60 s |
| travel_time calls | 148k | 492k (3.3×) |
| _try_pickup | 64k | 56k |
| _try_delivery | 86k | 47k |
| Time inside the rule | – | **0.875 s / 1.58 s** (54,723 updates and tests) |

- **Cost:** every label that survives Layer 1 pays: it updates the shadow of every picked order and runs the test.
- **Savings:** only about 0.2 s, because **94.7–98.7%** of the labels the rule removes already hold B orders, so only
  a few deliveries or the home leg are left (1–3 extensions saved per removal). 6.7–19% of them are completed
  prefixes with nothing on board.
- **Why it can only fire late:** the bound must hold for **every continuation**. Early in the route:
  - the detour caused by j is not fully known yet;
  - the time saved can be absorbed by waiting at later stops (term A);
  - the junction term reduces ΔD further.

  A precomputed lower-bound matrix gave a distance credit of only 0.5–0.75 against q of 15–21, and never fired.
- Many of the removals were OD dead ends, which the dead-end filter removes much more cheaply.
- Restricting the test (only labels that survived dominance — that is what C8 already did; or only labels with
  |P|<B, C8open) **cannot remove more**: the rule judges each label on its own, so testing fewer labels can only
  remove fewer. C8open removed only 1–5% as many labels as full Layer 3 and ran at 0.86–1.04×.

### 6.3 When Layer 3 does pay

Only when it removes **≥ 40%** of the remaining work: faster on 7/7 such instances (median 1.14×); slower on 31/32
instances where it removes < 35%. The correlation between gain and removed share is 0.89. That share is known only
after the run.

---

## 7. The bottleneck of C5h and the extra tests

**After the dead-end filter (5 label instances × B=3,4, shared travel-time table):**

- **Gigworkers do almost all the work:** OD < 1% of the extension attempts (e.g. 968 out of 4.37M on n20_s7, B=4).
- **The search explodes with B:** n15_s7 goes from 54k to 646k attempts (0.16 s → 2.05 s); n20_s7 from 237k to
  4.37M (0.79 s → 16.8 s).
- **Waste 1:** 47–54% (B=3) and 60–68% (B=4) of the labels created are then killed by Layer 1.
- **Waste 2:** only 1.3–8.9% of the gigworkers' completed routes enter K\*, so 91–99% are built in full and then
  thrown away by the frontier.
- **Profile** (one n=15, B=4 test instance): the main loop ~25%, `_try_delivery` ~20%, dead-end checks ~18%,
  `_try_pickup` ~15%, Layer 1 ~13%. There is no single hot spot: the cost is **number of labels × Python cost per
  label**.

**Extra tests (both negative):**
- **GW without the dead-end filter** (OD keep it): 0.79–1.14× of C5h, K\* identical. No clear gain, so the filter is
  kept for every driver.
- **C5s** (are the orders on board deliverable in some order before their deadlines? depth-first search, exact):
  removes 0–271 more labels (≤ 0.3% of attempts) while being run on 3.5k–324k labels; 0.70–0.84× of C5h. Reason:
  nearly every label that cannot be completed is already caught by the per-order test. What remains is waste on
  routes that *can* be completed but are expensive, which a feasibility test cannot touch.

**Conclusion:** among exact, feasibility-based filters, C5h is close to the limit. Going further needs a **cost
bound** (Layer 3 territory, which fires late) or **faster code** (numba/C++). The author does not want the latter,
because it would make the benchmark unfair.

---

## 8. Running time of A + B + C, and scalability

### 8.1 Data from the paper (production Algorithm A in Python 3.7 + CPLEX 12.10, one thread, B=3; `spec_2a_2b/results/rq_all`)

| n | A (median, s) | B + C (median, s) | Total |
|---|---|---|---|
| 10 | 0.26 (alignment 0.50) – 0.65 (0.90) | 0.04 – 0.13 | < 1 s |
| 15 | 1.00 – 2.20 | 0.09 – 0.25 | ~1.3 – 2.5 s |
| 20 | 2.56 – 7.40 (max 9.8) | 0.19 – 0.66 | ~3 – 8 s |
| 25 | 8.6 | – | ~10 s (max 13.7; includes extra solves) |
| 30 | 16.6 | – | **18.5 s median (max 28.8)** |

- With B=4: A = 13.6 s at n=15 (max 77 s); about 100 s at n=20.
- WDP alone (B, one solve; median): 0.12 s at n=20, B=3; 0.20 s at n=15, B=4.
- Pool size: about 5.4k routes at n=20 and 27k at n=30 (B=3).

### 8.2 Preliminary scale study (C5h + HiGHS; 6/76 instances; NOT for the paper)

| Instance | A_sum (s) | A_max (s) | B (s) | C (s) | Winners | Columns | RAM |
|---|---:|---:|---:|---:|---:|---:|---:|
| a0.90 n75 (3,3) rep0 | 85.4 | 29.7 | 13.39 | 59.52 | 6 | 95,188 | 3.0 GB |
| a0.90 n75 (3,3) rep1 | 75.5 | 26.4 | 3.98 | 17.58 | 6 | 48,196 | 2.9 GB |
| a0.50 n75 (3,3) rep0 | 29.6 | 10.1 | 0.01 | 0.01 | 1 | 129 | 1.1 GB |
| a0.50 n100 (3,3) rep0–2 | 63.8 – 88.0 | 21.4 – 48.6 | ≤ 0.10 | ≤ 0.17 | 2 – 4 | 219 – 1,026 | 2.1 – 2.3 GB |

Pilot runs: n=30 (3,3) a0.90: A_sum 7.2 s, B 0.20 s, C 0.95 s. n=50 (3,3) a0.90: A_sum 49.5 s (16–18 s per GW),
B 1.34 s, C 5.04 s.

### 8.3 Assessment for COR

- **Strengths to state in the paper:**
  - Algorithm A **reads no bid**, so it can run **before bidding closes**, while orders arrive. After the bids are
    in, only B + C are on the critical path, and they take < 1 s at n ≤ 20.
  - A runs **independently per driver**: linear in the number of drivers, and easy to parallelise.
- **Weaknesses a reviewer will see:**
  - The paper has n ≤ 30 and 4–8 drivers. That is small.
  - A grows roughly like n^B; Theorem 2 says no local rule can avoid this, so B ≤ 3 must be capped and the demand
    split into zones or time batches.
  - At large n with a competitive crowd, B + C is no longer negligible (n=75: 22–73 s on HiGHS). This must be
    measured with CPLEX.
- **What to do:** run Part A of `BENCHMARK_GUIDE.md` with CPLEX.

---

## 9. T4_Combined_v3: what changed and how it is organised

### 9.1 Removed (compared with v2)

- Theorem 3 (label rule preserves the frontier), Prop "label bound", Lemma "absorption of a time lead",
  Definition "shortcut quantities", Figures "junction" and "absorption".
- The "Layer 3" item in the description of Algorithm A; the "(b) / Case 2" branch of Lemma P3; "without Layer 3" in
  Lemma P4.
- Prop 5 (FD-dominance between labels), Procedure RuleFires, the `useRule` flag in the procedure.
- The label-rule audit table, the label-rule timing table, and the C8/C8h columns of the final table.
- ΔD, δ, A, β in the notation table (replaced by a row "label (v, IV, C, t, K, W)").
- The bullet "Theorem 3" in "How to read this note"; the boxes Lemma 3 / Prop 1 / Theorem 3 in the roadmap.

### 9.2 Added

- **Section 2.6 "Pruning partial routes by cost"**:
  - Remark "Rollback pruning needs a correction": in Lozano et al. (2016) time is a resource; here time is priced
    and waiting is allowed, so the direct transfer is unsafe. Two corrections (junction, absorption) make it safe;
    an earlier draft proved this, audited on about 5.65 million completions.
  - Example "Crediting the whole time saving is unsafe" (gigworker g0, o2, q = 17.13, credit 17.72 against a true
    saving of 7.24).
  - Paragraph "Why the rule is not part of Algorithm A", with the numbers of Section 6.
- One sentence on C5s in Section 2.8.

### 9.3 Structure of v3

- **Section 1 (self-contained):**
  - Notation table.
  - Preliminaries: Lemma P1 lines/envelopes, P2 removing stops never hurts, P3 completeness of Algorithm A, P4
    downward closure, P5 truthfulness (maximal-in-range).
  - The local frontier (definitions, Example "Twin instances").
  - **Theorem 1** (a: safety + Corollary 1 VCG; b: indispensability; c: minimality).
  - **Theorem 2** (price of locality, Θ(n^B)).
- **Section 2 (remarks, algorithms, evidence):**
  - 2.1 What the frontier is not (Remark three ways, Prop 1 NP-hard non-local, Remark realisable competitors).
  - 2.2 Loose feasibility (Remark Theorem 2 for OD).
  - 2.3 Monotonicity / Θ.
  - 2.4 Computing the frontier (Procedure 1).
  - 2.5 LP duality / literature.
  - **2.6 Pruning partial routes by cost.**
  - **2.7 The final Algorithm A** (Prop 2 in-loop frontier, Prop 3 dead ends, Procedure 2 GenerateRoutes).
  - 2.8 Computational evidence (synthetic audit, RQ4 table, certificate table, final Algorithm A table).
  - 2.9 Items to verify.

---

## 10. Assessment of the contribution and the reviewer risks

### 10.1 Removing Layer 3 does not weaken the paper much

- Its number in the manuscript ("35–76% fewer label extensions") was measured **against an enumerator without
  Layer 1**, not against Algorithm A. A reviewer who reproduces it would find a slowdown, so the claim was a risk.
- What is valuable (rollback cannot be transferred directly) is kept as a remark.
- The story is cleaner: **exact characterisation (Theorem 1) + impossibility of doing better (Theorem 2) +
  computational study.**

### 10.2 How strong the two theorems are

| Part | Assessment |
|---|---|
| Theorem 1(a) safety | Fairly natural (close to Sol 1994's redundancy). Two points make it non-trivial: the substitute may change with the report b, and safety must hold for every Clarke counterfactual. |
| Theorem 1(c) minimality | **The real content and the strongest point**: K\* is the smallest pool any local rule can keep ("optimal over a class"). |
| Theorem 2 price of locality | Medium to good. The construction is a standard technique, but it explains the GW/OD asymmetry structurally and closes the question with a tight bound. |
| Overall | A complete theoretical package (characterisation + minimality + tight bound), adequate for method-oriented OR journals (COR, TR-E, possibly EJOR). Not deep mathematics, but rigorous. |

**Real weakness:** K\* is obtained only *after* every route has been enumerated. The gain is in WDP and payments, not
in route generation. Say so plainly, and use Theorem 2 to justify that no local rule avoids the enumeration.

### 10.3 The risk "the authors pose the problem and solve it themselves, with no benchmark"

- The problem is not invented from scratch: the taxonomy comes from Luy et al. (2024); VCG on a platform-generated
  pool comes from Zou et al. (2022) and Li & Zhang (2026); FD at a public price corresponds to their backup
  vehicle / fixed price.
- The real desk-reject risk is the **lack of baselines against existing methods**. The fix is the benchmarks of
  Part B of `BENCHMARK_GUIDE.md` (classical safe rules, bid-reading pruning, Li & Zhang), not more theorems.
- T5 (component decomposition): the paper itself shows it brings little benefit (the conflict graph is almost
  always connected), so it should not be pushed into a strong theorem.

---

## 11. Preliminary literature search: positioning

(Only abstracts and snippets of search results; the proxy blocked INFORMS, RePEc, PMC and arXiv, so **no full text
has been read**.)

### 11.1 "No one has done combinatorial auctions, usually one driver – one order": not correct

- **Truckload procurement:** combinatorial auctions since 1992 (Sears, 6–20% savings; Caplice & Sheffi; reviews in
  IEEE Access 2023 and others).
- **Crowdshipping:**
  - Triki (2021, J. Cleaner Production): combinatorial auction for occasional drivers.
  - Mancini & Gansterer (Omega 2022; EURO JTL 2024): the company offers bundles (corridors/clusters), occasional
    drivers bid on bundles, at most one bundle per driver.
  - **Li & Zhang (Transportation Science, online 5 Jun 2026):** sealed-bid combinatorial auction, VCG + greedy,
    bundles along the carriers' routes. **The closest paper; cited in the manuscript as `li2026auction`.**
  - Oyama & Akamatsu: VCG with task chains.
  - Kafle, Zou & Lin (2017, TR-B): crowdsourcees bid.
- "One driver – one order" holds only for part of the literature (matching models, single-unit multi-attribute
  auctions).

### 11.2 Who solves the routing inside a bundle?

| Approach | Who routes | Examples | Drawback |
|---|---|---|---|
| **1. The bidder routes and prices each bundle** ("bid generation problem") | carrier / driver | Lee, Kwon & Ma (2007, TR-E); Song & Regan; Buer & Kopfer (2014); Mancini & Gansterer; Triki; Chen et al. (2023) | 2^n bundles; the bundle list must be restricted; the computational burden falls on the driver |
| **2. The platform routes, the driver bids one number** | platform | **Li & Zhang (2026)** (route-specific PDP, recursive branching on detour monotonicity, one detour-constrained class); Zou et al. (2022) | Relies on the detour budget, which an open-route GW does not have |

**HICA belongs to approach 2.** The positioning sentence to use:

> Platform-generated route pools exist, but they rely on detour monotonicity and so work for detour-constrained
> drivers. For open-route gigworkers that monotonicity breaks and the pool grows to Θ(n^B). This paper
> characterises exactly how far the pool can be reduced without breaking VCG (frontier, minimality, tight bound).

**Do not write "the first combinatorial auction / VCG for crowdshipping".**

### 11.3 To check in the full text of Li & Zhang (2026) (urgent)

1. Do their drivers bid one number (a value of time) or one price per bundle?
2. Do they prune the pool before bidding, and do they prove that the pruning is safe for VCG? If yes, the
   contribution must be repositioned carefully.
3. Do they include open-route drivers?
4. How does their greedy mechanism with a regret bound compare with the exact VCG of HICA?

Also check the citations Zou (2022) and Chen (2023) in `Paper.tex` (not confirmed by the search).

---

## 12. Checklist before bringing T4 v3 into Paper.tex

### 12.1 Layer 3 / label rule: remove or rewrite (line numbers as of 2026-10-09)

| Line(s) in `Paper.tex` | Content | Action |
|---|---|---|
| 80–81 | Abstract: "A provably safe label rule reaches the frontier with 35--76% fewer label extensions." | **Remove**. Replace, if wanted, with a sentence on the final Algorithm A (dead-end filter, in-loop frontier, 1.9–3.9× faster) or on rollback needing a correction. |
| 100 | Comment "A waiting-aware label rule…" | Remove. |
| 169–176 | Contribution 3 "A provably safe label rule (Theorems labelbound, preserve)… 35--76%" | **Rewrite or remove.** If kept: "direct transfer of rollback pruning is unsafe; a correction makes it safe but it fires too late to speed up enumeration". It is better merged into the Algorithm A contribution. |
| 209 | Organisation: "Section sec:label the label rule" | Edit. |
| 324–334 | Literature subsection "Label dominance and rollback pruning" | Keep, but change "Our label rule adapts rollback pruning" to a short remark. |
| 469 | "Sections sec:frontier and sec:label are stated…" | Remove sec:label. |
| 494 | Overview figure: "dominance, label rule, per-bundle Pareto" | Replace with "dominance, dead-end filter, per-bundle Pareto, in-loop frontier". |
| 586–587, 643 (`tab:layers`) | "Layer 3 is the optional FD-completion label rule…"; the Layer 3 row of the table | Remove the row; add a row for the dead-end filter. |
| 738, 747–748 | "Algorithm A without the label rule (useRule false)…"; "Pools produced with the label rule need not be downward closed; Theorem preserve…" | Simplify (no Layer 3 any more). |
| 1064–1237 | **Section "Reaching the frontier faster: an FD-completion label rule"** (rule, correctness, terms, implementation) | **Remove the whole section**; keep a short remark + Example `ex:rollback` (as in T4 v3, Section 2.6). |
| 1347 | RQ4: "How much work does the label rule save?" | Remove that question. |
| 1390 | "the production implementation does not use the label rule…" | Rewrite: say which Algorithm A version is timed (see 12.2). |
| 1440, 1447 | Heading "The frontier and the label rule"; "five further instances used for the label rule" | Edit the heading and wording. |
| 1502–1548 | Paragraph "The label rule" + Table `tab:label` (1.48×/2.19×…) | **Remove** (it was measured against an enumerator without Layer 1). |
| 1802, 1818 | Discussion/Conclusion mention the label rule | Edit. |
| 1942–2035 | Appendix "Proofs for the label rule" | Remove. |
| 2040, 2082 | Audit appendix: sec:label, table "Synthetic audit of the label rule" | Remove the label-rule part. |
| Bibliography | lozano2016exact, feillet2004exact | Keep (used in the remark). |

After editing, compile and search for `labelbound`, `thm:preserve`, `sec:label`, `useRule`, `Layer~3`, `label rule`
to catch broken references.

### 12.2 Final Algorithm A (C5h): bring in

- [ ] Describe Algorithm A = C5h (event tiers, Layer 1, dead-end filter, Layer 2, in-loop frontier). Procedure
      `GenerateRoutes` from T4 v3, Section 2.7.
- [ ] Bring in **Prop "in-loop frontier"** and **Prop "dead ends"** with their proofs (short, can go in the
      appendix).
- [ ] **Decide on the timings in the paper:** the main runs used production A (C1) in Python 3.7. Option (a): keep
      C1 and add the C5h vs C1 table as an "improved implementation". Option (b): re-run the RQs with C5h. **K\* is
      identical, so every economic result (Z, payments, RQ1–RQ3, RQ5) is unchanged; only the times change.**
- [ ] Numbers to quote: C5h is 1.9–3.9× faster than C1 on the label instances, 2.07×/2.35× on the grid sample; the
      dead-end filter removes 52–76% of the extension attempts and 99% of OD attempts.
- [ ] Say clearly that the dead-end filter is exact (R unchanged), not a heuristic.

### 12.3 Theory: keep and check

- [ ] Theorems 1–2 and Lemmas P1–P5, as in T4 v3 (Section 1). Renumber if Theorem 3 was referenced.
- [ ] **VERIFY** (T4 v3, Section 2.9):
  - Sol (1994) and Vanderbeck (1994) read directly (the statements now come from Lübbecke & Desrosiers 2005).
  - The route deleted in `ex:rollback` belongs to the frontier of g0.
  - The criterion behind 556/563 in the Remark "realisable competitors" (margin condition, or a full solve?).
  - The numerical tolerance of the frontier procedure and of `GenerateRoutes`.
  - Bibliographic details (marked `% VERIFY`).
- [ ] The `% VERIFY` comments in `Paper.tex`: Hershberger & Suri (2001); the positioning table; Sol's statement about
      distinct subproblems.
- [ ] The `% TODO` comments in `Paper.tex`: IQRs of B4/HEUR in `tab:rq2`; the loss of GW-first in RQ1; whether 4.0% /
      5.7% are medians or means.

### 12.4 Positioning and scalability

- [ ] Remove/avoid any "first combinatorial auction / VCG for crowdshipping" claim.
- [ ] Sharpen the difference with **Li & Zhang (2026)** after reading the full text (Section 11.3), and update the
      `tab:positioning` row for Li & Zhang.
- [ ] Add a "practical deployment" paragraph: A runs before bids close and parallelises per driver; B + C is the
      critical path.
- [ ] Add the scale-study results (CPLEX) once they are run (`BENCHMARK_GUIDE.md`, Part A).
- [ ] State the limits: n ≤ 30 in the main study; B = 3; zoning or time batching needed in practice.

---

## 13. Open questions and next steps

| Priority | Task | Who |
|---|---|---|
| 1 | Read the full text of Li & Zhang (2026); answer the 4 questions in 11.3 | author (needs library access) |
| 2 | Edit `Paper.tex` according to Section 12 | author / Claude Code when asked |
| 3 | Run the scale study with CPLEX (`BENCHMARK_GUIDE.md`, Part A) | author |
| 4 | Choose and agree the comparison benchmarks (`BENCHMARK_GUIDE.md`, Part B, questions B.5) | author → then Claude Code |
| 5 | Decide whether to re-run the RQs with C5h or keep the C1 times | author |
| 6 | (Optional) a deeper literature search, with a comparison table against HICA | Claude Code when asked |

---

## 14. Commits on the branch

| Commit | Content |
|---|---|
| `a6389c7` | T4_Combined_v2 (reader-friendly version) |
| `bf93b8b` | C8 (C5 + Layer 3), dead-end filter, C5h, EXPERIMENT_REPORT_C8 |
| `51d0315` | Dataset stub |
| `52b6676` | C5s (stronger dead-end test, negative) |
| `7086c8c` | **T4_Combined_v3** (Theorem 3 / Layer 3 removed) |
| `48c2b31` | HiGHS pipeline + check against CPLEX (48/48) |
| `7aa3083`, `0cd3531` | Partial scale study; BENCHMARK_GUIDE.md, CLAUDE.md |
