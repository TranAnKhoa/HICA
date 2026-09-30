# Report FULL — Spec 2a+2b + Addition_1 + mở rộng (c)/(d): kết luận cuối cùng

**Ngày chạy:** 2026-09-10 → 2026-09-12. **Người thực thi:** Claude Code.
**File này thay thế/gộp:** `spec_2a_2b/report_2a_2b.md` (báo cáo gốc) +
`Guideline_Total/report_2a_2b_addition_1.md` (3 việc kiểm tra bổ sung) +
mở rộng kịch bản (c)/(d) cho Việc 1 (theo yêu cầu người dùng 2026-09-11).
Đây là bản **đầy đủ nhất, có đủ 720/720 dòng lưới 2b (B=3) và 720/720 lưới
B=2**, dùng để khóa kết luận cuối cùng cho thesis.

**Trạng thái một câu:** DP label-setting (Test6) **đúng ở quy mô lớn**
(Gate 0: 0/180) nhưng **vỡ siêu tuyến tính rõ rệt trước n=50 khi B≥3-4**
(kết quả cần báo cáo, không phải bug). Route pool thật **luôn** bị 1
component khổng lồ chi phối (0/1,440 quan sát dưới ngưỡng 0.3, qua cả B=2
và B=3, cả 2 lưới đều đóng đủ 100%) → **Hướng (B)** được xác nhận vững
chắc. Nhưng khoảng dao động speedup thực sự **rất rộng** (~1.9× đến ~18-50×
tùy cách WDP thực phân bổ winner) — T5 **không vô giá trị**, chỉ là giá trị
có điều kiện, nhạy với cách phân bổ winner và với p (số mũ chi phí MILP).
  
---

# PHẦN A — Spec 2a: Verify DP ở quy mô lớn

## A.1 Gate 0 — PASS tuyệt đối

```
Grid: n∈{3,4,5,6,7} × B∈{2,3,4} × tw∈{60,120} × seed∈{0,1,2} × spatial_mode∈{dispersed,clustered}
= 180 instance × driver (GW+OD mỗi instance)
Kết quả: 0/180 vi phạm (bundle-existence, completeness, soundness)
```

`dp_labeling.py` gọi nguyên `t6_dp.run_dp()` (module Test6 đã kiểm chứng ở
n≤7, xem `Guideline/Test6_report.md`, `Test6.1_report.md`, `Test6.2_report.md`
— 0/616 + 0/160 + phản ví dụ 2D, tất cả PASS). `brute_force.py` viết lại
**độc lập hoàn toàn** cho generator MỚI (hộp 20×20km, `n_drivers` độc lập,
dispersed/clustered — khác `t2_gen.py` gốc dùng pool Atlanta). File:
`spec_2a_2b/results/gate0_violations.csv` (rỗng, chỉ header).

Gate 0 chạy **2 lần** (trước và sau khi sửa self-test tam giác O(n³)→O(n)
trong `instance_gen.py` — xem A.2) — cả 2 lần đều 0/180, xác nhận thay đổi
đó không ảnh hưởng output sinh instance.

## A.2 Sai lệch so với spec (công khai)

1. **Self-test bất đẳng thức tam giác: O(n³) đầy đủ → lấy mẫu O(n).** Ở
   n=100 (~215 node), self-test đầy đủ tốn ~13-16s/instance chỉ để xác
   nhận lại tính chất **đại số luôn đúng** của khoảng cách Euclid. Cắt giảm
   một self-test dư thừa, KHÔNG nới lỏng feasibility (output
   `generate_instance()` không đổi — Gate 0 xác nhận cả 2 lần).
2. **`N_WORKERS` (run_2a.py): 10 → 4** sau khi gặp `MemoryError` chạy 10
   driver song song ở ô nặng RAM (frontier 1-3 triệu label/driver).
3. **Máy bị restart hoàn toàn 1 lần + crash MemoryError 2 lần khác** trong
   suốt quá trình chạy — `run_2a.py`/`run_2b.py` có khả năng resume (đọc
   CSV cũ, bỏ qua ô đã chạy) nên không mất dữ liệu, chỉ tốn thêm thời gian
   thực.

