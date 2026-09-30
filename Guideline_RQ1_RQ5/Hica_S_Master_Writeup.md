# HICA-S — Master Write-up Source (T4 + T5 + RQ1–RQ5)

**Phiên bản:** 2026-09-28 · **Tác giả nghiên cứu:** Tran An Khoa · **Target:** Computers & Operations Research (C&OR)

**Mục đích file:** đây là nguồn duy nhất để viết lại toàn bộ bài báo/report bằng LaTeX. Mọi con số trong file đều lấy từ các báo cáo đã chạy (liệt kê ở §0.3). Không có con số nào được bịa hoặc ước lượng mà không ghi rõ. Chỗ nào còn thiếu bằng chứng được đánh dấu `[PENDING]`. Chỗ nào mình tự tính lại từ bảng đã có được đánh dấu `[DERIVED]`.

**Quy ước ngôn ngữ:** phần giải thích/ghi chú viết tiếng Việt. Mọi phát biểu định nghĩa, định lý, contribution, và câu có thể chép thẳng vào paper được viết **bằng tiếng Anh** và đặt trong khối `> ` (quote) để dễ copy.

---

## 0. Cách dùng file này

### 0.1 Trạng thái tổng

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| Mô hình + Algorithms A/B/C | Xong | Không đổi từ đề cương v4 |
| T4 Part I (Local Pruning Frontier, Price of Locality) | Chứng minh xong, **đang tự rà soát** | Checklist §5.10 |
| T4 Part II (FD-completion label rule) | Chứng minh xong, **đang tự rà soát** | Checklist §5.10 |
| T5 (component decomposition) | Chứng minh xong; hiệu quả thực nghiệm yếu | §7 |
| RQ1–RQ5 | Chạy xong theo spec khóa trước | §9–§14 |
| Kiểm tra bổ sung (a)(b)(c) | Chạy xong | §15 |
| Tách "K★ rỗng" thành hai loại | Chạy xong (2026-09-28) | §15.3, Runbook §18.1 |
| Thống kê RQ1 theo §0.4 | Chạy xong (2026-09-28) | §10, Runbook §18.4 |
| Kiểm Θ cho V8 | Chạy xong (2026-09-28) — case (iii), không phải (i)/(ii) | §2.3, Runbook §18.5 |
| Đối chiếu thời gian dựng K★ | Chạy xong (2026-09-28) | §13, Runbook §18.6 |
| Đọc literature gốc (Vanderbeck, Sol, …) | `[PENDING]` | §3.4 |
| Bản LaTeX | Lỗi thời, cần viết lại theo file này | §19 |

### 0.2 Việc đã làm trong file này (từ danh sách 1–3 của lượt trước)

1. **Tách K★ rỗng (feasibility vs FD-dominance):** *không làm được ở đây* — cần chạy trên máy có codebase và dữ liệu. Mình đã viết runbook ngắn ở §18.1 và đánh dấu mọi con số K★-rỗng là "chưa tách" trong file.
2. **Thống nhất quy ước thống kê:** *đã làm.* §0.4 khóa quy ước; mọi bảng trong file đã được quy về quy ước đó. Các con số tự tính lại đánh dấu `[DERIVED]`.
3. **Lát cắt alignment mịn hơn:** *không làm được ở đây* (cần chạy generator). Để ở §18.2 như việc tùy chọn.

Ngoài ra đã làm thêm một việc có thể làm ngay: **dựng phản ví dụ bằng số cụ thể cho Proposition "separability breaks" của T5** (bản LaTeX cũ chỉ có proof sketch). Xem §7.4.

### 0.3 Nguồn dữ liệu (mọi con số đều truy về một trong các file này)

| Mã | File | Nội dung |
|---|---|---|
| [S1] | `T4_Combined.tex/pdf` | Định nghĩa, định lý, chứng minh, audit synthetic của T4 |
| [S2] | `New_t4/files/Final_t4_Speedup_RESULTS.md` | Audit an toàn + timing label rule + B+C 20 profile trên 5 instance RQ1 |
| [S3] | `Guideline_Total/RQ_Master.md` | Spec khóa trước cho RQ1–RQ5 |
| [S4] | `Guideline_Total/Report_RQ_All.md` | Kết quả RQ1–RQ5 |
| [S5] | `Report_RQ1_Complementarity.md` | Chi tiết RQ1 |
| [S6] | `Report_2b_Component_Distribution.md` | Phân phối component của T5 trên pool đầy đủ |
| [S7] | Báo cáo ba việc kiểm tra bổ sung (a)(b)(c) | Calibration FD, T5 trên K★, tần suất K★ rỗng (số gộp, đã thay ở [S9]) |
| [S8] | Bản LaTeX paper skeleton (v4) | Literature review, model, T5 proofs |
| [S9] | Runbook chạy chốt A–D (2026-09-28), `spec_2a_2b/results/rq_all/kstar_empty_split_*.csv`, `rq1_comp_gain_recomputed*.csv`, `kstar_build_time_reconciliation.csv` | K★ rỗng đã tách hai loại; RQ1 theo quy ước §0.4; kiểm Θ V8; đối chiếu thời gian dựng K★ |

### 0.4 Quy ước thống kê (KHÓA — dùng thống nhất trong paper)

Lý do: các báo cáo cũ dùng lẫn "mean", "median", "mean của median cell", "tổng thời gian cộng dồn". Reviewer sẽ bắt được. Quy ước từ đây:

- **Hiệu ứng kinh tế (cost gain, premium, rent):** báo **median [IQR] · mean (95% paired bootstrap CI)**, tính **trên instance** (không trên cell). Bootstrap 2000 lần, resample theo instance.
- **Tỉ lệ (FD rate, % driver K★ rỗng):** báo **mean trên instance**. Nếu cần median, ghi rõ.
- **Speed-up:** báo **hai con số, luôn đi đôi**:
  - *median per-instance* (median của các median từng instance) — con số chính;
  - *pooled* (tổng thời gian baseline / tổng thời gian treatment) — con số phụ, ghi rõ là pooled.
- **"Mean của median cell" không được dùng** trong paper. Báo cáo [S7] có một đoạn dùng cách này (FD rate 0.856/0.833/1.000/0.681/0.361); file này đã thay bằng mean trên instance (§15.1).

---

## 1. Framing của paper

### 1.1 Tiêu đề đề xuất

> *Truthful Route-Bundle Procurement with Gigworkers and Occasional Drivers: The Local Pruning Frontier of Bid-Independent Route Generation*

Lý do đổi so với v4: trọng tâm kỹ thuật giờ là T4. Tiêu đề cũ ("…in Hybrid Last-Mile Fleets") chỉ nói setting, không nói đóng góp. Có thể giữ tiêu đề cũ nếu muốn nhấn setting; khi đó phải đưa "local pruning frontier" vào câu đầu abstract.

### 1.2 Câu chuyện một đoạn

> A platform that buys delivery service from gigworkers (open routes) and occasional drivers (detours around a personal trip), with a fixed-capacity fleet as a publicly priced outside option, can make truthful cost reporting a dominant strategy by running exact VCG on a route pool that is generated before any bid is seen. The practical bottleneck is the size of that pool: for gigworkers, who have no detour anchor, it grows as $\Theta(n^B)$. We characterise exactly how far such a pool can be pruned by any rule that reads neither bids nor other drivers' data — the local pruning frontier $\mathcal K^\star$ — prove that no such rule can do better, and show that the frontier can still be of size $\Theta(n^B)$ while containing no route that is ever optimal. We complement this limit with a provably safe label rule that reaches the frontier faster. On the experimental side, the economic value of letting both driver classes bid, of endogenous bundling, and the cost of truthfulness are all conditional: they are near zero when the fixed fleet is competitive and reach double digits when the crowd's trips align with demand.

### 1.3 Contributions (phiên bản khóa để viết paper)

> 1. **Local pruning frontier (Theorem 4).** For route pools generated before bids are observed, we define an FD-completion envelope and prove that deleting every route outside the resulting frontier $\mathcal K^\star_i$ preserves the optimal winner-determination value, every Clarke-pivot removal value, and hence all VCG payments. Conversely, every route in $\mathcal K^\star_i$ is indispensable in some instance with the same local information, so $\mathcal K^\star_i$ is the unique minimal pool retained by any deterministic, bid-independent rule that reads only driver $i$'s own data.
> 2. **Price of locality (Theorem 10).** We construct Euclidean instances in which a single gigworker's frontier contains $\Theta(n^B)$ routes, none of which is optimal for any bid profile. The $O(n^B)$ enumeration bound is therefore tight for the entire class of local bid-independent rules, and the gap between gigworkers and occasional drivers is structural rather than algorithmic.
> 3. **A provably safe FD-completion label rule (Theorems 23–24).** We adapt rollback pruning to a cost model in which working time is priced and waiting is allowed, prove that a waiting-absorption correction is necessary (Example 28) and sufficient, and show that the rule leaves $\mathcal K^\star$ unchanged while reducing label extensions by 35–76% on the experimental instances (median per-instance speed-ups of 1.48× at $B=3$ and 2.19× at $B=4$).
> 4. **Component decomposition of the payment chain (T5), with a matching negative result.** Under a separable outside option, the $n$ counterfactual solves decompose along the components of a static conflict graph; the decomposition fails under a shared outside-option capacity. We report that the decomposition gives little benefit on our instances because the conflict graph is almost always connected.
> 5. **A pre-registered computational study** of five research questions (all parameters locked and hashed before the main runs), showing that complementarity between driver classes, the value of endogenous bundling, and the payout premium of truthful procurement are all governed by one condition: whether the crowd can compete with the fixed fleet.

**Thứ tự quan trọng:** 1 và 2 là lõi. 3 là kỹ thuật thực dụng. 4 là kết quả phụ trung thực. 5 là bằng chứng thực nghiệm.

### 1.4 Những điều KHÔNG được claim (checklist trước khi nộp)

| Không được viết | Viết thay bằng | Lý do |
|---|---|---|
| "We propose a new truthful mechanism" | "We implement exact VCG on a bid-independent route range" | DSIC là hệ quả Groves/VCG maximal-in-range |
| "Three-class taxonomy" như đóng góp | "We adopt the FD/GW/OD taxonomy of Luy et al. (2024)" | Đã có ở POM 2024 |
| "Two route geometries induce two mechanism structures" | "…two column distributions over the same scalar type" | WDP không phân biệt được cột GW/OD |
| "$\mathcal K^\star$ is the smallest possible pool" | "…the smallest pool retained by any deterministic rule that reads only $L_i$" | Luật non-local có thể cắt thêm (§5.8) |
| "Bid-uniform dominance is new" | "…adapts Vanderbeck's (1994) parametric column dominance to a driver-local, FD-completed setting" | Walk-back §3.4 |
| "The label rule is a new algorithm" | "…an adaptation of rollback pruning (Lozano et al., 2016) with a necessary absorption correction" | |
| "T5 is our strongest contribution" | "T5 holds under a separable outside option but yields little speed-up on our instances" | §7.6, §15.2 |
| "$\mathcal K^\star$ speeds up the pipeline 3×" (không kèm điều kiện) | "3.0× on the payment step alone; 1.06× for a single auction including frontier construction" | §13 |
| "VCG is more expensive than pay-as-bid" | "Within the bounded bid range, strategic pay-as-bid pays less; VCG's advantage is DSIC" | §12.4 |
| "Price of truthfulness" về allocation | "Payout premium of truthful procurement" | Allocation đã efficient trong range |
| "first" không kèm điều kiện | "to the best of our search" | Systematic search chưa làm đầy đủ |

---

## 2. Mô hình

### 2.1 Tập hợp và dữ liệu

> A static dispatch session consists of a finite set of orders $O$ and a set of strategic drivers $N = G \cup C$, where $G$ are gigworkers and $C$ occasional drivers. Each order $o \in O$ has a pickup node $p_o$, a delivery node $d_o$, a demand, a release (ready) time, and time windows. Each order can always be delegated to the fixed-capacity fleet (FD) at a public price $q_o \ge 0$; for $A \subseteq O$ write $q(A) = \sum_{o\in A} q_o$. Travel distances $d(\cdot,\cdot)$ and times $\tau(\cdot,\cdot)$ are deterministic, nonnegative, and satisfy the triangle inequality. A bundle-size cap $B$ is published before bids.

Dữ liệu tài xế:

| Lớp | Dữ liệu công khai | Private |
|---|---|---|
| GW | vị trí xuất phát, availability, capacity, $\kappa_i$ | $\theta_i$ |
| OD | origin, personal destination, direct trip (distance/time), max detour $\tau_i$, availability, capacity, $\kappa_i$ | $\theta_i$ |
| FD | $q_o$ cho từng order | — (non-strategic) |

### 2.2 Chi phí

> Driver $i$ serving route $r$ incurs the true cost $C_{ir}(\theta_i) = K_{ir} + \theta_i W_{ir}$, where $K_{ir}$ (cost units) and $W_{ir}$ (hours) are computed by the platform from public data and $\theta_i$ (cost units per hour) is private. Given a report $b_i$, the reported cost is $c_{ir}(b_i) = K_{ir} + b_i W_{ir}$.

- **GW (open route):** $K_{ir} = \kappa_i \cdot \text{route distance}$, $W_{ir} = (\text{completion time} - t_0)/60$.
- **OD (incremental):** $K_{ir} = \kappa_i \max\{0, \text{route distance} - \text{direct distance}\}$, $W_{ir} = \max\{0, \text{route time} - \text{direct time}\}/60$; route kết thúc tại personal destination; detour time $\le \tau_i$.

Tham số thực nghiệm (khóa, [S3] §1): $\kappa = 1.0$ cost-unit/km; $\theta_i \sim U[18,25]$ cho cả GW và OD; $q_o = 8.0 + 3.0\max(0, \text{dist}_{km} - 1.0)$; tốc độ 20 km/h; service 5 phút/stop; `tw_width = 120`; $\tau = 30$ phút.

> Lưu ý: audit synthetic của T4 trong [S1] dùng tham số khác ($\kappa = 0.5$, $q_o = 8 + 3\max(0,d-2)$, service 2 phút). Trong paper phải tách rõ: số trong §5.9 là *synthetic checks of the mathematics*, số trong §9–§15 là *thesis experiments*.

### 2.3 Miền bid

> Reports are restricted to $\Theta = [\underline\theta, \overline\theta] = [18, 25]$, which coincides with the support of the type distribution. The restriction is part of the mechanism's message space and is required by the safety statement of Theorem 4.

**[ĐÃ KIỂM 2026-09-28, Runbook §18.5]** Đọc trực tiếp `rq_runner.py::run_rq5` và `rq_common.py::make_rq5_instance`/`vcg`: RQ5 (mọi biến thể, kể cả baseline V0) **không dùng $\Theta = [18,25]$ như một ràng buộc report ở bất kỳ bước nào**. `make_rq5_instance` chỉ đổi phân phối sinh $\theta$ thật (`theta_range` — $[18,25]$ cho baseline, $[15,30]$ cho V8); `run_rq5` sau đó gọi thẳng `C.vcg(pool, th, q, oids)` với `th` là $\theta$ thật, không hề clip/chặn về $[18,25]$ ở bất kỳ đâu trong pipeline (không có `min(max(\theta,18),25)`, không giới hạn report). RQ5 cũng **không gọi `prune_pool_by_kstar`** — không nhánh nào của $\mathcal K^\star$ được exercise trong RQ5 (khác RQ3/RQ4, nơi $\Theta$ và $\mathcal K^\star$ đều được dùng).

Vậy đây là **trường hợp thứ ba**, không phải (i) hay (ii) đã hình dung trước: VCG treatment của RQ5 hoàn toàn không sử dụng ràng buộc message-space $\Theta$-bounded — driver luôn báo đúng $\theta$ thật của mình bất kể nằm trong hay ngoài $[18,25]$, vì không có bước nào ép report vào khoảng đó. **Không có bug "ép khai sai lệch".** Nhưng hệ quả cho cách viết paper: V8 không kiểm độ nhạy của mechanism khi type vượt khỏi message space đã công bố (như lo ngại ban đầu) — nó đơn thuần kiểm độ nhạy của complementarity/bundling/VCG-overhead theo **độ phân tán của $\theta$ thật** trong một treatment VCG không bị giới hạn $\Theta$. Câu cho Limitations:

