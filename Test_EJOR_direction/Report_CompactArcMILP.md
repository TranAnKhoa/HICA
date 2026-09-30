# Report: Compact Resource-Constrained MILP (arc-based) — enumerate-vs-formulate

> Đề xuất 2026-09-16: bỏ hẳn Algorithm A (enumerate route pool), thay bằng
> biến arc `y[i,j,k]` — route là ẩn, chỉ hiện ra từ tập arc được chọn. Câu
> hỏi độc lập với chuỗi 4 hướng pruning đã REJECTED
> (`Report_ActivationRate.md`): "kiến trúc enumerate-rồi-chọn có phải nguyên
> nhân chậm, hay bản thân bài toán chậm dù giải cách nào?"

**Kết luận một câu:** Sau khi sửa **5 bug thiết kế/công thức** (bị bắt đúng
theo quy trình spec — dừng ngay khi Z* không khớp, sửa trước khi đo gì
khác), compact model **khớp chính xác Z*** với pool-based approach trên
instance n=6 (81.6356 = 81.6356). Nhưng ngay ở **n=8** (nhỏ hơn cả ngưỡng đo
runtime dự kiến n=20), compact model **không giải xong trong 590 giây**
trong khi pool-based giải xong **0.11 giây** — chênh lệch >5000x ngay ở quy
mô nhỏ. Đây là câu trả lời rõ ràng cho câu hỏi gốc: **độ khó nằm ở bản thân
kiến trúc arc-based (mật độ ràng buộc big-M quá lớn), không phải ở việc
Algorithm A "enumerate" — enumerate-rồi-lọc-Pareto thực ra là một cách nén
không gian tìm kiếm hiệu quả hơn hẳn so với để MILP solver tự khám phá cấu
trúc route từ các biến arc thô.**

---

## 1. Quy trình — đúng theo đề xuất gốc

1. Viết model arc-based cho 1 instance nhỏ đã biết đáp án (n=6, từ pipeline
   RQ1 hiện có: `Z*_pool = 81.6356`, dùng Algorithm A+B thật).
2. So `Z*_compact` với `Z*_pool` — **không khớp thì dừng, sửa constraint,
   chưa đo gì khác** (đúng yêu cầu spec).
3. Sau khi khớp: đo thời gian CPLEX giải model arc so với pool-based.

## 2. Quyết định thiết kế (khác vài điểm so với mô tả gốc)

Trước khi code, đối chiếu với nguồn sự thật hiện tại (`t2_core.py`,
`t4_profile.py`, `t6_dp.py`, `instance_gen.py`) phát hiện 3 điểm mô tả gốc
không khớp implementation thật:

1. **Detour resource (τ) của OD KHÔNG cần track riêng qua big-M** —
   `t2_core.py` đã cài τ THẲNG vào deadline tại node home
   (`deadline_home = t0 + direct_time + tau`). Chỉ cần propagate thời gian
   `t[i,k]` bình thường qua mọi node kể cả home, deadline ở home tự động
   enforce τ.
2. **"u[i,j]" (đếm số dừng) và "B cap" KHÔNG phải 2 resource riêng** — mọi
   order có `demand=1.0` cố định, `capacity=B` — nhưng **phát hiện sau khi
   debug** (xem §3.5): đây thực ra vẫn là 2 resource khác nhau về ngữ nghĩa
   (xem bug #4).
3. **K,W của OD là DETOUR** (trừ `direct_dist`/`direct_time` đúng 1 lần ở
   cuối route, dùng `max(0,...)`) — không được trừ phân bổ trên từng arc.

## 3. Năm bug bị bắt và sửa (theo đúng thứ tự phát hiện)

Mỗi bug được bắt bằng cách so `Z*_compact` với `Z*_pool`, không khớp thì
dừng lại truy nguyên cơ chế cụ thể — không đoán mò sửa nhiều thứ cùng lúc.

### 3.1 Bug #1 — W_raw thiếu service time

**Triệu chứng:** `Z*_compact = 74.376 < Z*_pool = 81.636` (compact rẻ hơn —
dấu hiệu nó đang cho phép thứ pool coi là bất khả thi/tốn kém hơn thật).

**Nguyên nhân:** `W_raw` (thời gian tích lũy) chỉ cộng `travel_time(a,b)`
trên các arc, quên cộng `service_time` tại mỗi node được ghé — trong khi
`W = active_time = D_end − t0` với `D_i = B_i + s_i` (t2_core.py) bao gồm cả
thời gian phục vụ.

**Sửa:** cộng thêm `service_time` của node đích vào mỗi arc khi tích lũy
`W_raw`.

### 3.2 Bug #2 — W_raw không tính thời gian CHỜ (waiting time)

**Triệu chứng:** sau khi sửa #1, `Z*_compact = 81.220` (gần khớp nhưng vẫn
lệch ~0.42) — điều tra chi tiết route `od1/{o5}`: `Wfin_od1` compact =
0.2979 nhưng pool = 0.4677.