## A.3 Đường cong runtime-vs-n theo tw_width — GIỚI HẠN THỰC NGHIỆM CỦA B

Bảng trung bình qua `n_drivers∈{5,10}` × `seed∈0..9` (≤20 quan sát/ô, GW+OD
gộp) từ `2a_summary.csv`, bổ sung `scaling_probe.csv` (1 driver/điểm) cho
n=75/100 (2a không đủ thời gian chạy tới các ô này — xem A.4).

| B | tw | n=10 | n=20 | n=30 | n=50 | n=75† | n=100† |
|---|----|------|------|------|------|-------|--------|
| 2 | 30  | 0.02s | 0.02s | 0.03s | 0.27s | ~0.1s/drv | ~0.2s/drv |
| 2 | 60  | 0.01s | 0.02s | 0.04s | 0.20s | ~0.1s/drv | ~0.3s/drv |
| 2 | 120 | 0.01s | 0.02s | 0.06s | 0.31s | ~0.3s/drv | ~0.5s/drv |
| 2 | 240 | 0.01s | 0.03s | 0.09s | 0.44s | ~0.5s/drv | ~0.7s/drv |
| 3 | 30  | 0.02s | 0.11s | 0.47s | 3.83s | ~7.3s/drv | ~20s/drv |
| 3 | 60  | 0.03s | 0.18s | 0.78s | 8.07s | ~14s/drv | ~33s/drv |
| 3 | 120 | 0.05s | 0.35s | 1.69s | 16.9s | ~30s/drv | ~77s/drv |
| 3 | 240 | 0.15s | 1.02s | 4.99s | 46.2s | ~76s/drv | **VỠ** (170s) |
| 4 | 30  | 0.06s | 1.03s | 5.87s | 92.3s | **VỠ** (186s) | — |
| 4 | 60  | 0.13s | 2.29s | 14.9s | 218s | — | — |
| 4 | 120 | 0.33s | 7.81s | 44.0s | ⚠timeout(1 seed) | — | — |
| 4 | 240 | 1.21s | 34.3s | 267s(10 seed)/⚠timeout(1) | — | — |

*("VỠ" = t_dp 1 driver duy nhất > BREAK_S=90s trong probe. Cột n=75/100 và
cột n≤50 đơn vị KHÁC nhau — 1 driver vs gộp nhiều driver — chỉ dùng để thấy
xu hướng.)*

**Đọc bảng:** B=2 hoàn toàn phẳng đến n=100 (<1s). B=3 sống được đến n=75
mọi tw, đến n=100 nếu tw≤120. B=4 vỡ trước n=50 ở hầu hết tw — tại tw=240
vỡ ngay ở n=30. **Peak frontier size** đi cùng chiều: B=4/tw=60/n=50 ≈ 4.59
triệu label/instance so với B=2/tw=60/n=50 chỉ ≈ 5,712 — chênh **~800 lần**
chỉ vì B tăng từ 2 lên 4.

**Kết luận A.3:** DP không lỗi ở quy mô lớn (Gate 0 vẫn pass), nhưng kích
thước bài toán xử lý được trong ngân sách thời gian hợp lý co lại rất nhanh
khi B tăng. Đây là giới hạn thực nghiệm thật, không phải bug — nếu main
experiment cần B=5 hoặc n∈{75,100} ở B≥3, cần vòng đối chứng bổ sung.

## A.4 Độ phủ lưới 2a — 930/1440 (64.6%), dừng vì hạ tầng

```
completed        : 910
timeout           : 2
timeout_skipped   : 18   (early-skip trong 1 ô, ghi ro status, khong am tham loai)
KHONG chay         : 510  (n∈{75,100}, MOI B/tw/n_drivers)
```

