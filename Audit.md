# AUDIT: is the FD-completion label rule actually running inside Algorithm A?

> **Cách dùng (Vietnamese):** đặt file này ở thư mục gốc của repo, mở Claude Code tại đó và gõ:
> `Đọc AUDIT_FD_LABEL_RULE.md và thực hiện lần lượt từng phase. Dừng lại ở các điểm STOP để báo cáo.`
> Phần còn lại viết bằng tiếng Anh để agent làm đúng.

---

## 0. Context (read first)

The manuscript (HICA-S, target: Computers & Operations Research) describes Algorithm A as a forward label-setting procedure with **three pruning layers**:

| Layer | What it does | Uses FD price `q`? | When it runs |
|---|---|---|---|
| 1 | Label dominance within a batch, same key `(v, IV, C)`, compares `(t, K, W)` | No | during generation |
| 2 | Per-bundle Pareto filter on completed routes `(K, W)` | No | after generation |
| 3 | **FD-completion label rule** (`RuleFires`): discard a label and all its extensions if `beta(L,T) >= q(T)` for some `T = {j}` | Yes | during generation, after every extension |
| Post | **Frontier** `Pi*`: keep only routes with `max_b mu_r(b) > 0` (computes `K*`) | Yes | after generation |

The manuscript says the **production implementation does not use Layer 3** (Section 8.1 "Computation", Section 9 "Limitations"), and that Layer 3 was evaluated separately on 5 instances. The author suspects the code really does not call it during the main runs, and wants to know exactly what runs.

**Hypothesis to test:** integrating Layer 3 into the generation loop (with Layer 1 on) reduces label extensions and the time of Algorithm A, shrinks the pool that `Frontier` must scan, and leaves the final `K*` **identical**.

## 1. Ground rules (do not break)

1. **Read-only first.** Phases 1–3 must not modify any tracked file.
2. **Never overwrite** anything under the results directories or the locked parameter file. Record `sha256sum` of the locked parameter file **before and after** the audit; they must match.
3. Do all code changes on a new branch `audit-fd-rule`. Record the base commit hash (`git rev-parse HEAD`).
4. **Do not fabricate.** Every claim in the report needs `path:line` evidence or a saved log. If something cannot be determined, write `UNKNOWN` and say what is missing.
5. Do not tune any parameter (alignment, FD tariff, tolerances) to make numbers look better. Use the locked values.
6. Save raw command output to `audit_logs/` and reference it from the report.
7. At each **STOP**, print a short summary and wait for the user.

## 2. Phase 1 — Static inspection (read-only)

### 1.1 Locate the code
Find, and list with `path:line`:
- the implementation of Algorithm A (label generation). Search for: `useRule`, `use_rule`, `RuleFires`, `rule_fires`, `rollback`, `shortcut`, `FilterDominated`, `filter_dominated`, `dominat`, `ParetoFront`, `pareto`.
- the implementation of `Frontier` / `K_star` / `mu`. Search for: `frontier`, `kstar`, `k_star`, `envelope`, `mu_r`.
- Algorithms B and C (winner determination, payments).

### 1.2 Answer these questions with evidence
Q1. Does a function implementing the **label rule** (shortcut triples `(D'_j, v'_j, r'_j)`, absorption term `A`, junction terms `d(v',v_m)`, `tau(v',v_m)`) exist in the codebase? If yes, where?

Q2. Is it **called from inside the generation loop**? Show the exact call site and the condition guarding it (flag name, default value, where the flag is set).

Q3. For **every experiment entry point** (main grid, RQ1, RQ2, RQ3, RQ4/frontier, RQ5 robustness, label-rule evaluation), fill in this table:

| script / function | calls Algorithm A as | rule flag value | Layer 1 on? | Frontier applied before B/C? | pool used by B and C |
|---|---|---|---|---|---|

Q4. Is Layer 1 implemented with key `(v, IV, C)` and dominance on `(t, K, W)` with "at least one strict"? Is the **coarser key** `(v, IV)` or `(v, |C|)` used anywhere? (It must not be: the manuscript shows it loses routes.)

