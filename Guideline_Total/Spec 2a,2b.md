# Spec 2a+2b — Mở rộng Algorithm A lên n=100 & đo phân phối component
## Guideline thực thi cho Claude Code

---

## Mục tiêu

Trả lời hai câu hỏi treo, độc lập với Algorithm B/CPLEX:

1. DP Label-Setting (Test6) còn đúng và đủ nhanh ở quy mô n=50–100 không?
2. Trên route pool **thật** do DP sinh ra, conflict graph giữa driver có tách thành
   nhiều component nhỏ, hay gộp thành 1–2 component khổng lồ như Case B của Test7?

Câu 2 quyết định T5 có đáng đầu tư tiếp vào 2c/2d hay không — đây là gate, không phải
việc chạy song song.

---

## Bối cảnh bắt buộc đọc trước khi code

Đây là phần mở rộng của một DP label-setting đã được kiểm chứng đúng ở n≤7
(completeness 100% qua brute-force độc lập, dominance rule khớp Dumas et al. 1991
Rule 1). Nhiệm vụ ở đây **không phải** thiết kế thuật toán mới — là (a) chạy đúng
thuật toán đã có ở quy mô lớn hơn và đo hiệu năng, (b) dùng route pool sinh ra để đo
một đại lượng thống kê (kích thước component).

**Không được** sửa dominance rule, **không được** nới lỏng điều kiện feasibility để
"chạy nhanh hơn" — nếu gặp bùng nổ, đó là kết quả cần báo cáo, không phải bug cần vá.

---

# PHẦN 2a — Verify DP ở quy mô lớn

## Trạng thái & dominance (không đổi so với Test6 — chép lại để không lệch)

```
Label = (v, IV, C, t, K, W)
  v: node hiện tại
  IV: tập order đang mang (pickup rồi, chưa delivery)
  C: tập order đã giao xong
  t: thời điểm hiện tại
  K: chi phí quãng đường tích lũy
  W: thời lượng tính phí tích lũy

Bất biến: |IV| + |C| ≤ B suốt quá trình

GW: bundle hoàn chỉnh khi IV=∅, 1≤|C|≤B, route kết thúc tại v hiện tại
OD: phải có transition riêng "về home" khi IV=∅; deadline_home = t0 + direct_time + tau

Dominance: Label_a ⪰ Label_b ⟺ cùng (v, IV, C) AND t_a≤t_b AND K_a≤K_b AND W_a≤W_b
           (ít nhất 1 strict) → xóa Label_b
```

Nếu codebase Test6 đã có sẵn, **dùng lại nguyên module đó** — không viết lại từ đầu.
Chỉ viết lại nếu không có sẵn, và nếu viết lại thì **bắt buộc** chạy lại gate n≤7
brute-force trước khi tin bất kỳ số nào ở quy mô lớn (xem Gate 0 bên dưới).

## Instance generator

Viết `generate_instance(n, B, tw_width, gw_od_ratio, seed)`:

- n orders, pickup/delivery ngẫu nhiên trong một vùng không gian cố định (ví dụ hộp
  20×20 km)
- time window mỗi order: rộng `tw_width` phút, đặt ngẫu nhiên trong khung ngày
- số driver: tách riêng thành tham số độc lập `n_drivers`, không suy ra tự động từ n
  orders (để không trộn hai biến khi phân tích)
- driver GW: vị trí bắt đầu ngẫu nhiên, availability window rộng
- driver OD: origin + home ngẫu nhiên, direct_time/direct_distance tính từ travel
  matrix, τ (detour budget) là tham số quét riêng ở phần 2b — ở 2a cứ để τ cố định
  vừa phải (ví dụ 20 phút) vì 2a chỉ quan tâm hiệu năng DP, không quan tâm component
- lưu seed để tái tạo được instance

## Lưới tham số 2a (khóa trước khi chạy, không đổi giữa chừng)

```
n           ∈ {10, 20, 30, 50, 75, 100}
B           ∈ {2, 3, 4}
tw_width    ∈ {30, 60, 120, 240}   (phút)
n_drivers   ∈ {5, 10}   (giữ tỷ lệ GW:OD = 50:50)
seeds       ∈ {0..9}    (10 replicate mỗi ô lưới)
```

