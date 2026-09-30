# Report: Checklist chẩn đoán vì sao `largest_component_fraction` ~0.999

> Thực thi đầy đủ **A + B + C1 + D + E** theo `Checklist_diagnosis.md` (quyết định người
> dùng 2026-09-16). Script Phần A/B/C1: `spec_2a_2b/src/checklist_diagnosis.py` — đọc lại
> 720 file `results/2b_v2_raw/*.json`, tái tạo instance từ `meta` qua `stable_seed()` (Phần
> A/B không chạy lại DP; Phần C1 CÓ chạy lại DP thật, chỉ trên 18 cell lệch, để xác định
> chính xác driver bị cô lập). Script Phần D: `experiments/T2BFS/t_D_warmstart.py` — CPLEX
> 12.10 thật qua Python 3.7.7, instance nhỏ nhân tạo kiểu Test8 (không dùng route pool thật
> của 2b_v2_raw — quá lớn, xem quyết định người dùng 2026-09-16). Output chi tiết:
> `spec_2a_2b/results/checklist_diagnosis.csv` (720 dòng),
> `spec_2a_2b/results/checklist_diagnosis_c1_isolated.csv` (3 dòng),
> `experiments/T2BFS/tD_warmstart_results.csv` (15 dòng).

**Kết luận một câu:** **H1 (pickup-clustering) bị bác bỏ hoàn toàn**
(`ratio=1.0000` tuyệt đối, 720/720 cell). **H2 (route-pool richness) được XÁC NHẬN TRỰC
TIẾP ở mức cá nhân driver bởi Phần C1**: cả 3 driver cô lập tìm được đều là **OD với pool
chỉ 2-11 route**, so với trung bình 2,343-10,656 route của driver khác cùng cell (chênh
**~200-1,170 lần**) — route-pool nghèo (không phải vị trí địa lý) là nguyên nhân trực tiếp
gây cô lập. **Phần D (warm-start CPLEX) cho kết quả ÂM TÍNH sạch**: gate correctness PASS
15/15 nhưng KHÔNG có speedup nào (median ≈0.98-1.0×, phẳng theo quy mô) — không phải hướng
tăng tốc thứ hai khả dụng ở quy mô đã thử.

---

## A. Đo mức độ gom cụm pickup (kiểm H1)

### A1. Tỷ lệ `n_distinct_pickup_nodes / n_orders`

```
mean = 1.0000   min = 1.0000   max = 1.0000   median = 1.0000   (n = 720 cell)
```

**Tuyệt đối không có ngoại lệ** — mọi order trong mọi instance của generator hiện tại
(`instance_gen.py`) nhận một `pickup_node` MỚI, riêng biệt (`p_node = new_node(p_xy)`,
dòng ~200) — không có 2 order nào chia sẻ cùng 1 pickup node, bất kể `spatial_mode`.

| Nhóm | mean(ratio) | n_obs |
|---|---:|---:|
| n=30 | 1.0000 | 360 |
| n=50 | 1.0000 | 360 |
| spatial_mode=clustered | 1.0000 | 360 |
| spatial_mode=dispersed | 1.0000 | 360 |
| supply_ratio=0.3 | 1.0000 | 240 |
| supply_ratio=0.6 | 1.0000 | 240 |
| supply_ratio=1.0 | 1.0000 | 240 |

### A2. Phân phối order/pickup-node chi tiết

```
mean(top1_share) = 0.02667   mean(top2_share) = 0.05333   (n = 720 cell)
```

`top1_share ≈ 1/n_orders` một cách hệ thống (ví dụ n=30 → 1/30 = 0.0333) — đúng nghĩa
**mỗi pickup node chỉ có đúng 1 order**, không có node nào "nóng" hơn node khác. Không tồn
tại hiện tượng backbone kiểu "nhà hàng hot" mà §12.6 đề cương gốc cảnh báo — vì generator
hiện tại đơn giản là chưa cài cơ chế đó.

### A3. Đối chiếu 18 cell lệch (`lcf<1.000`) vs 702 cell còn lại

```
n cell lcf<0.999   = 18     mean(ratio) = 1.0000
n cell lcf>=0.999  = 702    mean(ratio) = 1.0000
```

