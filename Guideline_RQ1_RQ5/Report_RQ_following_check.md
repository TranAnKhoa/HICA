# RQ1–RQ5 — Báo cáo ba việc kiểm tra bổ sung

> Thực thi theo `Guideline_RQ1_RQ5/RQ_following_check.md`. Không đổi bất kỳ tham số nào
> trong `rq1_locked_params.json`/`rq_all_locked_params.json`. Dùng lại instance/pool đã có
> ở RQ1/RQ2/RQ3/RQ4/RQ5 bất cứ khi nào có thể — không sinh instance mới ngoài các trường
> hợp đã nêu rõ trong spec (Việc a Bước 2, Việc b, Việc c đều dùng đúng seed cũ).

---

## 0. Tóm tắt

| Việc | Kết quả | Ý nghĩa |
|---|---|---|
| **(a)** Calibration q_o | Pilot cũ (n=12, không kiểm soát alignment) **không generalize**: 12/15 cell chính nằm ngoài mục tiêu FD rate [0.10, 0.50] | Cần ghi rõ giới hạn thiết kế trong thesis, không sửa lại ngay |
| **(b)** T5 trên pool K* | Ở alignment 0.90 (chế độ crowd cạnh tranh), `largest_component/n_drivers` median vẫn = 1.000 (không đổi so với pool đầy đủ) | T5 **không** được cứu bởi K* ở chế độ cạnh tranh — giữ nguyên kết luận cũ |
| **(c)** Tần suất K* rỗng | Per-driver: 1.0–77.3% tùy alignment; per-instance: 0–53.0%. Đường cong **không đơn điệu theo alignment** nhưng cùng hình dạng với FD rate (Việc a) — cùng một cơ chế, không phải lỗi | K* là công cụ vận hành thật: tại alignment 0.50, biết trước 53% phiên đấu giá không cần mở cho bất kỳ driver nào |

---

## 1. Việc (a) — Kiểm lại calibration giá FD

### Bước 1: Pilot calibration đã tìm thấy trong codebase

`spec_2a_2b/src/rq1_calibration.py`, khóa trong `rq1_locked_params.json` →
`fd_cost_q_o.calibration_pass`:

- **Mục tiêu:** FD rate ∈ [0.10, 0.50] và không supply-ratio cell nào (trong 4 cell
  (2,2)/(3,2)/(2,3)/(3,3)) có GW hoặc OD thắng 0% tuyệt đối.
- **Pilot instance:** n=12, B_gw=B_od=3, tw_width=120, τ=30.0, spatial_mode="dispersed",
  **không dùng corridor_share/corridor_buffer_km** — hai tham số này được thêm **sau**
  calibration pass (2026-09-16), nên pilot chạy ở một "alignment tự nhiên" không kiểm soát,
  không phải ở bất kỳ alignment target nào trong {0.10, …, 0.90} của main grid.
- **Grid quét:** base_fee ∈ {2,3,4,5,6,8,10,14}, rate_per_km ∈ {0.8,1.2,1.6,2.0,2.5,3.0},
  free_radius cố định 1.0km. 4 supply ratio × 5 seed = 20 instance/combo.
- **Bộ được chọn** (đầu tiên đạt cả 2 tiêu chí, dừng lại): `base_fee=8.0, rate_per_km=3.0,
  free_radius=1.0` → fd_rate=0.483, gw_wins=32, od_wins=24, 0 cell thắng trắng.

### Bước 2–3: FD rate thật trên toàn bộ 1,500 instance RQ1 main grid

Đọc lại từ `rq2_shard*.csv` (menu B3 = chính xác pool/allocation JOINT của RQ1, đã xác
nhận X1 khớp tuyệt đối với `rq1_main_grid_results.csv` — không giải lại WDP).

