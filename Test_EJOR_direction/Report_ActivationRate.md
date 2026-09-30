# Report: Activation Rate — route nào thực sự optimal-worthy qua toàn dải bid?

> Thí nghiệm mới (2026-09-16, đề xuất trực tiếp từ người dùng, chưa có spec
> file trước đó — không phải `Test_C.md`, dù cùng thư mục `Test_EJOR_direction/`).
> Một phép đo, hai kết quả đều dùng được: activation_rate cao → bằng chứng
> cho tightness (đáng viết construction); activation_rate thấp → cơ hội
> pruning thật, chưa khai thác.

**Kết luận một câu:** activation_rate rơi vào khoảng **0.42% - 1.54%** qua 5
instance độc lập (n∈{10,12,15}, số driver∈{4,5,6}, 4 seed + 1000 bid vector
Latin Hypercube mỗi instance) — **rất thấp, ổn định, bão hòa cực sớm** (không
đổi từ vector thứ 200 đến 1000). Đây là bằng chứng thực nghiệm mạnh cho **cơ
hội pruning thật**: tuyệt đại đa số route trong pool KHÔNG BAO GIỜ tối ưu với
bất kỳ bid nào trong toàn dải [18,25] USD/h đã khóa. Phân tích cấu trúc thêm
cho thấy: **mọi driver đều có route được activate (không driver nào "chết
hẳn"), nhưng mỗi driver chỉ có đúng ~1 route sống sót qua toàn dải bid**, bất
kể pool của driver đó lớn tới đâu (429-441 route ở GW cũng chỉ còn 1 route
sống). **Đã thử 4 hướng tìm điều kiện pruning rẻ (không cần giải WDP) để
khai thác phát hiện này — cả 4 đều REJECTED** (§5-8): hull cục bộ theo
driver, hull toàn cục, Min-Max Bound cross-driver, và LP-Dual Reduced-Cost —
3/4 thất bại vì cùng nguyên nhân gốc (WDP là bài toán set-cover toàn cục,
không tách rời được thành điều kiện cục bộ mà không mất an toàn), hướng thứ
4 (LP-dual) thất bại vì shortcut 1-điểm dựa trên giả định đơn điệu sai (dual
price không đơn điệu theo θ đối thủ). Bản thân hiện tượng activation-rate-
thấp vẫn đứng vững, nhưng hướng "pruning rule mới cho Algorithm A" đã dừng
hẳn theo quyết định người dùng.

---

## 1. Phương pháp

Lấy 1 instance đã có (n=10-15), sample `N` bid vector θ từ range đã khóa
(Uniform[18,25] USD/h — `rq1_cost_gen.THETA_MIN/THETA_MAX`) qua **Latin
Hypercube Sampling** thuần Python trên `[18,25]^m` (m = số driver). Với mỗi
bid vector, giải WDP thật (Algorithm B qua CPLEX, dùng lại nguyên
`rq1_wdp.solve_wdp_for_instance` — không logic mới, không cần Algorithm C).
Đếm:

```
activation_rate = |{route từng xuất hiện trong >=1 lời giải tối ưu}| / |pool|
```

Route pool dùng lại nguyên `dp_labeling.build_route_pool` (Algorithm A,
không đổi). Đối chiếu route giữa các lần giải bằng route-id ổn định (thứ tự
duyệt `dict.items()` trên CÙNG 1 `pool_by_driver` object không đổi qua toàn
bộ N lần solve — Python 3.7+ giữ thứ tự insertion, đảm bảo route-id nhất
quán).

## 2. Kết quả — 5 instance, N=1000 bid vector/instance

| n | n_drivers (m) | seed | pool_size | n_activated | activation_rate |
|---:|---:|---:|---:|---:|---:|
| 12 | 5 | 42 | 879 | 6 | 0.68% |
| 10 | 4 | 1 | 714 | 11 | 1.54% |
| 15 | 5 | 7 | 1,561 | 7 | 0.45% |
| 12 | 6 | 123 | 1,416 | 6 | 0.42% |
| 10 | 4 | 999 | 510 | 4 | 0.78% |

**Tất cả đều bão hòa từ vector thứ 200/1000** — số route activated không
đổi thêm dù tăng gấp 5 lần số bid vector sample (200→1000). Đây là dấu hiệu
mạnh cho thấy N=1000 đã dư thừa để tìm ra toàn bộ tập route activatable
trong range đã khóa — không phải hiện tượng "chưa sample đủ".

Không có instance nào lệch hướng — activation_rate luôn dưới 2% qua toàn bộ
5 instance, dù n/m/seed khác biệt đáng kể.

## 3. Phân tích cấu trúc — route nào sống sót (instance n=12, seed=42)

| route id | driver | class | bundle size | orders | K | W | pool của driver này |
|---|---|---|---:|---|---:|---:|---:|
| gw0_r136 | gw0 | GW | 3 | {o6,o10,o11} | 15.752 | 1.400 | 441 route |
| gw1_r129 | gw1 | GW | 3 | {o6,o10,o11} | 13.348 | 1.400 | 429 route |
| od0_r0 | od0 | OD | 1 | {o11} | 2.067 | 0.433 | 2 route |
| od1_r0 | od1 | OD | 1 | {o11} | 0.602 | 0.395 | 3 route |
| od1_r1 | od1 | OD | 1 | {o3} | 4.339 | 0.384 | 3 route |
| od2_r2 | od2 | OD | 1 | {o8} | 0.020 | 0.220 | 4 route |

**Quan sát chính:**
- **Cả 5/5 driver đều có ít nhất 1 route được activate** — không có driver
  nào "chết hẳn" (activation_rate=0% riêng cho driver đó). Điều này loại trừ
  khả năng activation thấp chỉ vì 1-2 driver bị driver khác lấn át hoàn toàn.
- **Nhưng mỗi driver chỉ có ĐÚNG 1 route sống sót** trong toàn bộ pool của
  nó — kể cả 2 driver GW có pool 429-441 route (lớn gấp ~100-200 lần số OD),
  cũng chỉ 1 route duy nhất từng optimal với bất kỳ bid nào trong range.
- 2 route GW sống sót đều là **cùng 1 bundle** `{o6,o10,o11}` (kích thước
  tối đa B=3) — gợi ý: khi θ đủ thấp để GW "đáng giải", GW luôn muốn gộp tối
  đa đơn hàng (route càng nhiều order càng khai thác được kinh tế theo quy
  mô của κ·distance cố định), không có route bundle nhỏ hơn nào từng thắng.
- Route OD sống sót đều bundle_size=1 (do τ detour budget hẹp — nhất quán
  với phát hiện ở `Report_RQ1_Sequential_PoolSize_Check.md`: OD pool vốn đã
  nhỏ, gần như toàn bộ pool nhỏ đó cũng dư thừa).

## 4. Đọc kết quả theo tiêu chí đề xuất

| activation_rate | Ý nghĩa | Áp dụng ở đây |
|---|---|---|
| Cao (>50%) | Bằng chứng cho tightness — đáng viết construction | Không áp dụng |
| **Thấp (<5%)** | **Cơ hội pruning thật, chưa khai thác** | **Áp dụng — 0.42-1.54%** |

Kết quả rơi rõ ràng vào nhánh "activation_rate rất thấp". Đây là **hướng
positive result mới**: tuyệt đại đa số route trong pool (>98%) không bao giờ
là lựa chọn tối ưu cho bất kỳ bid nào trong dải đã khóa — một cơ hội pruning
lớn, nếu tìm được điều kiện đủ để nhận diện route "không-activatable" mà
không cần giải hết mọi bid vector.

## 5. Thử tìm điều kiện pruning rẻ — REJECTED

Theo đúng đề xuất ban đầu: tìm điều kiện đủ, kiểm được **rẻ** (không cần
giải WDP cho từng bid) để nhận ra route không-activatable. Bước tiếp theo
trực tiếp sau §4 (2026-09-16), kết quả: **giả thuyết đầu tiên bị bác bỏ bằng
thực nghiệm** — ghi lại trung thực, không giấu, theo đúng kỷ luật của dự án
(giống các REJECTED trước đó: Test3 Pareto-dominance, Test4/5 fallback
bound).

### 5.1 Giả thuyết đã thử

Từ §3: mỗi driver chỉ có ~1 route sống sót trong pool riêng của nó, gợi ý
điều kiện pruning cục bộ: route `r` (thuộc driver `i`, chi phí
`true_cost = K_r + θ_i·W_r` — hàm affine theo `θ_i`) chỉ có thể tối ưu với
driver đó nếu nó nằm trên **lower convex hull** của toàn bộ pool driver `i`
(gộp mọi bundle, không tách theo bundle như Convex Hull Test A — vì driver
chỉ chọn 1 route duy nhất bất kể bundle nào), **và** khoảng slope θ mà tại
đó nó là argmin ("active range", tính từ giao điểm giữa các đoạn hull kề
nhau) giao khác rỗng với `[θ_min, θ_max]` đã khóa. Kỳ vọng đây là **điều
kiện cần** (route không thỏa thì chắc chắn không bao giờ tối ưu cho driver
đó), không cần giải WDP.

Dùng lại `lower_hull_on_pareto()` đã audit độc lập (Convex Hull Test A, 0
mismatch qua brute-force numeric) để tính hull, đối chiếu candidate set với
`activated_real` (route thật sự activate qua 1000 bid vector LHS + WDP CPLEX
— dữ liệu đã có ở §2).

### 5.2 Kết quả — bác bỏ ngay ở smoke test

Instance nhỏ (n=8, B_gw=B_od=3, n_drivers=4, seed=42, 50 bid vector):

```
pool_size                 = 344
|candidates| (dieu kien)  = 4    (1.16% cua pool)
|activated| (WDP that)    = 6    (1.74% cua pool)
missing (activated that nhung KHONG trong candidates) = 4
  [FAIL] gw0_r14, gw1_r105, od0_r1, od1_r1
```

**4/6 route activated thật không nằm trong candidate set** — điều kiện bỏ
sót đa số route thật sự được dùng. Bác bỏ ngay, không cần chạy tiếp 5
instance đầy đủ.

### 5.3 Tại sao sai — cơ chế cụ thể

Route `gw0_r14` (bundle `{o1,o3}`, K=5.882, W=0.637) KHÔNG nằm trên lower
hull của pool riêng `gw0` (pool 173 route, chỉ `gw0_r3` nằm trên hull) —
nhưng vẫn được WDP chọn thật ở một số bid vector. Nguyên nhân: `o1` và `o3`
**đều có route đơn lẻ (bundle size 1) ở nhiều driver khác** (gw0, gw1, od0,
od1):

| order | driver | K | W |
|---|---|---:|---:|
| o1 | gw0 | 3.594 | 0.487 |
| o1 | gw1 | 4.196 | 0.487 |
| o1 | od0 | 3.306 | 0.449 |
| o1 | od1 | 1.826 | 0.336 |
| o3 | gw0 | 3.792 | 0.366 |
| o3 | gw1 | 5.437 | 0.439 |
| o3 | od0 | 2.372 | 0.319 |
| o3 | od1 | 3.075 | 0.320 |

Với một số cấu hình θ, **gộp o1+o3 vào 1 route** ở gw0 (chia sẻ chi phí
κ·distance cố định của route) có thể rẻ hơn **tổng** chi phí phục vụ 2 đơn
riêng lẻ ở 2 driver khác nhau — dù route gộp đó không phải lựa chọn rẻ nhất
riêng cho gw0 nếu chỉ so trong pool của gw0. Đây là **kinh tế theo quy mô
route** tương tác với **ràng buộc covering toàn cục** (mỗi order chỉ được
phục vụ đúng 1 lần) — một hiệu ứng liên driver mà điều kiện cục bộ (chỉ nhìn
1 driver riêng lẻ) không thể nắm bắt được.

Thử biến thể ngược lại — gộp TOÀN BỘ route của mọi driver vào 1 hull chung
(không phân biệt driver) — cũng sai theo hướng khác: hull chỉ còn 2 điểm
toàn cục, và cả 4 route missing ở trên cũng không nằm trong hull này. Cách
này mất hoàn toàn ý nghĩa vì route của driver khác nhau không cạnh tranh
trực tiếp theo kiểu "chọn 1 trong nhiều" (θ của driver khác không nhất
thiết bằng θ của driver này).

### 5.4 Kết luận của bước này

Cả 2 biến thể đơn giản của điều kiện pruning hình học (hull cục bộ theo
driver, hull toàn cục gộp hết) **đều không an toàn hoặc vô nghĩa**. Đây là
một kết quả cấu trúc đáng ghi nhận: activation rate thấp (§2-4) là một hiện
tượng THẬT, nhưng **cơ chế đứng sau nó không đơn giản hóa được về 1 điều
kiện hình học cục bộ trên từng driver** — nó gắn liền với cấu trúc
order-sharing giữa nhiều driver trong bài toán set-cover toàn cục.

**Không dừng hẳn hướng activation-rate-thấp** (phát hiện ở §2-4 vẫn đứng
vững, đã kiểm qua 5 instance độc lập) — chỉ bác bỏ CÁCH TIẾP CẬN cụ thể này
để tìm điều kiện pruning rẻ.

## 6. Hướng thứ ba — Min-Max Bound (cross-driver alternative covering) — REJECTED

Theo `Test_EJOR_direction/Test_min_max.md` (2026-09-16): hướng pruning
cross-driver ĐẦU TIÊN được thử — khác hẳn §5 (vốn đều là trong-1-driver hoặc
trong-1-bundle), nhắm thẳng vào đúng cơ chế đã lộ ra ở §5.3 (route sống vì
rẻ hơn TỔNG chi phí tách order ra driver khác, không phải vì rẻ trong pool
riêng của chính nó).

### 6.1 Điều kiện

```
prune(r) := c_ir(b_min) >= Alt(S, i; b_max)
```
- `c_ir(b_min) = K_ir + b_min·W_ir` — chi phí route `r` (driver `i`, bundle
  `S`) tại kịch bản lợi nhất cho nó (θ_i = θ_min).
- `Alt(S, i; b_max)` — chi phí rẻ nhất để phủ đúng `S` bằng driver KHÁC `i`
  (mỗi route ứng viên định giá tại θ = θ_max, kịch bản bất lợi nhất cho đối
  thủ) hoặc FD, tính qua DP bitmask (`|S| ≤ B ≤ 5`, không cần ILP).

Kỳ vọng: nếu ngay ở kịch bản lợi nhất cho `r` mà vẫn thua kịch bản bất lợi
nhất cho đối thủ, không tồn tại `b` nào khiến `r` thắng thật.

### 6.2 Bước 1 (bắt buộc) — Audit trên ground truth đã có ở §2 — FAIL

Theo đúng thứ tự spec (audit rẻ TRƯỚC, không đo hiệu quả trước rồi mới
audit — bài học từ 2 lần làm sai thứ tự trước đó): dùng lại chính 5 instance
+ `activated_real` đã có ở §2 (không cần chạy lại WDP/LHS).

```
n=12 n_drivers=5 seed=42:  pool=879  activated=6   would_prune=873(99.32%)  violations=2
n=10 n_drivers=4 seed=1:   pool=714  activated=11  would_prune=587(82.21%)  violations=0
n=15 n_drivers=5 seed=7:   pool=1561 activated=7   would_prune=1355(86.80%) violations=0
n=12 n_drivers=6 seed=123: pool=1416 activated=6   would_prune=1044(73.73%) violations=0
n=10 n_drivers=4 seed=999: pool=510  activated=4   would_prune=473(92.75%)  violations=0

TONG violations = 2   ->  [FAIL - Buoc 1]
```

2 vi phạm, cả 2 đều trên cùng 1 instance (seed=42):
`gw0_r136` (bundle `{o6,o10,o11}`, c_bmin=40.943 vs alt=40.665) và `od0_r0`
(bundle `{o11}`, c_bmin=9.864 vs alt=9.630) — chênh lệch rất sát biên (<1%),
nhưng dứt khoát vi phạm điều kiện an toàn.

### 6.3 Cơ chế cụ thể — tại sao sai (không chỉ báo FAIL)

Xác nhận bằng cách giải WDP thật tại đúng bid vector biên
(`od0=θ_min=18, mọi driver khác=θ_max=25`): `od0_r0` **thực sự** được chọn
tối ưu (`z=166.845`), không phải hiện tượng do LHS sample thiếu — đây là vi
phạm toán học thật, không phải nhiễu thực nghiệm.

Truy nguyên: `alt_cost({o11}, exclude=od0, b_max=25)` dùng `od2_r0` (giá tại
θ_max=25 là 9.630) làm phương án thay thế rẻ nhất. Nhưng trong lời giải WDP
thật, `od2` **không phục vụ o11** — nó phục vụ `o8` (route `od2_r2`). Alternative
thật sự rẻ nhất khi loại `od0` là `od1_r0` (giá 10.489), không phải `od2_r0`.

**Lỗ hổng lý thuyết trong định nghĩa `Alt()`** (không phải lỗi code): hàm
`_min_cost_to_cover` giả định mỗi driver khác có thể **tự do, độc lập** dùng
route rẻ nhất của nó để phủ `S` — nhưng thực tế mỗi driver chỉ chọn **đúng 1
route cho toàn bộ instance**, không riêng cho `S`. Nếu route rẻ nhất của
driver đó cho `S` xung đột với việc nó cần phục vụ order khác ở nơi khác
trong lời giải toàn cục (ở đây: `od2` "bận" với `o8`), `Alt` đã **đánh giá
thấp hơn thực tế** chi phí thay thế — khiến điều kiện `prune()` prune nhầm
route vẫn còn activatable thật.

Đây là chỗ khác với dự đoán ban đầu của spec (Sec1: nghi ngờ do đơn giản hóa
"bỏ route dư, bundle ⊋ S") — cơ chế thật tinh vi hơn: vấn đề không phải ở
việc bỏ sót loại candidate nào, mà ở giả định **các driver đối thủ độc lập
với nhau và với phần còn lại của instance**, một giả định sai về bản chất
trong bài toán set-cover toàn cục (đúng cùng họ cơ chế đã bác bỏ 2 điều kiện
ở §5, nhưng lộ ra ở một góc khác — lần này ngay cả khi đã cố tình mô hình
hóa "đối thủ", vẫn bỏ sót ràng buộc 1-route-cho-cả-instance của chính đối
thủ đó).

### 6.4 Kết luận

Theo đúng bảng Interpretation của spec (Test_min_max.md §5): **Bước 1 FAIL
→ dừng, không chạy Bước 2/3 (Gate n≤6, đo prune rate)**. Theo §7 của spec:
đây là hướng cross-driver thứ 2 tính chung với §5 (nếu tính pruning-condition
hình học ở §5 là 1 "lần thử" dạng trong-driver, đây là lần thử dạng
cross-driver riêng biệt) — đã đủ để đánh giá độ khó của bài toán con này,
**không mở thêm biến thể thứ 3** của họ pruning-condition (dù bản thân
hướng "sửa `Alt()` để tính đúng ràng buộc 1-route/driver" là khả thi về mặt
lý thuyết, nó sẽ biến `Alt()` thành gần như giải lại 1 bài toán WDP con —
mất hết lợi thế "rẻ" ban đầu của cách tiếp cận này).

Theo đúng §7 của spec, dừng hẳn nhánh "tìm pruning rule mới cho Algorithm
A" — chuyển trọng tâm sang: (a) viết Proposition/Lemma đã có (Test6 forward
label-setting DP, Test7/8 component decomposition) vào luận văn, (b)
tightness construction nếu còn thời gian, (c) formalize phát hiện phụ RQ1
(OD-first vs GW-first, `Report_RQ1_Complementarity.md` §5).

