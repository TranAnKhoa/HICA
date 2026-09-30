# RQ1 → RQ5 — Spec thực thi tổng (Master)

> File này là spec chung cho **toàn bộ** 5 câu hỏi nghiên cứu ở `Master_Thesis_Q1.md` §12.1.
> RQ1 đã chạy xong theo `Rq1.md` (xem §2 dưới đây, chỉ trích dẫn, **không chạy lại**).
> RQ2–RQ5 dùng lại **nguyên** hạ tầng và tham số đã khoá của RQ1. Mọi tham số mới ở §3–§7
> bị KHOÁ (ghi vào `spec_2a_2b/results/rq_all/rq_all_locked_params.json` + SHA-256) **trước**
> instance đầu tiên của main run. Không sửa sau khi thấy kết quả.
>
> Nhãn: `[LOCK]` không đổi sau khi hash · `[IMPLEMENT]` cần code · `[CHECK]` gate bắt buộc
> pass trước khi tin số · `[DECISION]` quy tắc đọc kết quả, viết TRƯỚC khi chạy.

---

## 0. Bảng tổng

| RQ | Câu hỏi | Treatment | Đối chứng | Outcome chính | Trạng thái |
|---|---|---|---|---|---|
| RQ1 | Cho cả hai lớp GW/OD cùng bid có giá trị không? | JOINT (B=3) | GW-only, OD-only, OD-first→GW, GW-first→OD | Complementarity gain, FD rate | **Xong** (`Report_RQ1_Complementarity.md`) |
| RQ2 | Endogenous bundling có giá trị không? | B = 2, 3, (4) | B = 1, HEUR (bundle heuristic cố định) | Bundling gain, FD rate, bundle size, runtime | **Xong** 2026-09-27 (`Report_RQ_All.md` §2) |
| RQ3 | Truthful procurement tốn gì? | VCG exact | Oracle full-info, Pay-as-bid (best-response), Posted price | Payout, information rent, payment overhead, hiệu quả phân bổ | **Xong** (`Report_RQ_All.md` §3) |
| RQ4 | Exact payment có khả thi không? | Accelerated C (K*-pruned pool) | Naive C (full pool) | Runtime B+C, speed-up, equality error | **Xong** (`Report_RQ_All.md` §4) |
| RQ5 | Kết quả có bền không? | 10 biến thể one-at-a-time | Baseline | Paired effect RQ1/RQ2/RQ3 theo biến thể, solve rate | **Xong** (`Report_RQ_All.md` §5) |

## 1. Nền chung cho mọi RQ (kế thừa RQ1, `[LOCK]` sẵn — không khoá lại)

- **Cost model:** true cost route r của driver i = `K_r + θ_i·W_r`; κ = 1.0 cost-unit/km.
- **θ_i ~ Uniform[18, 25]** (cùng phân phối GW/OD) — `rq1_cost_gen.py`.
- **q_o = 8.0 + 3.0·max(0, dist_km − 1.0)** — `rq1_cost_gen.py`.
- **Generator:** `instance_gen.generate_instance`, `tw_width=120`, `tau=30.0`,
  `spatial_mode="dispersed"`, alignment → (corridor_share, corridor_buffer_km) theo bảng
  `locked_targets` của `rq1_locked_params.json`.
- **Algorithm A:** `dp_labeling.build_route_pool` (production, Layers 1–2). Layer 3
  (FD-completion rule) **không** dùng trong RQ2–RQ5 — nó chỉ đổi thời gian của A, không đổi
  pool mà K* trả về, và chưa được tích hợp vào code production.
- **Algorithm B:** `t8_cplex` (CPLEX 12.10, threads=1, mipgap=0, absmipgap=0).
- **Algorithm C (naive):** p_i = c_i(r_i) + Z*_{−i} − Z*, một removal-solve cho mỗi winner.
- **Instance pairing:** RQ2/RQ3/RQ4 dùng **đúng** các instance của RQ1 main grid (cùng
  `gen_seed = stable_seed(n, 3, 3, align, n_gw, n_od, rep, "rq1_main_grid")` và cùng
  `theta_seed`). Hệ quả kiểm được: JOINT ở B=3 của RQ2 phải trùng **tuyệt đối**
  `true_cost` JOINT trong `rq1_main_grid_results.csv` (`[CHECK]` X1).
- **Thống kê:** median + IQR + 95% bootstrap CI (2000 resample, resample theo đơn vị
  instance — paired, không resample dòng lẻ). Báo cáo cả tuyệt đối lẫn %.