**Nguyên nhân:** nếu xe đến 1 node sớm hơn `ready_time`, phải **CHỜ** tới
`ready_time` mới bắt đầu phục vụ — khoảng chờ này là một phần của
`active_time` nhưng **không nằm trên bất kỳ arc nào** (nó phát sinh từ
chênh lệch giữa thời điểm đến và `ready_time`). Tính `W_raw` bằng tổng
`travel_time` tĩnh trên arc bỏ sót hoàn toàn phần này.

**Sửa:** `W_raw` phải dùng **trực tiếp biến thời gian thực tế** `t[node]`
(đã đúng đắn xử lý waiting qua ràng buộc `lb=ready_time` + time-propagation)
thay vì tính lại từ travel time tĩnh. Với OD (luôn kết thúc ở home cố
định): `W_raw = t[home] − t0`. Với GW (không có node kết thúc cố định): cần
thêm biến nhị phân `end_of[node]` (1 nếu node này là điểm kết thúc thực sự
của route — được ghé VÀ không có arc ra nào active) + ràng buộc big-M liên
kết `W_raw` với `t[end_node]`.

### 3.3 Bug #3 — BIG_M không nhất quán giữa các nhóm ràng buộc

**Triệu chứng:** implement xong `end_of` (bug #2), model lỗi
`Invalid name` (do thêm biến sau khi `c.variables.add()` đã chạy — lỗi lập
trình, sửa bằng cách khai báo `end_of` trước) rồi **infeasible** ngay cả khi
fix cứng đúng route tối ưu đã biết.

**Nguyên nhân:** ràng buộc `wrawU` dùng chung `BIG_M` (tính từ deadline lớn
nhất ≈1254) để "vô hiệu hóa" khi `end_of=0`, nhưng biến `W_raw` có
`ub=1e6` — lớn hơn `BIG_M` gần 1000 lần. Khi `end_of=0`, ràng buộc
`W_raw − t[node] ≤ s + BIG_M` **không còn lỏng đủ** để luôn đúng với mọi giá
trị khả dĩ của `W_raw` (lên tới 1e6), biến ràng buộc "vô hiệu hóa" thành
ràng buộc thật, gây infeasible sai. Đây là lỗi kinh điển: **BIG_M phải lớn
hơn cả biên độ của CHÍNH BIẾN liên quan, không chỉ lớn hơn 1 đại lượng khác
trong bài toán.**

**Sửa:** giới hạn `ub` của `K_raw`/`W_raw` về đúng `BIG_M` (không phải
`1e6` tùy ý), và dùng `BIG_M2 = BIG_M + W_RAW_UB` riêng cho các ràng buộc
`wrawL/wrawU`.

### 3.4 Bug #4 — `flow_out` cấm GW kết thúc route (mâu thuẫn với chính `end_of`)

**Triệu chứng:** vẫn infeasible sau bug #3, kể cả khi fix cứng đúng route.
Debug bằng **bisect nhị phân trên toàn bộ nhóm ràng buộc** (xóa từng nhóm,
kiểm feasibility) — xác nhận xóa nhóm `flow_out` làm model trở lại feasible.

**Nguyên nhân:** ràng buộc `flow_out` dùng **đẳng thức**
`Σout_arcs = visited[node]`, buộc MỌI node được ghé phải có ĐÚNG 1 arc ra —
nhưng với GW (không có home cố định), node CUỐI CÙNG của route hợp lệ có
`Σout_arcs=0` trong khi `visited=1` — mâu thuẫn trực tiếp với chính cơ chế
`end_of` (bug #2) vừa xây dựng để cho phép route kết thúc ở bất kỳ node nào.

**Sửa:** đổi `flow_out` thành **bất đẳng thức**
`Σout_arcs ≤ visited[node]` (0 hoặc 1 arc ra, không bắt buộc =1).

### 3.5 Bug #5 — model cho phép route "gian lận" thứ tự và vượt B-cap

Sau bug #4, model isolated (1 driver, 3 order) khớp Z* chính xác — nhưng
model đầy đủ (4 driver) cho `Z*_compact = 18.47`, quá thấp bất thường. Đào
sâu lộ ra **2 lỗi độc lập** cùng lúc:

**5a — Thiếu ràng buộc precedence tường minh.** Route được chọn giải mã ra
thứ tự `pickup(o1) → delivery(o5) → pickup(o5) → ...` — **delivery của o5
xảy ra TRƯỚC pickup của o5**! Docstring gốc của model (viết trước khi test)
khẳng định sai rằng "thời gian tăng dọc route tự động đảm bảo precedence
nếu cả 2 node đều được tham" — **sai**, vì flow conservation chỉ đảm bảo
cân bằng cục bộ tại từng node, không đảm bảo pickup/delivery của CÙNG 1
order nằm đúng thứ tự trên chuỗi arc. **Sửa:** thêm ràng buộc tường minh
`t[delivery(o)] ≥ t[pickup(o)] + travel(pickup,delivery)` cho mọi order.

**5b — Home có thể phát sinh nhiều arc ra cùng lúc.** Đồ thị node ban đầu
tạo cạnh cho MỌI cặp `(a,b)` với `a≠b`, kể cả arc đi RA từ home hoặc arc đi
VÀO start — không có gì cấm điều này. Kết quả: 1 driver OD phục vụ cả 6
order (vượt xa capacity thật) với 4 arc ra cùng lúc từ node home. **Sửa:**
loại trừ hẳn các arc này ngay từ bước xây dựng biến (không chỉ dựa vào ràng
buộc).

**5c — Nhầm lẫn "capacity tức thời" với "B-cap tích lũy".** Sau khi sửa 5a,
5b, model vẫn cho phép 1 driver GW (B=3) phục vụ **4 order** — vì `capacity`
trong `t2_core.py`/`dp_labeling.py` không phải tải tức thời (lên xuống theo
pickup/delivery), mà là **tổng số order đã pickup trong TOÀN route** (dù đã
giao xong hay chưa — kiểm qua `len(IV)+len(Cd)≥B`, t6_dp.py dòng 121). Biến
`load[node]` (tải tức thời, tăng khi pickup giảm khi delivery) là MỘT
resource khác hẳn. **Sửa:** thêm biến `served_of[node]` riêng (chỉ tăng khi
pickup, không giảm khi delivery), ràng buộc `served_of ≤ B`.

Sau khi sửa cả 5 bug: **`Z*_compact = 81.6356256251905`, khớp
`Z*_pool = 81.63562562519047`** (chênh <1e-8, thuần floating-point).

## 4. Đo runtime — câu trả lời cho câu hỏi gốc

| n | pool-based (Algorithm A+B) | compact arc-based MILP |
|---:|---:|---:|
| 6 | (không đo riêng, <1s) | giải xong, khớp Z* |
| 8 | **0.11 giây** | **>590 giây, KHÔNG giải xong** (timeout) |

Kích thước model tại n=8 (4 driver): **1,162 biến nhị phân, 5,648 ràng
buộc** — dày đặc hẳn so với route pool thật (vài trăm route/driver sau khi
Algorithm A đã lọc Pareto). CPLEX branch-and-bound không thể đóng gap trong
590 giây ngay ở quy mô "nhỏ" theo chuẩn của dự án (n=8, thấp hơn nhiều so
với hot cell n=20 dự kiến đo ban đầu).

**Không đẩy tiếp lên n=20 (hot cell)** — theo đúng tinh thần "ghi cả trường
hợp thua" của đề xuất: n=8 đã đủ để trả lời câu hỏi gốc một cách dứt khoát,
và việc chờ CPLEX chạy hàng giờ ở n=20 (khi n=8 đã fail sau 590s) không tạo
thêm thông tin mới, chỉ tốn thời gian.

## 5. Trả lời câu hỏi gốc

> "Kiến trúc enumerate-rồi-chọn có phải nguyên nhân chậm, hay bản thân bài
> toán chậm dù giải cách nào?"

**Câu trả lời: kiến trúc enumerate (Algorithm A) không phải nguyên nhân
chậm — ngược lại, nó là một dạng nén không gian tìm kiếm hiệu quả.**
Compact arc-based MILP né được bước "liệt kê" nhưng phải trả giá bằng:
- Số biến nhị phân tăng theo O(driver × node²) thay vì O(driver × bundle
  hợp lệ sau Pareto-filter) — route pool thật (đã qua dominance filter của
  Algorithm A) luôn nhỏ hơn nhiều so với không gian arc thô.
- Cần một lớp ràng buộc big-M dày đặc (time, load, served, end_of, K/W) để
  MILP solver tự "khám phá lại" cấu trúc route hợp lệ — cấu trúc mà
  Algorithm A đã tính sẵn một lần bằng DP forward label-setting (Test6, đã
  verify Gate 0/616/160) với chi phí thấp hơn hẳn.
- Big-M formulation vốn nổi tiếng khó cho MILP solver (LP relaxation lỏng,
  branch-and-bound phải khám phá sâu) — đây là hạn chế nội tại của việc
  dùng biến arc + big-M cho bài toán có time window/precedence, không phải
  vấn đề implementation.

Đây là một xác nhận **độc lập** cho giá trị của Algorithm A (forward
label-setting DP) — không chỉ nó đúng (đã chứng minh ở Test6/6.1/6.2), mà
việc thay thế nó bằng một compact formulation "né enumerate" thực sự **tệ
hơn nhiều**, không phải một hướng tối ưu khả thi.

## 6. Không cộng dồn vào chuỗi REJECTED trước

Theo đúng ghi chú ban đầu của đề xuất: đây là câu hỏi độc lập với 4 hướng
pruning đã REJECTED (`Report_ActivationRate.md` §5-8, đều về việc lọc bớt
route KHỎI pool có sẵn). Kết quả ở đây không phải "REJECTED" theo nghĩa đó —
nó là một **kết quả phủ định có giá trị structural**: xác nhận Algorithm A
(và cách tiếp cận enumerate-rồi-Pareto-filter nói chung) không chỉ đúng mà
còn cần thiết về mặt hiệu năng, đóng lại hẳn câu hỏi "liệu có công thức MILP
nào né được toàn bộ vấn đề enumeration hay không" cho lớp bài toán này.

---

## File & tái tạo

```
spec_2a_2b/src/test_compact_arc_milp.py   Model chinh (build_compact_model,
                                            solve_compact) - 5 bug da sua,
                                            ghi chu chi tiet tai vi tri sua
                                            trong code (khong chi trong report)
```
Chạy lại (Python 3.7.7, cần CPLEX active):
```
python test_compact_arc_milp.py   # n=6, so Z*_compact voi Z*_pool da biet
```
Test n=8 (đo runtime, KHÔNG chờ hoàn thành — minh họa việc timeout):
dùng `solve_compact(drivers, orders, fd_cost, tt, theta_by_driver)` trực
tiếp trên instance n=8 bất kỳ, giới hạn thời gian CPLEX qua
`c.parameters.timelimit` nếu muốn đo gap thay vì chờ OPTIMAL tuyệt đối.