## 7. Hướng thứ tư — LP-Dual Reduced-Cost Fixing — REJECTED

Theo `Test_EJOR_direction/LP_dual.md` (2026-09-16): khác về BẢN CHẤT với 3
hướng trước — LP relaxation KHÔNG xấp xỉ sự cạnh tranh toàn cục bằng mô hình
đơn giản hóa, nó **giải đúng bài toán toàn cục thật** (mọi driver, mọi ràng
buộc covering, cùng lúc), chỉ nới biến 0/1 thành [0,1]. Dual price tự động
gộp hết tương tác giữa driver — đây là lý do hướng này được kỳ vọng tránh
được lỗi đã lộ ra ở §5-6 (giả định driver đối thủ độc lập).

### 7.1 Điều kiện

```
rc_ir(b) = c_ir(b_i) - Sum_{o in S} pi_o(b)     (reduced cost tai bid b)
prune(r) := rc_ir(b*) > 0
b* = (b_i = theta_min, b_j = theta_max voi moi j != i)   (kich ban loi nhat cho r)
```

`pi_o(b)` là dual price của ràng buộc covering order `o` trong LP relaxation
tại bid `b` — lấy qua `cplex.solution.get_dual_values()`.

Rủi ro riêng của hướng này (khác 3 lần trước): để rẻ, chỉ muốn kiểm 1 điểm
biên `b*` rồi suy ra an toàn cho toàn dải, dựa trên **giả định chưa kiểm
chứng** "`rc_ir(b)` đạt nhỏ nhất tại đúng `b*`" (đơn điệu theo θ của driver
khác). Spec yêu cầu kiểm giả định này TRƯỚC (Bước 0), tách biệt khỏi audit
ground truth (Bước 1) — một kỷ luật mới so với 3 lần trước (không có bước
kiểm giả định tương tự).