## 2. RQ1 — đã xong, chỉ trích dẫn

60 cell × 25 rep = 1,500 instance × 5 treatment, 7,500/7,500 OPTIMAL, dry-run gate 0/360.
Complementarity gain (mean của median cell): 0.01% / 0.08% / 0.00% / 0.93% / **5.86%** tại
alignment 0.10/0.30/0.50/0.70/0.90. Finding phụ: OD-first→GW ≈ JOINT, GW-first→OD mất
1.3–5.3% ở alignment cao. Không chạy lại.

---

## 3. RQ2 — Giá trị của endogenous bundling

### 3.1 Treatment `[LOCK]`

| Tên | Menu route mỗi driver được bid |
|---|---|
| **B1** | chỉ bundle \|S\| = 1 |
| **B2** | \|S\| ≤ 2 |
| **B3** | \|S\| ≤ 3 (= JOINT của RQ1) |
| **B4** | \|S\| ≤ 4 — **chỉ n ∈ {10, 15}** (n=20: Algorithm A ~100 s/instance, đo 2026-09-27; ghi nhận là giới hạn, không phải lựa chọn theo kết quả) |
| **HEUR** | singleton + các khối của 1 phân hoạch heuristic cố định do platform tính trước khi nhận bid (§3.2). HEUR ⊇ B1 |

Mọi treatment dùng **toàn bộ** driver (GW+OD) + FD. `B_gw = B_od = B`.

`[IMPLEMENT]` Pool B1/B2 lấy bằng **lọc** pool B3 theo \|S\| ≤ B (không chạy lại A). Pool B4
chạy A riêng với capacity 4 trên cùng seed hình học. `[CHECK]` G1 ở §7 xác nhận lọc == sinh
trực tiếp.

### 3.2 Heuristic bundle cố định (HEUR) `[LOCK]`

Bid-independent, tính một lần/instance:
1. Khoảng cách cặp order `d(o,o') = dist(p_o,p_o') + dist(d_o,d_o')` (km).
2. `D_max` = percentile-25 của mọi `d(o,o')` trong instance.
3. Duyệt cặp theo `d` tăng dần (tie-break theo id). Gộp nhóm chứa o và o' nếu: hợp hai nhóm
   có ≤ 3 order, **mọi** cặp trong hợp có `d ≤ D_max` và `|ready_p − ready_p'| ≤ tw_width`.
4. Menu HEUR của driver = pool B3 của driver đó giới hạn vào {singleton} ∪ {khối có ≥ 2 order}.

### 3.3 Grid `[LOCK]`

Toàn bộ grid RQ1: alignment {0.10, 0.30, 0.50, 0.70, 0.90} × n {10, 15, 20} × supply
{(2,2),(3,2),(2,3),(3,3)} × 25 rep = 1,500 instance. B4 chỉ trên 1,000 instance có n ≤ 15.

### 3.4 Metric

```
Bundling gain(B)    = (C_B1 − C_B) / C_B1          (B ∈ {B2, B3, B4, HEUR})
Endogenous vs HEUR  = (C_HEUR − C_B3) / C_HEUR
FD rate, mean bundle size (order/route thắng), runtime A và B
```

### 3.5 `[DECISION]` (viết trước khi chạy)
- Gain B3 vs B1 ≥ ~2% median trên phần lớn cell → bundling có giá trị vận hành.
- Gain < 1% hầu hết cell → finding hợp lệ: "trong thị trường này bundling gần như không tạo
  giá trị"; báo cáo trung thực, không tăng n/B để "câu" tín hiệu.
- B3 ≈ HEUR → giá trị nằm ở việc cho phép bundle, không ở việc để thị trường tự chọn bundle.
- Price of range B (B3 vs B4) nhỏ → B=3 là lựa chọn đủ.

---

## 4. RQ3 — Chi phí của truthful procurement

### 4.1 Grid `[LOCK]`
alignment {0.50, 0.90} × n {10, 15, 20} × 4 supply × 25 rep = **600 instance** (trùng
instance RQ1). 0.50 = mức tự nhiên không deviation; 0.90 = mức OD cạnh tranh mạnh nhất.
Menu B = 3.

### 4.2 Bốn cơ chế `[LOCK]`

1. **ORACLE (first-best, full-info):** allocation hiệu quả, trả đúng true cost.
   Payout = Z*. Rent = 0. Là cận dưới.
2. **VCG (exact, naive C):** allocation hiệu quả; winner i nhận
   `p_i = c_i(r_i) + Z*_{−i} − Z*`. Rent_i = `Z*_{−i} − Z*`.