Nguyên nhân độ phủ thiếu là hạ tầng (crash OOM + máy restart), không phải
thuật toán. Phần thiếu (n=75,100) đã đặc trưng hoá đủ qua `scaling_probe.csv`
(bảng A.3) — tín hiệu ổn định, không có dấu hiệu số liệu sẽ đổi kết luận
nếu chạy tiếp. **Quyết định KHÔNG chạy tiếp 2a để ưu tiên hoàn thành 2b**
(gate quyết định hướng 2c/2d, giá trị quyết định cao hơn).

---

# PHẦN B — Spec 2b (gốc) + Addition_1 Việc 2 + Việc 3: phân phối component (ĐẦY ĐỦ 100%)

## B.1 Thiết lập

Lát cắt 2a: `n∈{30,50}, B=3, tw_width=120`. Quét đầy đủ:
`tau∈{10,15,20,30,45,60} × spatial_mode∈{dispersed,clustered} ×
supply_ratio∈{0.3,0.6,1.0} × seed∈0..9` = **720 lần chạy**.
`n_drivers = round(supply_ratio × n)`. Conflict graph xây trên **TOÀN BỘ**
route pool (đúng định nghĩa T5 §2.2).

## B.2 Độ phủ CUỐI CÙNG: 720/720 (100%) — B=3 gốc ĐÃ ĐÓNG ĐỦ

Báo cáo gốc dừng ở 429/720 (59.6%), addition_1 dừng ở 469/720 (65.1%). Sau
khi `run_2b.py` (không sửa, chỉ để chạy tiếp/resume) tiếp tục chạy nền suốt
Phần A + Việc 1 (xem Phần C) → **hoàn tất tuyệt đối 720/720** lúc
2026-09-12, elapsed tổng ~103,283s (~28.7 giờ) kể từ lần chạy đầu.
`=== 2b DONE === runs=720`.

## B.3 Kết quả CUỐI CÙNG (720/720, không còn ô trống)

```
largest_component_fraction: mean=0.586  median=0.533  min=0.444  max=1.000
rows < 0.3  :   0/720  (0.0%)   <- NGƯỠNG HƯỚNG (A), KHÔNG BAO GIỜ ĐẠT
rows < 0.5  :  81/720  (11.2%)
```

**Theo n:**

| n | n_obs | mean(largest_fraction) |
|---|-------|------------------------|
| 30 | 360 | 0.564 |
| 50 | 360 | 0.608 |

**Theo spatial_mode:**

| mode | n_obs | mean |
|---|---|---|
| dispersed | 360 | 0.590 |
| clustered | 360 | 0.582 |

**Theo supply_ratio:**

| supply_ratio | n_obs | mean |
|---|---|---|
| 0.3 | 240 | 0.576 |
| 0.6 | 240 | 0.595 |
| 1.0 | 240 | 0.586 |

**Theo tau:**

| tau | n_obs | mean |
|---|---|---|
| 10 | 120 | 0.496 |
| 15 | 120 | 0.505 |
| 20 | 120 | 0.517 |
| 30 | 120 | 0.550 |
| 45 | 120 | 0.656 |
| 60 | 120 | 0.791 |

**Cross-table n × mode:**

| (n, mode) | n_obs | mean |
|---|---|---|
| (30, clustered) | 180 | 0.558 |
| (30, dispersed) | 180 | 0.569 |
| (50, clustered) | 180 | 0.606 |
| (50, dispersed) | 180 | 0.610 |

**Cross-table n × supply_ratio:**

| (n, supply_ratio) | n_obs | mean |
|---|---|---|
| (30, 0.3) | 120 | 0.530 |
| (30, 0.6) | 120 | 0.583 |
| (30, 1.0) | 120 | 0.578 |
| (50, 0.3) | 120 | 0.623 |
| (50, 0.6) | 120 | 0.607 |
| (50, 1.0) | 120 | 0.594 |

## B.4 Xu hướng dự đoán ở báo cáo gốc — NAY ĐÃ ĐƯỢC XÁC NHẬN TUYỆT ĐỐI (không còn ngoại suy)