### 7.2 Bước 0 — Kiểm giả định đơn điệu — FAIL lan rộng

Quét lưới thô (8 điểm bid ngẫu nhiên/route) trên 20 route gần biên prune
nhất (ưu tiên `rc_ir(b*)` gần 0 — nơi vi phạm dễ đổi kết luận nhất) × 5
instance:

```
n=12 n_drivers=5 seed=42:  checked=20 violations=5
n=10 n_drivers=4 seed=1:   checked=20 violations=3
n=15 n_drivers=5 seed=7:   checked=20 violations=0
n=12 n_drivers=6 seed=123: checked=20 violations=2
n=10 n_drivers=4 seed=999: checked=20 violations=7

TONG violations = 17/100 route kiem  ->  [FAIL - Buoc 0], 4/5 instance co vi pham
```

Vi phạm xác nhận là thật (không phải nhiễu numeric — ngưỡng dùng là 1e-6,
một số lệch tới -1.46, ví dụ instance seed=999: `od1_r1` có
`rc_star=-0.1785` nhưng tại 1 điểm test khác trong dải, `rc_test=-1.1653`,
thấp hơn `rc_star` tới 0.987). Không phải hiện tượng hiếm — FAIL trên 4/5
instance, với instance nặng nhất (n=10,seed=999) có tới 7/20 route vi phạm.

