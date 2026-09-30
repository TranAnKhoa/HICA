# Report tổng: RQ1 → RQ5

> Thực thi theo `Guideline_Total/RQ_Master.md`. RQ1 lấy từ `Report_RQ1_Complementarity.md`
> (không chạy lại). RQ2–RQ5 chạy ngày 2026-09-27, tham số khoá **trước** instance đầu tiên
> (`spec_2a_2b/results/rq_all/rq_all_locked_params.json`, SHA-256 `73f0ca62…`, kế thừa
> `rq1_locked_params.json` SHA-256 `16a84c77…`). Báo cáo toàn bộ cell, không cherry-pick.
> Bảng đầy đủ (mọi cell, IQR, CI): `spec_2a_2b/results/rq_all/rq_analysis_tables.md`.

Quy ước số: **median [IQR] · mean (95% bootstrap CI)**, bootstrap 2000 lần, resample theo
instance (paired).

---

## 0. Tóm tắt một trang

| RQ | Kết luận chính | Độ tin cậy |
|---|---|---|
| **RQ1** Cùng bid GW+OD có giá trị? | Gần 0 ở alignment ≤ 0.50; 0.9% ở 0.70; **5.9%** ở 0.90 | 7,500/7,500 OPTIMAL, gate 0/360 |
| **RQ2** Endogenous bundling có giá trị? | Gần 0 ở alignment 0.50 (median 0%); 2.5% ở 0.70; **11.3%** (B3) / **15.2%** (B4) ở 0.90. Bundle heuristic cố định chỉ lấy được ~½ giá trị đó | 7,000/7,000 OPTIMAL, gate 0/1,035, X1 khớp RQ1 1,500/1,500 |
| **RQ3** Truthful procurement tốn gì? | Ở alignment 0.90: VCG trả cao hơn first-best **14.1%** (median); posted price rẻ hơn VCG (9.1%) nhưng mất 4.0% hiệu quả; pay-as-bid best-response chỉ 5.8% — nhưng bị chặn bởi miền bid [18, 25] (xem §3.4) | 600/600 instance, mọi solve OPTIMAL |
| **RQ4** Exact payment khả thi? | Có: naive C ≤ 0.7 s median ở n=20. K* giữ **payment chính xác** (lệch ≤ 1.1e-13) và tăng tốc C **3.0×** tổng thể; nhưng **tính cả thời gian dựng K\*** cho một bid profile thì chỉ **1.06×** | 600 instance, 1,924 solve mỗi nhánh |
| **RQ5** Có bền không? | Dấu của mọi effect giữ nguyên qua 10 biến thể; **giá FD là tham số chi phối** (FD ×0.75 xoá bundling gain, ×1.25 tăng thêm 1.4 điểm %); tw/τ/θ/clustered ảnh hưởng nhỏ. Solve rate 100%, n=30 median 18.5 s/instance | 660 instance, mọi solve OPTIMAL |

**Thông điệp xuyên suốt:** mọi giá trị kinh tế (complementarity, bundling, chi phí
truthfulness) chỉ đáng kể khi crowd thật sự cạnh tranh được với FD — tức alignment cao
(0.90) hoặc FD đắt. Ở cấu hình trung tính (alignment 0.50, FD như đã calibrate), FD phục vụ
~95% order và mọi cơ chế cho kết quả gần như nhau. Đây là kết quả hợp lệ theo mọi quy tắc
`[DECISION]` đã viết trước, không phải thất bại.

---

## 1. RQ1 — Complementarity GW × OD (đã xong trước, trích dẫn)

60 cell × 25 rep = 1,500 instance × 5 treatment; gate 0/360; 7,500/7,500 OPTIMAL.

| alignment | 0.10 | 0.30 | 0.50 | 0.70 | 0.90 |
|---|---:|---:|---:|---:|---:|
| Complementarity gain (mean của median cell) | 0.01% | 0.08% | 0.00% | 0.93% | **5.86%** |

