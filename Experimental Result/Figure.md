# HICA-S — Figure Specification cho Claude Code

**Mục đích:** sinh toàn bộ hình thực nghiệm (và hình khái niệm tính được bằng giải tích) cho bài nộp *Computers & Operations Research* (C&OR), từ dữ liệu đã chạy xong. File này là spec — Claude Code đọc từ đầu tới cuối rồi mới code.

**Nguồn sự thật:** `HICA-S — Master Write-up Source` (rev. 2, 2026-09-28), gọi tắt là **[MASTER]**. Mọi giá trị kỳ vọng trong phần "Sanity check" dưới đây lấy từ [MASTER].

---

## 0. Luật bất di bất dịch (đọc trước khi viết dòng code nào)

1. **Không bịa, không ước lượng, không chạy lại solver.** Mọi điểm trên hình phải đọc từ file CSV/JSON/MD đã có. Được phép: group-by, median, IQR, bootstrap, tỉ lệ, log. Không được phép: giải lại WDP/VCG, sinh lại instance, nội suy dữ liệu thiếu.
2. **Thiếu cột → dừng và báo.** Nếu một hình cần cột không tồn tại, ghi vào `figures/MISSING.md` (hình nào, cần cột gì, đã tìm ở file nào) rồi chuyển sang hình khác. Không tự "thay thế gần đúng".
3. **Mỗi hình có sanity check tự động.** Script tính lại các con số chủ chốt và `assert` khớp với giá trị kỳ vọng của [MASTER] (sai số làm tròn ≤ 0.01 điểm % hoặc ≤ 1% tương đối cho thời gian). Assert fail → **không lưu hình**, ghi lỗi vào `figures/CHECK_FAILURES.md`. Không được sửa giá trị kỳ vọng cho khớp dữ liệu.
4. **Không đặt title bên trong hình.** Tiêu đề và giải thích nằm trong caption LaTeX. Chỉ dùng nhãn panel (a), (b), (c).
5. **Quy ước thống kê khóa ([MASTER] §0.4):**
   - Hiệu ứng kinh tế: median [IQR] + mean (95% paired bootstrap CI), **trên instance**, không trên cell. Bootstrap 2000 lần, resample theo instance, `seed=20260929`.
   - Speed-up: luôn báo **median per-instance** (con số chính) và **pooled** (tổng thời gian / tổng thời gian, ghi rõ "pooled").
   - **Cấm** "mean của median cell".
6. **Không gọi alignment 0.50 là "neutral".** Dưới mỗi tick alignment, ghi thêm FD rate quan sát được (xem §3.3).
7. **Hai loại số không trộn lẫn:** số từ *synthetic audit* (tham số κ=0.5, service 2 phút) và số từ *thesis experiments* (κ=1.0, service 5 phút). Hình dùng dữ liệu synthetic phải có chữ "synthetic" trong tên file và caption.

---

## 1. Môi trường và thư viện

### 1.1 Môi trường riêng cho plotting

Production code chạy Python 3.7.7 + CPLEX. **Không cài thư viện plot vào môi trường đó.** Tạo venv riêng (Python ≥ 3.10) chỉ đọc CSV:

```bash
python -m venv .venv-plots && source .venv-plots/bin/activate
pip install matplotlib numpy pandas scipy seaborn SciencePlots
# tùy chọn: pip install cnsplots
```

### 1.2 Chọn thư viện

| Thư viện | Vai trò | Ghi chú |
|---|---|---|
| **matplotlib + SciencePlots** | **Nền chính** | SciencePlots là bộ style matplotlib cho paper khoa học, ổn định, chuẩn trong ngành OR/engineering. Dùng `plt.style.use(["science", "no-latex"])` (hoặc `["science"]` nếu máy có LaTeX để font khớp paper). |
| seaborn | Hàm tiện cho box/strip/violin | Chỉ dùng hàm vẽ, **không** dùng theme của seaborn (sẽ đè style). |
| cnsplots | Tùy chọn | Có thật, trên PyPI, hướng tới figure cho Cell/Nature/Science (gốc bioinformatics), có sẵn skill cho Claude Code (`cnsplots skill install --agent claude --scope project`). Nhược điểm cho bài này: còn ở v0.x và đổi API phá vỡ tương thích giữa các bản; kích thước tính theo pixel; thẩm mỹ thiên về biology. **Nếu dùng: pin version trong `requirements-plots.txt`** và chỉ dùng cho box/strip; các hình runtime log-scale và forest plot vẫn làm bằng matplotlib để đồng nhất. |