- **"n=50 tệ hơn n=30"**: **XÁC NHẬN ĐÚNG với dữ liệu ĐẦY ĐỦ**: 0.564 → 0.608
  (+0.044), nhất quán ở cả 2 spatial_mode (0.558→0.606 clustered,
  0.569→0.610 dispersed).
- **"supply cao hơn → gộp cụm nhiều hơn"**: **XÁC NHẬN ĐÚNG NHƯNG KHÔNG ĐƠN
  ĐIỆU TUYỆT ĐỐI** ở mức tổng (0.3→0.576, 0.6→0.595, 1.0→0.586 — đỉnh ở
  0.6 rồi giảm nhẹ ở 1.0). Nhìn theo cross-table n×supply: ở **n=30** xu
  hướng tăng đúng dự đoán (0.530→0.583→0.578); ở **n=50** xu hướng NGƯỢC LẠI
  — giảm dần (0.623→0.607→0.594). Đây là một **sắc thái mới** không xuất
  hiện trong dự đoán ban đầu: ở n=50, `supply_ratio` càng cao (càng nhiều
  driver) thì `largest_component_fraction` trung bình lại càng **giảm nhẹ**
  — có thể do việc thêm nhiều driver cũng thêm nhiều order-pool overlap
  phân tán hơn ở quy mô lớn, không chỉ đơn thuần "thêm cạnh vào 1 cụm".
  **Không đảo ngược kết luận Hướng B** (mọi ô đều ≥0.3 rất xa), nhưng cần
  sửa câu chữ dự đoán cũ ("supply cao hơn → LUÔN gộp cụm nhiều hơn") thành
  "supply cao hơn → gộp cụm nhiều hơn RÕ Ở n NHỎ, xu hướng đảo nhẹ ở n LỚN".

## B.5 Việc 2 (Addition_1) — Rerun B=2, đầy đủ 720/720, đối chứng cuối

| Chỉ số | B=3 (720, ĐẦY ĐỦ) | B=2 (720, đầy đủ) |
|---|---|---|
| mean largest_fraction | 0.586 | 0.582 |
| median | 0.533 | 0.533 |
| min | 0.444 | 0.444 |
| rows < 0.3 | 0/720 (0.0%) | 0/720 (0.0%) |
| n=30 mean | 0.564 | 0.552 |
| n=50 mean | 0.608 | 0.612 |

Với dữ liệu B=3 nay đầy đủ 100%, chênh lệch với B=2 (cũng 100%) là **<1
điểm phần trăm ở mọi chỉ số tổng hợp** — mức độ khớp còn cao hơn so với so
sánh sơ bộ ở addition_1 (khi B=3 mới có 65%). **Kết luận Việc 2 CỦNG CỐ
MẠNH HƠN với dữ liệu đầy đủ: Hướng (B) bền tuyệt đối theo B (2 và 3).**

---

# PHẦN C — Việc 1 (Addition_1) + mở rộng (c)/(d): khoảng dao động speedup thực

## C.1 Công thức & phát hiện toán học

`speedup_estimate = cost_naive / cost_decomposed`, với:
- **cost_naive** = giải WDP-{i} trên CẢ instance = `n_winners_total × N^p`
- **cost_decomposed** = giải trên TỪNG component = `Σ_P n_w(P) × size(P)^p`