> RQ5's VCG treatment (all variants, including the baseline) reports true $\theta_i$ directly and is not restricted to $\Theta = [18,25]$; the frontier $\mathcal K^\star$ is not invoked. Variant V8 therefore tests sensitivity to the dispersion of the private type distribution, not sensitivity of the bounded-message-space mechanism used in RQ3/RQ4.

Sửa mô tả V8 trong bảng RQ5 (§14) theo đúng câu trên — không gọi nó là "robustness của mechanism gốc".

### 2.4 Winner determination (Algorithm B)

> $$ Z^\ast = \min_{x,z} \sum_{i\in N}\sum_{r\in R_i} c_{ir}(b_i)\,x_{ir} + \sum_{o\in O} q_o z_o $$
> subject to $\sum_{i}\sum_{r \ni o} x_{ir} + z_o = 1$ for all $o\in O$; $\sum_{r\in R_i} x_{ir} \le 1$ for all $i$; $x, z$ binary.

Biến: $x_{ir}=1$ nếu tài xế $i$ nhận route $r$; $z_o=1$ nếu order $o$ đi FD. Ràng buộc bằng đảm bảo mỗi order được phục vụ đúng một lần; FD không có giới hạn nên bài toán luôn khả thi.

Tie-breaking (không phụ thuộc bid): (1) cố định objective tại tối ưu; (2) tối thiểu số order đi FD; (3) lexicographic theo `route_id`.

Failure policy: chỉ nghiệm OPTIMAL với gap chứng nhận bằng 0 mới được dùng cho claim DSIC.

### 2.5 Payment (Algorithm C)

> For each winner $i$ with selected route $r_i^\ast$: $p_i = c_{i r_i^\ast}(b_i) + Z^\ast_{-i} - Z^\ast$, where $Z^\ast_{-i}$ is the optimal value with all routes of $i$ removed, on the same route range and with the same tie-breaking. Losers receive zero.

> **Proposition (DSIC and IR; adapted from Groves/VCG, see Nisan & Ronen 2007).** If the route pool is fixed before bids are observed, every base and removal solve is exact, and each driver's report is a single scalar entering the objective linearly, then truthful reporting is a dominant strategy and every winner's utility is nonnegative.

Không phải đóng góp mới — đặt ở model section.

### 2.6 Assumptions đã khóa

> Static, deterministic, single-session procurement; mandatory fulfilment (each order served exactly once, by a route or by FD); unit demand over routes; bounded allocation range fixed before bids; exact optimisation with bid-independent tie-breaking; single-parameter private information.

Not claimed: online/stochastic IC, unconditional budget balance, coalition-proofness, false-name-proofness, fairness.

Budget balance: chỉ dẫn điều kiện của Li & Zhang (2026) (weak BB khi $f_j = q_j$, strong BB khi $f_j \ge q_j$ có ít nhất một bất đẳng thức chặt), không claim vô điều kiện.

### 2.7 Biện minh single-parameter

> In last-mile geometry route time is approximately $d/s + \text{service}$, so the vectors $(d(B), t(B))$ of a driver's bundle menu lie close to a single ray. Measured angular spread is $\sigma_\psi \approx 1^\circ$, the median number of distinct bundle orderings over the type domain is one under tight time windows, and the welfare loss from projecting a two-dimensional cost onto one parameter is 0.002–0.05% (0.075% for a projection without oracle). The conclusion is unchanged when the coefficient of variation of speed is inflated eightfold: speed rotates a driver's menu rather than spreading it, and the spread is governed by $\text{service}(B)/d(B)$.

Nguồn: các vòng đo trước (đề cương v4 §11). Nửa trang + một hình trong paper. Bản LaTeX cũ viết đoạn này **hai lần** — xóa một.

### 2.8 Public vs private — điểm sẽ bị hỏi

Destination và detour tolerance của OD được giả định public/pre-committed. Trả lời trong Limitations bằng lập luận vận hành: platform quan sát qua GPS/lịch sử chuyến; OD phải commit trước khi phiên mở nên không lái được theo tập order. Report space là **restriction** của Li & Zhang (họ cho khai 4 tham số) — không được viết như thể xử lý cấu trúc thông tin phong phú hơn.

---

## 3. Định vị trong literature

### 3.1 Ba dòng literature cần tổng hợp (không liệt kê từng bài)

**(i) Taxonomy tài xế và crowdshipping có mechanism.** Luy, Hiermann & Schiffer (2024, POM 33(11):2177–2200) thiết lập taxonomy FD/GW/OD cho workforce planning dài hạn, chi phí là input đã biết, không có elicitation. Li & Zhang (2026, TS, DOI 10.1287/trsc.2025.0089) là benchmark gần nhất: exact VCG trên pool do platform sinh (qua PDP, cắt nhánh dựa trên tính đơn điệu không gian của detour), nhưng chỉ một lớp crowd strategic. Zou & Kafle (2022, Transportation Letters 15(8):992–1010) có exact VCG + Clarke pivot trên job pool do platform sinh, type 4 chiều, backup non-strategic, nhưng mọi job xuất phát từ depot và một lớp strategic. Các bài khác (Archetti et al. 2016; Triki 2021; Mancini & Gansterer 2022; Chen et al. 2023; Oyama & Akamatsu 2025; Xu et al. 2026) mỗi bài thiếu ít nhất một trong: hai lớp strategic, bundle do platform sinh, IC chứng minh được.

> Gap statement: no study in our search combines a strategic open-route class and a strategic detour-constrained class inside one truthful mechanism with platform-generated bundles. More importantly for this paper, none characterises how far a bid-independent route pool can be pruned without affecting the VCG outcome.

**(ii) Pruning cột an toàn / dominance.** Đây là dòng quyết định novelty của T4:
- Beasley (1987) dominance cột và Müller (1998) subsumed subsets: chi phí cố định, so sánh toàn pool, không có fallback định giá cho phần còn lại.
- Pereira & Averbakh (2013) robust set covering với chi phí khoảng: mục tiêu là một nghiệm min-max regret, không phải luật xóa an toàn từng cột.
- Aggarwal & Hartline (2006), Kempe, Salek & Moore (2010): pruning trước VCG để chặn frugality ratio; luật của họ có thể phụ thuộc bid; không chứng minh bảo toàn giá trị/payment chính xác.
- **Vanderbeck (1994)** qua Lübbecke & Desrosiers (2005, OR 53(6), §2): dominance "uniform over the domain of dual variables" — cấu trúc gần như đồng nhất với tính chất "uniform over $\Theta$" của $\mathcal K^\star$. **Claim novelty cho phần safety đã được rút lại** (xem §3.3).
- Sol (1994): redundant column cho PDP qua lập luận facet của đa diện đối ngẫu.

**(iii) Label dominance / rollback pruning.** Dumas, Desrosiers & Soumis (1991, EJOR 54(1):7–22) và Gschwind et al. (2018, EJOR 266(2):521–530) cho forward dominance trong PDPTW — Algorithm A dùng lại, không claim mới. Lozano, Duque & Medaglia (2016, TS, §4.3) rollback pruning trên nền dominance của Feillet et al. (2004) — gốc của label rule Part II.

**(iv) Tăng tốc tính VCG payment.** Nisan & Ronen (2000 EC; 2007 JAIR) đặt vấn đề "$n+1$ solves". Bleischwitz & Kliewer (2005) chia sẻ bound giữa các search đồng thời. Sandholm et al. (2005, CABOB) tách component cho một lần WDP. Bünz, Seuken & Lubin (2015) separability qua conflict graph hai phía cho core constraint generation. Wilkens & Sivan (2011) single-call mechanisms (truthful in expectation). Li & Zhang (2026) né $n+1$ bằng cơ chế greedy xấp xỉ.

### 3.2 Bảng định vị (dùng cho Table trong paper)

| Study | GW strategic | OD strategic | FD/backup | Bundle source | IC | Pool pruning characterised |
|---|---|---|---|---|---|---|
| Archetti et al. 2016 | Company fleet | OD, no bidding | — | — | No | No |
| Zou & Kafle 2022 | No | Yes (depot-based) | Non-strategic backup | Platform | Exact VCG, DSIC | No |
| Triki 2021 | Company fleet | OD bundle bids | — | Yes | No proof | No |
| Mancini & Gansterer 2022 | No | Yes | — | Corridor-based | No | No |
| Chen et al. 2023 | No | Occasional courier | — | Courier-selected | DSIC, fixed bundle | No |
| Luy et al. 2024 | Yes | Yes | Yes | — | No (cost known) | No |
| Oyama & Akamatsu 2025 | One population | — | Opt-out | Task chains | Truthful sub-auction | No |
| Xu et al. 2026 | Non-strategic | Strategic | Yes | Predetermined | Yes | No |
| Li & Zhang 2026 | No | Strategic | Dedicated, fixed price | Platform (PDP branching) | Exact VCG + greedy | Detour-monotone branching only |
| **This paper** | **Yes (open route)** | **Yes (detour)** | **FD, public price** | **Platform, bid-independent** | **Exact VCG** | **Yes: exact frontier + tightness** |

Cột cuối là cột mới so với bảng v4 — nó là lý do bài đứng ở C&OR.

### 3.3 Novelty position của T4 (câu chữ khóa)

> The safety half of Theorem 4 adapts parametric column dominance (Vanderbeck, 1994, as summarised by Lübbecke & Desrosiers, 2005) to a driver-local setting in which substitutes are subset routes of the same driver completed by a priced outside option, and in which the parameter domain is a message-space restriction fixed by the mechanism designer. The converse — that every retained route is indispensable in some instance with the same local information — and the price-of-locality construction have no counterpart in the sources we examined.

Bốn điểm phân biệt với Vanderbeck (giữ nguyên từ [S1] Remark 18): (a) không có đối tượng tương đương $D(r)$ (route con của cùng tài xế + FD cho phần còn lại); (b) miền của họ là miền đối ngẫu của LP hiện tại, không phải khoảng message space cố định trước; (c) mục đích của họ là tốc độ LP, không liên quan IC; (d) không có converse/tightness ở bất kỳ nguồn nào đã tìm.

### 3.4 Literature `[PENDING]` — phải xong trước khi nộp

1. Đọc trực tiếp Vanderbeck (1994) và Sol (1994). Nếu không lấy được bản gốc, trích "as summarised by Lübbecke & Desrosiers (2005)".
2. Barnhart et al. (1998) branch-and-price survey; Desrosiers & Lübbecke (2005) *A Primer in Column Generation*.
3. Ropke & Cordeau (2009), Feillet et al. (2004) — kiểm precedent gần hơn cho label rule.
4. **Hershberger & Suri (2001) có khả năng đang bị trích sai trong bản LaTeX cũ.** Bản cũ viết "all payments using $O(\sqrt n)$ shortest-path computations". Theo hiểu biết của mình, bài 2001 cho thấy trên đồ thị *vô hướng*, mọi Vickrey price tính được trong thời gian của *một* lần shortest path; con số $\sqrt n$ là *cận dưới* cho đồ thị *có hướng* (Hershberger, Suri & Bhosle, 2007). **Kiểm bản gốc trước khi dùng.**
5. Verify metadata: Chen et al. 2023, Triki 2021, Mancini & Gansterer 2022, Xu et al. 2026, Lehmann et al. 2002, Nisan & Ronen 2007 (page range), Wilkens & Sivan 2011, Pereira & Averbakh (2011 online vs 2013 print), Müller 1998 (venue), Aggarwal & Hartline 2006.
6. Systematic search cho gap tổng (đề cương v4 §13 điều kiện 1) — chưa làm đầy đủ; nếu không làm, giữ "to the best of our search".

---

## 4. Algorithm A — sinh route pool không đọc bid

### 4.1 Label và chuyển trạng thái