Finding phụ: OD-first→GW ≈ JOINT; GW-first→OD mất 1.3–5.3% ở alignment cao (cơ chế: OD
pool chỉ bằng 0.7–1.7% GW pool). Chi tiết: `Report_RQ1_Complementarity.md`.

---

## 2. RQ2 — Giá trị của endogenous bundling

**Thiết kế:** đúng 1,500 instance của RQ1 (cùng seed, cùng θ). Menu route: B1, B2, B3 (=
JOINT RQ1), B4 (chỉ n ≤ 15 — n=20 B=4 tốn ~100 s/instance cho Algorithm A, giới hạn đã ghi
trước khi chạy), HEUR (singleton + khối của phân hoạch heuristic cố định, bid-independent,
§3.2 spec). Mọi treatment có đủ GW+OD+FD.

**Gate:** G1a/G1b/G1c 0 fail (lọc pool B3 == sinh trực tiếp B1/B2, kể cả n ≥ 15: 0/32;
capacity 4 lọc ≤3 == B3; Z* CPLEX == oracle exhaustive cho B1/B2/B3/HEUR). **X1:** C_B3 trùng
JOINT RQ1 trên 1,500/1,500 instance, max |Δ| = 1.1e-13 — pipeline RQ2 tái lập đúng RQ1.

### 2.1 Bundling gain so với B1, `(C_B1 − C_M)/C_B1` (%)

| alignment | B2 | B3 | B4 (n≤15) | HEUR | B3 so với HEUR |
|---:|---|---|---|---|---|
| 0.10 | 0.00 [0.00, 1.11] · 0.70 | 0.57 [0.00, 2.56] · 1.55 (1.33–1.80) | 0.00 [0.00, 2.97] · 1.81 | 0.00 · 0.58 | 0.00 · 0.98 |
| 0.30 | 0.29 [0.00, 1.69] · 0.97 | 1.24 [0.00, 3.25] · 1.90 (1.66–2.15) | 1.21 [0.00, 4.23] · 2.35 | 0.00 · 0.86 | 0.04 · 1.05 |
| 0.50 | 0.00 [0.00, 0.00] · 0.16 | 0.00 [0.00, 0.00] · 0.49 (0.35–0.64) | 0.00 · 0.48 | 0.00 · 0.15 | 0.00 · 0.35 |
| 0.70 | 1.68 [0.65, 2.94] · 2.19 | 2.45 [1.24, 4.55] · 3.28 (2.95–3.61) | 2.70 [0.97, 4.88] · 3.42 | 0.51 · 1.43 | 1.43 · 1.87 |
| 0.90 | 6.37 [4.01, 8.78] · 6.64 | **11.32** [8.07, 14.54] · 11.47 (10.92–12.02) | **15.16** [10.88, 19.20] · 15.38 | 4.94 · 5.68 | 5.61 · 6.12 |

B3 so với B1 theo n (median / mean %):

| alignment | n=10 | n=15 | n=20 |
|---:|---|---|---|
| 0.10 | 0.00 / 1.23 | 0.30 / 1.31 | 1.80 / 2.12 |
| 0.30 | 0.00 / 1.22 | 1.86 / 2.27 | 1.84 / 2.20 |
| 0.50 | 0.00 / 0.27 | 0.00 / 0.34 | 0.00 / 0.85 |
| 0.70 | 1.84 / 2.47 | 2.12 / 2.95 | 3.49 / 4.41 |
| 0.90 | 9.94 / 10.68 | 11.09 / 11.78 | 11.79 / 11.95 |

### 2.2 Price of range B: `(C_B3 − C_B4)/C_B4` (%)

Gần 0 ở alignment ≤ 0.70 (median 0.00–0.47%, mean ≤ 0.93%); **4.0% (n=10) và 5.7%
(n=15)** ở alignment 0.90.