**Cơ chế cụ thể**: `b*` (θ_i=θ_min, mọi driver khác=θ_max) được kỳ vọng là
kịch bản "khó prune nhất" (đối thủ đắt nhất có thể, khiến `rc` cao nhất) —
nhưng dual price `π_o(b)` không đơn điệu đơn giản theo θ của driver khác:
khi 1 driver khác đắt lên, LP relaxation có thể chuyển sang dùng route của
1 driver khác nữa (không phải route đang xét), làm dual price của order
trong `S` thay đổi theo hướng không dự đoán được — một điểm bid **ở giữa
dải** (không phải ở biên) có thể cho `rc` thấp hơn cả tại `b*`, đúng như dữ
liệu thực nghiệm cho thấy.

### 7.3 Kết luận

Theo đúng bảng Interpretation của spec: **Bước 0 FAIL → không dùng shortcut
1-điểm**. Phương án dự phòng (§4 của spec) — kiểm reduced cost ở nhiều điểm
hơn/parametric LP thật (theo dõi vùng bid mà basis LP tối ưu không đổi) —
đắt hơn hẳn: cần giải LP nhiều lần/route thay vì 1 lần, và về bản chất tiệm
cận việc giải lại một họ bài toán WDP con, **mất hết lợi thế "rẻ" ban đầu**
của cách tiếp cận LP-dual. Theo quyết định người dùng (2026-09-16): dừng ở
đây, không triển khai phương án dự phòng — ghi nhận REJECTED.