Quyết định mặc định: **matplotlib + SciencePlots cho tất cả**. Chỉ chuyển sang cnsplots nếu người dùng yêu cầu rõ.

### 1.3 Style chung (`plots/style.py`)

- Kích thước theo hướng dẫn artwork của Elsevier:
  - `SINGLE = 90 mm` (≈ 3.54 in), `ONEHALF = 140 mm` (≈ 5.51 in), `DOUBLE = 190 mm` (≈ 7.48 in).
  - Chiều cao mặc định = rộng × 0.62; hình nhiều panel theo hàng chỉnh riêng.
- Font 8 pt (tick 7 pt, legend 7 pt). Sau khi đưa vào LaTeX không được scale — dùng `\includegraphics` đúng width đã thiết kế.
- Line width 1.0; marker size 3–4; lưới nhẹ `alpha=0.3` chỉ trục y.
- Xuất **PDF vector** (chính) + **PNG 600 dpi** (xem nhanh). `bbox_inches="tight"`, `pad_inches=0.02`. Nhúng font (`pdf.fonttype = 42`).
- Phải đọc được khi in đen trắng: mỗi series phân biệt bằng **marker + linestyle**, không chỉ màu.

### 1.4 Bảng màu và mã hóa cố định (dùng thống nhất mọi hình)

Palette Okabe–Ito (an toàn cho mù màu):

| Thực thể | Màu | Marker | Linestyle |
|---|---|---|---|
| GW (gigworker) | `#0072B2` xanh dương | `o` | `-` |
| OD (occasional driver) | `#D55E00` cam đỏ | `s` | `--` |
| FD (fixed fleet) | `#7F7F7F` xám | `^` | `:` |
| B1 / B2 / B3 / B4 | `#CCCCCC` / `#56B4E9` / `#0072B2` / `#003B5C` | `.` `v` `o` `D` | |
| HEUR | `#E69F00` cam | `x` | `-.` |
| ORACLE / VCG / PAB-BR / POSTED | `#000000` / `#0072B2` / `#009E73` / `#CC79A7` | `*` `o` `s` `^` | |
| $n = 10 / 15 / 20$ | 3 sắc độ xám-xanh `#9ecae1` `#4292c6` `#08519c` | `o` `s` `D` | |
| Regime FD-dominated (alignment 0.50) / crowd-competitive (0.90) | `#7F7F7F` / `#0072B2` | | |
| Naive / accelerated | rỗng (hollow) / đặc (filled) | | |

Tên hiển thị trên hình: "GW", "OD", "FD", "$B{=}3$", "HEUR", "VCG", "PAB-BR", "Posted price", "First-best". Nhãn trục bằng tiếng Anh.

---

## 2. Bước 1 — Khám phá dữ liệu (bắt buộc, trước khi vẽ)

Viết `plots/discover.py`:

1. Tìm (recursive) các file sau trong repo, in đường dẫn thật:

| Mã | File (tên có thể khác chút — tìm theo pattern) | Dùng cho |
|---|---|---|
| D1 | `rq1_main_grid_results.csv` | RQ1, FD rate |
| D2 | `rq1_comp_gain_recomputed*.csv` | RQ1 (đối chiếu) |
| D3 | kết quả RQ2 (pattern `*rq2*`) | Bundling, price of range, pool size, $t_A$ |
| D4 | kết quả RQ3 (pattern `*rq3*`) | Payout premium, rent, efficiency loss |
| D5 | kết quả RQ4 (pattern `*rq4*`) | Runtime, speed-up, $\mathcal K^\star$ cut, build time |
| D6 | kết quả RQ5 (pattern `*rq5*`) | Robustness, runtime $n=25,30$ |
| D7 | `kstar_empty_split_by_alignment.csv`, `..._instance.csv`, `kstar_empty_split_by_fd_price.csv` | Chứng nhận trước đấu giá |
| D8 | `kstar_build_time_reconciliation.csv` | Build time vs pool |
| D9 | `New_t4/files/compare_bc_runtime.csv` + raw timing của label rule (pattern `*speedup*`, `*dp_fast*`) | Label rule |
| D10 | `Final_t4_Speedup_RESULTS.md` | Bảng label rule (fallback nếu thiếu raw) |
| D11 | kết quả T5 component (pattern `*component*`) | T5 |
| D12 | `rq_analysis_tables.md`, `rq_all_locked_params.json`, `rq1_locked_params.json` | Tra cứu, hash |

