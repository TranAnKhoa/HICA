# Checklist chẩn đoán: vì sao largest_component_fraction ~0.999

> Mục tiêu: phân biệt 2 giả thuyết KHÔNG loại trừ lẫn nhau —
> **(H1) Pickup-clustering**: nhiều order dùng chung ít pickup node (kiểu backbone
> meal-delivery, đã cảnh báo ở §12.6 đề cương gốc) → driver chồng lấn vì đi qua cùng điểm.
> **(H2) Route-pool richness**: route pool của Algorithm A quá giàu (hàng nghìn-triệu bundle/
> driver) → xác suất chồng lấn ngẫu nhiên giữa 2 driver bất kỳ đã đủ cao dù pickup phân tán
> tốt.
>
> Không cần chạy lại `run_2b_v2.py`. Toàn bộ số dưới đây tính được từ dữ liệu 2a/2b đã có
> (route pool + instance data đã sinh sẵn trên đĩa).

---

## A. Đo trực tiếp mức độ gom cụm pickup (kiểm H1) — làm trước tiên, rẻ nhất

### A1. Tỷ lệ node/order

```python
# Với MỖI instance đã sinh (không cần chạy DP lại, chỉ cần file instance)
n_orders = len(orders)
n_distinct_pickup_nodes = len(set(o.pickup_node for o in orders))
ratio = n_distinct_pickup_nodes / n_orders
```

**Cách đọc:**
- `ratio ≈ 1.0` (mỗi order gần như 1 pickup node riêng) → pickup ĐÃ phân tán tốt, H1 yếu.
- `ratio` thấp rõ rệt (ví dụ ≤ 0.5, tức trung bình ≥2 order/pickup node) → xác nhận gom cụm,
  H1 có cơ sở.

**Chạy trên toàn bộ 720 cell đã có** (rẻ, thuần đọc dữ liệu), báo cáo phân phối
(min/mean/max) theo `n`, `spatial_mode`, `supply_ratio` — xem có cell nào lệch hẳn không.

### A2. Phân phối order/pickup-node (chi tiết hơn A1)

```python
from collections import Counter
pickup_counts = Counter(o.pickup_node for o in orders)
# In ra: max(pickup_counts.values()), và histogram
# Nếu top 1-2 node chiếm >30-40% tổng order -> gom cụm mạnh (giống nhà hàng hot)
```

### A3. Đối chiếu trực tiếp với 18 cell lệch đã tìm được ở báo cáo trước

Lấy đúng 18 cell có `lcf < 1.000` (tất cả đều τ=30) — so `ratio` (A1) của các cell NÀY với
`ratio` trung bình của 702 cell còn lại (`lcf = 1.000`). Nếu 18 cell lệch có `ratio` cao hơn
rõ rệt (pickup phân tán hơn) — đây là bằng chứng trực tiếp, không cần suy luận gián tiếp,
rằng pickup-clustering là biến số điều khiển lcf.

---

## B. Đo route-pool richness (kiểm H2) — cũng rẻ, dùng lại số đã có

### B1. Route pool size trung bình / driver, tại đúng các cell đã chạy 2b

```python
# Từ route_pool đã sinh bởi Algorithm A cho mỗi driver trong cell
avg_pool_size = mean(len(route_pool[driver]) for driver in drivers)
```

Đối chiếu `avg_pool_size` với `lcf` trên cùng 720 cell — vẽ scatter hoặc tính correlation
đơn giản (Pearson/Spearman). Nếu `avg_pool_size` và `lcf` tương quan dương rõ (pool càng
lớn, lcf càng cao, kể cả khi `ratio` ở mục A1 giữ nguyên) → H2 có cơ sở độc lập với H1.

### B2. Xác suất chồng lấn kỳ vọng theo mô hình ngẫu nhiên đơn giản (sanity bound)

Tính thử: nếu mỗi route trong pool của 1 driver chọn ngẫu nhiên `B` order trong tổng `n`
order (mô hình rất thô, chỉ để có cận so sánh), xác suất 2 driver có route pool giao nhau
≥1 order là bao nhiêu, với `avg_pool_size` đã đo? So con số lý thuyết thô này với `lcf` thật
— nếu order-of-magnitude khớp, củng cố H2 (chồng lấn là hệ quả thống kê tự nhiên của pool
lớn, không cần cơ chế địa lý gì đặc biệt).

---

## C. Nếu cả A và B đều không giải thích được rõ ràng — kiểm thêm

### C1. τ là biến chính hay biến phụ?

18 cell lệch đều ở τ=30 (nhỏ nhất lưới). Kiểm xem trong ĐÚNG 18 cell này, driver bị cô lập
có đặc điểm gì khác biệt (vị trí xuất phát xa nhất? route pool nhỏ nhất?) — dùng để xác nhận
cơ chế "τ nhỏ → route ngắn hơn → ít cơ hội chồng lấn" có nhất quán ở mức cá nhân driver,
không chỉ ở mức tổng.

### C2. Kiểm chéo giữa `dispersed` và `clustered` — có thực sự đổi được gì không?

Vì nghi ngờ ban đầu là "2 spatial_mode hiện tại không đổi được biến quan trọng", đối chiếu
trực tiếp: so `ratio` (A1) của `dispersed` vs `clustered` trên cùng n, cùng seed. Nếu hai
mode cho `ratio` gần như giống hệt nhau → xác nhận nghi ngờ: `spatial_mode` hiện tại chỉ đổi
vị trí driver, KHÔNG đổi mức độ gom cụm pickup — đúng lỗ hổng đã nêu trong thảo luận.

---

## D. Việc độc lập, không phụ thuộc kết quả A/B/C — thử nhanh warm-start

Không cần chờ chẩn đoán trên xong. Đo trên route pool đã có sẵn của 1-2 cell bất kỳ (kể cả
cell lcf≈1):

1. Lấy Algorithm C hiện tại (naive: xoá driver, giải lại từ đầu).
2. Thử bản warm-start basis/incumbent đơn giản nhất có thể: dùng lời giải Z* gốc làm
   incumbent/starting basis cho từng lần giải removal (tuỳ solver có hỗ trợ warm-start
   basis hay không — CPLEX/CBC đều có API cho việc này).
3. Đo runtime naive vs warm-start trên cùng driver set, **không cần connected component
   nhỏ** — đây là phép thử độc lập, không phụ thuộc lcf.
4. Gate bắt buộc như mọi lần: payment kết quả phải khớp naive ≤ 1e-6.

**Mục đích:** biết ngay có hướng tăng tốc thứ hai khả dụng hay không, phòng trường hợp A/B/C
xác nhận component decomposition vô dụng ở dữ liệu thực tế.

---

## E. Báo cáo lại — cần những con số gì

Khi quay lại, cần các bảng/số sau để đưa ra kết luận:

1. Bảng `ratio` (A1) theo n / spatial_mode / supply_ratio — đặc biệt so sánh `dispersed` vs
   `clustered` (mục C2).
2. `ratio` của 18 cell lệch vs 702 cell còn lại (mục A3).
3. Correlation `avg_pool_size` vs `lcf` (mục B1), cộng cận lý thuyết thô (mục B2).
4. Kết quả warm-start (mục D): runtime ratio + gate correctness.

Dựa trên (1)+(2)+(3), sẽ có đủ căn cứ trả lời dứt điểm: nguyên nhân lcf cao là do backbone
pickup-clustering (sửa được bằng đổi backbone dữ liệu, đăng ký trước theo §12.6), do
route-pool richness (không sửa bằng đổi backbone, cần hướng tăng tốc khác như warm-start),
hay cả hai cộng hưởng.