> A label is $\ell = (v, IV, C, t, K, W)$: current node, set of orders on board, set of delivered orders, clock after service, and cumulative raw cost accumulators. Transitions are TryPickup (requires $|IV| + |C| < B$ and arrival before the pickup's closing time; waits until the release time), TryDelivery (requires the order on board; waits until the delivery opening time), and, for occasional drivers only, TryHome (requires $IV = \emptyset$; the route ends at the personal destination). Every transition advances the clock by a nonnegative amount.

Completion: GW khi $IV = \emptyset$, $1 \le |C| \le B$; OD khi $IV=\emptyset$ và đã về destination. Chi phí OD được finalise một lần bằng cách trừ direct trip.

### 4.2 Dominance

> Labels are compared only under the full key $(v, IV, C)$; $\ell_A$ dominates $\ell_B$ if $t_A \le t_B$, $K_A \le K_B$, $W_A \le W_B$ with at least one strict inequality.

Đây là forward dominance của Dumas et al. (1991) — không claim mới.

> **Lemma (Disjoint reachable completions).** If $\ell_A, \ell_B$ share $(v, IV)$ but $C_A \ne C_B$, and some $j \in C_B \setminus C_A$ has pickup closing time $l(p_j) < t_A$, then no completion of $\ell_A$ contains $j$ while every completion of $\ell_B$ does; hence their completion sets are disjoint.

Hệ quả: key thô hơn $(v, IV, C)$ không an toàn nói chung. Proposition (existence): instance cụ thể $n=3$, $B=2$ (GW; $l(p_{o_0}) = 78.76 < t_A = 319.33$); trên 720 instance $n \le 6$, key rút gọn sai lệch 46–47% so với brute force. Điều kiện cần cho key thô an toàn là *pairwise* ($l(p_j) \ge \max(t_A, t_B)$ với mọi $j \in C_A \triangle C_B$), nên không mã hóa được thành key tính riêng từng label.

### 4.3 Tính chất

| # | Phát biểu | Trạng thái |
|---|---|---|
| A-P1 | Completeness: mọi route khả thi $|S| \le B$ nằm trong pool (sau Pareto) | Quy nạp; kiểm $n \le 6$ khớp brute force 100% |
| A-P2 | $|\text{pool}| = O(|O|^B (2B)!/2^B)$ mỗi tài xế, $B$ cố định | Đếm |
| A-P3 | Bid-independence: pool và `allocation_range_hash` bất biến theo bid | Cấu trúc code + regression test |
| A-P4 | Same-bundle Pareto dominance an toàn vì $b \ge 0$ | Trực tiếp |

Pairwise compatibility filter (PCF): đúng nhưng không tăng tốc đo được (runtime ratio ≈ 1.0–1.1×) — chỉ ghi để tài liệu hóa.

**Supported-completeness proposition** trong bản LaTeX cũ là trường hợp đặc biệt yếu hơn của $\mathcal K^\star$ ([S1] Remark 13: giới hạn $D(r)$ về cùng bundle và lấy $\Theta = [0,\infty)$). **Không giữ như một proposition riêng** — gộp thành một remark sau Theorem 4.

### 4.4 Bất đối xứng GW/OD (động lực của T4)

OD có "neo": detour đơn điệu theo tập order và có ngân sách $\tau_i$, nên cận dưới detour loại được cả cây con trước khi enumerate hoán vị (ví dụ minh họa: 3/10 subset vào DFS). GW không có neo: chỉ time window, không đơn điệu theo tập ($\{o_1\}$, $\{o_4\}$ khả thi nhưng $\{o_1, o_4\}$ không). Trên RQ1, pool OD chỉ bằng 0.7–1.7% pool GW ([S5]). T4 trả lời: bất đối xứng này là **cấu trúc**, không phải do thuật toán chưa đủ khéo (Theorem 10).

---

## 5. T4 Part I — Local Pruning Frontier

### 5.1 Định nghĩa

> **Definition 1 (Local view, local rule, safety).** The local view of driver $i$ is $L_i = (O, q, B, \Theta, R_i)$. A local pruning rule $\Pi$ is a deterministic map from local views to sets of routes to delete, $\Pi(L_i) \subseteq R_i$, applied to every driver. An instance is any finite set of drivers whose pools consist of routes with bundles of size at most $B$ and nonnegative coefficients. $\Pi$ is safe if $V(R^\Pi; b) = V(R; b)$ for every instance and every $b \in \Theta^N$.

> **Definition 2 (FD-completion envelope, local frontier).** For $r \in R_i$ let $D(r) = \{r' \in R_i \cup \{0_i\} \setminus \{r\} : S_{r'} \subseteq S_r\}$ and $E_r(b) = \min_{r' \in D(r)} \{c_{r'}(b) + q(S_r \setminus S_{r'})\}$. The local margin is $\mu_r(b) = E_r(b) - c_r(b)$, and the local frontier is $\mathcal K^\star_i = \{r \in R_i : \max_{b\in\Theta} \mu_r(b) > 0\}$. The rule $\Pi^\star$ deletes $R_i \setminus \mathcal K^\star_i$ for every driver.

Trực giác (viết trước định nghĩa trong paper): khi platform muốn bỏ route $r$ mà không nhìn tài xế khác, thứ thay thế duy nhất nó chứng nhận được là một route rẻ hơn của *chính tài xế đó* phục vụ một phần của $S_r$, phần còn lại giao FD. $\mathcal K^\star$ giữ lại đúng những route mà thứ thay thế đó không luôn thắng trên toàn bộ $\Theta$.

Ghi chú tính toán: $E_r$ là min của hữu hạn hàm affine nên lõm, tuyến tính từng khúc; $\mu_r$ lõm; max trên $\Theta$ đạt tại đầu mút hoặc kink của $E_r$.

### 5.2 Giả định

> **A1 (no duplicates):** distinct routes with the same bundle have distinct $(K,W)$. **A2 (downward closure):** for every $r' \in R_i$, $T \subseteq S_{r'}$ and $b \in \Theta$ there is $\hat r \in R_i \cup\{0_i\}$ with $S_{\hat r} = T$ and $c_{\hat r}(b) \le c_{r'}(b)$. **A3 (no free supersets):** if $S_r \subsetneq S_{r'}$ then $(K_r, W_r) \ne (K_{r'}, W_{r'})$.

> **Lemma 3 (Algorithm A pools are downward closed).** Under the triangle inequality, nonnegative service times, lower-bound time windows met by waiting, upper-bound deadlines/capacity/detour budget, the GW and OD cost formulas of §2.2, and complete enumeration followed by per-bundle Pareto (or supported) filtering, every pool produced by Algorithm A satisfies A1 and A2.

Cách trình bày (đã thống nhất): trong thân bài chỉ 3–4 dòng — "bất đẳng thức tam giác cho quãng đường; quy nạp ngắn trên thời điểm bắt đầu phục vụ cho thời gian, vì công thức có phép max (chờ khi tới sớm); và bước nối 'route rẻ hơn tồn tại' với 'route đó còn trong pool sau Pareto filter'". Chứng minh đầy đủ đưa vào Appendix. **Không** viết "chỉ cần bất đẳng thức tam giác".

### 5.3 Định lý chính

> **Theorem 4 (Local pruning frontier).** Let $\underline\theta < \overline\theta$.
> (a) *Safety.* If every pool satisfies A1, then $\Pi^\star$ is safe; moreover $V_{-k}(R^{\Pi^\star}; b) = V_{-k}(R; b)$ for every driver $k$ and every $b \in \Theta^N$.
> (b) *Indispensability.* If $R_i$ satisfies A1–A3 and $r \in \mathcal K^\star_i$, there exist an instance containing driver $i$ with the same local view $L_i$ and a bid profile $b \in \Theta^N$ such that every optimal allocation uses $r$ and $V(R \setminus \{r\}; b) \ge V(R; b) + \gamma/2$ for an explicit $\gamma > 0$.
> (c) *Exactness.* Let $\Pi$ be any deterministic rule whose output for driver $i$ depends only on $L_i$. If $\Pi$ is safe on every instance, then on local views satisfying A1–A3, $\Pi$ never deletes a route of $\mathcal K^\star_i$. Hence $\mathcal K^\star_i$ is the unique minimal pool retained by such rules, and $\Pi^\star$ attains it.

Phát biểu (c) ở trên là **bản đã viết lại** để lộ phạm vi (bản gốc [S1] viết "every safe local rule…"). Dùng bản này.

### 5.4 Cấu trúc chứng minh (để viết proof trong paper)

**Lemma 5 (retained substitute always exists).** Với $r \notin \mathcal K^\star_i$ và mọi $b \in \Theta$, tồn tại $u \in \mathcal K^\star_i \cup \{0_i\}$, $S_u \subseteq S_r$, $c_u(b) + q(S_r \setminus S_u) \le c_r(b)$.
Ý chính: xét $\Phi(\rho) = c_\rho(b) + q(S_r \setminus S_\rho)$ trên $D(r) \cup \{r\}$; lấy minimiser có bundle nhỏ nhất $k$. Nếu $k=0$ dùng $0_i$. Nếu $k \ge 1$, Claim A cho các bất đẳng thức chặt với mọi route con thực sự; do hữu hạn bất đẳng thức chặt nên đúng trong lân cận $\eta$ của $b$; tie-break theo slope $W$ (lấy $\min W$ khi $b < \overline\theta$ và dịch sang phải; lấy $\max W$ khi $b = \overline\theta$ và dịch sang trái) cho một route $u$ có $\mu_u > 0$ tại $b'$ gần $b$, tức $u \in \mathcal K^\star_i$. Đây là chứng minh khó nhất; A1 cần để các slope phân biệt.

**Proof of 4(a).** Lấy allocation tối ưu trên pool đầy đủ; thay từng route bị xóa $\rho_j$ bằng $u_j$ của Lemma 5, phần $S_{\rho_j} \setminus S_{u_j}$ giao FD. Bundle chỉ co lại nên vẫn rời nhau; thay đồng thời được vì không đụng tài xế khác. Chi phí không tăng. Bỏ tài xế $k$ tạo instance mới mà local view các tài xế còn lại không đổi, nên áp dụng lại cho $V_{-k}$.

**Corollary 6 (VCG outcomes).** Mechanism trên $R^{\Pi^\star}$ là VCG trên range bid-independent nên DSIC, IR. Nếu WDP đầy đủ có nghiệm tối ưu **duy nhất**, allocation và mọi payment trùng với pool đầy đủ. (Không claim rộng hơn khi có nhiều nghiệm.)

**Lemma 7 (margin against overlapping routes).** Với $r \in \mathcal K^\star_i$ tồn tại $b^\ast$ và $\gamma > 0$ sao cho $c_{r'}(b^\ast) + q(S \setminus S_{r'}) \ge c_r(b^\ast) + \gamma$ với mọi $r' \ne r$ của tài xế $i$. Ý chính: tập $\{\mu_r > 0\}$ mở, chứa khoảng $J$; ba trường hợp $S_{r'} \subseteq S$ (dùng $\mu_r$), $S \subsetneq S_{r'}$ (dùng A2 và A3), còn lại (dùng A2 trên phần giao).

**Proof of 4(b).** Dựng instance: tài xế $i$ với bid $b^\ast$; với mỗi $x \in O \setminus S$, thêm tài xế $j_x$ có đúng một route $\{x\}$, $K=\varepsilon$, $W=0$, $\varepsilon \le \gamma/(2B)$. Với route $r'$ của $i$: order trong $S \setminus S_{r'}$ chỉ đi FD được; order ngoài $S \cup S_{r'}$ tốn $\min\{\varepsilon, q_x\}$. Suy ra $F(r') - F(r) \ge \gamma - B\varepsilon \ge \gamma/2$.

**Proof of 4(c).** Giả sử $\Pi$ xóa $r \in \mathcal K^\star_i$. Trong instance của (b), local view của $i$ y hệt nên $\Pi$ (tất định, chỉ đọc $L_i$) vẫn xóa $r$. Pool sau cắt $\subseteq R \setminus \{r\}$ nên $V(R^\Pi) \ge V(R \setminus\{r\}) > V(R)$: không an toàn. "Unique" là hệ quả tự động (phần tử nhỏ nhất theo quan hệ bao hàm).

### 5.5 Ví dụ kiểm tay (dùng ngay sau Theorem 4 trong paper)

> **Example 11 (twin instances).** Gigworker $g_1$, orders $o_1, o_2$ with $q_{o_1} = 15$, $q_{o_2} = 45$, $\Theta = [18,25]$, routes $r_a: \{o_1\}, (K,W) = (6, 0.6)$; $r_b: \{o_2\}, (8, 0.8)$; $r_c: \{o_1,o_2\}, (11, 1.2)$. Then $r_a \notin \mathcal K^\star$ (always costlier than FD), $r_b \in \mathcal K^\star$ ($E_{r_b} = 45 > 8 + 0.8b$), $r_c \in \mathcal K^\star$ ($E_{r_c}(18) = 37.4 > 32.6$). In instance $I_0$ (no other driver) $r_c$ is optimal on all of $\Theta$ and $r_b$ is never optimal. In $I_1$ (same local view plus one driver serving $o_1$ at cost 0.5), at $b = 18$ the optimum is $22.4 + 0.5 = 22.9$ using $r_b$, versus 32.6 without $r_b$. A per-driver hull across bundles deletes $r_b$ ($r_a$ dominates it componentwise) and is therefore wrong on $I_1$; no local rule can distinguish $I_0$ from $I_1$.

Khuyến nghị trình bày cho người đọc không quen lập luận adversary (kể cả thầy hướng dẫn): đặt Example 11 **trước** Theorem 4(b)–(c).

### 5.6 Geometric realisability (hạ xuống thành Remark)

> **Remark (realisability with genuine occasional drivers).** The abstract competitors in the proof of Theorem 4(b) can be replaced by occasional drivers whose pool consists of a single zero-detour-distance route, at a credit $\lambda_x = \underline\theta\, s_x/60$ per overlapping order (1.20 with $s_x = 4$ min, $\underline\theta = 18$). In the synthetic audit, 556 of 563 frontier routes (98.8%) remained indispensable against fully geometric competitors, and the prediction was never violated. Whether a safe local rule can grant this credit in general is open.

Bản [S1] trình bày thành Lemma 8 + Proposition 9 đầy đủ — rút gọn thành remark này vì kết quả tự để ngỏ 1.2%.

### 5.7 Price of locality

> **Theorem 10.** Fix $B \ge 1$. For every $n \ge B$ there is a Euclidean instance $I_n$ with $n$ orders, one gigworker $g$ and $n$ occasional drivers such that (i) $R_g$ contains exactly one route per bundle of size at most $B$, all in $\mathcal K^\star_g$, so every safe local rule retains $\sum_{k=1}^B \binom nk = \Theta(n^B)$ routes of $g$; and (ii) for every bid profile, no optimal allocation uses a route of $g$.

Construction: mọi order có pickup $P$, delivery $D$, $d(P,D) = \ell$; ready time 0; FD giá chung $q_0$; $g$ xuất phát tại $A$, $d(A,P) = a$; OD $\omega_1..\omega_n$ origin $P$, destination $D$, detour budget $2s$. Điều kiện:
- (C1) $q_0 > 2s\overline\theta/60$
- (C2) $\kappa(a+\ell) + \overline\theta(T_0 + 2s)/60 < q_0$, với $T_0 = \tau(A,P) + \tau(P,D)$
- (C3) $\kappa(a+\ell) > B(\overline\theta - \underline\theta)\,2s/60$

Số minh họa: $s=2$ phút, $\Theta = [18,25]$, $\kappa = 0.5$, $a=2$ km, $\ell = 6$ km, 20 km/h, $q_0 = 20$: (C1) $20 > 1.67$; (C2) $12.4 < 20$; (C3) $4 > 1.4$.

Ý chứng minh: (i) sequence "gom hết pickup rồi mới delivery" có quãng đường $a + \ell$, thời gian $T_0 + 2sk$; mọi sequence khác quay lại $P$ nên bị Pareto-dominate; tại $b = \overline\theta$, (C1)(C2) cho $\mu > 0$. (ii) còn ít nhất $k$ OD rảnh; chuyển bundle của $g$ sang họ giảm chi phí theo (C3). Mọi bất đẳng thức chặt nên bền với nhiễu vị trí (đã kiểm với jitter).

**Cách nói với người đọc không quen:** đây là khẳng định dạng *tồn tại*, nên dựng một họ instance tham số hóa theo $n$ là chứng minh đầy đủ — cùng cấu trúc logic với hàm worst-case của Nesterov dùng để chứng minh cận dưới cho phương pháp bậc nhất.

### 5.8 Phạm vi của Theorem 4 — Remark "What $\mathcal K^\star$ is not" (bắt buộc có trong paper)

> $\mathcal K^\star_i$ is minimal only within the class of rules fixed in Definition 1. It can be beaten in three ways, each of which leaves that class. (i) *Non-local rules* that use public data of other drivers remain bid-independent and preserve DSIC; in the instance of Theorem 10 such a rule could delete every route of $g$, but deciding this requires reasoning about the other drivers' winner-determination problem, which is NP-hard for $B \ge 3$ already at a single bid profile (reduction from exact cover by 3-sets). (ii) *Instance-specific rules* that only need to be correct on the instance at hand: in our experiments only 0.4–1.5% of generated routes are ever optimal (1000 sampled bid profiles, five instances), whereas $\mathcal K^\star$ retains 3–23% of the pool on the RQ1 instances. (iii) *Restricting the instance class* to geometrically realisable competitors weakens the safety requirement; the gap is at most 1.2% of frontier routes in our audit (§5.6).

Các remark khác nên giữ từ [S1]: monotonicity ($\mathcal K^\star$ tăng theo $q$ và theo độ rộng $\Theta$ — Remark 14); computation ($O(|R_i| 2^B f \log(2^B f))$ mỗi tài xế, post-processing, không tăng tốc enumeration — Remark 15); unrestricted reports (thay $\Theta$ bằng $[0,\infty)$, vẫn an toàn nhưng frontier lớn hơn — Remark 16); quan hệ LP: $\pi_o \le q_o$ là tất cả những gì một tài xế biết về đối ngẫu, và construction của 4(b) hiện thực $\pi \approx q$ trên $S_r$, $\pi \approx 0$ ngoài (Remark 12). Remark 13 (supported completeness là trường hợp đặc biệt) thay thế proposition cũ ở §4.3.

### 5.9 Audit của Part I (synthetic — "checks of the mathematics", không phải kết quả thesis)

Nguồn [S1] §8: $n=8$, lưới $10\times10$ km, 2 GW + 2 OD, $B=3$, $\Theta=[18,25]$, $q = 8 + 3\max\{0, d-2\}$, $\kappa = 0.5$, 9 seed, solver HiGHS gap 0.

| Kiểm tra | Kết quả |
|---|---|
| Vi phạm A2 (mọi subset, 3 bid) | 0 |
| Pool sau Pareto / giữ bởi $\Pi^\star$ | 2,985 / 1,157 (38.8%) |
| (a) max $|V(R^{\Pi^\star}) - V(R)|$ (base + removal) | $5.7\times10^{-14}$ |
| Cor. 6: max chênh payment (1,737 payment) | $5.7\times10^{-14}$ |
| (b) route frontier được dựng instance làm indispensable | 1,157 / 1,157 |
| Mức tăng giá trị nhỏ nhất khi bỏ route | $3.4\times10^{-4}$ |
| Realisability với competitor hình học (4 seed) | 556 / 563 |
| Per-driver hull xóa bao nhiêu route frontier | 1,144 / 1,157 (luật đó không an toàn) |
| Route từng tối ưu (400 bid profile, 3 seed) | 1.9–3.8% pool, tất cả nằm trong $\mathcal K^\star$ |
| Thm 10, $n = 3,5,7,9$ | $|\mathcal K^\star_g| = \sum_k \binom nk$, $g$ không bao giờ tối ưu |
| Mutation (bỏ FD term khỏi $E_r$) | Bị phát hiện |