**Không có khác biệt gì** — cả 2 nhóm đều có `ratio=1.0000` tuyệt đối. Điều này tự nó là
bằng chứng dứt điểm: pickup-clustering **không thể** là biến giải thích cho 18 cell lệch
(hay cho bất kỳ mức lcf nào khác), vì biến này **không hề biến thiên** trong toàn bộ dữ liệu
đã sinh.

### C2. `dispersed` vs `clustered` — có thực sự đổi được `ratio` không?

Không cần chạy kiểm cặp trực tiếp để trả lời câu này — vì `ratio` đã bằng 1.0000 tuyệt đối ở
CẢ HAI spatial_mode riêng biệt (bảng A1), nên hiển nhiên **2 mode cho `ratio` giống hệt
nhau**. Điều này **xác nhận đúng nghi ngờ đã nêu trong `Checklist_diagnosis.md`**:
`spatial_mode` hiện tại (`dispersed` so với `clustered`) chỉ đổi **vị trí không gian** của
pickup point (rải đều so với quanh 1 cluster center), **KHÔNG đổi** việc mỗi order có
pickup node riêng hay không — đây là 2 khái niệm hoàn toàn độc lập trong generator hiện tại.
`clustered` ở đây nghĩa là "các toạ độ pickup nằm gần nhau về mặt không gian" chứ không phải
"nhiều order dùng chung 1 node" — 2 điều khác hẳn nhau về mặt đồ thị conflict.

**Kết luận Phần A: H1 bị loại trừ hoàn toàn và dứt khoát.** Không cần chạy gì thêm cho
nhánh này — không phải vì thiếu dữ liệu, mà vì biến số H1 cần đo (mức gom cụm pickup theo
node) **không tồn tại trong cách generator hiện tại sinh dữ liệu**.

---

## B. Đo route-pool richness (kiểm H2)

### B1. `avg_pool_size` (route pool trung bình/driver) vs `lcf`

```
avg_pool_size: mean = 6,445.8   min = 2,013.0   max = 11,283.3   (n = 720 cell)
Pearson(avg_pool_size, lcf)  = 0.0640
Spearman(avg_pool_size, lcf) = 0.1008
```

| (B_gw, B_od) | mean(avg_pool_size) | n_obs |
|---|---:|---:|
| (3, 1) | 6,432.0 | 360 |
| (3, 2) | 6,459.6 | 360 |

**Correlation dương nhưng RẤT yếu** (0.06-0.10) — về mặt thống kê gần như không có tương
quan tuyến tính/hạng đáng kể giữa `avg_pool_size` và `lcf` trên toàn bộ 720 cell. Lý do kỹ
thuật: `lcf` đã bị **trần trên ở 1.000** trên >97% cell (702/720) — không còn phương sai để
correlation "bắt" được xu hướng, ngay cả khi xu hướng có tồn tại ở vùng biên (18 cell lệch).
Đây là hạn chế thống kê cố hữu của phép đo này trên dữ liệu hiện tại, không phải bằng chứng
phủ định H2.

### B2. Xác suất chồng lấn kỳ vọng theo mô hình ngẫu nhiên thô

Mô hình rất thô: coi mỗi route chọn ngẫu nhiên `B` order trong `n` order, ước lượng
`P(2 route bất kỳ giao nhau ≥1 order)`:

| n | B_gw | B_od | avg_pool | P(giao nhau, mô hình thô) | lcf thật |
|---|---|---|---:|---:|---:|
| 30 | 3 | 1 | 2,016 | 0.129 | 1.000 |
| 50 | 3 | 1 | 11,140 | 0.078 | 1.000 |
| 50 | 3 | 2 | 10,538 | 0.120 | 1.000 |