2. Với mỗi file: in số dòng, danh sách cột, dtype, 3 dòng đầu, giá trị duy nhất của các cột phân loại (alignment, n, supply, treatment/menu/mechanism/variant).
3. Ghi toàn bộ vào `figures/DATA_MANIFEST.md`, kèm **SHA-256 của từng file đầu vào**.
4. Viết `plots/columns.py`: ánh xạ tên logic → tên cột thật (ví dụ `ALIGN = "alignment"`, `T_A = "t_A_s"`). Mọi script vẽ chỉ dùng tên logic.
5. **Dừng lại, in tóm tắt cho người dùng xem ánh xạ cột trước khi vẽ.** Nếu có cột mơ hồ (ví dụ hai cột thời gian), hỏi người dùng.

---

## 3. Hàm dùng chung

### 3.1 `plots/stats.py`

```python
def median_iqr(x) -> (med, q1, q3)
def mean_boot_ci(x, n_boot=2000, alpha=0.05, seed=20260929) -> (mean, lo, hi)
def paired_diff_boot_ci(df, key, a, b, col, ...)   # resample theo key instance
def speedup_median_per_instance(df, inst_key, t_base, t_treat)  # median của median từng instance
def speedup_pooled(df, t_base, t_treat)                         # sum/sum
```

Khóa instance: bộ `(alignment, n, supply, rep)` hoặc cột `instance_id` nếu có. Kiểm tra khóa là duy nhất cho mỗi treatment.

### 3.2 Kiểu hình "box + mean CI" (dùng lại nhiều lần)

Hộp = IQR, gạch giữa = median, râu = 1.5 IQR, **không** vẽ outlier từng điểm (tránh nhiễu) nhưng vẽ strip mờ (`alpha=0.15`, jitter nhỏ) nếu $n_{\text{instance}} \le 300$. Chồng lên một marker ◆ = mean, thanh dọc = 95% bootstrap CI. Legend nhỏ giải thích "box: IQR; ◆: mean with 95% CI".

### 3.3 Nhãn regime cho trục alignment

Tick label hai dòng: dòng 1 = giá trị alignment; dòng 2 = FD rate mean trên instance tính từ D1 (JOINT/B3), dạng `FD 0.95`. Giá trị kỳ vọng ([MASTER] §15.1): 0.830 / 0.812 / 0.949 / 0.691 / 0.374 cho alignment 0.10 / 0.30 / 0.50 / 0.70 / 0.90. Assert khớp ±0.001.

---

## 4. Danh sách hình

Ký hiệu ưu tiên: **[M]** = hình chính trong paper (mục tiêu 8–9 hình), **[A]** = appendix/online supplement.

Mỗi mục: mục đích → dữ liệu → thiết kế → sanity check → caption nháp (tiếng Anh, chép vào LaTeX).

---

### FIG C1 [M] — Trực giác của local frontier (giải tích, không cần dữ liệu)

**File:** `fig_c1_frontier_intuition.pdf` · width SINGLE×3 panel → dùng DOUBLE, 1 hàng 3 panel.

**Mục đích:** minh họa Definition 2 bằng Example 11 — route nằm trong/ngoài $\mathcal K^\star$ nhìn bằng mắt.

**Dữ liệu (Example 11, [MASTER] §5.5):** $q_{o_1}=15$, $q_{o_2}=45$; $r_a:\{o_1\}, (K,W)=(6,0.6)$; $r_b:\{o_2\}, (8,0.8)$; $r_c:\{o_1,o_2\}, (11,1.2)$; $\Theta=[18,25]$.

- (a) $r_a$: $c(b)=6+0.6b$, $E(b)=15$ (chỉ có $0_i$).
- (b) $r_b$: $c(b)=8+0.8b$, $E(b)=45$.
- (c) $r_c$: $c(b)=11+1.2b$, $E(b)=\min\{60,\ 51+0.6b,\ 23+0.8b\}$.

**Thiết kế:** trục $b \in [0, 35]$. Đường liền = $c_r(b)$; đường đứt = $E_r(b)$ (vẽ cả ba nhánh affine mờ ở panel (c), envelope đậm). Tô dải dọc $\Theta$ màu xám nhạt. Tô vùng $\mu_r(b) > 0$ **trong** $\Theta$ màu xanh nhạt. Ghi nhãn panel: "(a) $r_a \notin \mathcal K^\star$", "(b) $r_b \in \mathcal K^\star$", "(c) $r_c \in \mathcal K^\star$".