Kiểm độc lập (khác phương pháp): grid brute-force margin (5,000 điểm, không chung code với tính toán kink) khớp **42/42** driver-pool (19 synthetic + 23 RQ1).

Trên 5 instance RQ1 thật: $Z^\ast$, $Z^\ast_{-i}$ pool đầy đủ vs pool $\mathcal K^\star$ khớp (~$10^{-14}$); tỉ lệ cắt: seed42 96.81%, seed1 76.89%, seed7 89.43%, seed123 85.31%, seed999 84.90%; 0/5 instance có route active (1000 bid) nằm ngoài $\mathcal K^\star$.

### 5.10 Checklist tự rà soát chứng minh (đang làm)

Soát theo thứ tự phụ thuộc: Lemma 3 → Lemma 5 → 4(a) → Lemma 7 → 4(b) → 4(c); Lemma 21/22 → Thm 23 → Thm 24; Thm 10 riêng.

| Kết quả | Chỗ dễ sai nhất | Trạng thái |
|---|---|---|
| Lemma 3 | Quy nạp $a'_{l_j} \le a_{l_j}$ dùng tính đơn điệu của max; OD: chặng cuối coi như một stop; bước nối với Pareto filter | ☐ |
| Lemma 5 | Claim A cho cả $S_{\rho''} \subsetneq T$ và $S_{\rho''} = T$; tie-break slope hai phía; tồn tại $\eta$ | ☐ |
| 4(a) | Thay đồng thời không phá tính rời nhau; áp dụng lại cho $V_{-k}$ | ☐ |
| Cor. 6 | Chỉ khẳng định khi nghiệm tối ưu duy nhất | ☐ |
| Lemma 7 | $h_{r'}$ không đồng nhất 0 trên $J$ nhờ A3; ba trường hợp | ☐ |
| 4(b) | $j_x$ chỉ cho $x \notin S$; $F(r')$; $\gamma - B\varepsilon \ge \gamma/2$ | ☐ (đã soát sơ bộ) |
| 4(c) | Pool đối thủ cũng bị cắt — vẫn đúng vì bao hàm | ☐ (đã soát sơ bộ) |
| Thm 10 | Pareto-dominance của sequence khác; (C1)(C2) ở (i); còn $\ge k$ OD rảnh và (C3) ở (ii) | ☐ |
| Lemma 22 | Phân rã $a_j = \max\{U_1 + \mathrm{dur}, M_j\}$, $M_j$ chung | ☐ |
| Thm 23 | Path trung gian $\pi = (L\setminus T)\cdot\sigma$; junction; stop có opening time thuộc $F(L)$. **Mở rộng cho delivery có opening time** (RQ1 có $ready_d = ready_p$) — hiện chỉ ở Remark 27; nên đưa vào phát biểu | ☐ |
| Thm 24 | Bốn bước; bước (iii) xử lý route bị Pareto-dominate xuất hiện lại | ☐ |

---

## 6. T4 Part II — FD-completion label rule

### 6.1 Ý tưởng (viết trước ký hiệu trong paper)

$\mathcal K^\star$ chỉ tính được *sau* khi Algorithm A đã liệt kê hết route. Part II đưa một phần lập luận đó vào *bên trong* quá trình mở rộng label: khi một label đã phục vụ (hoặc đã pick up) một tập order $T$, ta chặn dưới — đồng đều trên mọi cách hoàn thành và mọi bid hợp lệ — khoản tiết kiệm nếu bỏ $T$ và giao FD. Nếu khoản tiết kiệm đó $\ge q(T)$, label và cả cây con bị bỏ. Rule không bao giờ bỏ một route của $\mathcal K^\star$, nên pipeline "A có rule, rồi $\Pi^\star$" cho ra **đúng cùng pool, cùng allocation, cùng payment**.

### 6.2 Định nghĩa

> **Definition 20 (Shortcut of a label).** For a label $L = (v_1,\dots,v_m)$ with picked set $P(L)$ and $\emptyset \ne T \subseteq P(L)$, let $L\setminus T$ be the subsequence without the stops of $T$, $v'$ its last point and $r'$ its ready time there ($v_0, t_0$ if empty), $D'$ its length, and $D, r, v_m$ those of $L$. Let $F(L)$ be the set of pickups of orders not yet picked that remain reachable before their closing time (empty if $|P(L)| = B$). Define
> $\Delta D = D - D' - d(v', v_m)$, $\delta = r - r' - \tau(v', v_m)$,
> $A = \max\{0, \max_{p_w \in F(L)} (e_{p_w} - r' - \tau(v', p_w))\}$,
> $\beta(L,T) = \kappa\,\Delta D + \underline\theta \max\{0, \delta - A\}/60$.
> *Rule:* discard $L$ and all its extensions if $\beta(L,T) \ge q(T)$ for some $\emptyset \ne T \subseteq P(L)$.

Giải thích từng thành phần (bắt buộc trong paper):
- $\Delta D$, $\delta$: quãng đường và thời gian label đã tiêu cho $T$, đo trên phần route đã biết.
- $d(v', v_m)$, $\tau(v', v_m)$ (**junction terms**): phần tiếp theo của route có thể bắt đầu từ điểm cuối của $L$, trong khi route tắt kết thúc ở $v'$.
- $A$ (**absorption term**): phần tiết kiệm thời gian có thể bị "nuốt" bởi việc phải chờ pickup mở cửa sau này.

Mở rộng cho delivery có opening time (trường hợp của RQ1): đưa vào $F(L)$ cả delivery của các order đang trên xe và của mọi order còn có thể pick up ([S1] Remark 27). Lemma 22 không đổi. **Nên đưa điều kiện này thẳng vào Definition 20 trong paper** thay vì để ở remark.

### 6.3 Hai lemma và hai định lý

> **Lemma 21 (Removing stops never hurts).** Deleting stops from a sequence does not increase its length, does not delay any retained stop, and does not delay completion (or arrival at the destination for an occasional driver).

> **Lemma 22 (Absorption of a time advantage).** If two paths continue with the same stops $w_1,\dots,w_k$, path 2 has no-wait arrival times $T_j$, and path 1 arrives at $w_1$ at least $\delta$ later, then $a^{(1)}_j - a^{(2)}_j \ge \delta - \max_{l\le j}(e_{w_l} - T_l)^+$ for every $j$.

Chứng minh Lemma 22: triển khai đệ quy thành $a_j = \max\{U_1 + \mathrm{dur}(1\to j), M_j\}$ với $M_j = \max_{l \le j}\{e_{w_l} + \mathrm{dur}(l \to j)\}$ chung cho cả hai path; xét ba trường hợp vị trí của $M_j$ so với $T_j$ và $T_j + \delta$.

> **Theorem 23 (Label bound).** For every label $L$, every $\emptyset \ne T \subseteq P(L)$ and every feasible route $\rho$ with prefix $L$: $K_\rho - K_{\rho\setminus T} \ge \kappa\,\Delta D$, $W_\rho - W_{\rho\setminus T} \ge \max\{0, \delta - A\}/60$, hence $c_\rho(b) - c_{\rho\setminus T}(b) \ge \beta(L,T)$ for all $b \ge \underline\theta$.

> **Theorem 24 (The rule preserves the local frontier exactly).** Let $R_i$ be the pool of Algorithm A and $R'_i$ the pool obtained when Algorithm A additionally discards some or all labels satisfying the rule. Under the assumptions of Lemma 3 and $\underline\theta < \overline\theta$, $\mathcal K^\star_i(R'_i) = \mathcal K^\star_i(R_i)$. Consequently Theorem 4 and Corollary 6 apply verbatim to the pipeline with the rule.