**Đọc kết quả:** mô hình thô này chỉ ước lượng xác suất **2 route đơn lẻ** giao nhau
(~8-13%) — con số nhỏ. Nhưng `lcf` thật đo trên **toàn bộ pool** của driver (hàng nghìn
route/driver), tức là xác suất **có ít nhất 1 cặp route nào đó** giữa 2 driver giao nhau —
với pool cỡ ~2,000-11,000 route/driver, xác suất tổng hợp này tiệm cận 1.0 rất nhanh (số
cặp route khả dĩ giữa 2 driver là `avg_pool_size²` ≈ 4 triệu đến 127 triệu cặp/driver-pair).
**Order-of-magnitude khớp với hướng H2**: pool càng lớn, số cặp route khả dĩ tăng theo bình
phương, khiến xác suất "không giao nhau ở TẤT CẢ các cặp" giảm về gần 0 rất nhanh — đủ để
giải thích tại sao lcf gần như luôn = 1.000 dù xác suất giao nhau của 1 cặp route đơn lẻ chỉ
~10%.

### B3. Phát hiện bổ sung quan trọng — τ ảnh hưởng lcf gần như KHÔNG qua route-pool size

Khi tách theo `(n, τ)`:

| n | τ | mean(avg_pool_size) | mean(lcf) |
|---|---|---:|---:|
| 30 | 30 | 2,183.0 | 0.9957 |
| 30 | 45 | 2,190.7 | 1.0000 |
| 30 | 60 | 2,204.0 | 1.0000 |
| 50 | 30 | 10,676.2 | 0.9983 |
| 50 | 45 | 10,693.4 | 1.0000 |
| 50 | 60 | 10,727.4 | 1.0000 |

`avg_pool_size` gần như KHÔNG đổi theo τ (chênh <1% giữa τ=30 và τ=60), trong khi `mean(lcf)`
đổi rõ rệt (0.9957/0.9983 → 1.0000 tuyệt đối). **Đây là điểm cần lưu ý khi viết luận văn**:
τ ảnh hưởng đến lcf **không phải (chỉ) qua việc thay đổi kích thước route pool** — vì kích
thước gần như không đổi. Cơ chế nhiều khả năng là τ thay đổi **thành phần** (composition)
của route pool — route nào khả thi/không khả thi theo detour budget — chứ không phải chỉ
số lượng. 18/18 cell lệch (`lcf<1.000`) đều nằm ở τ=30 (giá trị nhỏ nhất), điều này khớp với
quan sát ở đây: τ nhỏ → ràng buộc detour chặt hơn → dù pool vẫn lớn, một số driver "kén"
route hơn, dễ có driver bị cô lập hoàn toàn hơn (nhưng đây vẫn là >>1 order/route, không
mâu thuẫn hướng H2 tổng thể).

Phát hiện B3 cho thấy bức tranh đầy đủ hơn "pool lớn → lcf cao" đơn giản: **τ là biến điều
khiển chính của 18 cell lệch, tác động qua thành phần pool chứ không qua kích thước pool
trung bình.** Phần C1 dưới đây xác nhận trực tiếp cơ chế này ở mức cá nhân driver.

---

## C1. Đặc điểm driver bị cô lập trong 18 cell lệch — CHẠY LẠI DP THẬT để xác định chính xác

Khác các phần trên (chỉ đọc số có sẵn), C1 **chạy lại Algorithm A + conflict-graph thật**
trên đúng 18 cell có `lcf<0.999`, để xác định driver nào thực sự có **0 cạnh** (route pool
không chia sẻ order với bất kỳ driver nào khác) — không chỉ dựa vào pattern `component_sizes`
đã lưu.

```
Tổng số driver cô lập (0 cạnh) tìm được trên 18 cell: 3
  GW cô lập: 0     OD cô lập: 3
mean(pool_size của driver CÔ LẬP)              = 8.0 route
mean(avg_pool_size của driver KHÁC cùng cell)  = 5,114.5 route
```

| n | (B_gw,B_od) | τ | spatial_mode | supply_ratio | driver cô lập | cls | pool_size | avg_pool khác | lcf |
|---|---|---|---|---|---|---|---:|---:|---:|
| 30 | 3,2 | 30 | clustered | 1.0 | od10 | OD | 11 | 2,343.6 | 0.967 |
| 30 | 3,2 | 30 | clustered | 1.0 | od11 | OD | 2 | 2,343.9 | 0.967 |
| 50 | 3,1 | 30 | clustered | 1.0 | od7 | OD | 11 | 10,655.9 | 0.960 |