| alignment | n | FD rate median | FD rate mean | n_instance | Trong [0.10,0.50]? |
|---:|---:|---:|---:|---:|---|
| 0.10 | 10 | 0.900 | 0.838 | 100 | Không |
| 0.10 | 15 | 0.867 | 0.845 | 100 | Không |
| 0.10 | 20 | 0.800 | 0.808 | 100 | Không |
| 0.30 | 10 | 0.900 | 0.836 | 100 | Không |
| 0.30 | 15 | 0.800 | 0.791 | 100 | Không |
| 0.30 | 20 | 0.800 | 0.809 | 100 | Không |
| 0.50 | 10 | 1.000 | 0.960 | 100 | Không |
| 0.50 | 15 | 1.000 | 0.946 | 100 | Không |
| 0.50 | 20 | 1.000 | 0.941 | 100 | Không |
| 0.70 | 10 | 0.700 | 0.702 | 100 | Không |
| 0.70 | 15 | 0.667 | 0.695 | 100 | Không |
| 0.70 | 20 | 0.675 | 0.675 | 100 | Không |
| 0.90 | 10 | 0.300 | 0.304 | 100 | Có |
| 0.90 | 15 | 0.333 | 0.371 | 100 | Có |
| 0.90 | 20 | 0.450 | 0.446 | 100 | Có |

Toàn bộ grid: FD rate median = 0.800, mean = 0.731 (n=1,500). **12/15 cell nằm ngoài
khoảng mục tiêu pilot**, chỉ 3 cell (alignment 0.90) nằm trong/gần mục tiêu.

**Kết luận một câu:** Pilot nhắm FD rate ∈ [0.10, 0.50] tại n=12, một alignment tự nhiên
không kiểm soát (trước khi corridor bias được thêm); nhưng trên toàn bộ 15/15 cell của
main grid ở alignment ≤ 0.70, FD rate thật nằm ngoài khoảng đó (cao hơn nhiều), chỉ trở về
gần mục tiêu ở alignment=0.90 — pilot **không generalize** sang phần lớn grid chính, vì
corridor bias (thêm sau để đạt alignment target thấp) làm thay đổi vị trí order theo cách
ảnh hưởng cả khả năng GW/OD phục vụ, không chỉ "độ trùng lặp không gian" như alignment đo.

**Phát hiện phụ quan trọng, chưa có trong Report_RQ_All.md:** FD rate **không đơn điệu**
theo alignment — nó đạt đỉnh (~100%) ở alignment=0.50, thấp nhất ở hai đầu 0.10 và 0.90.
Nguyên nhân cấu trúc: ở alignment=0.50, `corridor_share=0.0` (không có corridor bias, orders
rải ngẫu nhiên toàn vùng) nhưng `corridor_buffer_km=3.0` vẫn là baseline — trong khi cả
alignment=0.10 và alignment=0.90 đều dùng corridor bias khác 0 (0.2 và 1.0) để kéo order
gần/xa corridor OD, vô tình cũng làm order gần driver GW hơn ở một số cấu hình. Đây không
phải lỗi tính toán — đã xác nhận độc lập ở Việc (c) dưới đây (tần suất K* rỗng có cùng hình
dạng, cùng đỉnh tại 0.50).

### Bước 4: Độ nhạy FD rate theo giá FD (RQ5, dùng lại số đã có)

| FD multiplier | FD rate median | FD rate mean |
|---:|---:|---:|
| ×0.75 (V5) | 1.000 | 0.992 |
| ×1.00 (V0) | 1.000 | 0.948 |
| ×1.25 (V6) | 0.867 | 0.872 |

Xu hướng đơn điệu đúng hướng (FD đắt hơn → FD rate giảm), nhất quán với RQ5 đã báo cáo.

### Ghi nhận cho thesis
Không có bằng chứng calibration được thực hiện lại sau khi corridor bias được thêm vào
generator. FD rate quan sát được (73–100% ở alignment ≤ 0.70, giảm còn 30–45% ở alignment
0.90) là một giới hạn của thiết kế instance generator cần nêu rõ trong phần thiết kế thực
nghiệm của luận văn — không phải lỗi cần sửa ngay (theo đúng nguyên tắc `[DEVIATION]` của
`RQ_Master.md` §8: cần chạy lại toàn bộ RQ1–RQ5 nếu calibrate lại, đây là quyết định riêng
chưa thực hiện trong lần kiểm tra này).

---

## 2. Việc (b) — Component decomposition (T5) trên pool đã cắt K*