### 2.3 Vận hành

| menu | FD rate | order/route thắng | pool (mean) | t_A (s) | t_B (s) |
|---|---:|---:|---:|---:|---:|
| B1 | 0.897 | 1.00 | 45 | lọc từ B3 | 0.005 |
| B2 | 0.802 | 1.55 | 442 | lọc từ B3 | 0.020 |
| B3 | 0.731 | 2.03 | 2,829 | 1.76 | 0.071 |
| B4 (n≤15) | 0.679 | 2.37 | 5,313 | 12.46 | 0.129 |
| HEUR | 0.805 | 1.55 | 67 | lọc từ B3 | 0.007 |

t_A theo n: B3 0.35 / 1.32 / 3.60 s (n = 10/15/20); B4 3.09 / 21.82 s (n = 10/15). HEUR tạo
trung bình 4.2 khối ≥2 order/instance (0–9).

### 2.4 Đọc theo `[DECISION]` đã viết trước
- Gain B3 vs B1 ≥ ~2% chỉ ở alignment ≥ 0.70 (và 0.30 ở n ≥ 15); < 1% median ở 0.10 và 0.50
  → bundling có giá trị **có điều kiện**, cùng điều kiện với RQ1.
- **B3 ≠ HEUR**: ở alignment 0.90, để thị trường tự chọn bundle thắng bundle heuristic cố
  định 5.6% (median) — HEUR chỉ lấy được ~44% giá trị bundling của B3. Giá trị nằm ở
  **endogenous** bundling, không chỉ ở việc cho phép bundle.
- Price of range B không nhỏ ở alignment 0.90 (4–6%) → B=3 **chưa đủ** ở chế độ cạnh tranh
  cao; nhưng chi phí Algorithm A của B4 tăng ~16× ở n=15. Đây là đánh đổi cần nêu trong
  thesis, không phải lý do đổi B của RQ khác.

---

## 3. RQ3 — Chi phí của truthful procurement

**Thiết kế:** 600 instance (alignment {0.50, 0.90} × n {10,15,20} × 4 supply × 25 rep,
trùng RQ1), B=3. Bốn cơ chế: ORACLE (trả true cost, cận dưới), VCG (exact, naive C), PAB-BR
(pay-as-bid, mỗi driver best-response đơn phương trên lưới bid bước 0.5 trong Θ=[18,25],
rồi áp đồng thời), POSTED (giá π_o = λ·q_o, **λ = 0.80** khoá bằng pilot 120 instance riêng —
λ tối ưu cho posted price, tức baseline mạnh nhất có thể).

**Gate G2:** VCG (Z*, mọi Z*_{−i}, payment) 0/120; POSTED 0/72; PAB-BR (Z tại mọi điểm lưới)
0/315 — đều khớp oracle exhaustive.

### 3.1 Payout premium so với first-best `(Payout − Z*)/Z*` (%)

| alignment | n | VCG | PAB-BR | POSTED |
|---:|---:|---|---|---|
| 0.50 | all | 0.00 [0.00, 0.47] · 0.52 (0.39–0.66) | 0.00 [0.00, 0.27] · 0.30 (0.22–0.38) | 0.00 [0.00, 0.49] · 0.55 (0.42–0.70) |
| 0.90 | 10 | 13.58 [10.10, 17.47] · 14.01 | 5.26 [3.58, 7.99] · 5.90 | 10.38 [7.27, 15.02] · 11.00 |
| 0.90 | 15 | 14.11 [10.74, 18.67] · 15.54 | 6.31 [4.64, 8.34] · 6.37 | 8.62 [6.39, 12.30] · 9.81 |
| 0.90 | 20 | 14.98 [11.37, 19.31] · 15.62 | 5.84 [4.30, 7.47] · 6.06 | 8.78 [6.51, 12.03] · 9.17 |
| 0.90 | **all** | **14.13** [10.76, 18.60] · 15.05 (14.30–15.79) | **5.78** [4.23, 7.84] · 6.11 (5.81–6.43) | **9.12** [6.59, 12.98] · 9.99 (9.48–10.53) |