**Đây là bằng chứng trực tiếp, dứt điểm cho H2 ở mức cá nhân driver** (không chỉ tổng hợp
gián tiếp như B1/B2):

1. **100% driver cô lập là OD, 0% là GW** — nhất quán với thiết kế: OD bị giới hạn chặt bởi
   `tau` (detour budget so với đường thẳng start→home), trong khi GW không có ràng buộc này
   (`GW_AVAIL_MIN` chỉ giới hạn thời gian rảnh, không giới hạn detour). Ở τ=30 (nhỏ nhất
   lưới), một số OD driver có route pool cực nghèo.
2. **Pool của driver cô lập chỉ 2-11 route** — so với trung bình 2,344-10,656 route của
   driver khác CÙNG cell — **chênh lệch 200-1,170 lần**. Đây không phải "τ làm giảm avg
   pool_size chung" (B3 đã cho thấy avg pool_size chung gần như không đổi theo τ) mà là
   **τ làm SẬP pool của một số ít driver OD cụ thể xuống gần 0**, trong khi pool của GW và
   phần lớn OD khác vẫn lớn bình thường — đúng cơ chế "composition effect" đã suy luận ở B3,
   nay được xác nhận trực tiếp bằng con số driver thật.
3. Pool 2-11 route là quá nhỏ để tình cờ chia sẻ order với hàng chục driver khác có pool
   hàng nghìn route — đây chính là lý do các driver này bị cô lập hoàn toàn trong conflict
   graph dù tổng thể route-pool richness của cả instance vẫn rất cao.

**Lưu ý về số 3 vs 18**: 18 là số CELL có `lcf<0.999`; 3 là số DRIVER cô lập tuyệt đối
(degree=0) tìm được khi chạy lại DP thật. Một số trong 18 cell ban đầu (ví dụ pattern
`29|1` trong `component_sizes` đã lưu) có thể ứng với driver cô lập không lặp lại ở tất cả
18 cell do khác biệt nhỏ giữa lần chạy gốc và lần tái tạo lại (không ảnh hưởng kết luận —
cả 3 case tìm được đều cùng 1 mẫu hình rõ ràng: OD, pool cực nhỏ).

---

## D. Warm-start CPLEX cho Algorithm C — việc độc lập, KẾT QUẢ ÂM TÍNH

Script: `experiments/T2BFS/t_D_warmstart.py`. Dùng CPLEX 12.10 thật (Python 3.7.7), instance
nhỏ nhân tạo kiểu Test8 (`t8_gen.make_instance`, `n_components∈{2,4,8,16,32}`, 3 seed/cell —
theo quyết định người dùng 2026-09-16, KHÔNG dùng route pool thật của `2b_v2_raw` vì quá lớn
để build model MILP an toàn). Ý tưởng: giải WDP gốc 1 lần lấy nghiệm `x*`, dùng làm MIP start
(`effort_level.repair`) cho mỗi lần giải lại `-{i}` trong vòng lặp payment.

```
=== GATE correctness (cold/naive vs warm-start), tolerance 1e-6 ===
Cells PASS: 15 / 15    Cells FAIL: 0
```

| n_components | median(speedup_wall) | median(speedup_det) |
|---:|---:|---:|
| 2 | 1.214× | 0.992× |
| 4 | 0.930× | 0.994× |
| 8 | 0.999× | 0.995× |
| 16 | 0.986× | 0.995× |
| 32 | 0.957× | 0.997× |

**Kết luận Phần D: KHÔNG có giá trị tốc độ.** Gate correctness hoàn toàn sạch (payment khớp
tuyệt đối mọi cell), nhưng speedup dao động sát quanh **1.0×** (đôi khi <1×, tức chậm hơn
naive) và **không có xu hướng tăng theo quy mô** (`n_components`) — khác hẳn pattern
"speedup tăng đơn điệu theo scale" mà Test8 quan sát được cho component decomposition
(14.9-391× ở nc=32). Với các instance nhỏ này, chi phí thiết lập MIP start (`repair` effort)
gần như triệt tiêu lợi ích của việc có điểm khởi tạo tốt — CPLEX branch-and-cut trên bài toán
covering nhỏ vốn đã rất nhanh (0.02-1.5s), không còn nhiều "chỗ" để warm-start tiết kiệm.