**Sanity:** $E_{r_c}(18)=37.4$, $c_{r_c}(18)=32.6$; $c_{r_a}(18)=16.8>15$; giao điểm $c_{r_a}=E_{r_a}$ tại $b=15$ (ngoài $\Theta$).

**Caption:**
> Local margins in Example 11. Solid lines: reported cost $c_r(b)$; dashed: FD-completion envelope $E_r(b)$; grey band: report domain $\Theta=[18,25]$. A route belongs to $\mathcal K^\star$ iff the envelope lies strictly above its cost somewhere in $\Theta$ (shaded). Route $r_a$ is deleted only because $\Theta$ excludes bids below 15; with unrestricted reports it would be retained (Remark 16).

---

### FIG 1 [M] — Tăng trưởng pool theo $n$: GW vs OD

**File:** `fig01_pool_growth.pdf` · SINGLE (hoặc ONEHALF nếu 2 panel).

**Mục đích:** hiện thực hóa bất đối xứng GW/OD (§4.4) và độ tăng $\Theta(n^B)$ mà Theorem 10 nói là không tránh được.

**Dữ liệu:** D3 (pool size theo driver class, menu B3 và B4). Cần cột số route **tách theo GW/OD**. Nếu D3 chỉ có tổng pool → ghi MISSING, **không** tự chia. (Có thể dùng D5 nếu D5 có pool theo class.)

**Thiết kế:** x = $n \in \{10,15,20\}$; y = số route mỗi driver (median, thanh IQR), **log scale**. Series: GW-B3, OD-B3, GW-B4 ($n\le15$), OD-B4. Thêm đường tham chiếu mờ $\propto n^3$ và $\propto n^4$ neo tại $n=10$ của GW, nhãn "$\propto n^B$". Panel (b) tùy chọn: tỉ lệ pool OD/GW (%) theo alignment.

**Sanity:** pool mean tổng B3 = 2,829, B4 = 5,313 (§11.3, trên toàn instance tương ứng); tỉ lệ OD/GW nằm trong 0.7–1.7% (§4.4).

**Caption:**
> Route-pool size per driver generated by Algorithm A (log scale). Gigworkers, who have no detour anchor, follow the $\Theta(n^B)$ growth that Theorem 10 shows cannot be avoided by any local bid-independent rule; occasional drivers' pools remain two orders of magnitude smaller.

---

### FIG 2 [M] — Phân rã thời gian chạy theo $n$

**File:** `fig02_runtime_breakdown.pdf` · DOUBLE, 1×2 panel (FD-dominated | crowd-competitive).

**Mục đích:** trả lời câu "khi $n$ tăng thì tốc độ ra sao" và cho thấy bottleneck là Algorithm A, không phải payment.

**Dữ liệu:** D5 (RQ4, 600 instance, alignment ∈ {0.50, 0.90}); $t_A$ cho B4 lấy từ D3 nếu muốn thêm một series mờ.

**Thiết kế:** x = $n$; y = thời gian (s), **log scale**, median + dải IQR. Series: $t_A$ (Algorithm A), $t_B$ (WDP), $t_C$ naive, $t_C$ on $\mathcal K^\star$, $t_{\text{build}}(\mathcal K^\star)$. Cùng trục y giữa hai panel (`sharey=True`).

**Sanity (alignment 0.90, median):** $t_A$ = 0.65 / 2.20 / 7.40 s; $t_C$ naive = 0.134 / 0.248 / 0.655 s; $t_C$ accel = 0.060 / 0.144 / 0.259 s. (Alignment 0.50: $t_A$ = 0.26 / 1.00 / 2.56; $t_C$ naive = 0.039 / 0.086 / 0.186.)

**Caption:**
> Median running time per component (log scale; bands: interquartile range) in the fixed-fleet-dominated regime (a) and the crowd-competitive regime (b). Exact VCG payments never exceed 0.66 s at $n=20$; route generation dominates the pipeline.

---

### FIG 3 [M] — Speed-up của bước payment nhờ $\mathcal K^\star$

**File:** `fig03_payment_speedup.pdf` · ONEHALF.