Tổng: 6 × 3 × 4 × 2 × 10 = **1440 lần chạy**. Nếu quá tốn thời gian ở n=100/tw=240,
cho phép timeout riêng (ví dụ 600s/instance) — instance timeout vẫn được **ghi nhận
là timeout**, không loại bỏ khỏi báo cáo.

## Đo, với mỗi lần chạy

```
- runtime_seconds (wall clock của DP)
- peak_frontier_size (số label tối đa đồng thời trong FRONTIER)
- total_states_generated (kể cả label sau này bị dominate)
- total_states_surviving (label còn lại sau dominance)
- survival_ratio = surviving / generated
- n_complete_bundles_found (kích thước |COMPLETE| cuối)
- theoretical_sequence_cap: tính (2k)!/2^k tổng trên các k thực tế xuất hiện, để so
  với total_states_generated (nếu DP đúng, phải nhỏ hơn nhiều)
- status: "completed" | "timeout"
```

## Gate 0 — bắt buộc chạy TRƯỚC khi tin bất kỳ số liệu n>7 nào

```
Chạy lại DP ở n ∈ {3,4,5,6,7}, B ∈ {2,3,4}, so với brute-force độc lập
(brute-force viết lại K/W từ công thức gốc, KHÔNG import chung code với DP,
đúng tinh thần Test6.1).

PASS = 0 vi phạm completeness (route_pool DP == route_pool brute-force,
        so theo Pareto-front (K,W) từng bundle).

Nếu dùng lại module Test6 nguyên vẹn và có log Test6.1 cũ chứng minh đã PASS
→ có thể skip, nhưng phải trích dẫn log cũ trong báo cáo, không được ngầm bỏ qua.
```

## Điều kiện dừng / báo cáo bắt buộc

- Nếu runtime hoặc peak_frontier_size tăng **siêu tuyến tính rõ rệt** trước n=50 (đặc
  biệt ở tw_width=240), đây là **kết quả**, ghi vào báo cáo dưới dạng "giới hạn thực
  nghiệm của B cố định", kèm đồ thị runtime-vs-n theo từng tw_width, không tìm cách vá
  bằng nới dominance.
- Nếu có instance timeout, báo cáo tỷ lệ timeout theo từng ô lưới — đừng lặng lẽ loại
  khỏi thống kê trung bình.

---

# PHẦN 2b — Đo phân phối kích thước component trên route pool thật

Chỉ chạy trên các instance ở 2a có `status = "completed"` (không dùng route pool từ
instance bị timeout — không đầy đủ).

## Build conflict graph

```
build_conflict_graph(route_pool):
    node = driver
    với mỗi cặp driver (i, k):
        nếu tồn tại route trong pool[i] và route trong pool[k]
            có chung ít nhất 1 order
        → thêm cạnh (i, k)
    # Dùng TOÀN BỘ route pool của mỗi driver, không chỉ route trong alloc* —
    # vì ở 2b chưa có Algorithm B/alloc*, và vì định nghĩa T5 (§2.2) cũng
    # dùng toàn bộ pool.
    return connected_components(graph)
```

## Biến cần quét thêm (mới so với 2a, vì đây là biến quyết định độ rời rạc component)

```
tau (detour budget của OD)  ∈ {10, 15, 20, 30, 45, 60}  phút
order_spatial_mode          ∈ {"dispersed", "clustered"}
    - dispersed: pickup/delivery rải ngẫu nhiên toàn vùng (parcel-like)
    - clustered: pickup gom quanh vài điểm cố định (meal-delivery-like,
      xem cảnh báo §12.6 đề cương — dùng để so sánh, KHÔNG dùng làm
      backbone chính nếu kết luận sau này chọn hướng parcel)
supply_ratio (n_drivers / n_orders) ∈ {0.3, 0.6, 1.0}
```

Khóa lưới này **TRƯỚC KHI CHẠY** — ghi vào file config có timestamp, không sửa sau
khi thấy kết quả đầu.