### 3.2 Information rent và hiệu quả phân bổ

| alignment | VCG overhead rent/Σc_i (%) | PAB rent/Σc_i (%) | PAB efficiency loss (%) | POSTED efficiency loss (%) | FD rate VCG / PAB / POSTED |
|---:|---|---|---|---|---|
| 0.50 | 8.45 [2.96, 17.34] · 17.68 | 5.35 [1.76, 10.19] · 6.86 | 0.00 · 0.00 | 0.00 · 0.37 | 0.949 / 0.949 / 0.985 |
| 0.90 | **24.73** [17.91, 32.37] · 26.29 | 9.65 [7.20, 12.68] · 10.01 | 0.00 [0.00, 0.09] · 0.31 | **3.99** [2.05, 6.15] · 4.46 | 0.374 / 0.382 / 0.540 |

- Alignment 0.90: số winner mean 4.01; rent VCG chia GW/OD = 44% / 56%; VCG payout > PAB-BR
  ở 300/300 instance; VCG payout < POSTED chỉ ở 35/300.
- Alignment 0.50: số winner mean 0.41 (FD phục vụ ~95% order) → mọi cơ chế gần như trùng
  nhau; overhead % dao động mạnh vì mẫu số Σc_i rất nhỏ.

### 3.3 Đọc kết quả
- **Giá của truthfulness** (VCG so với first-best) ≈ **14% payout** ở chế độ cạnh tranh
  (alignment 0.90), ≈ 0 ở chế độ trung tính. Rent ≈ 25% chi phí thật của winner.
- **Posted price** trả ít hơn VCG ~5 điểm % nhưng mất **4.0% hiệu quả** (median) và đẩy FD
  rate từ 37% lên 54% — đánh đổi payout lấy hiệu quả phân bổ.
- **Pay-as-bid** trả ít nhất và gần như không mất hiệu quả trong mô hình này — xem giới hạn
  §3.4 trước khi dùng số này.

### 3.4 Giới hạn quan trọng (bắt buộc nêu khi trích dẫn PAB-BR)
1. Bid bị chặn trong Θ = [18, 25] (miền bid của cơ chế, dùng cho định lý K*). Markup tối đa
   của driver là 25 − θ_i, trung bình chỉ 2.54 USD/h ở alignment 0.90. VCG payment **không**
   bị chặn như vậy. So sánh VCG vs PAB-BR vì thế thiên về PAB-BR.
2. PAB-BR là best response **đơn phương** (các driver khác bid thật) áp đồng thời, **không**
   phải cân bằng Nash. Nó là benchmark chỉ báo, không phải dự đoán hành vi.
3. Vì hai lý do trên, câu đúng để viết là: "trong miền bid bị chặn, pay-as-bid chiến lược
   đơn giản trả ít hơn VCG; lợi thế của VCG là DSIC (không cần driver tính chiến lược),
   không phải payout thấp hơn". Không viết "VCG đắt hơn pay-as-bid" như một kết luận chung.

---

## 4. RQ4 — Tính khả thi của exact payment

**Thiết kế:** trên chính 600 instance RQ3. Naive C: full solve + một removal-solve cho mỗi
winner, pool đầy đủ. Accelerated C: K* cắt pool một lần/instance (bid-independent), rồi cùng
các solve đó. Thứ tự đo luân phiên theo parity rep; 3 process song song trên máy 12 luồng
(không chạy gì khác cùng lúc). T5 decomposition không đo lại (đã đóng: component gộp ≥ 0.889
driver ở scale chính).