**Dữ liệu:** D5.

**Thiết kế:** x = $n$, nhóm theo regime (2 nhóm × 3 $n$). Hai hộp mỗi vị trí: "payment step only" (đặc) và "including frontier construction" (rỗng). y = speed-up, **log scale**, đường ngang tại 1 (đứt, xám). Góc trên phải: hộp text "pooled: 3.01× (payment only), 1.06× (incl. construction)".

**Sanity (median payment-only):** 11.20 / 17.98 / 30.40 (0.50); 2.34 / 1.81 / 2.72 (0.90). Median incl. build: 1.13 / 0.63 / 0.60 (0.50); 1.44 / 1.05 / 1.24 (0.90). Pooled 3.01 và 1.06. Max $|\Delta p| \le 1.1\times10^{-13}$ (assert, không vẽ).

**Caption:**
> Speed-up of exact payment computation on the pruned pool $\mathcal K^\star$ relative to the full pool, per instance (log scale). Pruning never changed a payment (maximum deviation $1.1\times10^{-13}$). The gain on the payment step is offset for a single auction by the cost of constructing the frontier in our implementation.

⚠️ Không dùng hình này như "headline speed-up". Caption phải có câu về single auction.

---

### FIG 4 [M] — Label rule (Part II): tiết kiệm extension và speed-up

**File:** `fig04_label_rule.pdf` · DOUBLE, 1×2 panel.

**Dữ liệu:** D9 raw timing (ưu tiên). Nếu không có raw, dùng bảng trong D10 và **ghi rõ trong DATA_MANIFEST** là dùng số tổng hợp; khi đó chỉ vẽ median + IQR đã báo cáo, không vẽ strip.

**Thiết kế:**
- (a) Dot plot: y = 5 instance (nhãn "n12 s42", …), x = speed-up (log), điểm = median, thanh = IQR; hai màu cho $B=3$, $B=4$. Đường dọc tại 1. Chú thích median per-instance và pooled.
- (b) Bar ngang: % label extensions saved, cùng thứ tự instance, $B=3$ vs $B=4$.

**Sanity:** median per-instance 1.48× ($B=3$), 2.19× ($B=4$); pooled 1.72×, 2.94×; extension saved $B=3$: 44.2 / 35.5 / 57.3 / 50.1 / 39.4%; $B=4$: 61.0 / 49.5 / 76.2 / 69.7 / 55.8%.

**Caption:**
> Effect of the FD-completion label rule on Algorithm A for the five experimental instances. (a) Speed-up per instance (median and IQR over repeated runs); (b) share of label extensions avoided. The rule leaves $\mathcal K^\star$ unchanged (Theorem 24) and never fired for occasional drivers.

---

### FIG 5 [M] — RQ1: complementarity gain theo regime

**File:** `fig05_rq1_complementarity.pdf` · ONEHALF.

**Dữ liệu:** D1 (tính lại), đối chiếu D2.

**Thiết kế:** kiểu §3.2. x = alignment (tick 2 dòng theo §3.3), hue = $n$ (3 hộp mỗi vị trí). y = complementarity gain (%), trục tuyến tính. Thêm đường ngang 0.

**Sanity (trên mọi $n$, $n_{\text{inst}}=300$ mỗi alignment):** median 0.00 / 0.00 / 0.00 / 0.77 / 5.84; mean 0.33 / 0.51 / 0.04 / 1.39 / 6.06; CI mean ở 0.90 = (5.68, 6.46). Theo $n$ ở 0.90: median 5.01 / 5.84 / 7.00. 0 instance bị loại.

**Caption:**
> Complementarity gain of joint bidding over the better single-class procurement, per instance. Second tick row: observed fixed-fleet share. Boxes: IQR; diamonds: mean with 95% bootstrap CI.

Hình phụ tùy chọn [A] `fig05b_sequential.pdf`: loss của OD-first→GW và GW-first→OD so với JOINT theo alignment — **chỉ vẽ nếu tính lại theo §0.4** (MASTER ghi con số 1.3–5.3% vẫn theo cách gộp cũ).

---

### FIG 6 [M] — RQ2: giá trị của endogenous bundling

**File:** `fig06_rq2_bundling.pdf` · DOUBLE, 1×2 panel.

**Dữ liệu:** D3.