Cấu trúc chứng minh Theorem 24: (i) route bị bỏ nằm ngoài $\mathcal K^\star_i(R_i)$ (dùng Thm 23 + downward closure); (ii) $\mathcal K^\star_i(R_i) \subseteq R'_i$; (iii) $\mathcal K^\star_i(R_i) \subseteq \mathcal K^\star_i(R'_i)$ (xử lý route từng bị Pareto-dominate xuất hiện lại trong $R'_i$); (iv) chiều ngược lại qua Lemma 5.

Kết hợp với label dominance (Remark 26): nếu $L_2$ bị $L_1$ dominate (cùng end stop, cùng tập picked/delivered) và $L_1$ bị rule bỏ, completion của $L_2$ cũng nằm ngoài $\mathcal K^\star$ — chứng minh Thm 24 không đổi.

### 6.4 Vì sao từng thành phần là cần thiết

> **Example 28 (Direct transfer of rollback pruning is unsafe).** Setting $A \equiv 0$ reproduces rollback pruning. On a synthetic instance (seed 2, gigworker $g_0$, $B=3$), for $L = (p_{o_2}, d_{o_2})$ and $T = \{o_2\}$ with $q_{o_2} = 17.13$, the uncorrected bound credits 42.9 minutes and gives $17.72 \ge q_{o_2}$, so the label is discarded. In the feasible completion $(p_{o_2}, d_{o_2}, p_{o_0}, d_{o_0})$ the pickup of $o_0$ opens late, so without $o_2$ the driver would wait; the true time saving is 7.8 minutes and the true saving at $\underline\theta$ is $7.24 < 17.13$. The uncorrected rule deletes a route that must be kept.

Lý do cấu trúc: trong ESPPRC gốc, chi phí cộng theo cung và thời gian chỉ là resource nên tới sớm luôn miễn phí; ở đây thời gian làm việc nằm trong objective và được phép chờ.

**Kết quả âm (nên giữ trong paper):** forward lower-bound matrix (quyết định *trước* khi thăm pickup) an toàn nhưng **không bao giờ fire** trên instance synthetic. Median distance credit 0.5–0.75 so với giá FD 15–21; median time credit 0 vì detour ~5 phút bị hấp thụ hoàn toàn bởi thời gian chờ pickup (median absorption 34–46 phút). Nguyên nhân cấu trúc: trước khi thăm pickup, continuation chưa biết và cận phải đúng cho continuation rẻ nhất.

### 6.5 Cài đặt

Mỗi label mang thêm, cho mỗi order $j$ đã pick, bộ ba $(D'_j, v'_j, r'_j)$ của shortcut $L \setminus \{j\}$ — cập nhật $O(1)$ mỗi lần mở rộng. Kiểm $\beta$ với $A=0$ trước (cận trên); chỉ tính $A$ khi cần. Overhead $O(B)$ mỗi mở rộng cộng hiếm khi $O(n)$. Subset $|T| \ge 2$ gần như không thêm gì — không cần.

### 6.6 Audit synthetic của Part II ([S1] §15)

| Kiểm tra | $B=3$ (3 seed) | $B=4$ (2 seed) |
|---|---|---|
| Rule firings audited | 5,868 | 33,292 |
| Completions checked against bound | 9,975 | 87,744 |
| Bound violations | 0 | 0 |
| $\mathcal K^\star$ giống nhau có/không rule | có | có |
| Max WDP value difference (random bids) | $2.8\times10^{-14}$ | $1.3\times10^{-13}$ |
| Mutation $A\equiv0$ | 1,339 vi phạm, $\mathcal K^\star$ đổi | — |
| Mutation bỏ junction terms | 4,173 vi phạm, $\mathcal K^\star$ đổi | — |

Bài học phương pháp (nên nêu một câu trong paper): trong cả hai mutation, giá trị WDP trên 40 bid ngẫu nhiên/seed **vẫn trùng** — route bị xóa nhầm hiếm khi tối ưu, nên lấy mẫu bid không phát hiện được lỗi; chỉ audit ở mức bound từng completion và so sánh $\mathcal K^\star$ mới phát hiện.

Khoảng cách tới trần lý thuyết (tính theo label nằm trên đường tới một route của $\mathcal K^\star$): luật lý tưởng giữ 2.7% ($B=3$) / 0.6% ($B=4$); rule giữ 56% / 50% — đóng được 45% / 50% khoảng cách đạt được.

Độ nhạy theo giá FD (synthetic, $B=4$, median 3 seed × 2 GW): FD ×0.6 → 73–76% extension tiết kiệm, 2.8–3.1×; ×1.0 → 27–30%, ≈1.0×; ×1.4 → 7–9%, 0.75× (chậm hơn không có rule).

**Remark bắt buộc (tránh category error):** rule không làm pool mà B/C nhận được nhỏ đi — pool đó là $\mathcal K^\star$, bất biến theo Thm 24. Nó chỉ làm $R_i$ trung gian nhỏ đi 3–12% và giảm chi phí *chạy* Algorithm A.

---

## 7. T5 — Component decomposition của chuỗi payment

### 7.1 Định nghĩa

> **Definition (Conflict graph).** $\mathcal G = (N, E)$ with $(i,k) \in E$ iff some route of $i$ and some route of $k$ share an order. It is built once from the full pool before any bid is observed. Let $\mathcal P$ be its connected components, $O(S) = \bigcup_{i\in S}\bigcup_{r\in R_i}\mathrm{ord}(r)$ the order footprint of $S \subseteq N$, and $O_0 = O \setminus O(N)$.

> **Assumption (Separable outside option).** $q_o$ is a fixed public constant that does not depend on which other orders use FD, on which drivers are present, or on any shared FD capacity.

### 7.2 Kết quả

> **Lemma (Footprint disjointness).** For distinct components $P, Q$: $O(P) \cap O(Q) = \emptyset$.

> **Proposition (Additive separability).** Under the assumption, $Z^\ast(N) = \sum_{P\in\mathcal P} Z^\ast(P) + \sum_{o\in O_0} q_o$.

> **Proposition (Component-local counterfactuals).** Under the assumption, for every winner $i$ with component $P(i)$: $Z^\ast(N\setminus\{i\}) - Z^\ast(N) = Z^\ast(P(i)\setminus\{i\}) - Z^\ast(P(i))$.

> **Corollary (Payment via component caching).** $p_i = c_i(x^\ast) + Z^\ast(P(i)\setminus\{i\}) - Z^\ast(P(i))$; only the sub-model of $P(i)$ needs re-solving.

Chứng minh: miền khả thi là tích Descartes theo component (bổ đề footprint), objective tách được theo cùng phân hoạch (giả định separable) → tối ưu từng khối. Bỏ đỉnh $i$ chỉ có thể tách component của $i$, không gộp hay đụng component khác.

**Đánh giá thẳng:** về toán, đây là "ILP khối chéo tách được theo khối" — đúng nhưng nhẹ. Giá trị (nếu có) nằm ở việc dùng một conflict graph *tĩnh, không phụ thuộc allocation* cho *cả loạt* $n$ counterfactual, khác với Bünz et al. (2015) (đồ thị hai phía, dựng lại mỗi vòng) và CABOB (một lần WDP). Trình bày như kết quả phụ.

### 7.3 Kết quả âm: khi separability hỏng

> **Proposition (Non-separability under a shared outside-option capacity).** If the outside option is subject to a shared capacity constraint $\sum_{o\in O} z_o \omega_o \le \bar\Omega$, then in general $Z^\ast(N\setminus\{i\}) - Z^\ast(N) \ne Z^\ast(P(i)\setminus\{i\}) - Z^\ast(P(i))$; moreover the removal problem may become infeasible.

(Tương đương với dạng $\sum(1-z_o)\omega_o \ge \Omega$ của bản LaTeX cũ, với $\bar\Omega = \sum_o\omega_o - \Omega$.)

### 7.4 Phản ví dụ bằng số `[DERIVED — dựng mới trong file này]`

Bản LaTeX cũ chỉ có proof sketch mơ hồ ("shadow price thay đổi…"). Phản ví dụ cụ thể, kiểm tay được:

> **Example (two components, shared FD capacity).** Orders $o_1, o_2$ with $q_{o_1} = 10$, $q_{o_2} = 5$; driver $a$ owns one route $\{o_1\}$ with reported cost 3; driver $b$ owns one route $\{o_2\}$ with reported cost 8. The drivers share no order, so $\mathcal P = \{\{a\},\{b\}\}$. Impose $\omega_o = 1$, $\bar\Omega = 1$ (at most one order may use FD).
> *Base.* Feasible allocations: $a$ and $b$ (cost 11); $a$ and FD for $o_2$ (cost 8); FD for $o_1$ and $b$ (cost 18). Hence $Z^\ast(N) = 8$; $a$ wins, $b$ loses.
> *Removing $a$.* $o_1$ must use FD, so the capacity forces $o_2$ onto $b$: $Z^\ast(N\setminus\{a\}) = 10 + 8 = 18$. The global externality is $18 - 8 = 10$ and $p_a = 3 + 10 = 13$.
> *Component-local formula.* $Z^\ast(\{a\}) = 3$, $Z^\ast(\emptyset) = 10$, externality $7$, $p_a = 10 \ne 13$.
> Removing $a$ changes the allocation inside the other component ($o_2$ moves from FD to $b$) although no driver or order of that component was touched. If $b$ is also absent, removing $a$ makes the problem infeasible.

Kiểm tra lại (đã làm tay): base 8 < 11 < 18 ✓; bỏ $a$ chỉ còn một phương án khả thi (FD $o_1$, $b$ phục vụ $o_2$) = 18 ✓; công thức cục bộ = $(10) - (3) = 7$ ✓.

### 7.5 Trạng thái trong HICA-S

Mô hình hiện tại thỏa separable (FD không giới hạn, $q_o$ theo hợp đồng) — decomposition đúng. Proposition non-separability đánh dấu biên của kết quả.

### 7.6 Kết quả thực nghiệm của T5 (kết luận khóa)

| Pool | Alignment | Largest component / $n_{\text{drivers}}$ (median) | % driver cô lập | Instance có ≥2 component |
|---|---:|---:|---:|---:|
| Đầy đủ ([S6], scale chính) | — | ≥ 0.889 | — | — |
| Đầy đủ ([S7]) | 0.50 | 0.500 | — | — |
| Đầy đủ ([S7]) | 0.90 | 1.000 | — | — |
| $\mathcal K^\star$ ([S7]) | 0.50 | 0.250 | 79.6% | — |
| $\mathcal K^\star$ ([S7]) | 0.90 | **1.000** | **1.3%** | **22/300** |

> Under the separable outside option the decomposition is exact, but on our instances the conflict graph is almost always connected in the regime where the crowd competes with the fixed fleet (largest component covers all drivers at the median, alignment 0.90), and pruning to $\mathcal K^\star$ does not change this. The decomposition therefore yields little computational benefit here; it would matter in sparser markets (tight detour budgets, narrow time windows).

Ở alignment 0.50 component nhỏ vì $\mathcal K^\star$ xóa gần hết crowd — **không** dùng số đó làm bằng chứng T5 có ích. Hướng này đã đóng; không thử thêm biến thể.

---

## 8. Hiệu quả tính toán của T4 trên dữ liệu RQ1 thật ([S2])

Năm instance RQ1: $(n, \text{seed}) \in \{(12,42), (10,1), (15,7), (12,123), (10,999)\}$. Label rule chạy trong `dp_fast.py` (Python thuần, **chưa tích hợp** production `t6_dp.py`).

### 8.1 Audit an toàn trên code đã mở rộng (delivery có opening time)

| | Firings | Completions kiểm (toàn bộ, không lấy mẫu) | Vi phạm | Driver có $\mathcal K^\star$ đổi |
|---|---:|---:|---:|---:|
| $B=3$, 15 driver | 78,163 | 114,627 | 0 | 0 |
| $B=4$, 15 driver | 2,261,235 | 5,539,924 | 0 | 0 |

Mutation (seed 42 + 999): `no_absorb` 4,279/21,406 vi phạm ($B=3$), 123,237/735,023 ($B=4$); `no_junction` 3,149/21,969 ($B=3$), 96,112/738,770 ($B=4$); $\mathcal K^\star$ đổi ở 2–4/4 GW mỗi trường hợp. Bước (0): `dp_fast` không rule khớp brute force trên mọi driver.

Phân loại audit (ghi rõ trong paper): đây là *ground-truth recomputation* (tính lại chênh lệch $K, W$ trực tiếp trên completion thật), khác loại với *independent reimplementation* dùng cho $\mathcal K^\star$ ở §5.9.

### 8.2 Tốc độ Algorithm A (label rule) — theo quy ước §0.4

| Instance | $B=3$ median [IQR] | Ext. saved | $B=4$ median [IQR] | Ext. saved |
|---|---|---:|---|---:|
| n12 s42 | 1.48× [1.42–1.57] | 44.2% | 2.19× [2.17–2.22] | 61.0% |
| n10 s1 | 1.32× [1.26–1.36] | 35.5% | 1.70× [1.67–1.70] | 49.5% |
| n15 s7 | 2.10× [2.02–2.19] | 57.3% | 3.76× [3.71–3.79] | 76.2% |
| n12 s123 | 1.74× [1.67–1.81] | 50.1% | 2.94× [2.92–2.94] | 69.7% |
| n10 s999 | 1.41× [1.36–1.53] (N=20) | 39.4% | 1.98× [1.97–1.98] | 55.8% |
| **Median per-instance** `[DERIVED]` | **1.48×** | | **2.19×** | |
| Pooled (tổng thời gian) | 1.72× [1.69–1.75] | | 2.94× [2.93–2.96] | |

N=10 lần lặp/instance (seed 999 ở $B=3$ tăng lên N=20 vì sd/median = 0.158 > 0.15 ở lần đầu). Xen kẽ thứ tự đo on/off, `gc.collect()` trước mỗi lần đo. Mọi instance sd/median < 0.15. Rule không bao giờ fire trên OD (pool OD sau lọc chỉ 5–24 route) — đúng dự đoán cấu trúc.

Câu cho paper:

> On five experimental instances the rule reduced label extensions by 35–57% at $B=3$ and 49–76% at $B=4$, with median per-instance speed-ups of 1.48× and 2.19× (pooled 1.72× and 2.94×). It never fired for occasional drivers, whose detour budget already keeps their pools small.

### 8.3 Tốc độ Algorithm B+C trên pool $\mathcal K^\star$ — 20 bid profile

| Instance | Pool đầy đủ → $\mathcal K^\star$ | Cắt | B+C median full | B+C median $\mathcal K^\star$ | Speed-up [IQR] | max $|\Delta Z|$ |
|---|---|---:|---:|---:|---|---:|
| n12 s42 | 879 → 28 | 96.81% | 0.147 s | 0.029 s | 5.02× [4.32–5.48] | $2.8\times10^{-14}$ |
| n10 s1 | 714 → 165 | 76.89% | 0.096 s | 0.044 s | 2.17× [2.03–2.31] | $2.8\times10^{-14}$ |
| n15 s7 | 1561 → 165 | 89.43% | 0.168 s | 0.059 s | 2.87× [2.76–3.01] | $5.7\times10^{-14}$ |
| n12 s123 | 1416 → 208 | 85.31% | 0.208 s | 0.075 s | 2.79× [2.61–2.88] | $2.8\times10^{-14}$ |
| n10 s999 | 510 → 77 | 84.90% | 0.088 s | 0.025 s | 3.63× [3.35–3.75] | $2.8\times10^{-14}$ |
| **Median per-instance** `[DERIVED]` | | | | | **2.87×** | |
| Pooled (100 profile) | | | 14.69 s | 4.85 s | 3.03× | |

**Cảnh báo bắt buộc:** các con số này là trên 20 bid profile cùng một pool (thời gian dựng $\mathcal K^\star$, 17–75 ms, được chia cho 20). Cho **một phiên đấu giá**, xem RQ4 (§13): 1.06× khi tính cả thời gian dựng.

---

## 9. Thiết kế thực nghiệm chung (RQ1–RQ5)

### 9.1 Nguyên tắc pre-registration (nên nêu trong paper như một điểm mạnh)

> All parameters of the main experiments were fixed in a parameter file and hashed (SHA-256) before the first main-run instance was generated (`rq1_locked_params.json`, `16a84c77…`; `rq_all_locked_params.json`, `73f0ca62…`). Every cell and variant is reported; decision rules for interpreting each research question were written before the runs.

Quy tắc chống bịa kết quả ([S3] §8): hash trước main run; báo cáo toàn bộ cell; sửa tham số giữa chừng thì ghi `[DEVIATION]` và chạy lại toàn bộ RQ đó; không chỉnh $\lambda$, $\Theta$, lưới $\hat\theta$, $D_{\max}$, biến thể RQ5 sau khi xem kết quả.

### 9.2 Instance generator

`instance_gen.generate_instance`, `spatial_mode = "dispersed"`, `tw_width = 120`, $\tau = 30$, service 5 phút/stop, 20 km/h; delivery có opening time bằng ready time của pickup. Alignment $\in \{0.10, 0.30, 0.50, 0.70, 0.90\}$ được hiện thực qua cặp `(corridor_share, corridor_buffer_km)` theo bảng `locked_targets`; ở alignment 0.50: `corridor_share = 0.0`, `buffer = 3.0`. $n \in \{10, 15, 20\}$; supply $(n_{GW}, n_{OD}) \in \{(2,2),(3,2),(2,3),(3,3)\}$; 25 rep mỗi cell.

**Quan trọng khi viết paper:** "alignment" không phải một trục đơn điệu về độ cạnh tranh của crowd trong generator này (§15.1). Mô tả mỗi mức bằng tham số thật của generator và bằng FD rate quan sát được, không chỉ bằng con số alignment.

### 9.3 Solver và pipeline

Algorithm A: `dp_labeling.build_route_pool` (production; label rule **không** dùng trong RQ2–RQ5 vì chưa tích hợp và không đổi pool $\mathcal K^\star$). Algorithm B: CPLEX 12.10, `threads=1`, `mipgap=0`, `absmipgap=0`. Algorithm C naive: một removal-solve cho mỗi winner. Python 3.7.7.

### 9.4 Gates (kiểm trước main run)

Oracle độc lập: pool từ `brute_force.brute_pool_for_driver`, WDP bằng duyệt exhaustive thuần Python. Grid gate: $n \in \{3,4,5,6\}$ × tw $\in \{60, 120\}$ × 3 seed × 4 driver.

| Gate | Nội dung | Kết quả |
|---|---|---|
| RQ1 dry-run | — | 0/360 fail |
| G1 (RQ2) | lọc pool B3 theo $|S|\le B$ == sinh trực tiếp; capacity 4 lọc $\le 3$ == B3; $Z^\ast$ CPLEX == oracle cho B1/B2/B3/HEUR | 0 fail (kể cả $n\ge15$: 0/32) |
| G2 (RQ3) | $Z^\ast$, mọi $Z^\ast_{-i}$, payment VCG; POSTED; PAB-BR tại mọi điểm lưới | 0/120; 0/72; 0/315 |
| G3 (RQ4) | $Z^\ast$, $Z^\ast_{-i}$ trên pool $\mathcal K^\star$ == pool đầy đủ | 0/360 |
| X1 (sau RQ2) | $C_{B3}$ == `true_cost` JOINT của RQ1 | 1,500/1,500, max $|\Delta| = 1.1\times10^{-13}$ |

Tổng gate RQ2–RQ4: 0/1,035 fail.

### 9.5 Metric

$$\text{Complementarity gain} = \frac{\min(C_{GW\text{-only}}, C_{OD\text{-only}}) - C_{\text{joint}}}{\min(C_{GW\text{-only}}, C_{OD\text{-only}})}, \quad \text{Bundling gain}(M) = \frac{C_{B1} - C_M}{C_{B1}}$$
$$\text{Price of range } B = \frac{C_{B3} - C_{B4}}{C_{B4}}, \quad \text{Payout premium}(M) = \frac{\text{Payout}(M) - Z^\ast}{Z^\ast}$$
$$\text{Information rent} = \sum_{i \in \text{winners}} [p_i - c_i(r_i)], \quad \text{Payment overhead} = \frac{\text{rent}}{\sum_i c_i(r_i)}, \quad \text{Efficiency loss}(M) = \frac{\text{TrueCost}(M) - Z^\ast}{Z^\ast}$$

Ở đây $C$ là true system cost (chi phí thật của route thắng cộng FD), Payout là tổng payment cho crowd cộng FD.

---

## 10. RQ1 — Giá trị của việc cho cả hai lớp cùng bid

**Thiết kế:** 60 cell (5 alignment × 3 $n$ × 4 supply) × 25 rep = 1,500 instance × 5 treatment (JOINT $B=3$; GW-only; OD-only; OD-first→GW; GW-first→OD). 7,500/7,500 solve OPTIMAL.

**[ĐÃ TÍNH LẠI 2026-09-28, Runbook §18.4]** Bảng dưới đây theo đúng quy ước §0.4 (median [IQR] · mean (95% bootstrap CI), trên instance, $n=300$ mỗi alignment = 3 giá trị $n$ × 4 supply × 25 rep). Tính lại trực tiếp từ `rq1_main_grid_results.csv`, không giải lại gì. 0/1,500 instance bị loại (không cell nào có $\min(C_{GW\text{-only}}, C_{OD\text{-only}}) = 0$).

| Alignment | median [IQR] · mean (95% CI), % | $n$ instance |
|---:|---|---:|
| 0.10 | 0.00 [0.00, 0.13] · 0.33 (0.24, 0.43) | 300 |
| 0.30 | 0.00 [0.00, 0.70] · 0.51 (0.40, 0.62) | 300 |
| 0.50 | 0.00 [0.00, 0.00] · 0.04 (0.01, 0.07) | 300 |
| 0.70 | 0.77 [0.00, 2.06] · 1.39 (1.20, 1.62) | 300 |
| 0.90 | **5.84 [3.70, 8.23] · 6.06 (5.68, 6.46)** | 300 |

So với bảng cũ ("mean của median cell", **không dùng trong paper nữa**: 0.01/0.08/0.00/0.93/5.86%): hình dạng giữ nguyên (lõm rõ tại alignment=0.50, tăng đơn điệu từ 0.50 lên 0.90), giá trị tuyệt đối cao hơn một chút ở mọi mức — đúng dự kiến vì mean trên instance nhạy với đuôi phân phối hơn mean của median cell. `[CHECK]` §18.4 (hình dạng phải giữ nguyên) PASS.

Bảng phụ theo alignment × $n$ (median / mean %, `rq1_comp_gain_recomputed_by_n.csv`):

| Alignment | $n=10$ | $n=15$ | $n=20$ |
|---:|---|---|---|
| 0.10 | 0.00 / 0.21 | 0.00 / 0.30 | 0.00 / 0.49 |
| 0.30 | 0.00 / 0.30 | 0.00 / 0.62 | 0.16 / 0.60 |
| 0.50 | 0.00 / −0.00 | 0.00 / 0.04 | 0.00 / 0.07 |
| 0.70 | 0.00 / 0.89 | 0.64 / 1.14 | 1.80 / 2.16 |
| 0.90 | 5.01 / 5.53 | 5.84 / 6.09 | 7.00 / 6.56 |

Finding phụ: OD-first→GW ≈ JOINT; GW-first→OD mất 1.3–5.3% ở alignment cao. Cơ chế: pool OD chỉ bằng 0.7–1.7% pool GW, nên cho OD chọn trước gần như không lấy mất lựa chọn nào của GW, còn chiều ngược lại thì có.

> Letting both classes bid jointly adds essentially nothing when the fixed fleet dominates, and 5.9% when occasional drivers' personal trips align with demand. Sequential procurement that consults occasional drivers first recovers almost all of the joint value; consulting gigworkers first does not.

---

## 11. RQ2 — Giá trị của endogenous bundling

**Thiết kế:** cùng 1,500 instance RQ1. Menu: B1, B2, B3 (= JOINT RQ1), B4 (chỉ $n \le 15$, 1,000 instance — $n=20$ tốn ~100 s/instance cho Algorithm A, giới hạn ghi trước khi chạy), HEUR (singleton + khối của một phân hoạch heuristic bid-independent: $d(o,o') = \text{dist}(p_o,p_{o'}) + \text{dist}(d_o,d_{o'})$, $D_{\max}$ = percentile 25, gộp nhóm $\le 3$ order khi mọi cặp $\le D_{\max}$ và chênh ready $\le$ `tw_width`). 7,000/7,000 OPTIMAL.

### 11.1 Bundling gain so với B1 (%), median [IQR] · mean (CI)

| Alignment | B2 | B3 | B4 ($n\le15$) | HEUR | B3 vs HEUR |
|---:|---|---|---|---|---|
| 0.10 | 0.00 [0.00, 1.11] · 0.70 | 0.57 [0.00, 2.56] · 1.55 (1.33–1.80) | 0.00 [0.00, 2.97] · 1.81 | 0.00 · 0.58 | 0.00 · 0.98 |
| 0.30 | 0.29 [0.00, 1.69] · 0.97 | 1.24 [0.00, 3.25] · 1.90 (1.66–2.15) | 1.21 [0.00, 4.23] · 2.35 | 0.00 · 0.86 | 0.04 · 1.05 |
| 0.50 | 0.00 [0.00, 0.00] · 0.16 | 0.00 [0.00, 0.00] · 0.49 (0.35–0.64) | 0.00 · 0.48 | 0.00 · 0.15 | 0.00 · 0.35 |
| 0.70 | 1.68 [0.65, 2.94] · 2.19 | 2.45 [1.24, 4.55] · 3.28 (2.95–3.61) | 2.70 [0.97, 4.88] · 3.42 | 0.51 · 1.43 | 1.43 · 1.87 |
| 0.90 | 6.37 [4.01, 8.78] · 6.64 | **11.32 [8.07, 14.54] · 11.47 (10.92–12.02)** | **15.16 [10.88, 19.20] · 15.38** | 4.94 · 5.68 | 5.61 · 6.12 |

B3 vs B1 theo $n$ (median / mean %):

| Alignment | $n=10$ | $n=15$ | $n=20$ |
|---:|---|---|---|
| 0.10 | 0.00 / 1.23 | 0.30 / 1.31 | 1.80 / 2.12 |
| 0.30 | 0.00 / 1.22 | 1.86 / 2.27 | 1.84 / 2.20 |
| 0.50 | 0.00 / 0.27 | 0.00 / 0.34 | 0.00 / 0.85 |
| 0.70 | 1.84 / 2.47 | 2.12 / 2.95 | 3.49 / 4.41 |
| 0.90 | 9.94 / 10.68 | 11.09 / 11.78 | 11.79 / 11.95 |

### 11.2 Price of range $B$

$(C_{B3} - C_{B4})/C_{B4}$: median 0.00–0.47%, mean ≤ 0.93% ở alignment ≤ 0.70; **4.0% ($n=10$) và 5.7% ($n=15$)** ở alignment 0.90.

### 11.3 Vận hành

| Menu | FD rate | Order/route thắng | Pool (mean) | $t_A$ (s) | $t_B$ (s) |
|---|---:|---:|---:|---:|---:|
| B1 | 0.897 | 1.00 | 45 | lọc từ B3 | 0.005 |
| B2 | 0.802 | 1.55 | 442 | lọc từ B3 | 0.020 |
| B3 | 0.731 | 2.03 | 2,829 | 1.76 | 0.071 |
| B4 ($n\le15$) | 0.679 | 2.37 | 5,313 | 12.46 | 0.129 |
| HEUR | 0.805 | 1.55 | 67 | lọc từ B3 | 0.007 |

$t_A$ theo $n$: B3 0.35 / 1.32 / 3.60 s ($n$ = 10/15/20); B4 3.09 / 21.82 s ($n$ = 10/15). HEUR tạo trung bình 4.2 khối ≥2 order/instance (0–9).

### 11.4 Đọc kết quả (theo decision rule viết trước)

> Bundling is valuable only where the crowd competes: the median gain of $B=3$ over $B=1$ is below 1% where the fixed fleet dominates and 11.3% (15.2% with $B=4$) when occasional drivers align with demand. At that level, letting drivers bid on platform-generated bundles beats a fixed bid-independent partition by 5.6% (median): a heuristic partition captures only about half of the value of bundling, so the value lies in endogenous bundle selection rather than in allowing bundles per se. The price of the bounded range is not negligible in the competitive regime (4–6% from $B=3$ to $B=4$), but the cost of Algorithm A grows about sixteen-fold at $n = 15$.

RQ2 là kết quả kinh tế mạnh nhất; nó cũng là lập luận trực tiếp cho thiết kế "platform sinh bundle, tài xế bid".

---

## 12. RQ3 — Chi phí của truthful procurement

**Thiết kế:** 600 instance (alignment $\{0.50, 0.90\}$ × $n \in \{10,15,20\}$ × 4 supply × 25 rep, trùng RQ1), $B=3$. Bốn cơ chế:

1. **ORACLE** (first-best, full information): allocation hiệu quả, trả đúng true cost. Payout $= Z^\ast$, rent $= 0$. Cận dưới.
2. **VCG** (exact, naive C).
3. **PAB-BR** (pay-as-bid, unilateral best response): winner được trả đúng bid. Mỗi tài xế chọn $\hat\theta_i$ trên lưới $\{\theta_i, \theta_i + 0.5, \dots\} \cup \{25\}$ trong $\Theta = [18,25]$ để tối đa $(\hat\theta_i - \theta_i) W_{r(\hat\theta_i)}$, giữ mọi tài xế khác bid thật; sau đó áp đồng thời mọi $\hat\theta_i$. **Không phải cân bằng Nash** — benchmark chỉ báo.
4. **POSTED** (posted price): giá $\pi_o = \lambda q_o$, tài xế nhận route $r$ nếu $\sum_{o\in S_r}\pi_o \ge c_i(r)$; platform chọn tập route chấp nhận được để tối thiểu payout. $\lambda = 0.80$ khóa bằng pilot 120 instance riêng (tag khác main), chọn $\lambda$ cho payout nhỏ nhất — tức baseline mạnh nhất có thể cho POSTED.

600/600 instance, mọi solve OPTIMAL.

### 12.1 Payout premium so với first-best (%)

| Alignment | $n$ | VCG | PAB-BR | POSTED |
|---:|---:|---|---|---|
| 0.50 | all | 0.00 [0.00, 0.47] · 0.52 (0.39–0.66) | 0.00 [0.00, 0.27] · 0.30 (0.22–0.38) | 0.00 [0.00, 0.49] · 0.55 (0.42–0.70) |
| 0.90 | 10 | 13.58 [10.10, 17.47] · 14.01 | 5.26 [3.58, 7.99] · 5.90 | 10.38 [7.27, 15.02] · 11.00 |
| 0.90 | 15 | 14.11 [10.74, 18.67] · 15.54 | 6.31 [4.64, 8.34] · 6.37 | 8.62 [6.39, 12.30] · 9.81 |
| 0.90 | 20 | 14.98 [11.37, 19.31] · 15.62 | 5.84 [4.30, 7.47] · 6.06 | 8.78 [6.51, 12.03] · 9.17 |
| 0.90 | **all** | **14.13 [10.76, 18.60] · 15.05 (14.30–15.79)** | **5.78 [4.23, 7.84] · 6.11 (5.81–6.43)** | **9.12 [6.59, 12.98] · 9.99 (9.48–10.53)** |

### 12.2 Information rent và hiệu quả

| Alignment | VCG overhead (%) | PAB rent/$\sum c_i$ (%) | PAB efficiency loss (%) | POSTED efficiency loss (%) | FD rate VCG / PAB / POSTED |
|---:|---|---|---|---|---|
| 0.50 | 8.45 [2.96, 17.34] · 17.68 | 5.35 [1.76, 10.19] · 6.86 | 0.00 · 0.00 | 0.00 · 0.37 | 0.949 / 0.949 / 0.985 |
| 0.90 | **24.73 [17.91, 32.37] · 26.29** | 9.65 [7.20, 12.68] · 10.01 | 0.00 [0.00, 0.09] · 0.31 | **3.99 [2.05, 6.15] · 4.46** | 0.374 / 0.382 / 0.540 |

Alignment 0.90: số winner mean 4.01; rent VCG chia GW/OD = 44%/56%; VCG payout > PAB-BR ở 300/300 instance; VCG payout < POSTED chỉ ở 35/300. Alignment 0.50: mean 0.41 winner/instance — overhead % dao động mạnh vì mẫu số nhỏ; **không trích overhead % ở alignment 0.50**.

### 12.3 Đọc kết quả

> In the competitive regime, truthful procurement costs a payout premium of 14.1% (median) over the full-information benchmark, and information rent amounts to about a quarter of the winners' true cost. A posted price calibrated to its best level pays about five points less than VCG but loses 4.0% efficiency and raises the share of orders sent to the fixed fleet from 37% to 54%. Where the fixed fleet dominates, all mechanisms coincide.

### 12.4 Giới hạn bắt buộc khi trích PAB-BR

1. Bid bị chặn trong $\Theta = [18,25]$: markup tối đa $25 - \theta_i$, trung bình chỉ 2.54 USD/h ở alignment 0.90. VCG payment **không** bị chặn như vậy → so sánh thiên về PAB-BR.
2. Best response đơn phương áp đồng thời, không phải cân bằng Nash.
3. Câu đúng: *"Within the bounded bid range, a simple strategic pay-as-bid benchmark pays less than VCG; VCG's advantage is dominant-strategy incentive compatibility — drivers need not reason strategically — rather than a lower payout."* Không viết "VCG đắt hơn pay-as-bid" như kết luận chung.

---

## 13. RQ4 — Tính khả thi của exact payment

**Thiết kế:** 600 instance của RQ3. Naive C: full solve + removal-solve mỗi winner trên pool đầy đủ. Accelerated C: $\mathcal K^\star$ cắt pool một lần/instance, rồi cùng các solve đó. Thứ tự đo luân phiên theo parity rep; 3 process song song trên máy 12 luồng.

**Equality error:** max $|Z^\ast_{\text{naive}} - Z^\ast_{\text{accel}}|$ = max $|p_{\text{naive}} - p_{\text{accel}}|$ = $1.1\times10^{-13}$ trên 600 instance (1,924 solve mỗi nhánh; 408 instance có ≥1 winner).

| Alignment | $n$ | $\mathcal K^\star$ cắt (median) | $t_C$ naive | $t_C$ accel | Speed-up C, median [IQR] | Speed-up tính cả dựng $\mathcal K^\star$ | $t_A$ |
|---:|---:|---:|---:|---:|---|---:|---:|
| 0.50 | 10 | 100.0% | 0.039 | 0.003 | 11.20× [10.11, 13.14] | 1.13× | 0.26 |
| 0.50 | 15 | 100.0% | 0.086 | 0.005 | 17.98× [14.62, 22.05] | 0.63× | 1.00 |
| 0.50 | 20 | 100.0% | 0.186 | 0.006 | 30.40× [21.92, 41.85] | 0.60× | 2.56 |
| 0.90 | 10 | 75.2% | 0.134 | 0.060 | 2.34× [1.69, 3.04] | 1.44× | 0.65 |
| 0.90 | 15 | 76.6% | 0.248 | 0.144 | 1.81× [1.56, 2.57] | 1.05× | 2.20 |
| 0.90 | 20 | 77.2% | 0.655 | 0.259 | 2.72× [2.11, 3.37] | 1.24× | 7.40 |

(thời gian tính bằng giây, median)

Pooled 600 instance: $t_C$ naive 148.2 s, accelerated 49.2 s → **3.01×**; cộng thời gian dựng $\mathcal K^\star$ 90.6 s → **1.06×**.

**[ĐÃ ĐỐI CHIẾU 2026-09-28, Runbook §18.6]** So thời gian dựng $\mathcal K^\star$ trên đúng 5 instance của [S2] (đọc trực tiếp `compare_bc_runtime.csv`, cột `kstar_build_s`) với 5 instance chọn tường minh từ RQ4 (3× $n=20$/alignment 0.90/(gw2,od2), 2× $n=10$/alignment 0.50/(gw2,od2)):

| Nguồn | $n$ | alignment | pool size (tổng) | $t_{\mathcal K^\star\text{-build}}$ (s) |
|---|---:|---:|---:|---:|
| [S2] instance 1 (n12 s42) | 12 | — | 879 | 0.03593 |
| [S2] instance 2 (n10 s1) | 10 | — | 714 | 0.04746 |
| [S2] instance 3 (n15 s7) | 15 | — | 1561 | 0.05249 |
| [S2] instance 4 (n12 s123) | 12 | — | 1416 | 0.04657 |
| [S2] instance 5 (n10 s999) | 10 | — | 510 | 0.01773 |
| RQ4 sample 1 | 20 | 0.90 | 4283 | 0.23253 |
| RQ4 sample 2 | 20 | 0.90 | 3845 | 0.19768 |
| RQ4 sample 3 | 20 | 0.90 | 3851 | 0.19580 |
| RQ4 sample 4 | 10 | 0.50 | 551 | 0.02652 |
| RQ4 sample 5 | 10 | 0.50 | 678 | 0.03696 |

Tương quan pool size ↔ thời gian dựng: **0.988** trên 10 điểm này, **0.979** trên toàn bộ 600 instance RQ4 (`rq34_shard*.csv`, cột `pool_full`/`t_kstar`) — gần tuyến tính, đúng $O(|R_i|\,2^B f \log(2^B f))$ (Remark 15). Pool mean của RQ4 (2,930 route) gấp 2.9× pool mean của [S2] (1,016 route); $t_{\text{build}}$ mean gấp 3.8× (151 ms vs 40 ms) — cùng chiều, hợp lý ($B$ mix của RQ4 ở $n=20$/alignment 0.90 cho pool trung bình lớn hơn theo tỉ lệ hơn tuyến tính đơn giản, do phần đuôi phân phối). **Kết luận: chênh lệch 17–75 ms vs ~151 ms là do kích thước pool, không phải khác cài đặt hay môi trường** — không cần điều tra thêm.

### 13.1 Đọc kết quả

> Exact payments are cheap: naive payment computation takes at most 0.66 s (median) at $n = 20$, always below the time of Algorithm A (7.4 s). Pruning to $\mathcal K^\star$ never changed a payment (maximum deviation $1.1\times10^{-13}$), removed 75–100% of the pool, and sped up the payment step by 1.8–30× (3.0× pooled). For a single auction, however, constructing the frontier in our pure-Python implementation offsets most of that gain (1.06× pooled, below 1× where payments were already trivial). The frontier pays off computationally when the same pool is solved repeatedly — multiple bid profiles, sensitivity analysis, repeated removal solves — and a vectorised construction would be needed to realise a single-session speed-up.

**Hệ quả cho cách trình bày T4 (sửa so với handoff v2):** không dẫn đầu phần thực nghiệm bằng "3.03×". Giá trị của $\mathcal K^\star$ trong paper là (1) định lý; (2) nén pool 75–100% mà không đổi bất kỳ payment nào; (3) chứng nhận trước khi đấu giá (§15.3); tăng tốc chỉ là lợi ích phụ, có điều kiện.

---

## 14. RQ5 — Độ bền (one-at-a-time)

**Thiết kế:** baseline $n=15$, alignment 0.50 (`corridor_share 0.0`, `buffer 3.0`), tw 120, $\tau$ 30, FD ×1.0, $\theta \sim U[18,25]$, dispersed; 4 supply × 15 rep = 60 instance/biến thể. Seed không chứa tham số biến thể → V0–V8 paired theo hình học. V9/V10 dùng supply $\{(3,3),(4,3),(3,4),(4,4)\}$.

| Biến thể | Complementarity % | Bundling B3 vs B1 % | VCG overhead % | FD rate | OPTIMAL | ≤300 s | $t$ median (s) |
|---|---|---|---|---:|---:|---:|---:|
| V0 baseline | 0.00 · 0.03 | 0.00 · 0.38 | 9.02 · 20.31 | 0.948 | 267/267 | 60/60 | 1.34 |
| V1 tw=60 | 0.00 · −0.00 | 0.00 · 0.29 | 6.37 · 18.95 | 0.953 | 263/263 | 60/60 | 0.73 |
| V2 tw=240 | 0.00 · 0.13 | 0.00 · 0.71 | 5.58 · 16.95 | 0.919 | 277/277 | 60/60 | 2.63 |
| V3 $\tau$=20 | 0.00 · −0.00 | 0.00 · 0.39 | 4.26 · 11.54 | 0.957 | 259/259 | 60/60 | 1.17 |
| V4 $\tau$=45 | 0.00 · 0.03 | 0.00 · 0.37 | 9.24 · 20.66 | 0.947 | 268/268 | 60/60 | 1.20 |
| V5 FD ×0.75 | 0.00 · −0.00 | 0.00 · 0.00 | 21.74 · 27.54 | 0.992 | 247/247 | 60/60 | 1.16 |
| V6 FD ×1.25 | 0.00 · 0.17 | 0.52 · 1.76 | 9.95 · 17.11 | 0.872 | 292/292 | 60/60 | 1.27 |
| V7 clustered | 0.00 · 0.02 | 0.00 · 0.66 | 2.82 · 11.65 | 0.938 | 264/264 | 60/60 | 1.24 |
| V8 $\theta\sim U[15,30]$ | 0.00 · 0.10 | 0.00 · 0.68 | 8.05 · 16.28 | 0.926 | 274/274 | 60/60 | 1.19 |
| V9 $n=25$ | 0.00 · 0.07 | 0.04 · 1.05 | 6.84 · 11.89 | 0.919 | 293/293 | 60/60 | 9.95 |
| V10 $n=30$ | 0.00 · 0.02 | 0.00 · 0.57 | 7.57 · 14.66 | 0.949 | 286/286 | 60/60 | 18.48 |

(ô = median · mean, %)

Paired difference so với V0 (điểm %, mean (95% CI)):

| Biến thể | $\Delta$ complementarity | $\Delta$ bundling | $\Delta$ VCG overhead |
|---|---|---|---|
| V1 tw=60 | −0.03 (−0.09, −0.00) | −0.09 (−0.17, −0.04) | −3.82 (−5.90, −1.92) |
| V2 tw=240 | 0.09 (−0.00, 0.22) | 0.33 (0.18, 0.51) | 1.12 (−4.38, 5.11) |
| V3 $\tau$=20 | −0.03 (−0.09, 0.00) | 0.01 (−0.00, 0.02) | −0.72 (−2.16, 0.00) |
| V4 $\tau$=45 | 0.00 (−0.00, 0.00) | −0.01 (−0.02, 0.00) | −0.12 (−0.78, 0.42) |
| V5 FD ×0.75 | −0.03 (−0.09, 0.00) | −0.38 (−0.64, −0.17) | −28.64 (−43.31, −4.28) |
| V6 FD ×1.25 | 0.14 (0.00, 0.31) | **1.38 (0.97, 1.81)** | 2.47 (−5.56, 10.21) |
| V7 clustered | −0.01 (−0.09, 0.06) | 0.28 (−0.18, 0.77) | −11.79 (−31.81, 7.94) |
| V8 $\theta\sim U[15,30]$ | 0.07 (−0.00, 0.18) | 0.30 (0.14, 0.47) | −0.79 (−6.39, 3.76) |

### 14.1 Đọc kết quả

> No variant reverses the sign of any effect — as expected, since the menus are nested — so the conclusion that the gains vanish in the fixed-fleet-dominated regime is robust. The price of the fixed fleet is the governing parameter: at 0.75× the crowd almost never wins (FD rate 99.2%) and all gains vanish; at 1.25× the bundling gain rises by 1.4 points, the largest effect of any variant. Time windows, detour budgets, the dispersion of private types, and spatial clustering have small effects. All solves are optimal with zero gap; at $n = 30$ the full pipeline takes 18.5 s (median) and all 60 instances finish within 300 s.

Cảnh báo: RQ5 baseline đặt ở alignment 0.50 — chế độ crowd **kém cạnh tranh nhất** của generator (§15.1). Nên hầu hết hiệu ứng bằng 0 là do chọn baseline, không phải do các tham số khác không quan trọng. Phải nêu điều này trong paper; nếu có thời gian, lặp lại V1–V8 ở alignment 0.90 (tùy chọn, §18.3).

**V8 và $\Theta$ (đã kiểm, §2.3):** V8 không mở rộng message-space $\Theta$ của một mechanism bị chặn — RQ5's VCG treatment không dùng $\Theta$-bounded report hay $\mathcal K^\star$ ở bất kỳ biến thể nào. V8 đo độ nhạy của complementarity/bundling/VCG-overhead theo độ phân tán của $\theta$ thật ($U[15,30]$ so với $U[18,25]$ baseline), không phải độ nhạy của mechanism khi type vượt khỏi message space công bố. Diễn giải bảng V8 ở §14.1/§14 theo câu này, không gọi là "robustness của mechanism gốc".

---

## 15. Kiểm tra bổ sung (a)(b)(c) — theo quy ước §0.4

### 15.1 (a) Calibration giá FD

**Pilot gốc** (`spec_2a_2b/src/rq1_calibration.py`, khóa trong `rq1_locked_params.json → fd_cost_q_o.calibration_pass`): mục tiêu FD rate $\in [0.10, 0.50]$ và không supply cell nào có GW hoặc OD thắng 0%. Pilot: $n = 12$, $B=3$, tw 120, $\tau$ 30, dispersed, **không có corridor bias** (hai tham số corridor được thêm sau, 2026-09-16). Grid: base_fee $\in \{2,3,4,5,6,8,10,14\}$ × rate_per_km $\in \{0.8,1.2,1.6,2.0,2.5,3.0\}$, free radius 1.0 km; 4 supply × 5 seed = 20 instance/combo. Bộ đầu tiên đạt cả hai tiêu chí: base 8.0, rate 3.0 → FD rate 0.483, GW thắng 32, OD thắng 24.

**FD rate trên main grid (1,500 instance, đọc lại từ allocation B3 = JOINT RQ1):**

| Alignment | $n$ | Median | Mean | Trong $[0.10, 0.50]$? |
|---:|---:|---:|---:|---|
| 0.10 | 10 / 15 / 20 | 0.900 / 0.867 / 0.800 | 0.838 / 0.845 / 0.808 | Không |
| 0.30 | 10 / 15 / 20 | 0.900 / 0.800 / 0.800 | 0.836 / 0.791 / 0.809 | Không |
| 0.50 | 10 / 15 / 20 | 1.000 / 1.000 / 1.000 | 0.960 / 0.946 / 0.941 | Không |
| 0.70 | 10 / 15 / 20 | 0.700 / 0.667 / 0.675 | 0.702 / 0.695 / 0.675 | Không |
| 0.90 | 10 / 15 / 20 | 0.300 / 0.333 / 0.450 | 0.304 / 0.371 / 0.446 | Có |

**FD rate mean trên instance theo alignment `[DERIVED]`** (mỗi cell có đúng 100 instance nên mean trên instance = trung bình cộng mean các cell): **0.830 / 0.812 / 0.949 / 0.691 / 0.374** (alignment 0.10 / 0.30 / 0.50 / 0.70 / 0.90). Toàn grid: median 0.800, mean 0.731. 12/15 cell nằm ngoài mục tiêu pilot.

> Chuỗi "0.856 / 0.833 / 1.000 / 0.681 / 0.361" trong [S7] là *trung bình của median cell* — không dùng trong paper.

Theo giá FD (RQ5, alignment 0.50): ×0.75 → median 1.000, mean 0.992; ×1.00 → 1.000, 0.948; ×1.25 → 0.867, 0.872. Đơn điệu đúng hướng.

**Phát hiện cấu trúc:** FD rate **không đơn điệu** theo alignment — đỉnh ở 0.50, thấp ở hai đầu. Ở alignment 0.50 generator dùng `corridor_share = 0.0` (order rải đều toàn vùng), còn 0.10 và 0.90 dùng corridor bias khác 0, vô tình kéo order gần tài xế GW ở một số cấu hình. Complementarity (RQ1) và bundling gain (RQ2) cũng thấp nhất ở 0.50 — nhất quán với cơ chế này. Chưa phân tích định lượng (§18.2).

Câu cho paper (phần Experimental design / Limitations):

> The fixed-fleet tariff was calibrated on a pilot without corridor bias to yield a fixed-fleet share between 10% and 50%. After corridor bias was introduced to control alignment, the calibration did not carry over: the fixed fleet serves 69–95% of orders at alignment levels up to 0.70 and 37% at 0.90. Moreover, the fixed-fleet share is not monotone in the nominal alignment level — it peaks at 0.50, where orders are spread uniformly — so we describe each regime by its generator parameters and observed fixed-fleet share rather than by the alignment label alone. We did not recalibrate after observing the results.

### 15.2 (b) T5 trên pool $\mathcal K^\star$

Xem bảng §7.6. Kết luận khóa: ở alignment 0.90, largest component / $n_{\text{drivers}}$ median vẫn 1.000 trên pool $\mathcal K^\star$; 1.3% driver cô lập; 22/300 instance có ≥2 component. Điều kiện dừng đã khóa trước (≥ 0.85) kích hoạt → không đo speed-up component-wise. T5 không được cứu bởi $\mathcal K^\star$.

### 15.3 (c) Tần suất $\mathcal K^\star$ rỗng — **đã tách hai loại (2026-09-28, Runbook §18.1)**

**Định nghĩa:** $R_i = \emptyset$ (`feasible_empty`) — tài xế không có route khả thi nào, sự thật hình học/dữ liệu (chủ yếu OD bị chặn bởi $\tau$ budget), **không liên quan Theorem 4**. $R_i \ne \emptyset$ nhưng $\mathcal K^\star_i = \emptyset$ (`fd_dominated`) — mọi route bị FD-completion vượt trội trên toàn $\Theta$; **đây mới là hệ quả trực tiếp của Theorem 4**, và là loại duy nhất được phép trích dẫn như "chứng nhận trước khi đấu giá". Đo trên đúng 1,500 instance RQ1 (7,500 driver) và 180×5=900 driver RQ5 V0/V5/V6, không giải lại WDP.

**Per-driver, theo alignment (mean trên toàn bộ driver, %):**

| Alignment | % feasible_empty | % fd_dominated (trên mọi driver) | % fd_dominated \| $R_i \ne \emptyset$ |
|---:|---:|---:|---:|
| 0.10 | 14.8% | 20.4% | 23.9% |
| 0.30 | 12.3% | 19.5% | 22.3% |
| 0.50 | 43.1% | **34.3%** | 60.2% |
| 0.70 | 2.5% | 10.5% | 10.7% |
| 0.90 | 0.1% | 1.0% | 1.0% |

**Per-instance, theo alignment (%):**

| Alignment | % instance mọi driver `feasible_empty` | % instance mọi driver `kstar_empty` (gộp cũ) | % instance mọi driver có $R_i\ne\emptyset$ đều `fd_dominated` |
|---:|---:|---:|---:|
| 0.10 | 0.0% | 8.3% | 8.3% |
| 0.30 | 0.0% | 7.7% | 7.7% |
| 0.50 | 0.0% | 53.0% | **53.0%** |
| 0.70 | 0.0% | 1.7% | 1.7% |
| 0.90 | 0.0% | 0.0% | 0.0% |

Cột `% instance mọi driver feasible_empty` = 0.0% ở mọi alignment: không instance nào có toàn bộ driver thiếu route khả thi (luôn có ít nhất 1 GW có route) — hệ quả là cột per-instance thứ ba (mọi driver *có route* đều bị FD vượt trội) trùng với cột "kstar_empty" gộp cũ ở mức per-instance (nhưng khác hẳn ở per-driver, nơi 43.1% vs 34.3% tại alignment=0.50).

**Theo giá FD (RQ5 V0/V5/V6, alignment=0.50 cố định), per-driver:**

| FD multiplier | % feasible_empty | % fd_dominated (mọi driver) | % fd_dominated \| $R_i \ne \emptyset$ |
|---:|---:|---:|---:|
| ×0.75 | 43.7% | 52.0% | 92.3% |
| ×1.00 | 43.7% | 33.3% | 59.2% |
| ×1.25 | 43.7% | 13.0% | 23.1% |

**`[CHECK]` cả hai đều PASS:** `% feasible_empty` bất biến tuyệt đối theo giá FD (43.7% ở cả 3 mức — đúng lý thuyết: feasibility hình học không phụ thuộc giá). `% fd_dominated` giảm đơn điệu khi FD đắt hơn (52.0% → 33.3% → 13.0%) — **đúng như Remark 14 dự đoán** ($\mathcal K^\star$ tăng theo $q$). Một kiểm chứng thực nghiệm sạch cho lý thuyết.

Theo alignment: `feasible_empty` và `fd_dominated` **cả hai đều không đơn điệu** theo alignment (đỉnh tại 0.50) — cùng hiện tượng generator đã giải thích ở §15.1 (corridor bias), không phải lỗi; đã xác nhận độc lập bằng cách tách được thành hai đại lượng có cơ chế khác nhau (một do $\tau$-feasibility, một do giá FD) mà vẫn cùng hình dạng, củng cố thêm rằng nguyên nhân nằm ở corridor bias tác động lên cả vị trí order lẫn khả năng phục vụ.

Đối chiếu RQ4 (pool cut, pool-level): 0.50 → cut 100%, `fd_dominated` (driver-level) 34.3%; 0.90 → cut 76.6%, `fd_dominated` 1.0%. Nhất quán hướng — cut ratio cao không có nghĩa driver bị loại hoàn toàn nhiều hơn theo cùng tỉ lệ (cut đo route, `fd_dominated` đo driver), nhưng cả hai giảm/tăng cùng chiều.

Câu cho paper (dùng số `fd_dominated`, không dùng số gộp cũ):

> Because $\mathcal K^\star$ is computed before any bid is observed, an empty frontier certifies in advance that a driver has no route worth considering at any admissible bid — distinct from a driver simply having no feasible route at all. In the regime most dominated by the fixed fleet (alignment 0.50), 34.3% of all drivers (60.2% of drivers with a nonempty feasible pool) are certified in advance as FD-dominated, and this share falls monotonically as the fixed-fleet tariff rises (52.0% at 0.75× to 13.0% at 1.25×), exactly as predicted by the monotonicity of the frontier in the tariff (Remark 14).

File: `kstar_empty_split_by_alignment.csv` (7,500 dòng per-driver), `kstar_empty_split_by_alignment_instance.csv` (1,500 dòng per-instance), `kstar_empty_split_by_fd_price.csv` (900 dòng per-driver).

---

## 16. Tổng hợp: một finding thống nhất và cách kể chuyện

### 16.1 Finding thống nhất

Ba câu hỏi kinh tế (RQ1, RQ2, RQ3) và RQ5 cùng chỉ ra **một điều kiện chi phối**: crowd có cạnh tranh được với FD hay không. Khi FD chiếm ưu thế (FD rate ≳ 0.8), complementarity, bundling gain, và payout premium đều ≈ 0, và mọi cơ chế cho kết quả gần như nhau. Khi crowd cạnh tranh (alignment 0.90, FD rate 0.37), complementarity 5.9%, bundling 11–15%, payout premium của VCG 14%. RQ5: giá FD là tham số điều khiển mạnh nhất.

Viết thành **một** finding có điều kiện, không phải ba kết quả rời:

> Across all research questions, the economic effects are governed by a single condition — whether the crowd can compete with the fixed fleet. Where it cannot, joint bidding, endogenous bundling and truthful payments all make little difference; where occasional drivers' trips align with demand, they matter at the level of 6–15% of system cost, and truthful payments carry a payout premium of about 14%.

### 16.2 Trả lời câu hỏi "FD thắng gần hết thì đề tài có ý nghĩa không?"

Có, với ba lập luận nên viết vào Discussion:
1. **Thực tế vận hành:** nền tảng không cần crowd mọi lúc; cần một cơ chế đúng khi crowd trở nên cạnh tranh (nhu cầu lệch vùng, FD đắt/quá tải). Kết quả cho thấy hệ thống phản ứng đúng hướng và đơn điệu theo giá FD.
2. **Lý thuyết dự đoán đúng dữ liệu:** Remark 14 nói $\mathcal K^\star$ co lại khi FD rẻ; RQ4 cho thấy ở chế độ FD chiếm ưu thế $\mathcal K^\star$ cắt 100% pool; §15.3 cho thấy tỉ lệ rỗng đơn điệu theo giá FD. Định lý và thực nghiệm khớp nhau.
3. **$\mathcal K^\star$ là công cụ phát hiện:** nó cho biết *trước khi đấu giá* khi nào crowd đáng cân nhắc — số liệu đã tách (§15.3): 34.3% driver bị chứng nhận FD-dominated trước ở chế độ FD chiếm ưu thế nhất, giảm đơn điệu đúng lý thuyết khi FD đắt hơn.

### 16.3 "Alignment 0.50" không phải "trung tính"

Các báo cáo cũ gọi alignment 0.50 là "cấu hình trung tính/tự nhiên". Dữ liệu cho thấy đây là chế độ **crowd kém cạnh tranh nhất** của generator. Trong paper, đổi tên các mức thành các "regime" mô tả bằng tham số thật và FD rate quan sát được; bỏ chữ "neutral".

---

## 17. Limitations và sổ theo dõi claim

### 17.1 Limitations (viết vào paper)

1. OD destination và detour tolerance giả định public/pre-committed; report space là restriction của Li & Zhang (2026).
2. Type một chiều (biện minh §2.7), tuyến tính theo report.
3. Miền bid bị chặn $\Theta = [18,25]$; ảnh hưởng tới so sánh PAB-BR (§12.4); V8 cần kiểm (§2.3).
4. $\mathcal K^\star$ tối tiểu chỉ trong lớp luật local tất định (§5.8); khoảng realisability 1.2% chưa đóng.
5. Calibration FD không chuyển sang main grid; alignment không đơn điệu (§15.1). Không recalibrate sau khi thấy kết quả.
6. RQ5 baseline đặt ở chế độ crowd kém cạnh tranh nhất.
7. $B=4$ không chạy ở $n=20$; label rule chưa tích hợp production.
8. $\mathcal K^\star$ build bằng Python thuần; không tăng tốc cho một phiên đơn lẻ.
9. Dữ liệu synthetic; tĩnh, một phiên; không có online IC, budget balance vô điều kiện, collusion.
10. T5 cần outside option separable; hỏng khi FD có capacity chung (§7.4).

### 17.2 Claim ledger

| Claim trong paper | Bằng chứng | Trạng thái |
|---|---|---|
| Thm 4(a) safety | Chứng minh + audit 42/42 + RQ1 ~$10^{-14}$ + RQ4 $1.1\times10^{-13}$ | ✅ (chờ tự rà soát) |
| Thm 4(b)(c) indispensability/exactness | Chứng minh + 1,157/1,157 | ✅ (chờ tự rà soát) |
| Thm 10 price of locality | Chứng minh + $n = 3,5,7,9$ + jitter | ✅ (chờ tự rà soát) |
| Thm 23–24 label rule | Chứng minh + 0 vi phạm / 5.65 triệu completion RQ1 + mutation | ✅ (chờ tự rà soát) |
| Label rule speed-up | Median 1.48× ($B=3$), 2.19× ($B=4$) | ✅ |
| $\mathcal K^\star$ không đổi payment | RQ4 1,924 solve | ✅ |
| $\mathcal K^\star$ speed-up | 3.0× bước C; 1.06× một phiên | ✅ (phải kèm điều kiện) |
| $\mathcal K^\star$ rỗng như chứng nhận trước đấu giá | §15.3 | ✅ đã tách `feasible_empty`/`fd_dominated`; check bất biến/đơn điệu PASS |
| T5 exact decomposition | Chứng minh | ✅ |
| T5 negative result | Phản ví dụ §7.4 | ✅ (mới) |
| T5 hữu ích thực nghiệm | Không (≥0.889; 1.000 trên $\mathcal K^\star$) | ❌ không claim |
| RQ1–RQ3 hiệu ứng có điều kiện | §10–§12 | ✅ RQ1 đã tính lại theo §0.4 (§18.4) |
| RQ5 bền về dấu | §14 | ✅ (baseline caveat) |
| Novelty safety half | Vanderbeck (1994) | ⚠️ đã walk-back; đọc bản gốc `[PENDING]` |
| Gap tổng (GW+OD strategic) | Search chưa systematic | ⚠️ "to the best of our search" |

---

## 18. Việc còn lại `[PENDING]` — runbook ngắn

**Bốn việc bắt buộc A/B/C/D (18.1, 18.4, 18.5, 18.6) đã chạy xong 2026-09-28** — xem kết quả trực tiếp ở §15.3, §10, §2.3/§14, §13. Còn lại chỉ ba việc tùy chọn (18.2, 18.3, 18.7) và literature (§3.4).

### 18.1 ✅ (Bắt buộc, rẻ) Tách $\mathcal K^\star$ rỗng thành hai loại — XONG, xem §15.3

Trong `kstar_empty_rate.py` và `kstar_empty_rate_shard.py`, thêm cho mỗi driver:

```python
feasible_empty = (len(R_i) == 0)
kstar_empty = (len(local_frontier(R_i, (18, 25), inst.q)) == 0)
fd_dominated = kstar_empty and not feasible_empty
```

Báo cáo theo alignment và theo FD multiplier ba cột: `% feasible_empty`, `% fd_dominated` (trên mọi driver), `% fd_dominated | R_i ≠ ∅` (trên driver có pool khác rỗng); per-instance: `% instance mọi driver có pool khác rỗng đều fd_dominated` và `% instance mọi driver kstar_empty`. Không giải lại WDP; chỉ đọc lại pool. Chỉ loại `fd_dominated` được gắn với Theorem 4.

### 18.2 (Tùy chọn) Lát cắt alignment mịn

Thêm alignment $\{0.40, 0.45, 0.55, 0.60\}$ (và các cặp `corridor_share/buffer` tương ứng theo cùng quy tắc sinh bảng `locked_targets`), $n = 15$, 4 supply × 15 rep, chỉ treatment JOINT B3. Mục đích: vẽ hình dạng FD rate và $\mathcal K^\star$-empty theo alignment. Không đổi kết luận RQ nào.

### 18.3 (Tùy chọn) RQ5 ở alignment 0.90

Lặp V1–V8 với baseline alignment 0.90 để có robustness ở chế độ crowd cạnh tranh. Đây là `[DEVIATION]` so với spec RQ5 (baseline khác) — ghi rõ là phân tích bổ sung, không thay thế RQ5.

### 18.4 ✅ (Bắt buộc, rẻ) Tính lại thống kê RQ1 theo §0.4 — XONG, xem §10

### 18.5 ✅ (Bắt buộc, rẻ) Kiểm V8 và $\Theta$ — XONG, xem §2.3/§14 (case thứ ba: RQ5 không dùng $\Theta$-bounded report ở bất kỳ biến thể nào)

### 18.6 ✅ (Rẻ) Đối chiếu thời gian dựng $\mathcal K^\star$ — XONG, xem §13 (tương quan pool-size 0.988/0.979, do kích thước pool, không phải khác cài đặt)

### 18.7 (Tùy chọn, kỹ thuật) Vector hóa $\mathcal K^\star$

Chỉ nếu muốn claim tăng tốc cho một phiên. Không bắt buộc cho paper.

---

## 19. Bản đồ viết LaTeX

### 19.1 Cấu trúc paper đề xuất (C&OR, ~30–35 trang review format)

| Section paper | Nội dung | Lấy từ file này |
|---|---|---|
| 1 Introduction | Bối cảnh 3 lớp tài xế; vấn đề pool bid-independent; contributions; tóm tắt kết quả | §1.2, §1.3, §16.1 |
| 2 Related literature | 4 dòng: taxonomy/crowdshipping mechanisms; safe column pruning & dominance; label dominance & rollback; VCG payment acceleration. Bảng định vị | §3 |
| 3 Model | Sets, cost, bid space, WDP, VCG payment, Proposition DSIC (adapted), assumptions, public/private, single-parameter justification | §2 |
| 4 Bid-independent route generation | Labels, dominance, disjoint-completions lemma, properties, GW/OD asymmetry | §4 |
| 5 The local pruning frontier | Def 1–2, A1–A3, Lemma 3 (ngắn), Example 11, Theorem 4, Cor 6, Remark "what $\mathcal K^\star$ is not", realisability remark, Theorem 10 | §5 |
| 6 Reaching the frontier faster | Def 20, Lemmas 21–22, Theorems 23–24, Example 28, negative result, implementation | §6 |
| 7 Payment computation | Naive C; component decomposition; non-separability với phản ví dụ | §2.5, §7 |
| 8 Computational study | 8.1 Design & pre-registration; 8.2 Frontier and label rule on experimental instances; 8.3 Economic results (RQ1–RQ3, RQ5); 8.4 Frontier as a pre-auction certificate | §8, §9–§15 |
| 9 Discussion and limitations | Finding thống nhất; FD dominance; regime naming; limitations | §16, §17.1 |
| 10 Conclusion | | §1.3 rút gọn |
| Appendix A | Chứng minh đầy đủ: Lemma 3, Lemma 5, Lemma 7, Thm 4, Thm 10, Lemma 22, Thm 23, Thm 24, T5 props | [S1], [S8] |
| Appendix B | Audit tables | §5.9, §6.6, §8.1 |
| Appendix C | Bảng đầy đủ RQ theo cell | `rq_analysis_tables.md` |

### 19.2 Hình và bảng nên có

| # | Loại | Nội dung |
|---|---|---|
| Fig 1 | Diagram | Pipeline: public data → A (label rule) → $\Pi^\star$ → pool $\mathcal K^\star$ → bids → B → C; đánh dấu chỗ không đọc bid |
| Fig 2 | Diagram | Example 11: hai instance song sinh $I_0$/$I_1$ cùng local view |
| Fig 3 | Diagram | Construction Theorem 10 (A, P, D, gigworker, OD) |
| Fig 4 | Plot | Menu bundle gần một tia (biện minh single-parameter) |
| Fig 5 | Plot | $E_r(b)$ và $c_r(b)$ theo $b$ cho một route trong/ngoài $\mathcal K^\star$ (trực giác Def 2) |
| Fig 6 | Plot | Bundling gain theo regime (B2/B3/B4/HEUR) |
| Fig 7 | Plot | FD rate và % $\mathcal K^\star$ rỗng (loại FD-dominated) theo alignment và theo giá FD |
| Tab 1 | Table | Định vị literature (§3.2) |
| Tab 2 | Table | Public/private |
| Tab 3 | Table | Label rule: safety audit + speed-up (§8.1–§8.2) |
| Tab 4 | Table | RQ4 (§13) |
| Tab 5–7 | Table | RQ2, RQ3, RQ5 tóm tắt |

### 19.3 Sửa cụ thể trong bản LaTeX cũ [S8]

1. Viết lại abstract, contributions, bảng theorem package, Conclusion, Journal fit theo §1.3. T4 không còn "open".
2. Thay "Open question (T4)" ở cuối Section Algorithm A bằng dẫn sang Section 5.
3. Xóa proposition "Supported completeness suffices" (và dòng rác "Proposition (Supported Completeness Sufffices)"); thay bằng remark sau Theorem 4.
4. Thay tham chiếu cứng "Section 9.2 / 8.1 / 7.5 / 9.4" bằng `\ref`.
5. Đổi ký hiệu dominance key $\kappa_{\mathrm{full}}$ (trùng với hệ số quãng đường $\kappa_i$), ví dụ $\sigma(\ell)$.
6. Xóa đoạn lặp trong biện minh single-parameter.
7. Thay proof sketch của Proposition non-separability bằng phản ví dụ §7.4.
8. Sửa trích dẫn Hershberger & Suri (§3.4 mục 4).
9. Thay Experimental Design (kế hoạch) bằng kết quả; bỏ mục "Known risk", "data backbone" (meal delivery), "Immediate next steps".
10. Thống nhất thuật ngữ "payout premium of truthful procurement" (không dùng "price of truthfulness").
11. Đổi "alignment 0.50 = neutral" thành mô tả regime.

---

## 20. Đánh giá tiến độ cho C&OR và có cần thêm contribution không

### 20.1 Tiến độ ước lượng

| Hạng mục | Trọng số | Hoàn thành | Ghi chú |
|---|---:|---:|---|
| Mô hình, Algorithms A/B/C | 10% | 100% | |
| Lý thuyết T4 | 20% | ~90% | Còn tự rà soát chứng minh |
| Lý thuyết T5 | 5% | 100% | Có phản ví dụ mới |
| Thực nghiệm | 20% | ~90% | Còn §18.1, §18.4, §18.5 (rẻ) |
| Literature | 10% | ~70% | Đọc bản gốc, verify metadata, sửa Hershberger |
| Viết bản thảo | 35% | ~30% | Skeleton có; phần lõi T4 chưa vào LaTeX; phần thực nghiệm chưa viết |
| **Tổng** | 100% | **~68%** | Nghiên cứu ~90%, bản thảo ~30% |

Nói gọn: **phần nghiên cứu gần xong, phần viết mới khoảng một phần ba.** Thời gian còn lại chủ yếu là viết, không phải chạy thêm.

### 20.2 Có cần một contribution mới không?

**Không.** Lý do:

- C&OR chấp nhận bài có một đóng góp thuật toán/combinatorial rõ ràng mà không cần lý thuyết kinh tế mới. Theorem 4 (có converse) cùng Theorem 10 (tightness) là loại kết quả này, và nó giải thích một hiện tượng đo được (0.4–1.5% route từng tối ưu, trong khi mọi luật cắt rẻ đều không an toàn).
- Thêm một contribution mới lúc này làm tăng rủi ro (chứng minh mới, audit mới, literature mới) trong khi phần yếu thật của bài là **bản thảo**, không phải số lượng kết quả.

**Rủi ro reviewer và cách xử lý bằng cái đã có (thay vì tìm cái mới):**

| Rủi ro | Xử lý |
|---|---|
| "Theorem 4(a) chỉ là parametric dominance" | Đã walk-back; đặt trọng tâm vào converse và Theorem 10; đọc Vanderbeck gốc |
| "Tăng tốc thực tế nhỏ (1.06× một phiên)" | Trình bày $\mathcal K^\star$ là định lý + nén pool + chứng nhận trước đấu giá; tăng tốc là phụ. Tùy chọn: vector hóa (§18.7) |
| "Hiệu ứng kinh tế yếu" | Với C&OR đây là phần bổ trợ; viết thành một finding có điều kiện, có pre-registration |
| "Instance synthetic, calibration lệch" | Minh bạch (§15.1), mô tả regime bằng FD rate |
| "$\mathcal K^\star$ tối tiểu — quá mạnh?" | Phát biểu (c) đã viết lại + remark §5.8 |

**Nếu muốn củng cố thêm, ưu tiên theo thứ tự lợi ích/chi phí** (đều là làm chắc cái đã có, không phải contribution mới):
1. §18.1 tách $\mathcal K^\star$ rỗng — biến "chứng nhận trước đấu giá" thành một kết quả thực nghiệm sạch gắn trực tiếp với Theorem 4.
2. Vector hóa $\mathcal K^\star$ — nếu thành công, speed-up một phiên trở thành claim thật.
3. Tích hợp label rule vào production rồi chạy $B=4$ ở $n=20$ — cho thấy label rule mở rộng được vùng khả thi (hiện $n=20$, $B=4$ tốn ~100 s/instance cho Algorithm A).

**Venue:** C&OR vẫn là lựa chọn chính. EJOR là stretch (cần reviewer chấp nhận Theorem 4/10 như kết quả dominance/complexity đủ mạnh). Phần kinh tế hiện không đủ mạnh để TRE làm target chính. Trước khi chọn venue dự phòng, kiểm quartile hiện hành trên SJR/JCR — file này không xác nhận quartile.

---

*Hết file. Mọi con số truy về [S1]–[S8]; con số tự tính ghi `[DERIVED]`; việc chưa làm ghi `[PENDING]`.*