Khác biệt với §5-6: lỗi lần này không phải do mô hình hóa sai cạnh tranh
liên driver (LP relaxation giải đúng bài toán toàn cục) — mà do **shortcut
kiểm 1 điểm** dựa trên giả định đơn điệu không đúng. Bản thân LP relaxation/
reduced cost vẫn là công cụ đúng đắn về mặt lý thuyết; chỉ riêng cách rút
gọn để làm nó "rẻ" (chỉ 1 điểm thay vì toàn dải) là không an toàn ở bài
toán này.

## 8. Tổng kết — 4 hướng pruning đã thử, cả 4 đều REJECTED

| # | Hướng | Cơ chế thất bại | Trạng thái |
|---|---|---|---|
| 1 | Hull cục bộ theo driver (§5.1-5.2) | Bỏ qua cạnh tranh liên driver (kinh tế theo quy mô route vs covering toàn cục) | REJECTED — bác bỏ ngay smoke test |
| 2 | Hull toàn cục gộp hết (§5.2 biến thể) | Mất ý nghĩa — route khác driver không cạnh tranh trực tiếp theo 1 trục θ | REJECTED — vô nghĩa |
| 3 | Min-Max Bound cross-driver (§6) | `Alt()` giả định driver đối thủ độc lập, bỏ qua ràng buộc 1-route/driver của chính đối thủ | REJECTED — FAIL Bước 1, 2/5 instance |
| 4 | LP-Dual Reduced-Cost (§7) | Shortcut 1-điểm `b*` dựa trên giả định đơn điệu sai — dual price không đơn điệu theo θ đối thủ | REJECTED — FAIL Bước 0, 4/5 instance |