**Thiết kế:**
- (a) x = alignment (tick §3.3); y = bundling gain vs B1 (%); 4 series B2, B3, B4 ($n\le15$), HEUR: median (marker + đường nối) + dải IQR mờ. Dùng point-range thay vì box để 4 series không chồng.
- (b) Price of range $B$: $(C_{B3}-C_{B4})/C_{B4}$ (%), x = alignment, hue $n \in \{10,15\}$, kiểu box.

**Sanity (alignment 0.90):** median B2 6.37, B3 11.32, B4 15.16, HEUR 4.94; mean B3 11.47 (CI 10.92–12.02); B3 vs HEUR median 5.61. Price of range 0.90: 4.0% ($n=10$), 5.7% ($n=15$) — kiểm xem MASTER ghi mean hay median trước khi assert; nếu không rõ, in ra cả hai và đánh dấu `[CHECK]`.

**Caption:**
> (a) Cost reduction relative to single-order routes ($B=1$) for platform-generated bundles up to size 2, 3 and 4 and for a fixed bid-independent partition (HEUR); points: median, bands: IQR. (b) Cost of restricting bundles to size 3 instead of 4.

---

### FIG 7 [M] — RQ3: chi phí của truthful procurement

**File:** `fig07_rq3_mechanisms.pdf` · DOUBLE, 1×2 panel. **Chỉ alignment 0.90** (ở 0.50 mọi cơ chế ≈ nhau; nêu trong caption).

**Dữ liệu:** D4.

**Thiết kế:**
- (a) Payout premium vs first-best (%), x = $n$, hue = VCG / PAB-BR / POSTED, kiểu §3.2.
- (b) Scatter per instance: x = efficiency loss (%), y = payout premium (%), màu/marker theo cơ chế, alpha 0.4; thêm marker lớn = median mỗi cơ chế. Thông điệp: VCG và PAB-BR nằm trên trục x = 0 (hiệu quả), POSTED lệch phải.

**Sanity (all $n$):** premium median VCG 14.13, PAB-BR 5.78, POSTED 9.12; mean VCG 15.05 (14.30–15.79). Efficiency loss median POSTED 3.99; PAB 0.00. VCG payout > PAB-BR ở 300/300 instance.

**Caption:**
> Crowd-competitive regime (alignment 0.90). (a) Payout premium over the full-information benchmark. (b) Payout premium against efficiency loss per instance; large markers: medians. PAB-BR is a unilateral best-response benchmark within the bounded bid range, not an equilibrium. In the fixed-fleet-dominated regime all mechanisms coincide (not shown).

---

### FIG 8 [M] — Regime và chứng nhận trước đấu giá

**File:** `fig08_regimes_certificate.pdf` · DOUBLE, 1×3 panel.

**Dữ liệu:** D1 (FD rate), D7.

**Thiết kế:**
- (a) FD rate (mean trên instance, CI) theo alignment, hue $n$ — cho thấy **không đơn điệu**, đỉnh tại 0.50. Chú thích nhỏ `corridor_share` của từng mức nếu có trong locked params.
- (b) Stacked bar 100% theo alignment, per-driver: `feasible_empty` (xám đậm, hatch `//`), `fd_dominated` (xanh), còn lại "frontier non-empty" (trắng viền).
- (c) Cùng kiểu stacked bar theo FD multiplier ×0.75 / ×1.00 / ×1.25 (RQ5, alignment 0.50).

**Sanity:**
- (a) 0.830 / 0.812 / 0.949 / 0.691 / 0.374.
- (b) feasible_empty 14.8 / 12.3 / 43.1 / 2.5 / 0.1; fd_dominated 20.4 / 19.5 / 34.3 / 10.5 / 1.0.
- (c) feasible_empty 43.7 ở cả ba mức (assert **bằng nhau tuyệt đối**); fd_dominated 52.0 / 33.3 / 13.0 (assert giảm đơn điệu).

**Caption:**
> (a) Share of orders served by the fixed fleet; the share is not monotone in the nominal alignment level. (b–c) Drivers with no feasible route (hatched) and drivers whose feasible routes are all dominated by fixed-fleet completion over the entire report domain, i.e. certified before bidding by Theorem 4 (blue). The certified share falls monotonically with the fixed-fleet tariff, as predicted by Remark 14; the infeasible share does not depend on the tariff.

---

### FIG 9 [M] — RQ5: forest plot độ bền

**File:** `fig09_rq5_forest.pdf` · DOUBLE, 1×3 panel (chung trục y = biến thể).