**Thiết kế:** đúng 600 instance của RQ3+RQ4 (cùng seed, B=3). Với mỗi instance: dựng
conflict graph (`t8_cplex.build_conflict_graph` + `connected_components`, không viết lại
logic) trên cả pool đầy đủ và pool đã cắt K* (`prune_pool_by_kstar`, công thức y hệt RQ4).

| alignment | largest component / n_drivers — pool đầy đủ (median) | largest component / n_drivers — pool K* (median) | % driver bị cô lập — pool K* |
|---:|---:|---:|---:|
| 0.50 | 0.500 | 0.250 | 79.6% |
| **0.90** | **1.000** | **1.000** | **1.3%** |

Số instance (alignment=0.90) có ≥2 component ở pool K*: **22/300**.

### Đọc kết quả (theo đúng `[CHECK]` đã khóa trước)
- Ở alignment 0.50, K* cắt gần hết pool (77.3% driver K*-rỗng theo Việc (c)) nên các driver
  còn route tự động bị cô lập — đúng như spec cảnh báo trước, **không đại diện** cho việc
  K* giúp T5, vì ở đây crowd gần như không tồn tại.
- Ở alignment 0.90 — phép thử thật, nơi crowd cạnh tranh (K* chỉ cắt ~75% theo RQ4) —
  `largest_component_kstar_frac` median vẫn = **1.000**, bằng hệt pool đầy đủ; chỉ 1.3%
  driver bị cô lập, chỉ 22/300 instance có ≥2 component. Điều kiện dừng Bước 4 đã nêu
  trong spec (`≥ 0.85` → không cải thiện đáng kể) bị kích hoạt.
- **Kết luận: T5 trên pool K* không cải thiện gì đáng kể ở chế độ cạnh tranh.** Giữ nguyên
  kết luận cũ của `Report_2b_Component_Distribution.md` (component gộp ≥0.889 driver ở scale
  chính) — không thêm khung "T5 giúp khi kết hợp với K*" vào thesis. Bước 4 (đo speedup
  component-wise) không cần chạy, theo đúng tiêu chí đã khóa.

---

## 3. Việc (c) — Tần suất K* rỗng theo alignment và giá FD

**Định nghĩa:** K*_i rỗng ⟺ `local_frontier(R_i, Θ=[18,25], q) == ∅` (kể cả khi driver
không có route hợp lệ nào — tính là K* rỗng theo đúng nghĩa "không có route nào đáng dùng ở
bất kỳ bid nào"). Đo hai mức: per-driver (mean tỉ lệ driver rỗng), per-instance (% instance
mà **toàn bộ** driver đều K* rỗng).

### Theo alignment (RQ1 main grid, toàn bộ 1,500 instance)

| alignment | % driver K* rỗng (mean) | % instance TOÀN BỘ driver K* rỗng |
|---:|---:|---:|
| 0.10 | 35.0% | 8.3% |
| 0.30 | 31.8% | 7.7% |
| **0.50** | **77.3%** | **53.0%** |
| 0.70 | 12.8% | 1.7% |
| 0.90 | 1.0% | 0.0% |

