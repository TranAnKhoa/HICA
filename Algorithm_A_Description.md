# Algorithm A — Mô tả chi tiết (bản đang chạy trong pipeline `spec_2a_2b`)

> Tài liệu này mô tả **chính xác thuật toán đang thực thi thật** trong pipeline hiện tại
> (`run_2a_stepB.py`, `run_2b_v2.py`, Gate 0, Gate T4-B), dựa trên đọc trực tiếp code —
> không suy đoán, không mô tả theo lý thuyết chưa cài đặt.
>
> Các file nguồn liên quan:
> - `experiments/T2BFS/t6_dp.py` — lõi DP (module gốc "Test6", tái dùng nguyên vẹn)
> - `spec_2a_2b/src/dp_labeling.py` — lớp gọi (chọn B_gw/B_od, đóng gói route pool)
> - `spec_2a_2b/src/instance_gen.py` — sinh instance + precompute PCF (`build_compat_graph`)
> - `spec_2a_2b/src/brute_force.py` — oracle đối chiếu (dùng cho Gate 0 / Gate T4-B)

---

## 1. Algorithm A là gì, trong ngữ cảnh nào

Algorithm A là bước **sinh route pool** (route/bundle generation) cho từng tài xế: với một
tập order công khai và một tài xế cụ thể, liệt kê **mọi bundle order khả thi** (mọi tập con
order mà tài xế có thể phục vụ trong 1 route hợp lệ), và với mỗi bundle giữ lại **Pareto
front** các cặp chi phí (K, W) — không giữ toàn bộ route cụ thể, chỉ giữ các điểm không bị
thống trị (dominate) trên 2 chiều chi phí.

Route pool này là đầu vào cho bước phân bổ/đấu giá (VCG) phía sau — **Algorithm A không đọc
bid, không tối ưu hoá phân bổ**, nó thuần tuý là bước liệt kê route khả thi + chi phí.

Về mặt lý thuyết luận văn, Algorithm A tương ứng với **Test6 — forward label-setting DP**
(đã được xác nhận là kết quả tốt nhất, thay thế các phương án trước đó là Test3/Test4/Test5).
**Đây không phải** là "T4" trong `experiments/T4/` (MST/1-tree lower-bound diagnostic của
Test1.md — file đó tự ghi chú "Khong OD", không liên quan), và **cũng không phải** là công
thức `LB_detour(S) ≥ 2·min dist(corridor, j)` ở §7.3/§16.2 của `Master_Thesis_Q1.md` (công
thức đó được liệt kê là **"bài toán mở của thesis — cần chứng minh"**, chưa được cài đặt).

---

## 2. Ý tưởng cốt lõi: DP nhãn tiến (forward label-setting)

Thay vì liệt kê **mọi hoán vị pickup/delivery hợp lệ** rồi kiểm tra khả thi từng cái (cách
làm brute-force, chi phí `(2k)!/2^k` hoán vị cho bundle kích thước k — xem bảng ở §7.3 thesis:
k=4 đã là 2,520 hoán vị/bundle), Algorithm A xây route **tăng dần theo thời gian**, giữ lại
tại mỗi bước chỉ những "nhãn" (label) không bị nhãn khác thống trị — nhờ đó không phải mở
rộng lại các nhánh chắc chắn thua kém.

### 2.1 Định nghĩa nhãn (Label)

```
Label = (v, IV, C, t, K, W)
  v  = node hiện tại của tài xế
  IV = tập order đang mang trên xe (đã pickup, chưa delivery)
  C  = tập order đã giao xong (cả pickup lẫn delivery)
  t  = thời điểm hiện tại (SAU service_time tại v)
  K  = kappa × quãng đường tích lũy THÔ (chưa trừ phần đường đi thẳng cho OD)
  W  = thời lượng tích lũy THÔ (active_time = t − t0)
```