Q5. Does the rule use the **lower bound of the report domain** (`theta_low = 18`) when converting time saving into cost, and only the test `T = {j}` (single order)? Is there any place where it reads a bid or a sampled type?

Q6. **Baseline definition in the label-rule table** (Table 7 of the manuscript, "saved" = share of label extensions, speed-up of Algorithm A): in the "without rule" configuration, is **Layer 1 on or off**? What exactly is counted as a "label extension" (calls to which function)? Copy the counting code.

Q7. How is "pool removed 75–100%" (RQ4 table) computed? Relative to which pool: Layer-2 output without the rule? If the rule is later integrated, this denominator must stay the **rule-off pool** so numbers remain comparable.

### STOP 1
Print the Q1–Q7 answers and the Q3 table. Wait for the user.

## 3. Phase 2 — Instrumentation (branch `audit-fd-rule`)

Add counters **without changing behaviour**. Gate them so the default run is byte-identical. Counters per driver and per instance:

| counter | meaning |
|---|---|
| `ext_attempts` | calls to TryPickup / TryDelivery / TryHome (use the **same definition** found in Q6) |
| `labels_created` | extensions that returned a non-null label |
| `killed_layer1` | labels removed by FilterDominated |
| `killed_layer3` | extensions for which the rule fired (and so never entered the queue) |
| `complete_labels` | labels added to the completed set |
| `routes_layer2` | routes after the per-bundle Pareto filter |
| `routes_kstar` | routes after Frontier |

Also time with `time.perf_counter()`: `t_A` (generation incl. Layer 2), `t_F` (Frontier), `t_total = t_A + t_F`.

**Regression test before going on:** run the instrumented code with the rule OFF on the five instances below and confirm pools and `K*` are identical to the uninstrumented code (compare the canonical signature set, see 4.2).

## 4. Phase 3 — Controlled comparison

### 4.1 Configurations
| id | Layer 1 | Layer 3 (rule) | Layer 2 | Frontier after |
|---|---|---|---|---|
| **C1** | on | **off** | on | yes |
| **C2** | on | **on** | on | yes |
| C0 (only if Q6 shows the old baseline had Layer 1 off, or if the code supports it) | off | off | on | yes |

Do not add other configurations.

### 4.2 Instances
The five instances used for the label-rule table (same generator, same seeds, locked parameters), at `B = 3` and `B = 4`:
`n=12 seed 42`, `n=10 seed 1`, `n=15 seed 7`, `n=12 seed 123`, `n=10 seed 999`.

Then a sample from the main grid: alignment 0.90 and alignment 0.50, `n = 15`, supply mix `(3,3)`, first 10 replications of each, `B = 3` only. (`B = 4` only for `n <= 15`.)

### 4.3 Equality checks (C1 vs C2) — these decide everything
For every driver of every instance, build the canonical signature set
`{ (driver, frozenset(bundle), round(K, 9), round(W, 9)) }` and compare:

1. `K*` under C1 vs `K*` under C2: **must be identical**.
2. Number of routes in the Layer-2 pool: C2 must be `<=` C1, and every route in `K*` must be in both pools.
3. On 20 report profiles per instance (truthful profile plus 19 uniform draws from `[18, 25]`, fixed seed): `V`, every `V_{-k}`, and every payment, computed on the `K*` pool of C1 and of C2. Report the maximum absolute difference (expected `~1e-13`).
4. Allocation equality. If allocations differ, check whether it is a tie and say so; do not hide it.
5. For the smallest instances (`n <= 6`, 3 seeds) also compare with brute-force enumeration if the repo has the oracle: with the rule **on**, `K*` must equal the brute-force `K*`.

### 4.4 Timing protocol
- one thread, same machine, nothing else running, record CPU model and Python version;
- each configuration timed **10 times**, **alternating order** (C1, C2, C1, C2, ...);
- report median and IQR per instance; also the pooled ratio of total times;
- report `t_A`, `t_F`, `t_total` separately: the question is whether `t_A(C2) + t_F(C2) < t_A(C1) + t_F(C1)`.