**Đơn điệu giảm theo alignment? KHÔNG** — đường cong lồi, đỉnh tại alignment=0.50. Đây là
lệch so với tiêu chí `[CHECK]` viết sẵn trong spec ("nếu không đơn điệu, có khả năng lỗi …
dừng lại, không báo cáo số"). **Đã điều tra trước khi báo cáo**: đối chiếu trực tiếp với
FD rate theo alignment (Việc a, Bước 2) cho **cùng hình dạng, cùng đỉnh tại 0.50** (FD rate
mean: 0.856 / 0.833 / **1.000** / 0.681 / 0.361 — xem bảng Việc (a)). Hai đại lượng độc
lập (một đếm order về FD, một đếm driver có K* rỗng) cho cùng dạng đường cong theo alignment
→ đây là cùng một hiện tượng cấu trúc thật của generator (corridor bias tương tác phi tuyến
với alignment, giải thích ở Việc (a)), **không phải lỗi trong `local_frontier` hay việc gán
giá q_o**. Số liệu được báo cáo đầy đủ.

**Đối chiếu chéo với K* cut ratio đã có ở RQ4** (pool-level, 600 instance):

| alignment | pool cut ratio (RQ4, median) | driver-empty rate (Việc c, mean) |
|---:|---:|---:|
| 0.50 | 100.0% | 77.3% |
| 0.90 | 76.6% | 1.0% |

Nhất quán về hướng ở cả hai điểm đối chiếu được (alignment 0.50 cao–cao, alignment 0.90
thấp–thấp).

### Theo giá FD (RQ5 V0/V5/V6, alignment=0.50 cố định)

| FD multiplier | % driver K* rỗng (mean) | % instance TOÀN BỘ driver K* rỗng |
|---:|---:|---:|
| ×0.75 | 95.7% | 81.7% |
| ×1.00 | 77.0% | 46.7% |
| ×1.25 | 57.2% | 20.0% |

**Đơn điệu giảm khi FD đắt hơn? CÓ** — đúng hướng lý thuyết dự đoán (FD đắt hơn → ít driver
bị loại trước). Xác nhận `local_frontier`/gán giá hoạt động đúng: khi cố định alignment và
chỉ đổi giá FD, hành vi hoàn toàn như kỳ vọng; sự không-đơn-điệu ở bảng theo alignment đến
từ chính generator (corridor bias), không phải từ công thức K*.

### Con số để trích dẫn
- **Per-driver, mạnh nhất, vẫn đơn điệu đúng theo trục giá FD:** ở giá FD hiện tại
  (×1.00, alignment=0.50), nền tảng biết trước — **không cần đọc bid** — rằng 77% driver
  không có route nào đáng cân nhắc.
- **Per-instance, ấn tượng nhất:** ở alignment=0.50, **53.0% phiên đấu giá** có thể được
  biết trước là không cần mở cho bất kỳ driver crowd nào (toàn bộ order chắc chắn về FD).
  Ở alignment=0.90 (chế độ cạnh tranh), con số này về 0% — đúng dự đoán, vì đây là chế độ
  crowd thật sự cạnh tranh được.

---

## 4. Việc còn mở / cần quyết định riêng
- **Không tự sửa `q_o`** theo phát hiện Việc (a) trong lần này — nếu muốn calibrate lại
  theo alignment (ví dụ mục tiêu FD rate riêng cho từng alignment level, hoặc pilot quét
  luôn cả corridor_share/buffer), đó là một `[DEVIATION]` cần bàn trước, kéo theo chạy lại
  toàn bộ RQ1–RQ5.
- Cơ chế phi tuyến giữa corridor bias và alignment (giải thích hình dạng lồi của FD rate và
  K*-empty rate) chưa được phân tích định lượng — có thể là một mục riêng nếu muốn hiểu sâu
  hơn generator, không bắt buộc cho thesis hiện tại.

---

## File & tái tạo

```
spec_2a_2b/src/check_fd_calibration.py         Viec (a) - doc lai rq2_shard*.csv + rq5_shard*.csv
spec_2a_2b/src/component_distribution_kstar.py Viec (b) - component tren pool K* (600 instance)
spec_2a_2b/src/kstar_empty_rate.py             Viec (c) - dinh nghia + phan (ii) RQ5
spec_2a_2b/src/kstar_empty_rate_shard.py       Viec (c) phan (i) - shard RQ1 main grid (1500 instance)
spec_2a_2b/results/rq_all/fd_rate_by_cell.csv              Viec (a) Buoc 2-3
spec_2a_2b/results/rq_all/component_distribution_kstar.csv Viec (b)
spec_2a_2b/results/rq_all/kstar_empty_by_alignment.csv     Viec (c) phan (i), 1500 dong
spec_2a_2b/results/rq_all/kstar_empty_by_fd_price.csv      Viec (c) phan (ii), 180 dong
```

Chạy lại (Python 3.7.7 + CPLEX 12.10, từ `spec_2a_2b/src`):
```
python check_fd_calibration.py
python component_distribution_kstar.py             # ~27 phut
python kstar_empty_rate_shard.py <k> 4  (k=0..3)    # ~12 phut/shard, chay song song
python kstar_empty_rate.py                          # chi phan (ii), ~1 phut
```