`K` và `W` đều là đại lượng cần **minimize** (không phải maximize) — đây là 2 trục chi phí
của route, dùng để so sánh Pareto giữa các route khác nhau cho cùng một bundle.

### 2.2 Ràng buộc capacity

`|IV| + |C| ≤ B` tại mọi thời điểm — B ở đây là **cận cứng số order tối đa một route được
mang** (không phải cận thống kê, là ràng buộc capacity thật của driver).

### 2.3 Điều kiện "nhãn hoàn chỉnh" — khác nhau giữa GW và OD

- **GW (gigworker, open-route):** hoàn chỉnh khi `IV = ∅` (đã giao hết) và `1 ≤ |C| ≤ B`.
  Không cần quay về đâu cả — route "mở", kết thúc tại điểm giao hàng cuối cùng.
- **OD (occasional driver, home-terminating):** phải ghé qua node `home` sau khi `IV = ∅`.
  Hoàn chỉnh khi `v = home` và `IV = ∅`.

Đây chính là điểm khác biệt cấu trúc giữa 2 lớp tài xế mà thuật toán phải xử lý minh bạch
(GW không có "điểm neo" bắt buộc phải quay về, OD có).

### 2.4 3 phép chuyển trạng thái (transition)

1. **Pickup order j** (`_try_pickup`): chỉ hợp lệ nếu `j` chưa nằm trong `IV`/`C`, và
   `|IV|+|C| < B`. Kiểm tra time-window tại điểm pickup (`Bt ≤ p.l`), cộng dồn K/W.
2. **Delivery order j** (`_try_delivery`): chỉ hợp lệ nếu `j ∈ IV`. Kiểm tra time-window tại
   điểm giao, cộng dồn K/W, chuyển j từ `IV` sang `C`.
3. **Về home** (`_try_home`, chỉ áp dụng cho OD): chỉ hợp lệ khi `IV = ∅`. Đây là nhãn lá,
   không mở rộng tiếp.

### 2.5 Dominance — cơ chế cắt tỉa chính

Hai nhãn cùng "key" `(v, IV, C)` (cùng vị trí, cùng tập đang mang, cùng tập đã giao) được so
sánh: nhãn `a` **thống trị** nhãn `b` nếu `t_a ≤ t_b`, `K_a ≤ K_b`, `W_a ≤ W_b`, và **ít nhất
một bất đẳng thức là chặt**. Nhãn bị thống trị bị loại ngay — không mở rộng tiếp từ nó.

Đây là dominance **chính xác theo ID node** (không phải theo toạ độ hình học/khoảng cách xấp
xỉ) — điểm này đã được xác minh (qua Test6.1/Test6.2, xem `test4-fwdslack-inprogress.md`
trong bộ nhớ) là **miễn nhiễm** với lỗi "hidden diagonal shortcut" từng làm hỏng dominance của
Test3/Test4 trong không gian 2D.

### 2.6 Xử lý theo "round" — vì sao đúng đắn

Đồ thị trạng thái là DAG theo `|IV|+|C|` (không giảm qua pickup/delivery, luôn tăng qua
home vì home là nút lá). Thuật toán xử lý **theo round tăng dần** `touched = 0, 1, ..., B`:

- Trong mỗi round, có một **closure con**: lặp lại delivery/home cho đến khi bão hoà (vì
  delivery không làm tăng `touched`, nhiều delivery liên tiếp có thể xảy ra trong cùng round).
- Dominance được áp dụng **ngay sau mỗi closure**, trên các nhãn vừa sinh — không phải lọc
  một lần ở cuối. Điều này đảm bảo nhãn bị thống trị không bao giờ được dùng làm nguồn cho
  round tiếp theo (tránh lãng phí tính toán trên nhánh chắc chắn thua).
- Sau closure, mới thực hiện **pickup** để sinh sang round `touched+1`.

### 2.7 Hoàn tất chi phí cho OD — trừ đường đi thẳng

