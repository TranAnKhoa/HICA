# Patch bắt buộc — Sửa lỗi OD feasibility trong `instance_gen.py` & chạy lại toàn bộ pipeline

## Bối cảnh — vì sao đây không phải một việc nhỏ

Toàn bộ kết luận đã có cho tới nay (`report_2a_2b.md`, `report_2a_2b_addition_1.md`,
`report_2a_2b_full.md`, và báo cáo đo speedup thật bằng CPLEX) đều dựa trên dữ liệu
sinh từ `instance_gen.py` — bộ sinh dữ liệu **dùng chung** cho mọi script:
`run_2a.py`, `run_2b.py`, `run_2b_B2.py`, `probe_scaling.py`, `run_gate0.py`, và
`viec_extra_real_wdp_speedup.py`.

Báo cáo đo speedup thật vừa xác nhận: **81.8% driver OD trong toàn bộ dữ liệu có route
pool RỖNG** — vì pickup/delivery của OD được rải ngẫu nhiên toàn bản đồ thay vì quanh
đoạn đường tự nhiên (start→home) của họ, khiến hầu hết route vi phạm hạn chót
`deadline_home = t0 + direct_time + tau`.

**Đây chính xác là lỗi đã từng gặp và đã từng sửa** ở `t2_gen.py` (Test2, patch "Việc
1" — neo `ready_time` theo `t0`/`tau`, cộng thêm corridor bias cho vị trí pickup/
delivery). Khi viết `instance_gen.py` mới cho vòng test quy mô lớn (n tới 100, hộp
20×20km, n_drivers độc lập), fix này **không được mang sang**.

**Hệ quả:** mọi kết luận "Hướng (B)" hiện tại thực chất được rút ra từ dữ liệu mà driver
OD gần như vắng mặt — tức là gần như chỉ đo cấu trúc route pool của riêng GW. Không biết
kết luận sẽ đổi thế nào cho tới khi sửa và chạy lại toàn bộ.

## Nguyên tắc bắt buộc trước khi bắt tay vào sửa

- **Sửa đúng một chỗ — `instance_gen.py`** — không sửa `dp_labeling.py`, không sửa
  dominance rule, không sửa `conflict_graph.py`. Đây là lỗi ở khâu sinh dữ liệu đầu vào,
  không phải lỗi thuật toán.
- **Không tinh chỉnh tham số corridor bias để "ra số đẹp".** Chọn một giá trị hợp lý
  (ví dụ theo đúng gợi ý của patch cũ: 70% điểm trong buffer quanh corridor, 30% ngẫu
  nhiên toàn vùng), ghi rõ đây là **giả định thiết kế**, khóa nó, rồi chạy — không đổi
  qua đổi lại tỷ lệ cho tới khi thấy feasibility rate "đẹp".
- **Chạy lại Gate 0 trước tiên**, vì generator đổi = phải xác nhận lại DP vẫn đúng trên
  dữ liệu mới, trước khi tin bất kỳ số liệu quy mô lớn nào.
- **Toàn bộ pipeline phải chạy lại** — không chỉ 2b, vì 2a (giới hạn B của DP) cũng dùng
  chung generator này; nếu OD giờ có route pool khác 0, kích thước route pool của mỗi
  driver sẽ đổi, kéo theo runtime/peak-frontier của Phần A cũng có thể đổi.

---

## Việc 1 — Sửa `instance_gen.py`

### 1.1 Neo `ready_time` theo `t0`/`tau` (bắt buộc, đã có công thức sẵn từ patch cũ)

```python
# Trong hàm sinh order cho driver OD (áp dụng cho từng order mà driver OD reachable):
ready_time_pickup = t0 + random.uniform(0, tau)
deadline_pickup    = ready_time_pickup + tw_width   # giữ nguyên công thức tw hiện có
```

Không đổi công thức `tw_width` hay cách sinh time window của order — chỉ đổi cách neo
điểm bắt đầu của time window theo `t0`/`tau` của driver OD đang xét, đúng như patch cũ.

**Lưu ý quan trọng khác với Test2 gốc:** ở `instance_gen.py` mới, order là chung cho cả
GW và OD (không sinh riêng theo từng loại driver như `t2_gen.py`) — vì `n_drivers` và
`n_orders` độc lập, một order có thể "reachable" bởi cả GW và OD. Cách xử lý đúng: giữ
time window của order **cố định, không phụ thuộc driver nào** (như hiện tại), nhưng khi
tính feasibility cho một driver OD cụ thể, **không sửa time window của order** — thay
vào đó áp dụng đúng những gì patch cũ đề xuất ở mức **vị trí order** (§1.2 dưới đây), vì
đó mới là biến quyết định driver OD có "chạm" được order hay không mà không cần sửa time
window chung.

### 1.2 Corridor bias cho vị trí pickup/delivery (bắt buộc nếu chỉ sửa 1.1 chưa đủ)