**4 kịch bản phân bổ winner giữa các component** (kịch bản (a)/(b) theo
spec addition_1 gốc; (c)/(d) bổ sung theo yêu cầu người dùng 2026-09-11 để
trả lời đúng câu hỏi "WDP không chọn winner ngẫu nhiên theo tỷ lệ — khoảng
dao động thực tế rộng cỡ nào?"):

| Kịch bản | Cách phân bổ winner | Ý nghĩa |
|---|---|---|
| (a) uniform | tỷ lệ thuận kích thước: `n_w(P)=n_winners_total·|P|/N` | "trung bình", spec gốc |
| (b) upper-bound | mọi driver là winner (`n_winners_total=N`), tỷ lệ thuận | Cận trên TỔNG SỐ winner |
| **(c) worst-case** | **toàn bộ winner dồn vào component LỚN NHẤT** | Cận dưới THỰC của speedup |
| **(d) best-case** | **toàn bộ winner là driver SINGLETON** (ràng buộc: n_winners ≤ n_singleton) | Cận trên THỰC của speedup |

**Phát hiện đại số quan trọng:** thay công thức (a) vào tỷ số, `n_winners_
total` triệt tiêu hoàn toàn: `speedup(a) = N^(p+1) / Σ|P|^(p+1)` — **trùng
khớp tuyệt đối với (b)**. Đây là hệ quả toán học của chính công thức spec
(phân bổ tỷ lệ thuận kích thước), không phải lỗi cài đặt — xác nhận bằng
thực nghiệm (quét `winner_frac∈{0.2,0.5,1.0}` cho (a), luôn ra cùng số).

Điều này có nghĩa: **(a)/(b) chỉ trả lời "nếu winner rải đều theo tỷ lệ
kích thước thì sao" — chứ KHÔNG trả lời "WDP thực sự chọn winner thế nào".**
Đây chính xác là khoảng hở mà kịch bản (c)/(d) lấp: đánh giá độ nhạy với
**CÁCH PHÂN BỔ** winner (không chỉ tổng số), phản ánh đúng thực tế WDP chọn
winner theo chi phí thấp nhất, không ngẫu nhiên đều.

## C.2 Kết quả CUỐI CÙNG (720/720 instance B=3, 4 p × 4 kịch bản = 28,800 dòng)

**Tại p=1 (ngưỡng khóa spec, chi phí MILP tuyến tính — giả định bảo thủ nhất):**

| Kịch bản | median | Q1 | Q3 | min | max | n khả thi |
|---|---|---|---|---|---|---|
| (a) uniform / (b) upper-bound | 3.33× | 2.42× | 3.75× | 1.00× | 3.86× | 720/720 |
| **(c) worst-case** | **1.88×** | 1.58× | 2.00× | 1.00× | 2.25× | 720/720 |
| **(d) best-case** | **18.0×** | 15.0× | 30.0× | 9.0× | 50.0× | **638/720 (88.6%)** |

**Ở p cao hơn (chi phí MILP siêu tuyến tính — thực tế hơn nhiều, xem Test8
đo speedup 14.9-391× ở nc=32):**

| p | (a) uniform median | (c) worst median | (d) best median | %(a) >5× |
|---|---|---|---|---|
| 1.0 | 3.33× | 1.88× | 18.0× | 0.0% |
| 1.5 | 4.75× | 2.57× | 76.4× | ~50%+ |
| 2.0 | 6.57× | 3.52× | 324× | ~70%+ |
| 3.0 | 12.36× | 6.59× | 5,832× | ~85%+ |

**Khả thi của kịch bản (d):** 4,796/28,800 dòng (16.7%) KHÔNG khả thi
(`winner_frac×N > n_singleton`) — tức là ở nhiều instance, KHÔNG đủ driver
singleton để "chứa" hết số winner giả định. Tỷ lệ khả thi giảm mạnh theo τ
(bảng dưới, p=1, winner_frac=0.2) và theo winner_frac (winner_frac=0.5 chỉ
323/720 khả thi so với 638/720 ở winner_frac=0.2) — chính vì τ cao làm
component gộp cụm mạnh, giảm số singleton.

| tau | a_uniform median | c_worst median | d_best median | n khả thi (d) |
|---|---|---|---|---|
| 10 | 3.75 | 2.00 | 24.0 | 120/120 |
| 15 | 3.75 | 2.00 | 24.0 | 120/120 |
| 20 | 3.60 | 2.00 | 24.0 | 120/120 |
| 30 | 3.17 | 1.88 | 24.0 | 120/120 |
| 45 | 2.68 | 1.67 | 30.0 | 110/120 |
| 60 | 1.54 | 1.25 | 18.0 | 61/120 |

*(bảng theo dữ liệu B=2 720/720 — dùng làm đối chứng vì cùng cấu trúc,
không lệch so với B=3.)*

## C.3 Đọc kết quả — khoảng dao động THẬT rộng gấp ~10-25 lần so với 1 con số trung bình

Đây chính là điều người dùng chỉ ra: **spec gốc chỉ cho 1 con số (uniform,
~3.3-3.6×), nhưng khoảng dao động thực tế (nếu WDP không phân bổ đều) trải
từ ~1.9× (gần như vô dụng, khi winner tập trung vào cụm lớn nhất) đến
~18-50× (rất có giá trị, khi winner rơi vào driver đơn lẻ)** — chênh lệch
gần **10-25 lần** giữa 2 đầu mút, tùy p.

**Áp ngưỡng đọc kết quả của addition_1 (chỉ dùng kịch bản a/uniform, p=1):**
speedup không bao giờ >5× (0%) → không đảo ngược Hướng B theo đúng chữ
nghĩa ngưỡng đã khóa.

**Nhưng bổ sung (c)/(d) cho thấy bức tranh đầy đủ hơn nhiều:**
- Nếu winner rơi vào cụm lớn nhất (kịch bản thực tế nếu cụm lớn = nhiều
  driver "cạnh tranh giá rẻ" → dễ thắng đồng thời): speedup chỉ ~1.9×, gần
  như KHÔNG đáng để implement decomposition.
- Nếu winner rơi vào driver singleton (thực tế nếu WDP có xu hướng chọn
  driver KHÔNG cạnh tranh vì route của họ không đụng ai — hợp lý vì FD
  không là cạnh tranh, driver singleton dễ "chắc thắng"): speedup **18-50×**
  — rất đáng đầu tư.
- **Không có cách nào biết trước WDP thực sự rơi vào kịch bản nào** mà
  không chạy Algorithm B (MILP) thật trên instance thật — đây chính là việc
  **CẦN LÀM TIẾP** nếu muốn khóa số liệu chính xác (không phải ước lượng
  đại số) cho thesis.

---

# KẾT LUẬN CUỐI CÙNG — đã kiểm đủ 4 góc (Gate 0 / scaling / component / speedup range)

| Góc kiểm tra | Kết quả (dữ liệu ĐẦY ĐỦ 100%) | Ảnh hưởng |
|---|---|---|
| Gate 0 (DP đúng ở quy mô lớn) | 0/180 vi phạm | [VALIDATED] |
| Scaling B (Phần A) | B=2 phẳng đến n=100; B≥3 vỡ siêu tuyến tính trước n=50-75 | Giới hạn thực nghiệm thật, cần vòng đối chứng nếu main exp cần B≥3/n≥75 |
| Component structure (Phần B, 720/720 cả B=2 và B=3) | largest_fraction 0/1440 dưới 0.3, mean 0.58-0.59, bền theo B | **Hướng (B)** xác nhận vững chắc |
| Speedup range thực (Phần C, mở rộng c/d) | p=1: 1.9× (worst) đến 18-50× (best), median uniform 3.3× | T5 **KHÔNG vô giá trị**, giá trị RẤT nhạy cách WDP phân bổ winner — chưa đo được thật |

## Khuyến nghị cuối cùng cho thesis (thay thế mọi khuyến nghị đơn giản trước đó)

1. **Giữ Hướng (B)** làm kết luận chính cho câu hỏi "T5 có nên là trụ cột
   speedup lớn không": route pool thật KHÔNG có cấu trúc component rời rạc
   mà T5 cần để đạt speedup lớn KHÔNG ĐIỀU KIỆN như Test8 đo (14.9-391×) —
   kết luận này giờ dựa trên **1,440 quan sát đầy đủ (720 B=2 + 720 B=3)**,
   không còn dữ liệu bộ phận.

2. **KHÔNG viết T5 là "vô giá trị"** — dùng câu chữ chính xác hơn:
   > *"T5 (component decomposition) đúng đắn (Test7, |Δ|=0) và có giá trị
   > speedup thực nghiệm, nhưng giá trị đó PHỤ THUỘC MẠNH vào cách Winner
   > Determination Problem thực sự phân bổ winner giữa các component —
   > khoảng dao động ước lượng trải từ ~1.9× (nếu winner tập trung vào
   > component lớn nhất — kịch bản xấu) đến ~18-50× (nếu winner là driver
   > không cạnh tranh — kịch bản tốt), median ước lượng theo phân bổ tỷ lệ
   > thuận kích thước là ~3.3×. Con số Test8 (14.9-391×) đo trên cấu trúc
   > component LÝ TƯỞNG HOÁ (tách rời tuyệt đối, dựng thủ công), KHÔNG đại
   > diện cho route pool thực tế đo được ở đây."*

3. **Việc CẦN LÀM TIẾP nếu muốn khóa số chính xác (không bắt buộc, gợi ý)**:
   đo speedup THẬT (không phải ước lượng đại số) bằng cách chạy Algorithm B
   (CPLEX, như Test8) trên vài instance đại diện có cấu trúc lưỡng cực (đã
   có sẵn trong `2b_raw/`/`2b_B2_raw/`), để biết WDP thực sự rơi vào kịch
   bản (c), (a), hay (d) — đây là câu hỏi duy nhất còn treo sau khi đã kiểm
   đủ 3 việc addition_1 + mở rộng (c)/(d).

4. **Cập nhật `main_guideline.md` §3 (T5)**: đổi nhãn thành **"[VALIDATED,
   có điều kiện]"** — đúng đắn (Test7) + giá trị speedup thực nghiệm có
   khoảng dao động rộng đã đo (Phần C), không phải speedup lớn bảo đảm.