**Equality error: max |Z*_naive − Z*_accel| = max |p_naive − p_accel| = 1.1e-13** trên 600
instance (1,924 solve mỗi nhánh; 408 instance có ≥1 winner). Gate G3 trước đó 0/360. K*
không làm sai bất kỳ payment nào.

| alignment | n | K* cắt pool (median %) | t_C naive (s) | t_C accel (s) | speed-up C, median [IQR] | speed-up tính cả K* build | t_A (s) |
|---:|---:|---:|---:|---:|---|---:|---:|
| 0.50 | 10 | 100.0 | 0.039 | 0.003 | 11.20× [10.11, 13.14] | 1.13× | 0.26 |
| 0.50 | 15 | 100.0 | 0.086 | 0.005 | 17.98× [14.62, 22.05] | 0.63× | 1.00 |
| 0.50 | 20 | 100.0 | 0.186 | 0.006 | 30.40× [21.92, 41.85] | 0.60× | 2.56 |
| 0.90 | 10 | 75.2 | 0.134 | 0.060 | 2.34× [1.69, 3.04] | 1.44× | 0.65 |
| 0.90 | 15 | 76.6 | 0.248 | 0.144 | 1.81× [1.56, 2.57] | 1.05× | 2.20 |
| 0.90 | 20 | 77.2 | 0.655 | 0.259 | 2.72× [2.11, 3.37] | 1.24× | 7.40 |

Tổng 600 instance: t_C naive 148.2 s, accelerated 49.2 s (**3.01×**); cộng K* build 90.6 s
→ **1.06×**.

### Đọc kết quả
- **Exact payment khả thi ngay với naive C**: median ≤ 0.66 s ở n=20, luôn nhỏ hơn Algorithm
  A (7.4 s). Bottleneck của pipeline là A, không phải C.
- K* cắt 75–100% pool và tăng tốc phần B+C 2–30×, **chính xác tuyệt đối**. Nhưng K* hiện
  viết bằng pure Python, và khi cơ chế chỉ chạy **một** bid profile/instance (đúng thực tế
  của một phiên đấu giá), thời gian dựng K* ăn gần hết lợi ích (1.06× tổng; < 1× ở alignment
  0.50 vì C vốn đã rẻ). Con số **3.03×** trong `Final_t4_Speedup_RESULTS.md` là trên 20 bid
  profile, tức thời gian dựng được chia cho 20 — đúng về số đo, nhưng không phải tình huống
  một phiên. Khi trích dẫn cần nói rõ đang chia thời gian dựng cho bao nhiêu profile.
- Giá trị thật của K* vì thế là **lý thuyết + nén pool** (75–100%) và tăng tốc khi cùng
  pool được giải nhiều lần (nhiều bid profile, phân tích độ nhạy, removal-solve lặp). Nếu
  muốn speed-up một phiên, cần viết lại K* build (ví dụ vector hoá), không cần đổi thuật toán.

---

## 5. RQ5 — Độ bền (one-at-a-time)

**Thiết kế:** baseline n=15, alignment 0.50, 4 supply × 15 rep = 60 instance/biến thể; seed
không chứa tham số biến thể → V0–V8 paired theo hình học đầu vào. V9/V10 (n = 25/30) dùng
supply {(3,3),(4,3),(3,4),(4,4)}.