3. **PAB-BR (pay-as-bid, best response):** winner được trả đúng bid `K + θ̂_i·W`. Mỗi driver
   chọn θ̂_i trên lưới `{θ_i, θ_i+0.5, …} ∪ {25}` trong miền bid Θ = [18, 25] để tối đa
   `(θ̂_i − θ_i)·W_{r(θ̂_i)}`, **giữ mọi driver khác bid thật** (unilateral best response;
   tie → θ̂ nhỏ nhất). Sau đó áp **đồng thời** mọi θ̂_i → allocation + payout.
   Đây là benchmark chỉ báo (không phải cân bằng Nash), ghi rõ trong báo cáo.
   Dừng quét sớm khi driver không còn thắng (đơn điệu: tăng θ̂ chỉ làm route của i đắt hơn).
4. **POSTED (posted price):** platform niêm yết giá `π_o = λ·q_o`. Driver i chấp nhận route r
   iff `Σ_{o∈S_r} π_o ≥ c_i(r)`. Platform chọn tập route chấp nhận được (≤1/driver, phủ
   đúng 1 lần, phần còn lại FD) để tối thiểu payout `Σ π + Σ q_FD`. λ khoá bằng pilot §4.3.

### 4.3 Pilot khoá λ `[LOCK]`
Instance pilot riêng (tag `"rq3_pilot_lambda"`, KHÔNG trùng instance main): alignment
{0.50, 0.90} × n {10, 15, 20} × 4 supply × 5 rep = 120 instance. λ ∈ {0.40, 0.45, …, 1.00}.
Chọn λ có **mean payout nhỏ nhất** trên pilot (có lợi cho POSTED — baseline mạnh nhất có
thể). Ghi vào locked params, không chỉnh lại.

### 4.4 Metric
```
Payout(M)            = Σ payment cho crowd + Σ q_o (FD)
Information rent     = Σ_i [p_i − c_i(r_i)]          (winner)
Payment overhead     = rent / Σ_i c_i(r_i)
Payout premium vs ORACLE = (Payout(M) − Z*) / Z*
Efficiency loss      = (TrueCost(allocation M) − Z*) / Z*   (PAB-BR, POSTED)
```

### 4.5 `[DECISION]`
- Premium VCG vs ORACLE là **giá của truthfulness**. So VCG với PAB-BR: nếu PAB-BR payout ≥
  VCG thì truthfulness "miễn phí" so với pay-as-bid chiến lược; nếu thấp hơn, báo cáo mức
  chênh + efficiency loss của PAB-BR (đánh đổi payout vs hiệu quả).
- POSTED payout/efficiency cho biết giá trị của việc thu thập bid.
- Mọi hướng đều là kết quả hợp lệ, không chỉnh λ/Θ sau khi xem số.

---

## 5. RQ4 — Tính khả thi của exact payment

Trên **chính 600 instance của RQ3** (cùng θ thật):
- **Naive C:** full solve + removal-solve cho mỗi winner trên pool đầy đủ.
- **Accelerated C:** K* (`kstar_rule.local_frontier`, Θ=[18,25], FD = q_o) cắt pool **một lần
  / instance** (bid-independent), rồi full solve + removal-solve trên pool đã cắt.
- Thứ tự đo luân phiên theo parity của rep. Báo: pool cut %, t_B+C naive, t_B+C accel,
  t_K*build, speed-up (có và không tính t_K*build), `max |p_naive − p_accel|` (equality
  error, `[CHECK]` phải ≤ 1e-6), `|Z*_naive − Z*_accel|`.
- Decomposition T5: đã đóng ở `Report_2b_Component_Distribution.md` (component gộp ≥ 0.889
  driver ở scale chính) → chỉ trích dẫn, không đo lại.
- Layer 3 (Algorithm A): trích dẫn `New_t4/files/Final_t4_Speedup_RESULTS.md`.

`[DECISION]` Equality error > 1e-6 ở bất kỳ instance nào → dừng, điều tra (vi phạm Định lý K*),
không báo speed-up.

---

## 6. RQ5 — Độ bền (one-at-a-time)

### 6.1 Baseline và biến thể `[LOCK]`
Baseline: n = 15, alignment 0.50 (corridor_share 0.0, buffer 3.0), supply 4 ratio, tw 120,
τ 30, FD ×1.0, θ ~ U[18,25], dispersed. 15 rep/supply → 60 instance/biến thể.