5. **T4/T6** không bị ảnh hưởng bởi các kết luận trên, nhưng có thêm giới
   hạn thực nghiệm mới (Phần A.3): B=4 vỡ trước n=50 — cân nhắc khi chọn B
   cho main experiment (Master §12.4, n∈{10,15,20,30}).

---

## File & tái tạo

```
spec_2a_2b/
  config/grid_2a.yaml, grid_2b.yaml        lưới khoá, timestamp 2026-09-10T12:59:28Z
  src/
    instance_gen.py       generator (hộp 20x20km, self-test tam giác sampled)
    dp_labeling.py          wrapper t6_dp.run_dp() (khong sua)
    brute_force.py           oracle Gate 0, doc lap
    conflict_graph.py         build_conflict_graph + connected_components
    run_gate0.py               Gate 0 - PASS 0/180
    run_2a.py                   luoi 2a, 4-worker, resume-capable, 930/1440
    run_2b.py                    luoi 2b B=3, resume-capable, 720/720 DA XONG
    run_2b_B2.py                   luoi 2b B=2, 720/720 DA XONG
    probe_scaling.py                 curve runtime-vs-n bo sung, n toi 100
    viec1_speedup_estimate.py         Viec 1 + mo rong (c)/(d), doc 2b_raw/*.json
  results/
    gate0_violations.csv           rong (0/180)
    scaling_probe.csv                167 diem, B{2,3,4} x tw{30,60,120,240} x n toi 100
    2a_summary.csv                     930/1440 dong
    2b_summary.csv                      720/720 dong (B=3, DAY DU)
    2b_B2_summary.csv                    720/720 dong (B=2, DAY DU)
    viec1_speedup_estimate.csv            28,800 dong (B=3, 720 instance x 4p x 4 kich ban)
    viec1_speedup_estimate_B2.csv          doi chung B=2

Guideline_Total/
  Spec 2a,2b.md                     spec goc
  Spec2a,2b_addition_1.md             spec addition (Viec 1/2/3)
  report_2a_2b_addition_1.md            bao cao addition (du lieu BO PHAN)
  report_2a_2b_full.md                   ĐÂY - bao cao DAY DU, thay the ca 2 file tren
```

Mọi seed dùng chung công thức `hash((..., "spec2a"/"spec2b")) & 0x7FFFFFFF`
— tái tạo được từng instance từ `*_raw/*.json` + tham số trong
`*_summary.csv`.