| biến thể | complementarity % | bundling B3 vs B1 % | VCG overhead % | FD rate | solve OPTIMAL | ≤300 s | t median (s) |
|---|---|---|---|---:|---:|---:|---:|
| V0 baseline | 0.00 · 0.03 | 0.00 · 0.38 | 9.02 · 20.31 | 0.948 | 267/267 | 60/60 | 1.34 |
| V1 tw=60 | 0.00 · −0.00 | 0.00 · 0.29 | 6.37 · 18.95 | 0.953 | 263/263 | 60/60 | 0.73 |
| V2 tw=240 | 0.00 · 0.13 | 0.00 · 0.71 | 5.58 · 16.95 | 0.919 | 277/277 | 60/60 | 2.63 |
| V3 τ=20 | 0.00 · −0.00 | 0.00 · 0.39 | 4.26 · 11.54 | 0.957 | 259/259 | 60/60 | 1.17 |
| V4 τ=45 | 0.00 · 0.03 | 0.00 · 0.37 | 9.24 · 20.66 | 0.947 | 268/268 | 60/60 | 1.20 |
| V5 FD ×0.75 | 0.00 · −0.00 | 0.00 · 0.00 | 21.74 · 27.54 | 0.992 | 247/247 | 60/60 | 1.16 |
| V6 FD ×1.25 | 0.00 · 0.17 | 0.52 · 1.76 | 9.95 · 17.11 | 0.872 | 292/292 | 60/60 | 1.27 |
| V7 clustered | 0.00 · 0.02 | 0.00 · 0.66 | 2.82 · 11.65 | 0.938 | 264/264 | 60/60 | 1.24 |
| V8 θ~U[15,30] | 0.00 · 0.10 | 0.00 · 0.68 | 8.05 · 16.28 | 0.926 | 274/274 | 60/60 | 1.19 |
| V9 n=25 | 0.00 · 0.07 | 0.04 · 1.05 | 6.84 · 11.89 | 0.919 | 293/293 | 60/60 | 9.95 |
| V10 n=30 | 0.00 · 0.02 | 0.00 · 0.57 | 7.57 · 14.66 | 0.949 | 286/286 | 60/60 | 18.48 |

(ô = median · mean, %)

Paired difference so với baseline (điểm %, mean (CI95)):

| biến thể | Δ complementarity | Δ bundling gain | Δ VCG overhead |
|---|---|---|---|
| V1 tw=60 | −0.03 (−0.09–−0.00) | −0.09 (−0.17–−0.04) | −3.82 (−5.90–−1.92) |
| V2 tw=240 | 0.09 (−0.00–0.22) | 0.33 (0.18–0.51) | 1.12 (−4.38–5.11) |
| V3 τ=20 | −0.03 (−0.09–0.00) | 0.01 (−0.00–0.02) | −0.72 (−2.16–0.00) |
| V4 τ=45 | 0.00 (−0.00–0.00) | −0.01 (−0.02–0.00) | −0.12 (−0.78–0.42) |
| V5 FD ×0.75 | −0.03 (−0.09–0.00) | −0.38 (−0.64–−0.17) | −28.64 (−43.31–−4.28) |
| V6 FD ×1.25 | 0.14 (0.00–0.31) | **1.38 (0.97–1.81)** | 2.47 (−5.56–10.21) |
| V7 clustered | −0.01 (−0.09–0.06) | 0.28 (−0.18–0.77) | −11.79 (−31.81–7.94) |
| V8 θ~U[15,30] | 0.07 (−0.00–0.18) | 0.30 (0.14–0.47) | −0.79 (−6.39–3.76) |

### Đọc kết quả
- **Không biến thể nào đảo dấu** effect của RQ1/RQ2 (complementarity và bundling gain ≥ 0
  ở mọi biến thể, đúng lý thuyết vì menu lồng nhau) → kết luận "gần 0 ở cấu hình trung
  tính" là **bền**.
- **Giá FD là tham số chi phối**: FD ×0.75 → crowd gần như không bao giờ thắng (FD rate
  99.2%), mọi gain về 0; FD ×1.25 → bundling gain tăng rõ nhất trong mọi biến thể. Kết hợp
  với RQ1/RQ2 (alignment), cả hai chỉ ra cùng một cơ chế: giá trị chỉ xuất hiện khi crowd
  cạnh tranh được với FD. Nên nêu trong thesis rằng calibration q_o (khoá theo FD rate
  10–50% trên pilot n=12) là một lựa chọn thiết kế có ảnh hưởng lớn.