`K`, `W` tích luỹ trong nhãn là giá trị **thô** (chưa trừ gì). Chỉ khi một nhãn **hoàn
chỉnh**, hàm `finalize_KW` mới áp dụng phép trừ **một lần duy nhất** cho OD:

```
K_final = max(0, K_raw − kappa × direct_distance)
W_final = max(0, (W_raw − direct_time) / 60)
```

Tức là "chi phí thật" (detour) của OD = tổng chi phí route − chi phí nếu đi thẳng từ điểm
xuất phát về nhà. Với GW không có bước trừ này (không có "đường đi thẳng" tham chiếu).

---

## 3. Bộ lọc bổ sung: Pairwise Compatibility Filter (PCF) — mới trong new03.md

PCF là một **điều kiện cần (không đủ)** được thêm vào bước pickup để cắt nhánh sớm hơn nữa,
áp dụng cho **cả GW lẫn OD** (không phân biệt driver class trong compat_graph — graph này
tính chung cho toàn instance, độc lập driver).

### 3.1 Precompute (`build_compat_graph`, chạy 1 lần/instance)

Với mỗi cặp order `(i, j)`, thử **cả 6 thứ tự hợp lệ** (thoả ràng buộc pickup-trước-delivery
của từng đơn: `Pi<Di`, `Pj<Dj`):

```
Pi Di Pj Dj | Pj Dj Pi Di | Pi Pj Di Dj | Pi Pj Dj Di | Pj Pi Di Dj | Pj Pi Dj Di
```

Điểm xuất phát giả định = pickup sớm nhất trong 2 đơn (không gắn với driver cụ thể nào — đây
là tính chất **chung cho cả instance**, dùng lại cho mọi driver). Nếu **ít nhất 1 trong 6**
thứ tự thoả mãn time-window liên tục thì cặp `(i,j)` được đánh dấu **tương thích** (`True`).
Nếu **cả 6 đều vi phạm** time-window ở đâu đó, cặp bị đánh dấu **không tương thích**
(`False`) — và về mặt toán học (dùng bất đẳng thức tam giác, đã kiểm chứng), **không bundle
nào chứa cả i và j có thể khả thi**.

### 3.2 Áp dụng trong DP (`_try_pickup`)

Khi cố pickup order `j` vào một nhãn đang mang `IV ∪ C`, nếu có `compat_graph`, thuật toán
kiểm tra **`j` phải tương thích với TẤT CẢ order hiện có trong `IV` và `C`** trước khi cho
phép pickup — nếu không, từ chối ngay (không cần tính time-window thật, tiết kiệm một bước
kiểm tra tốn kém hơn).

### 3.3 Bản chất: cần nhưng không đủ

PCF **không thay thế** feasibility check hiện có (time-window thật vẫn được kiểm tra như
bình thường ngay sau đó) — nó chỉ là một bộ lọc cắt nhánh sớm, dựa trên tính **di truyền
(hereditary)** của tính khả thi dưới bất đẳng thức tam giác: nếu bundle kích thước k khả thi
thì mọi tập con của nó cũng khả thi; do đó nếu một cặp bất kỳ trong bundle không khả thi
(theo cả 6 thứ tự), bundle chứa cặp đó chắc chắn không khả thi.

### 3.4 Phát hiện thực nghiệm quan trọng (new03.md Việc 2.0/2.4)

- Đo `pair_infeasibility_rate` tách theo driver class: **GW = 0.00%** ở mọi tổ hợp tham số
  đã thử (PCF không có gì để cắt cho GW), **OD = 86–96%** (nhưng OD vốn đã có ràng buộc τ
  làm "neo" riêng, ít cần PCF theo đúng tinh thần thiết kế ban đầu của PCF).
- Đo lợi ích thật (runtime, peak_frontier_size, PCF bật/tắt) trên cùng tham số: tỷ lệ
  runtime (PCF-on / PCF-off) trung bình **~1.0–1.1×** — tức PCF **không giúp tăng tốc**, đôi
  khi còn **chậm hơn nhẹ** do chi phí tra `compat_graph` ở mỗi lần thử pickup vượt quá lợi
  ích cắt nhánh thực tế thu được.