**Dữ liệu:** D6.

**Thiết kế:** y = V1…V8 (nhãn ngắn: "TW 60", "TW 240", "Detour 20", "Detour 45", "FD ×0.75", "FD ×1.25", "Clustered", "θ∼U[15,30]"). Mỗi panel một metric: Δ complementarity, Δ bundling, Δ VCG overhead (điểm %, paired vs V0): điểm = mean, thanh = 95% CI. Đường dọc 0. Panel VCG overhead có trục x riêng (thang lớn hơn nhiều).

**Sanity:** V6 Δbundling = 1.38 (0.97, 1.81); V5 ΔVCG overhead = −28.64 (−43.31, −4.28); V1 Δbundling = −0.09 (−0.17, −0.04).

**Caption:**
> One-at-a-time robustness around the baseline (alignment 0.50, $n=15$): paired differences from the baseline with 95% bootstrap CIs. The baseline lies in the fixed-fleet-dominated regime, so most effects are close to zero; the fixed-fleet tariff is the governing parameter.

---

### Appendix

#### FIG A1 [A] — Thời gian dựng $\mathcal K^\star$ theo kích thước pool
`figA1_kstar_build_vs_pool.pdf` · SINGLE. Dữ liệu D5 (600 điểm) + D8 (10 điểm). Scatter log-log, 600 điểm mờ màu theo regime; 10 điểm đối chiếu marker rỗng lớn (5 của [S2] khác marker với 5 của RQ4). Đường hồi quy trên log. Chú thích Pearson $r$ (tuyến tính, không log).
Sanity: $r = 0.979$ (600), $r = 0.988$ (10 điểm); µs/route: 33–41 ([S2] trừ n10 s1 = 66), 48–54 (RQ4 sample).
Caption: *Frontier construction time against pool size. Open markers: the ten instances used to reconcile the two timing sources.*

#### FIG A2 [A] — Mức nén pool
`figA2_pool_compression.pdf` · SINGLE. Scatter log-log: x = |pool đầy đủ|, y = |$\mathcal K^\star$| (+1 để log được khi rỗng; ghi rõ trong caption), đường chéo $y=x$ và $y = 0.25x$. Màu theo regime.
Sanity: median cut 100% (0.50), 75.2 / 76.6 / 77.2% (0.90, $n$=10/15/20).

#### FIG A3 [A] — T5: kích thước component lớn nhất
`figA3_t5_components.pdf` · SINGLE. ECDF của (largest component / $n_{\text{drivers}}$); 4 đường: {full, $\mathcal K^\star$} × {0.50, 0.90}. Đường dọc tại 0.85 (ngưỡng dừng khóa trước).
Sanity: median full 0.90 = 1.000; $\mathcal K^\star$ 0.90 = 1.000; $\mathcal K^\star$ 0.50 = 0.250; 22/300 instance ≥2 component ($\mathcal K^\star$, 0.90).
Caption nhấn: *on the crowd-competitive instances the conflict graph is almost always connected, so component decomposition yields little benefit.*

#### FIG A4 [A] — Price of locality (Theorem 10), synthetic
`figA4_synthetic_price_of_locality.pdf` · SINGLE. x = $n \in \{3,5,7,9\}$; y (log) = $|\mathcal K^\star_g|$ quan sát (marker) và $\sum_{k=1}^{B}\binom nk$ (đường). Chú thích: "routes of $g$ optimal for any sampled bid profile: 0". Nếu không tìm được file audit → MISSING (không được vẽ chỉ đường lý thuyết rồi coi là kiểm chứng).

#### FIG A5 [A] — Khả năng mở rộng pipeline đầy đủ (RQ5)
`figA5_pipeline_scaling.pdf` · SINGLE. x = $n \in \{15, 25, 30\}$ (V0, V9, V10), y = tổng thời gian pipeline (s, log), box; đường ngang 300 s "time limit". Chú thích số solve OPTIMAL.
Sanity: median 1.34 / 9.95 / 18.48 s; 60/60 ≤ 300 s ở mọi mức. ⚠️ V9/V10 dùng supply khác — ghi trong caption.

#### FIG A6 [A] — Label rule theo giá FD (synthetic)
`figA6_synthetic_label_rule_fd_price.pdf` · SINGLE. x = FD multiplier {0.6, 1.0, 1.4}, trục trái: extension saved (%), trục phải: speed-up (×) với đường ngang 1. Sanity: 73–76%/2.8–3.1×; 27–30%/≈1.0×; 7–9%/0.75×. Tránh twin-axis nếu xấu → 2 panel nhỏ.