- VCG overhead (%) có phương sai rất lớn ở mọi biến thể alignment 0.50 (mẫu số Σc_i nhỏ, 0–1
  winner) — không nên trích dẫn overhead % ở chế độ này; dùng §3 alignment 0.90.
- **Scalability**: solve rate 100% (OPTIMAL, gap 0) ở mọi biến thể; n=30 với 8 driver hoàn
  tất A+B+C trong median 18.5 s, 60/60 dưới 300 s.

---

## 6. Hệ quả cho thesis

1. **Framing:** cả ba câu hỏi kinh tế (RQ1, RQ2, RQ3) cho cùng một hình mẫu — effect lớn
   khi crowd cạnh tranh được với FD (alignment 0.90 / FD đắt), gần 0 ở cấu hình trung tính.
   Nên viết như **một** finding thống nhất có điều kiện, không phải 3 kết quả rời. Nhất quán
   với `[DECISION]` RQ1: trọng tâm C&OR (T4/T5), phần kinh tế là bổ trợ có giới hạn rõ ràng.
2. **RQ2 cho kết quả mạnh nhất phía kinh tế**: 11–15% ở alignment 0.90, và endogenous >
   heuristic cố định ~5.6% — đây là lập luận trực tiếp cho thiết kế "platform-generated
   bundle + để driver bid".
3. **RQ3**: báo "giá của truthfulness ≈ 14% payout ở chế độ cạnh tranh" kèm giới hạn §3.4.
4. **RQ4**: exact payment rẻ (bottleneck là Algorithm A). K* chính xác tuyệt đối; speed-up
   phải trích dẫn kèm số profile dùng chia thời gian dựng (1.06× cho một phiên, 3.0× chỉ
   tính phần C).

## 7. Việc còn mở (không làm trong lần chạy này)
- RQ3 PAB với miền bid mở rộng / cân bằng lặp (best-response dynamics) — nếu muốn so VCG vs
  pay-as-bid công bằng hơn.
- K* build vector hoá (để speed-up một phiên thành hiện thực).
- RQ2 B4 ở n=20 (cần Layer 3 / `dp_fast` tích hợp vào production để giảm ~100 s/instance).

---

## File & tái tạo

```
Guideline_Total/RQ_Master.md                 Spec tong RQ1-RQ5 (khoa truoc khi chay)
spec_2a_2b/src/rq_common.py                  Instance/pool/solver/VCG/posted/PAB-BR
spec_2a_2b/src/rq_gate.py                    Gate G1-G3: PASS 0/1035
spec_2a_2b/src/rq3_pilot_lambda.py           Pilot khoa lambda=0.80 (+ G1a n>=15: 0/32)
spec_2a_2b/src/rq_runner.py                  Runner RQ2 / RQ3+RQ4 / RQ5 (shard + resume)
spec_2a_2b/src/rq_analysis_all.py            Phan tich + X1
spec_2a_2b/results/rq_all/rq_all_locked_params.json   Tham so khoa, SHA-256 73f0ca62...
spec_2a_2b/results/rq_all/rq3_pilot_lambda.json       Ket qua pilot lambda
spec_2a_2b/results/rq_all/rq2_shard*.csv     7,000 dong
spec_2a_2b/results/rq_all/rq34_shard*.csv    600 dong
spec_2a_2b/results/rq_all/rq5_shard*.csv     660 dong
spec_2a_2b/results/rq_all/rq_analysis_tables.md       Toan bo bang
```

Chạy lại (Python 3.7.7 + CPLEX 12.10, từ `spec_2a_2b/src`):
```
python rq_gate.py
python rq3_pilot_lambda.py
python rq_runner.py rq2 <k> 7     (k = 0..6)   ~37 phut/shard
python rq_runner.py rq5 <k> 2     (k = 0..1)   ~20 phut/shard
python rq_runner.py rq34 <k> 3    (k = 0..2)   ~16 phut/shard
python rq_analysis_all.py
```