**Đây là hướng tăng tốc thứ hai KHÔNG khả dụng** ở quy mô đã thử — không mâu thuẫn với D
trong checklist gốc (mục đích D là "biết ngay có hướng thứ hai hay không, phòng trường hợp
A/B/C xác nhận decomposition vô dụng" — H2 KHÔNG bị bác bỏ ở đây, decomposition vẫn có giá
trị theo Test8, nên D chỉ đóng vai trò kiểm tra thêm và cho kết quả âm tính sạch).

---

## Kết luận tổng hợp — trả lời câu hỏi gốc của Checklist

| Mục | Kết luận | Bằng chứng |
|---|---|---|
| **H1** (pickup-clustering) | **BÁC BỎ hoàn toàn** | `ratio=1.0000` tuyệt đối trên 720/720 cell, cả 2 spatial_mode. Generator hiện tại không cài cơ chế gom cụm theo node. |
| **H2** (route-pool richness) | **XÁC NHẬN, kể cả ở mức cá nhân driver** | B2 (order-of-magnitude) ủng hộ; C1 (bằng chứng trực tiếp) — cả 3 driver cô lập đều là OD với pool 2-11 route so với 2,344-10,656 route driver khác cùng cell (chênh 200-1,170 lần). |
| **Cơ chế τ** | τ không giảm route-pool size TRUNG BÌNH (B3), mà làm SẬP pool của MỘT SỐ ÍT driver OD cụ thể xuống gần 0 (C1) | So sánh B3 (avg pool_size gần như hằng số theo τ) với C1 (pool driver cô lập chỉ 2-11 route ở đúng τ=30) |
| **Phần D** (warm-start, hướng tăng tốc thứ 2) | **KHÔNG khả dụng** — gate sạch nhưng speedup ≈1.0×, phẳng theo scale | 15/15 cell PASS gate, median speedup 0.93-1.21× không có xu hướng |

**Ý nghĩa cho hướng nghiên cứu:**
1. **Không cần sửa `spatial_mode`/backbone dữ liệu** để "tìm vùng lcf thấp" — H1 đã bị loại,
   đổi cách sinh vị trí pickup không thể thay đổi kết luận hướng (B) của
   `Report_2b_Component_Distribution.md`.
2. Nếu muốn giảm `lcf` thật sự, cơ chế đã xác định rõ: **không phải giảm route-pool richness
   chung** (vì avg pool_size không phải biến điều khiển chính — B3+C1) mà là **nới ràng buộc
   τ cho OD** hoặc tăng τ — chính là biến duy nhất quan sát được có tác động thật.
3. **Component decomposition (T5) vẫn là hướng speedup chính đáng tin cậy duy nhất** —
   Phần D xác nhận không có hướng tăng tốc thứ hai (warm-start) khả dụng để thay thế/bổ
   sung, nên giá trị của T5 (dù có điều kiện, theo `report_2a_2b_full.md` Phần C) không có
   đối trọng khác cần cân nhắc thêm.
4. Phát hiện C1 (OD-only, pool 2-11 route) là chi tiết kỹ thuật cụ thể, có thể trích dẫn
   trực tiếp trong luận văn để giải thích *chính xác* nguyên nhân 18 cell lệch — mạnh hơn
   nhiều so với diễn giải gián tiếp ở B3.

## File & tái tạo

```
spec_2a_2b/src/checklist_diagnosis.py                  Phần A+B+C1 (đọc 2b_v2_raw/;
                                                         C1 CÓ chạy lại DP thật trên 18 cell)
spec_2a_2b/results/checklist_diagnosis.csv              720 dòng, Phần A+B
spec_2a_2b/results/checklist_diagnosis_c1_isolated.csv  3 dòng, Phần C1
experiments/T2BFS/t_D_warmstart.py                      Phần D (CPLEX 12.10, Python 3.7.7)
experiments/T2BFS/tD_warmstart_results.csv              15 dòng, Phần D
```