- Kết luận: PCF là một nỗ lực hợp lý về mặt lý thuyết (điều kiện cần, đúng đắn, đã được Gate
  T4-B xác nhận không làm mất bundle hợp lệ nào), nhưng **không mang lại lợi ích tốc độ đo
  được** trong không gian tham số đã khảo sát — bài toán mở "bound cho open-route bundle
  generation" (§7.3 thesis) vẫn **chưa được giải quyết** theo hướng này.

---

## 4. Tham số B tách lớp: B_gw và B_od (new03.md Việc 1)

Trước đây (bản gốc/2a cũ) dùng **một giá trị B chung** cho mọi driver. Bản hiện tại tách
riêng:

- **B_od**: cận capacity cho tài xế OD. Vì OD đã bị ràng buộc chặt bởi τ (ngân sách detour),
  bundle OD lớn gần như không có ý nghĩa thực tế (khả năng khả thi giảm rất nhanh) — nên
  B_od giữ nhỏ (thường B_od ∈ {1, 2} trong các lưới đo).
- **B_gw**: cận capacity cho tài xế GW. GW không có ràng buộc τ tương tự, nên cần khảo sát
  B_gw rộng hơn (B_gw ∈ {2, 3, 4, 5} trong lưới 2a Bước B hiện tại) để hiểu rõ đặc tính scale.

`dp_labeling.py::run_pool` chọn `B = B_gw if driver["cls"]=="GW" else B_od` **trước khi** gọi
`t6_dp.run_dp` — bản thân `t6_dp.py` **không tự đọc `driver["cls"]`** để chọn B, nó nhận một
giá trị B hiệu lực duy nhất cho mỗi lần gọi. Việc tách này **không ảnh hưởng DSIC/VCG** vì B
vẫn là tham số được công bố trước (pre-announced), không phụ thuộc bid.

---

## 5. Độ phức tạp thực nghiệm đã đo (2a Bước B, ndrv=10, dispersed)

| n | B_gw | Runtime/driver-set điển hình |
|---:|---:|---:|
| 20 | 2–3 | ~1–5s |
| 20 | 4 | ~15–145s |
| 20 | 5 | ~180–360s (đã chạm ngưỡng timeout 300s ở một số seed) |
| 30 | 4 | ~93–225s |
| 50–100 | 3 | vài chục đến vài trăm giây (tăng dần theo n) |
| 50–100 | 4–5 | **loại khỏi lưới** — xác nhận bùng nổ tổ hợp qua đo trực tiếp (n=7,B_gw=5 timeout >60s/driver ở Gate T4-B; ngoại suy n≥50,B_gw≥4 sẽ mất hàng nghìn giây/cell) |

Việc bùng nổ này **độc lập với PCF bật/tắt** — xác nhận rằng cắt nhánh theo cặp không đủ để
kiểm soát tăng trưởng tổ hợp khi B_gw lớn; đây chính là bài toán mở §7.3 của thesis còn để
ngỏ ("Cận dựa trên spanning structure" và "Dominance giữa các tập" được liệt kê là hướng ứng
viên nhưng chưa chứng minh/cài đặt).

---

## 6. Tóm tắt một câu

**Algorithm A hiện tại = DP nhãn tiến theo round (Test6), dominance chính xác theo
(node, tập-đang-mang, tập-đã-giao) trên 3 trục (t, K, W) minimize, cộng thêm một bộ lọc
tương thích cặp (PCF) làm điều kiện cần bổ sung ở bước pickup — đã được xác nhận đúng đắn
tuyệt đối (Gate T4-B: 0 vi phạm) nhưng PCF không cải thiện tốc độ đo được; bài toán cận dưới
mạnh cho GW (không có ràng buộc τ) vẫn là câu hỏi mở của thesis.**