Chạy `feasibility_rate_k1` (xem Việc 2) sau khi chỉ sửa 1.1. Nếu vẫn dưới ngưỡng 50% ở
tau nhỏ (10-20 phút) — rất có khả năng, vì bản chất hộp 20×20km khiến khoảng cách trung
bình giữa 2 điểm ngẫu nhiên đã lớn hơn nhiều so với detour budget nhỏ — thêm bias:

```python
CORRIDOR_SHARE = 0.7        # tỷ lệ order đặt gần corridor — GIẢ ĐỊNH THIẾT KẾ, khóa trước
CORRIDOR_BUFFER_KM = 3.0    # bề rộng vùng đệm quanh đoạn thẳng start->home

def sample_order_location(driver_od, corridor_share=CORRIDOR_SHARE,
                           buffer_km=CORRIDOR_BUFFER_KM):
    if random.random() < corridor_share:
        # lấy điểm ngẫu nhiên trên đoạn thẳng start->home, rồi lệch vuông góc
        # trong khoảng [-buffer_km, +buffer_km]
        t = random.uniform(0, 1)
        base = lerp(driver_od.start, driver_od.home, t)
        perp_offset = random.uniform(-buffer_km, buffer_km)
        return offset_perpendicular(base, driver_od.start, driver_od.home, perp_offset)
    else:
        return sample_uniform_in_box()   # như cũ, 20x20km toàn vùng
```

**Ghi rõ tỷ lệ 70/30 này vào report** như một giả định thiết kế — không phải tham số
trung lập được đo từ đâu đó, đúng như patch cũ đã nhắc.

**Vấn đề cần quyết định trước khi code:** vì một order giờ dùng chung cho cả GW và OD
(khác Test2 — nơi mỗi class có generator order riêng), corridor bias **chỉ nên áp dụng
khi sinh vị trí ban đầu của TOÀN BỘ order** theo một cách trộn hợp lý — ví dụ: với xác
suất `CORRIDOR_SHARE`, chọn ngẫu nhiên MỘT driver OD trong instance, đặt order quanh
corridor của driver đó; ngược lại đặt ngẫu nhiên toàn vùng như cũ. Cách này giữ order
vẫn "chung", không thiên vị tuyệt đối cho một driver OD cụ thể, nhưng vẫn tạo đủ order
nằm gần corridor của ít nhất một vài OD để họ có route khả thi.

### 1.3 Không đổi phần sinh dữ liệu của GW

GW không có `home`/`tau`, không bị ảnh hưởng bởi lỗi này — giữ nguyên cách sinh vị trí
bắt đầu và time window của GW như hiện tại.

---

## Việc 2 — Gate feasibility bắt buộc, chạy ngay sau khi sửa, trước khi đụng vào pipeline lớn

### Thủ tục

Với mỗi tổ hợp `(tau, spatial_mode, supply_ratio)` trong lưới đã dùng ở 2b (không cần
lưới mới — dùng lại `grid_2b.yaml`), sinh vài instance mẫu (10 seed đủ), và tính:

```python
feasibility_rate_k1 = (
    số order mà driver OD reachable với bundle size k=1 (chỉ 1 order)
    / tổng số order mà driver OD "trong tầm" xét thô (trước feasibility check)
)
```

Tính bằng cách brute-force kiểm từng cặp (driver OD, order) riêng lẻ — không cần chạy
DP, chỉ cần kiểm 1 phép tính đơn giản: `pickup → deliver → home` có kịp deadline không.

### Ngưỡng bắt buộc (khóa trước khi xem số)

```
assert feasibility_rate_k1 >= 0.5
```

In bảng `feasibility_rate_k1` theo `tau` (giống patch cũ yêu cầu). Nếu vẫn dưới 50% sau
khi đã áp cả 1.1 và 1.2 → còn nguyên nhân khác chưa tìm ra, **dừng lại, không chạy tiếp
pipeline lớn**, quay lại xem hộp 20×20km có quá lớn so với tau đang xét hay không (có
thể cần giảm kích thước hộp, hoặc tăng tau tối thiểu trong lưới — đây là điều chỉnh
tham số instance, không phải bug, nhưng cần quyết định có chủ đích, ghi rõ lý do).

### So sánh bắt buộc

In bảng `feasibility_rate_k1` **trước và sau patch**, cạnh nhau theo từng `tau` — đúng
yêu cầu "đối chiếu bảng feasibility k=1 mới với bảng cũ" của patch gốc. Đây là bằng
chứng trực tiếp cho thấy patch có tác dụng, cần đưa vào phần "sai lệch/sửa lỗi" của
report cuối.

---

## Việc 3 — Chạy lại Gate 0 (bắt buộc, generator đã đổi)

Y nguyên thủ tục Gate 0 đã dùng trước đó (n∈{3..7}, B∈{2,3,4}, so DP với brute-force độc
lập) — nhưng giờ chạy trên `instance_gen.py` **đã sửa**. Không skip bước này dù logic DP
không đổi — vì input mà DP nhận (route pool khả thi của OD) sẽ khác hẳn trước, cần xác
nhận lại completeness trên chính loại dữ liệu mới này.