| ID | Thay đổi so với baseline |
|---|---|
| V0 | baseline |
| V1 / V2 | tw_width = 60 / 240 |
| V3 / V4 | τ = 20 / 45 |
| V5 / V6 | q_o × 0.75 / × 1.25 |
| V7 | spatial_mode = clustered |
| V8 | θ ~ U[15, 30] (khuyến nghị: thay đổi mức dị biệt tư nhân) |
| V9 / V10 | n = 25 / n = 30 (scalability), supply {(3,3),(4,3),(3,4),(4,4)} |

Seed: `stable_seed(n, n_gw, n_od, rep, "rq5")` — **không** chứa tham số biến thể ⇒ V0–V8 dùng
cùng hình học đầu vào (paired giữa biến thể trong giới hạn generator cho phép).

### 6.2 Outcome mỗi biến thể
Complementarity gain (JOINT vs best single — RQ1), bundling gain B3 vs B1 (RQ2), VCG payment
overhead (RQ3), FD rate, runtime A / B / C, **solve rate** = tỉ lệ solve OPTIMAL (gap 0) và
tỉ lệ instance hoàn tất A+B+C trong ≤ 300 s.

### 6.3 `[DECISION]`
Một kết luận RQ1–RQ3 được gọi là "bền" nếu dấu và bậc độ lớn của median effect giữ nguyên ở
mọi biến thể V1–V10. Biến thể nào đảo dấu → báo cáo tường minh, không loại biến thể.

---

## 7. Gate bắt buộc trước main run `[CHECK]`

Grid gate: n ∈ {3,4,5,6} × tw ∈ {60,120} × seed ∈ {0,1,2} × 4 driver, tag `"rq_all_gate"`.
Oracle độc lập: pool từ `brute_force.brute_pool_for_driver`, WDP bằng duyệt exhaustive thuần
Python (không CPLEX).

- **G1 (RQ2):** (a) lọc pool B3 theo \|S\|≤B == `build_route_pool` trực tiếp với B ∈ {1,2};
  (b) pool capacity 4 lọc \|S\|≤3 == pool B3; (c) Z* CPLEX == oracle cho B1/B2/B3/HEUR.
- **G2 (RQ3):** Z*, mọi Z*_{−i}, payment VCG == oracle; payout POSTED == oracle (λ ∈ {0.6,
  0.8, 1.0}); với PAB-BR, giá trị Z tại mọi điểm lưới θ̂ của mọi driver == oracle.
- **G3 (RQ4):** Z*, Z*_{−i} trên pool K* == trên pool đầy đủ.
- **X1 (sau main run RQ2):** C_B3 == `true_cost` JOINT của RQ1 trên cả 1,500 instance.

Ngưỡng: |Δ| ≤ 1e-6 (tương đối với tổng cost ~100: dùng 1e-6 tuyệt đối).

## 8. Quy tắc chống bịa kết quả (không thương lượng)
1. Hash `rq_all_locked_params.json` trước instance đầu tiên của main run.
2. Báo cáo **toàn bộ** cell/biến thể; không cherry-pick.
3. Cần sửa tham số giữa chừng → `[DEVIATION]` + chạy lại toàn bộ RQ đó từ đầu.
4. Không chỉnh λ, Θ, lưới θ̂, D_max, biến thể RQ5 sau khi xem kết quả.
5. Mọi kết luận (kể cả "không có giá trị") được ghi vào báo cáo.

## 9. Thứ tự thực thi
1. Viết code (`rq_common.py`), chạy gate §7 → PASS.
2. Pilot λ (§4.3) → khoá.
3. Ghi + hash `rq_all_locked_params.json`.
4. Chạy RQ2, RQ3+RQ4, RQ5 (song song, process riêng, threads=1 mỗi CPLEX).
5. Phân tích, kiểm X1, viết `Guideline_Total/Report_RQ_All.md` (gom RQ1–RQ5).

## 10. File
```
spec_2a_2b/src/rq_common.py          instance/pool/treatment/payment helpers dung chung RQ2-5
spec_2a_2b/src/rq_gate.py            Gate §7 G1-G3
spec_2a_2b/src/rq3_pilot_lambda.py   Pilot khoa lambda (§4.3)
spec_2a_2b/src/rq2_run.py            RQ2 main
spec_2a_2b/src/rq34_run.py           RQ3 + RQ4 main (cung instance)
spec_2a_2b/src/rq5_run.py            RQ5 main
spec_2a_2b/src/rq_analysis_all.py    Phan tich RQ2-5 + X1
spec_2a_2b/results/rq_all/           locked params, CSV, log
Guideline_Total/Report_RQ_All.md     Bao cao tong RQ1-RQ5
```