3/4 hướng thất bại vì cùng một nguyên nhân gốc: **WDP là bài toán
set-cover/set-packing toàn cục, không thể tách rời thành điều kiện cục bộ
mà không mất tính an toàn.** Hướng thứ 4 (LP-dual) khác — bản thân công cụ
đúng, nhưng cách rút gọn để làm nó rẻ (1 điểm thay vì toàn dải) không an
toàn ở bài toán này; phiên bản đắt hơn (parametric LP) có thể vẫn đúng
nhưng mất lợi thế "rẻ" ban đầu, không đáng triển khai theo quyết định người
dùng. Phát hiện activation-rate-thấp (§2-4) vẫn đứng vững như một hiện
tượng thực nghiệm thật — nhưng sau 4 hướng thử, nỗ lực tìm điều kiện pruning
RẺ để khai thác nó đã cạn các hướng khả dĩ trong phạm vi thời gian hợp lý
của thesis.

---

## File & tái tạo

```
spec_2a_2b/src/testC2_activation_rate.py     Script chinh §2-4 (LHS sampling +
                                               WDP loop + route-id matching,
                                               khong logic cost/route moi -
                                               dung lai dp_labeling/rq1_wdp
                                               nguyen ven)
spec_2a_2b/src/testC2_pruning_condition.py   Script §5 (hull rieng driver +
                                               hull toan cuc, ca 2 deu
                                               REJECTED - giu lai code de
                                               tham khao, KHONG dung lam co
                                               so cho buoc tiep theo)
spec_2a_2b/src/test_minmax_pruning.py        Script §6 (Min-Max Bound Buoc 1
                                               audit - REJECTED, FAIL 2/5
                                               instance - giu lai code de
                                               tham khao)
spec_2a_2b/src/test_lpdual_pruning.py        Script §7 (LP-Dual Buoc 0
                                               monotonicity check - REJECTED,
                                               FAIL 4/5 instance - giu lai
                                               code de tham khao)
spec_2a_2b/results/testC2_activation_rate.log     Instance dau tien (n=12,seed=42)
spec_2a_2b/results/testC2_multi_instance.log      4 instance bo sung (seed 1,7,123,999)
spec_2a_2b/results/test_minmax_step1_audit.log    Buoc 1 audit Min-Max Bound (5 instance)
spec_2a_2b/results/test_lpdual_step0.log          Buoc 0 monotonicity check LP-dual (5 instance)
```
Chạy lại (Python 3.7.7, cần CPLEX active):
```
python testC2_activation_rate.py      # 1 instance mac dinh (n=12,seed=42), 1000 bid vector
python testC2_pruning_condition.py    # kiem dieu kien pruning §5 (da REJECTED o smoke test)
python test_minmax_pruning.py         # kiem dieu kien pruning §6 (da REJECTED - Buoc 1 FAIL)
python test_lpdual_pruning.py         # kiem dieu kien pruning §7 (da REJECTED - Buoc 0 FAIL)
```
Đổi tham số qua `run_activation_rate(n=..., n_drivers=..., seed=..., n_bid_vectors=...)`.