### 4.5 Output tables to produce

**Table A: work saved** (per instance, `B = 3` and `B = 4`)

| instance | B | ext_attempts C1 | ext_attempts C2 | saved % | killed_layer3 | routes_layer2 C1 | routes_layer2 C2 | routes_kstar (C1 = C2?) |
|---|---|---|---|---|---|---|---|---|

**Table B: time**

| instance | B | t_A C1 | t_A C2 | t_F C1 | t_F C2 | t_total C1 | t_total C2 | speed-up total |
|---|---|---|---|---|---|---|---|---|

**Table C: equality**

| instance | B | K* identical? | max |dV| | max |dV_-k| | max |dPayment| | allocation identical? (ties?) |
|---|---|---|---|---|---|---|

**Table D (main-grid sample):** same as A and B, aggregated per alignment level, plus the share of drivers for which the rule fired at least once, **split by GW and OD** (the manuscript claims it never fires for OD).

### STOP 2
Print Tables A–D and the equality verdict. Do not edit the manuscript.

## 5. Phase 4 — Interpretation (fill in honestly)

Decide with this table and quote the evidence:

| Observation | Meaning | Action |
|---|---|---|
| Rule exists, but no main-experiment script passes it on | Main tables (RQ1–RQ5, frontier) were produced with Layer 1 + Layer 2 + post-hoc Frontier only | Safe to keep the manuscript wording; optionally integrate and re-run as a regression test |
| Rule is on in some scripts and off in others | The reported numbers mix configurations | List exactly which tables come from which configuration; fix the manuscript text |
| C2 `K*` != C1 `K*` on any driver | **Bug or a gap in Theorem "rule preserves the frontier"** | STOP. Save the smallest counterexample: instance, driver, label prefix, witness `T`, both values of `beta` and `q(T)`. Do **not** continue to timing claims |
| C2 `K*` == C1 `K*`, payments equal, `t_total` lower | Integration is safe and faster | Report the measured speed-up only; do not extrapolate to `n = 20` or `B = 4` beyond what was run |
| C2 `K*` == C1 `K*`, `t_total` not lower | Extra bookkeeping (shortcut triples, `O(B)` per extension) outweighs the savings in pure Python | Report it; say where the time goes (profile with `cProfile` if needed) |
| Rule fires for OD drivers | Contradicts the manuscript ("never fired for occasional drivers") | Report counts; check the detour-budget filtering order |

Also answer, with numbers: **does `Frontier` itself get faster when run on the smaller C2 pool?** (`t_F` is roughly proportional to pool size in the manuscript; is that visible here?) The final `K*` must not change, so any gain is computational only.

## 6. Final deliverable: `AUDIT_REPORT.md`

Write it in the repo root with exactly these sections:

1. **Environment**: commit hash, branch, Python version, CPU, `sha256` of the locked parameter file before and after (must match).
2. **What runs today**: the Q1–Q7 answers and the Q3 table, each with `path:line`.
3. **Measurements**: Tables A–D (raw logs under `audit_logs/`).
4. **Equality verdict**: one line, `K* identical on X of Y drivers`, plus the maximum deviations.
5. **Interpretation**: use the table in Phase 4, one row only.
6. **What this does NOT show**: e.g. untested `n = 20`, untested `B = 4` on the main grid, single machine.
7. **Recommended manuscript edits**: only statements that the evidence supports. For example, "The production implementation uses Layers 1 and 2 followed by `Frontier`" versus "The production implementation integrates the label rule".

## 7. Things the agent must NOT do

- Do not re-run the full 1,500-instance grid unless the user asks.
- Do not change any locked parameter, instance generator, or seed.
- Do not report a speed-up without the equality check passing.
- Do not merge `audit-fd-rule` into the main branch.
- Do not edit the `.tex` file.