Vì đây là lưới mới (τ, spatial_mode, supply_ratio) nhân thêm vào các ô của 2a sẽ quá
lớn — **rút gọn**: chỉ chạy 2b trên một lát cắt cố định của 2a (ví dụ n=30, n=50, B=3,
tw_width=120 — chọn ô "trung bình", không chọn ô cực đoan), rồi quét đầy đủ (τ,
spatial_mode, supply_ratio) trên lát cắt đó, mỗi ô 10 seed.

```
Lưới 2b: n ∈ {30, 50}  ×  τ (6 giá trị)  ×  spatial_mode (2)  ×  supply_ratio (3)  ×  seeds (10)
       = 2 × 6 × 2 × 3 × 10 = 720 lần chạy
```

## Đo, với mỗi lần chạy

```
- n_components
- component_sizes: list đầy đủ (không chỉ median) — cần histogram
- largest_component_fraction = max(size) / n_drivers
- n_singleton_components (driver hoàn toàn cô lập, không cạnh tranh ai)
```

## Output bắt buộc

Một bảng hoặc heatmap: `largest_component_fraction` và `median(component_size)` là
hàm của (τ, spatial_mode, supply_ratio), giữ n cố định để so sánh công bằng.

## Kết luận cần rút ra (viết tường minh, đừng để ngầm hiểu)

- Nếu ở phần lớn vùng tham số hợp lý (τ ≤ 20–30 phút, dispersed, supply_ratio vừa
  phải) mà `largest_component_fraction` nhỏ (ví dụ < 0.3–0.5, không có ngưỡng cứng —
  báo cáo số thật) và có nhiều component → **hướng (A):** T5 có giá trị thực nghiệm,
  tiếp tục 2c/2d.
- Nếu component luôn gộp gần hết driver bất kể tham số → **hướng (B):** ghi nhận,
  không tiếp tục đầu tư 2c/2d ở mức độ đo speedup lớn, hạ kỳ vọng phần đóng góp T5
  xuống "correctness result".

**Cảnh báo lặp lại:** không rework/quét lại tham số cho tới khi thấy tín hiệu đẹp rồi
mới dừng — đây là lỗi đã xảy ra hai lần trong dự án (time window phi thực tế; release
spread chọn để đạt gate). Khóa lưới, chạy hết, báo cáo toàn bộ đường cong dù kết quả
ra sao.

---

## Cấu trúc thư mục đề xuất

```
spec_2a_2b/
  config/
    grid_2a.yaml       # lưới tham số 2a, có timestamp khi khóa
    grid_2b.yaml       # lưới tham số 2b, có timestamp khi khóa
  src/
    instance_gen.py
    dp_labeling.py     # tái dùng module Test6 nếu có, else viết theo spec trên
    brute_force.py     # cho Gate 0, độc lập với dp_labeling.py
    conflict_graph.py
    run_2a.py
    run_2b.py
  results/
    2a_raw/            # 1 file json/csv mỗi lần chạy, đủ để truy vết seed
    2a_summary.csv
    2b_raw/
    2b_summary.csv
  gate0_log.md         # kết quả Gate 0, hoặc trích dẫn log Test6.1 cũ
  report_2a_2b.md      # đồ thị + kết luận (A) hay (B), viết trung thực
```

---

## Việc KHÔNG được làm

- Không sửa dominance rule để "chạy nhanh hơn" ở n lớn.
- Không loại bỏ instance timeout khỏi thống kê mà không báo cáo.
- Không quét τ cho tới khi thấy component nhỏ rồi dừng — chạy hết lưới đã khóa.
- Không skip Gate 0 nếu code DP bị viết lại (dù chỉ một phần).
- Không tự ý đổi n_drivers hoặc supply_ratio giữa 2a và 2b mà không ghi rõ — hai phần
  dùng lưới khác nhau có chủ đích, không phải sơ suất.

---

## Sau khi hoàn thành

Khi có kết quả (`report_2a_2b.md` + summary CSV), gửi lại để đọc theo đúng khung
Gate/Validated/Rejected và quyết định hướng (A) hay (B) cho 2c/2d.