#### FIG A7 [A] — Biện minh single-parameter (bundle menu gần một tia)
`figA7_single_parameter_menu.pdf`. Dữ liệu từ các vòng đo trước (σ_ψ, số quạt, welfare loss). **Tìm file; nếu không có → MISSING.** Thiết kế nếu có: scatter $(d(B), t(B))$ của menu một tài xế điển hình + tia fit; inset histogram độ lệch góc.

#### Sơ đồ (không làm bằng Python)
Pipeline (Fig 1 trong paper theo [MASTER] §19.2), hai instance song sinh (Example 11), construction Theorem 10 → **vẽ bằng TikZ trong LaTeX**. Không sinh bằng matplotlib. Ghi TODO vào `figures/README.md`.

---

## 5. Cấu trúc code

```
plots/
  style.py          # rcParams, SciencePlots, palette, kích thước mm→in, savefig()
  columns.py        # ánh xạ tên logic → cột thật (sinh sau discover)
  discover.py       # §2
  data.py           # loader cho D1–D12, kiểm khóa instance duy nhất
  stats.py          # §3.1
  expected.py       # MỌI giá trị kỳ vọng ở mục Sanity, dạng dict, có trích mục [MASTER]
  checks.py         # assert_close(name, got, exp, tol) → ghi CHECK_FAILURES.md
  fig_c1.py, fig01.py, ..., fig09.py, figA1.py, ...
  make_all.py       # chạy tất cả; tổng kết OK / MISSING / CHECK_FAIL
figures/
  *.pdf, *.png
  DATA_MANIFEST.md  # file đầu vào + SHA-256 + cột
  MISSING.md
  CHECK_FAILURES.md
  captions.tex      # \newcommand hoặc khối caption cho từng hình
  README.md         # bảng: hình → script → file dữ liệu → hash → trạng thái
requirements-plots.txt  # pin version (matplotlib, SciencePlots, seaborn, pandas, numpy, scipy[, cnsplots])
```

`make_all.py` cuối cùng in bảng:

| Figure | Status | Checks passed | Notes |

---

## 6. Snippet LaTeX kèm theo

Sinh `figures/captions.tex` theo mẫu:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=190mm]{figures/fig02_runtime_breakdown.pdf}
  \caption{<caption từ spec>}
  \label{fig:runtime-breakdown}
\end{figure}
```

Dùng đúng width đã thiết kế (90 / 140 / 190 mm) — **không** dùng `\linewidth` cho hình SINGLE trong layout một cột review (sẽ phóng to font).

---

## 7. Checklist QA trước khi giao lại

- [ ] Mọi hình main có sanity check pass; CHECK_FAILURES.md rỗng hoặc đã báo người dùng.
- [ ] In thử grayscale (`convert -colorspace Gray` hoặc render PNG xám): phân biệt được mọi series.
- [ ] Font thực tế sau khi chèn ≥ 7 pt; không chữ nào bị cắt.
- [ ] Trục log có ghi "(log scale)" trong nhãn hoặc caption.
- [ ] Đơn vị trên mọi trục: s, %, ×, routes per driver.
- [ ] Không có title trong hình; nhãn panel (a)(b)(c) góc trên trái, đậm.
- [ ] Không hình nào dùng "mean của median cell".
- [ ] Hình synthetic có chữ "synthetic" trong tên file và caption.
- [ ] Tick alignment có dòng FD rate; không có chữ "neutral".
- [ ] Fig 3 caption có câu về single auction (1.06×).
- [ ] Fig 7 caption nói PAB-BR không phải equilibrium.
- [ ] DATA_MANIFEST có SHA-256; README có bảng provenance.

---

## 8. Thứ tự thực hiện đề nghị

1. `discover.py` → dừng, người dùng duyệt ánh xạ cột.
2. `style.py`, `stats.py`, `expected.py`, `checks.py`.
3. FIG C1 (không cần dữ liệu — kiểm style trước).
4. FIG 5, 6, 7, 8 (kinh tế; dữ liệu nhiều nhất, dễ lộ lỗi ánh xạ).
5. FIG 2, 3, 1, 4 (runtime).
6. FIG 9, rồi appendix.
7. `make_all.py`, QA checklist, báo cáo tổng.