```
PASS = 0/180 vi phạm (giữ nguyên cấu trúc lưới Gate 0 cũ)
```

---

## Việc 4 — Sửa luôn bug seed không ổn định (nhân tiện, cùng một đợt sửa code)

Đã phát hiện ở báo cáo đo speedup thật: `hash()` của Python không ổn định xuyên tiến
trình → mọi seed dùng `hash((...)) & 0x7FFFFFFF` không tái tạo được đúng.

**Sửa một lần cho tất cả script** (`run_2a.py`, `run_2b.py`, `run_2b_B2.py`,
`probe_scaling.py`, `run_gate0.py`) — thay bằng hàm ổn định đã có sẵn mẫu
(`stable_seed()` dựa `hashlib.sha256`, đã dùng trong `viec_extra_real_wdp_speedup.py`):

```python
import hashlib

def stable_seed(*args) -> int:
    s = "|".join(str(a) for a in args)
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) & 0x7FFFFFFF
```

Thay mọi chỗ `gen_seed = hash((n, tau, mode, sr, seed, "spec2b")) & 0x7FFFFFFF` thành
`gen_seed = stable_seed(n, tau, mode, sr, seed, "spec2b")`. Làm việc này **cùng lúc** với
việc sửa generator (Việc 1) để không phải chạy lại pipeline hai lần.

---

## Việc 5 — Chạy lại toàn bộ pipeline theo đúng thứ tự cũ

Không có gì thay đổi về cấu trúc lưới hay quy trình — chỉ chạy lại với `instance_gen.py`
đã sửa + seed đã ổn định:

```
1. run_gate0.py          → xác nhận 0/180 (Việc 3)
2. run_2a.py              → lưới 2a như cũ (1440 ô), CHÚ Ý runtime/peak-frontier có thể
                             đổi vì OD giờ có route pool thật, không còn rỗng
3. run_2b.py               → lưới 2b B=3 như cũ (720 ô)
4. run_2b_B2.py              → lưới 2b B=2 như cũ (720 ô)
5. probe_scaling.py           → curve n tới 100 như cũ
6. viec1_speedup_estimate.py   → ước lượng đại số lại, trên component graph MỚI
7. viec_extra_real_wdp_speedup.py → đo speedup thật lại bằng CPLEX, trên route pool MỚI
```

**Không rút gọn lưới ở lần chạy lại này** — vì đây là lần chạy quyết định (dữ liệu cũ đã
biết là sai), cần độ phủ đầy đủ ngay từ đầu nếu tài nguyên máy cho phép, để tránh phải
lặp lại chu trình "báo cáo bộ phận → phát hiện thiếu → chạy bổ sung" thêm một lần nữa.

## Việc 6 — Đọc và so sánh kết quả mới với kết quả cũ, không thay thế lặng lẽ

Khi có kết quả mới, viết report theo đúng cấu trúc cũ nhưng **thêm một bảng so sánh
trực tiếp**: `largest_component_fraction`, tỷ lệ OD có route pool rỗng, và speedup thật
đo bằng CPLEX — cột "trước patch" và "sau patch" cạnh nhau. Đây là bằng chứng cho thấy
patch có tác dụng thực sự, và là tài liệu quan trọng để giải thích trong thesis tại sao
kết luận thay đổi (nếu có) hoặc vì sao vẫn giữ nguyên (nếu Hướng B vẫn đúng dù OD giờ có
route thật).

**Không viết đè lên báo cáo cũ và xóa nó đi** — giữ cả report cũ (đánh dấu rõ "dữ liệu có
bug OD, đã phát hiện và sửa ở phiên sau") và report mới, để có dấu vết đầy đủ của quá
trình nghiên cứu — đúng tinh thần Proven/Validated/Rejected/[đã sửa] đã áp dụng xuyên
suốt dự án.

---

## Việc KHÔNG được làm

- Không chỉnh `CORRIDOR_SHARE`/`CORRIDOR_BUFFER_KM` nhiều lần cho tới khi thấy
  `feasibility_rate_k1` "đẹp" rồi dừng — chọn giá trị hợp lý, khóa, chạy, báo cáo thật.
- Không chạy lại một phần pipeline (ví dụ chỉ 2b) rồi giữ nguyên phần khác (2a) từ dữ
  liệu cũ — vì generator đổi ảnh hưởng đến toàn bộ, không chỉ phần liên quan trực tiếp
  đến OD component.
- Không âm thầm xóa/ghi đè báo cáo cũ — giữ lại làm dấu vết, đánh dấu rõ trạng thái.
- Không bỏ qua Gate 0 dù tin rằng "DP logic không đổi" — generator đổi nghĩa là input
  cho DP đổi, luôn cần xác nhận lại completeness trên dữ liệu mới.

---

## Sau khi hoàn thành

Gửi lại: (1) bảng feasibility_rate_k1 trước/sau patch theo tau, (2) kết quả Gate 0 mới,
(3) bảng so sánh largest_component_fraction và speedup thật trước/sau patch. Đây sẽ là
cơ sở để quyết định kết luận cuối cùng cho phần T5 trong thesis.