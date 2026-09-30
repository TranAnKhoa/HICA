# Patch T4 — Tách B theo lớp (B_GW / B_OD) + Bộ lọc tương thích cặp (Pairwise Compatibility Filter)

## Bối cảnh và lý do gộp chung vào MỘT đợt sửa

Hiện đang có 1 patch OD-corridor-bias + stable-seed **đã được duyệt nhưng chưa chạy pipeline
lớn** (đang chờ chạy `run_gate0.py → run_2a.py → run_2b.py → ...`, tốn nhiều giờ). Đây là
lúc đúng để chèn thêm 2 thay đổi mới — **KHÔNG chạy pipeline lớn 2 lần liên tiếp cho 2 đợt
sửa riêng**, vì mỗi lần chạy tốn hàng chục giờ. Gộp cả 3 thay đổi (OD-corridor-bias,
B_GW/B_OD tách rời, bộ lọc tương thích cặp) vào **một** lần sửa code, kiểm chứng từng phần
bằng gate riêng, rồi chạy pipeline lớn **đúng một lần duy nhất** cho tất cả.

**Ba thay đổi trong đợt này:**
1. Tách `B` (bundle cap) thành `B_GW` và `B_OD` — hai tham số độc lập, không còn dùng chung
   1 giá trị.
2. Thêm **bộ lọc tương thích cặp** (Pairwise Compatibility Filter, viết tắt **PCF**) vào
   Algorithm A — đây là lời giải ứng viên cho bài toán mở **A-T4** đã treo từ trước (cận cắt
   nhánh cho open-route GW, vốn không có anchor như τ của OD).
3. (Đã duyệt từ trước, đi kèm trong lần chạy này) OD-corridor-bias + stable-seed +
   `tau ∈ {30,45,60}` (bỏ 10,15,20 vì bất khả thi cấu trúc — xem patch trước).

---

## Việc 1 — Tách `B_GW` / `B_OD`

### 1.1 Lý do và giả thuyết cần kiểm

Giả thuyết: OD đã bị giới hạn chặt bởi `τ` (detour budget) — một bundle OD lớn (3-4 đơn)
gần như chắc chắn vi phạm `deadline_home` trước khi kịp bàn tới việc "route có quá nhiều
đơn". Vì vậy `B_OD` kỳ vọng nhỏ (1-2) là đủ — tăng lên không thêm được nhiều bundle mới
(cần XÁC NHẬN bằng dữ liệu, không mặc định đúng). Ngược lại GW không có ràng buộc τ, nên
`B_GW` là trục thật sự cần khảo sát rộng (2-5) — đây cũng chính là trục mà giới hạn thực
nghiệm (bùng nổ trước n=50 ở B≥4) đã được phát hiện ở lần chạy trước.

### 1.2 Sửa code

- Thay mọi chỗ dùng 1 tham số `B` (bất biến kích thước bundle) bằng `B_gw` và `B_od`, đọc
  từ config theo **loại driver**, không theo tên biến chung.
- Điều kiện bất biến trong DP (`|IV|+|C| ≤ B`, §1.5.1) tách theo lớp:
  ```
  GW: |IV|+|C| ≤ B_gw
  OD: |IV|+|C| ≤ B_od
  ```
- Không đổi bất kỳ điều kiện feasibility nào khác (time window, capacity, dominance rule).

### 1.3 Sửa tài liệu model (đề cương + `main_guideline.md`)

- §2.1 (Input) và §6.1 (Phạm vi được claim) của đề cương: thay "bundle cap B" (số ít) bằng
  "bundle cap theo lớp `B_GW`, `B_OD`" — ghi rõ đây là **quyết định thiết kế có chủ đích**
  (không phải do giới hạn kỹ thuật), lý do: hai lớp có cơ chế ràng buộc bundle-size khác
  nhau về bản chất (τ của OD gián tiếp giới hạn kích thước, GW thì không).
- Việc này **không ảnh hưởng đến DSIC/VCG** — B (dù chung hay tách theo lớp) vẫn là
  **route range công bố trước, bid-independent**, đúng điều kiện sống còn #2 của đề cương
  gốc (mục 0, "Bốn điều kiện sống còn"). Ghi rõ một câu xác nhận điều này trong phần sửa,
  để tránh reviewer hiểu nhầm đây là kẽ hở DSIC.

---

## Việc 2 — Bộ lọc tương thích cặp (Pairwise Compatibility Filter — PCF)

### 2.0 ★ Chẩn đoán rẻ TRƯỚC KHI cài đặt — bắt buộc, làm trước Gate T4-B

**Lý do làm bước này trước:** đã đối chiếu ý tưởng PCF (và một ý tưởng liên quan — ma
trận lower-bound kiểu Lozano, Duque & Medaglia 2016) với kết quả đã có ở **Test5**
(`self-survival bound UB1/UB2`). Test5 cho thấy: mọi bộ lọc dựa trên **feasibility** chỉ
cắt được khi ràng buộc *đang bó chặt* — kết quả đo được là *"sound tuyệt đối (0/62.728)
nhưng prune_rate = 0 tuyệt đối ở vùng bùng nổ"*, vì *"cận chỉ âm khi route đã chật (tw
hẹp) — vùng đó vốn không bùng nổ"*. PCF thuộc đúng họ bộ lọc này — không có gì đảm bảo nó
tránh được số phận tương tự, đặc biệt sau khi đã giảm `AREA_KM=8` (bản đồ nhỏ hơn → nhiều
cặp order tương thích hơn → PCF ít việc để làm hơn).

**Không cài PCF đầy đủ (Gate T4-B, §2.3) trước khi biết chẩn đoán này** — chi phí chẩn
đoán rẻ (vài phút, không cần sửa DP), trong khi cài Gate T4-B + chạy lại toàn bộ pipeline
tốn hàng chục giờ. Biết trước PCF có việc để làm hay không sẽ quyết định có đáng đầu tư
tiếp hay không.

**Thủ tục:**

```python
def pair_infeasibility_rate(orders, driver_class, tw_width, tau=None):
    """
    Với driver_class='GW': dùng thẳng cặp order bất kỳ + time window, không cần tau.
    Với driver_class='OD': cần tau + home + direct_time của driver mẫu.
    Đếm cặp (i,j) mà CẢ 6 thứ tự hợp lệ (P_i D_i P_j D_j, ..., xem §2.1) đều infeasible
    — dùng ĐÚNG hàm feasibility đã có trong t6_dp.py (không viết công thức riêng).
    """
    total_pairs = 0
    infeasible_pairs = 0
    for i, j in itertools.combinations(orders, 2):
        total_pairs += 1
        if not any_of_6_orderings_feasible(i, j, driver_class, tw_width, tau):
            infeasible_pairs += 1
    return infeasible_pairs / total_pairs
```

Chạy trên vài ô đại diện — ưu tiên đúng vùng đã biết bùng nổ ở Phần A (§1.3 báo cáo
trước: `tw ∈ {120, 240}`, `n ∈ {30, 50}`), cộng 1-2 ô ở `tw` hẹp để đối chứng:

```
tw_width ∈ {60, 120, 240}   x   n ∈ {30, 50}   x   driver_class ∈ {GW, OD}
x   seed ∈ {0,1,2}  (3 đủ cho chẩn đoán, không cần 10)
= 36 lần đo, mỗi lần vài giây
```

**Ngưỡng đọc kết quả (khóa trước khi xem số):**

| `pair_infeasibility_rate` ở `tw∈{120,240}` | Kết luận |
|---|---|
| **< 10%** | PCF (và mọi biến thể LB-matrix kiểu Lozano) **gần như chắc chắn không cứu được** vùng bùng nổ — đúng lặp lại kịch bản Test5. **Không cài Gate T4-B / PCF đầy đủ** — bỏ Việc 2 khỏi đợt patch này, quay lại hướng (a)/(c) đã đề xuất (reachability filtering chặt hơn / bidirectional labeling cho OD) nếu vẫn muốn tăng tốc T4. Ghi rõ vào `main_guideline.md`: "PCF đã được xem xét và loại bằng chẩn đoán rẻ trước khi cài đặt — xem lý do ở §2.0" — đây vẫn là một kết quả hợp lệ, KHÔNG phải thất bại, đúng tinh thần Rejected có giải thích cơ chế.
| **10–25%** | Vùng xám — cài Gate T4-B (§2.3) nhưng hạ kỳ vọng ở Việc 2.4, chuẩn bị tinh thần cải thiện khiêm tốn. |
| **> 25%** | PCF có cơ sở thật để cắt nhánh đáng kể — tiến hành Gate T4-B + Việc 2.4 đầy đủ như dự kiến. |

**Không chạy lại chẩn đoán nhiều lần với tham số khác nhau cho tới khi thấy tỷ lệ đẹp** —
đo đúng 1 lần trên lưới đã khóa ở trên, đọc kết quả theo đúng ngưỡng, quyết định dứt khoát.

---

### 2.1 Cơ sở toán học

**Tính chất di truyền (đã dùng ngầm định trong dự án, giờ phát biểu tường minh):** nếu một
bundle kích thước k là khả thi (tồn tại ít nhất 1 thứ tự ghé thăm hợp lệ), thì **mọi tập
con** của nó cũng khả thi.

**Điều kiện để tính chất này đúng:** ma trận travel/distance phải thỏa **bất đẳng thức tam
giác** — bỏ bớt một điểm dừng trung gian không bao giờ làm route đến các điểm còn lại
**trễ hơn** (vì đi thẳng luôn ≤ đi vòng qua điểm đã bỏ). `instance_gen.py` **đã tự kiểm**
tính chất này (self-test tam giác, dù đã rút gọn từ O(n³) xuống lấy mẫu O(n) — xem báo cáo
2a trước) — nên điều kiện này **đã được đảm bảo**, không cần kiểm lại, chỉ cần trích dẫn.

**Hệ quả (đảo lại):** nếu 2 đơn hàng `i, j` **không thể** đi cùng nhau dưới bất kỳ thứ tự
nào trong 6 cách sắp xếp hợp lệ của cặp (P_i D_i P_j D_j, P_i P_j D_i D_j, P_i P_j D_j D_i,
và 3 hoán vị đối xứng đổi vai trò i↔j), thì **mọi bundle chứa cả i và j đều chắc chắn
infeasible** — không cần chạy DP/DFS đầy đủ cho bất kỳ tập nào chứa cặp đó.

**⚠️ Đây là điều kiện CẦN, không phải ĐỦ.** Ba đơn hàng đôi một tương thích không đảm bảo
cả ba đi chung được (thời gian tích lũy qua nhiều điểm dừng có thể hỏng dù mọi cặp riêng lẻ
đều ổn). PCF chỉ **loại sớm** các tập chắc chắn hỏng — vẫn phải chạy DP đầy đủ để xác nhận
các tập còn lại. Không được viết trong thesis rằng PCF "xác định chính xác" bundle khả thi
— chỉ là một bộ lọc cắt nhánh.

### 2.2 Đặc tả thuật toán — tích hợp trực tiếp vào Label-Setting DP, không xây cấu trúc riêng

**Không** đi theo hướng "liệt kê toàn bộ clique kích thước ≤ B trước rồi mới chạy DP" (bản
thân việc liệt kê clique cũng là bài toán tổ hợp, có thể đắt không kém). Thay vào đó, nhúng
kiểm tra tương thích **trực tiếp vào transition PICKUP** của DP đã có (§1.5.2a) — chi phí
gần như O(1) mỗi bước, tái dùng đúng vòng lặp DP hiện có.

```
BƯỚC 0 — Precompute 1 lần cho mỗi instance (trước khi chạy DP cho bất kỳ driver nào):
    compat_graph[i][j] = True/False, cho mọi cặp order (i,j) instance-wide
    (không phụ thuộc driver cụ thể nào — chỉ phụ thuộc vị trí, time window của order)

    Cách tính compat_graph[i][j]:
        thử đủ 6 thứ tự hợp lệ của cặp (i,j) — dùng ĐÚNG hàm feasibility đã có sẵn
        trong DP (không viết công thức feasibility thứ 2, tránh lặp lỗi "2 nguồn tính
        toán khác nhau" đã cảnh báo ở gate K/W trước)
        compat_graph[i][j] = True nếu ÍT NHẤT 1 trong 6 thứ tự khả thi
                              (bỏ qua ràng buộc capacity/driver cụ thể — chỉ xét
                              time window + travel, vì đây là precompute CHUNG cho
                              mọi driver, không riêng ai)

SỬA transition (a) PICKUP order j trong DP (§1.5.2):
    (a) PICKUP order j  [điều kiện CŨ giữ nguyên] AND
        [ĐIỀU KIỆN MỚI] với mọi order m ∈ IV ∪ C của label hiện tại:
            compat_graph[j][m] PHẢI = True
            (nếu có bất kỳ m nào compat_graph[j][m]=False → loại nhánh ngay,
             không tính transition)
```

**Không sửa transition DELIVERY hay "về home"** — chỉ chặn ở bước PICKUP, vì đó là lúc một
order mới được thêm vào tập đang xét.

**Không cần sửa dominance rule** — PCF là một bộ lọc *trước khi tạo label mới*, độc lập với
so sánh dominance *giữa các label đã tạo*. Hai cơ chế cắt nhánh này cộng dồn, không xung đột.

### 2.3 Validation bắt buộc — Gate T4-B (đúng khung Gate 0, không được bỏ qua)

```
Lưới: n∈{3,4,5,6,7} × B_gw∈{2,3,4,5} × B_od∈{1,2} × tw∈{60,120} × seed∈{0,1,2} ×
      spatial_mode∈{dispersed,clustered}
So sánh: route_pool (PCF bật) vs route_pool (PCF tắt, tức DP gốc) vs brute_force (oracle)
PASS = cả 3 nguồn cho CÙNG route_pool (theo Pareto-front K,W từng bundle), 0 vi phạm
```

Nếu PCF làm mất bundle hợp lệ nào (route_pool PCF-bật thiếu so với 2 nguồn kia) → PCF
**sai**, quay lại kiểm điều kiện tam giác hoặc lỗi cài đặt compat_graph, **không được** nới
lỏng gate để "cho qua".

### 2.4 Đo lợi ích thật — chỉ làm sau khi Gate T4-B PASS tuyệt đối

Chạy lại đúng curve runtime-vs-n (giống bảng A.3 báo cáo trước) nhưng thêm 1 chiều mới
`filter_mode ∈ {off, on}`, tập trung vào vùng đã biết "vỡ" trước đây:

```
n ∈ {20, 30, 50, 75}, B_gw ∈ {3, 4, 5}, tw_width ∈ {60, 120, 240}, filter_mode ∈ {off, on}
seed ∈ {0..4}  (5 seed đủ cho việc đo tốc độ, không cần 10 như gate correctness)
```

**Đo:** runtime, peak_frontier_size, theo `filter_mode` — so sánh trực tiếp on/off cùng
tham số. Đây là câu trả lời thật cho câu hỏi gốc "làm vậy có giúp T4 nhanh hơn không".

**Đọc kết quả — không có ngưỡng áp đặt trước, báo cáo trung thực:**
- Nếu `filter_mode=on` đẩy lùi được "điểm vỡ" của B_gw=4 (hiện tại vỡ trước n=50) ra xa
  hơn đáng kể → PCF là một đóng góp thật, có thể viết thành một phần của T4 trong thesis,
  và **đây chính là lời giải cho bài toán mở A-T4** — nâng cấp trạng thái từ [OPEN] lên
  [VALIDATED].
- Nếu cải thiện không đáng kể (ví dụ do phần lớn cặp order trong hộp bản đồ nhỏ đã tương
  thích với nhau, PCF hiếm khi lọc được gì) → ghi nhận trung thực, A-T4 vẫn [OPEN], không
  ép số liệu để "chứng minh PCF có ích".

---

## Việc 3 — Thiết kế lại lưới 2a/2b cho `B_GW`/`B_OD` tách rời

### 3.1 Lưới 2a (giới hạn scaling theo B) — thu gọn, không nhân chéo toàn bộ

Vì `B_OD` kỳ vọng ít ảnh hưởng (giả thuyết ở Việc 1.1, cần xác nhận nhưng không cần quét
sâu), **không nhân đầy đủ `B_gw × B_od`** — tách 2 bước:

```
Bước A — xác nhận B_od không tạo bùng nổ (rẻ, làm trước):
  n ∈ {10,30,50,75,100}, B_od ∈ {1,2}, B_gw CỐ ĐỊNH = 2 (baseline rẻ nhất),
  tw ∈ {30,60,120,240}, seed ∈ {0..4}
  → xác nhận runtime OD-side phẳng như B=2 cũ, không có gì bất ngờ

Bước B — trục chính, khảo sát B_gw mở rộng (thêm B_gw=5, trước đây chưa test):
  n ∈ {10,20,30,50,75,100}, B_gw ∈ {2,3,4,5}, B_od CỐ ĐỊNH = 2 (giá trị "thực tế" nhất
  theo giả thuyết 1.1), tw ∈ {30,60,120,240}, n_drivers ∈ {5,10}, seed ∈ {0..9},
  filter_mode ∈ {off, on}  <- gộp luôn Việc 2.4 vào đây, không chạy tách riêng
```

Bước B thay thế hoàn toàn bảng A.3 cũ (không chạy `B` chung nữa) — và đồng thời trả lời
Việc 2.4, tránh chạy 2 lần cho cùng một trục n/tw.

### 3.2 Lưới 2b (component structure) — chọn 2-3 tổ hợp `(B_gw, B_od)` đại diện

Không nhân chéo toàn bộ `B_gw × B_od` với lưới `tau × mode × supply` (sẽ quá lớn) — chọn:

```
(B_gw=3, B_od=1)   — baseline nhỏ nhất cho cả 2 lớp
(B_gw=3, B_od=2)   — B_od tăng, xem component OD có đổi không
(B_gw=5, B_od=2)   — B_gw tối đa mới, kiểm giả thuyết "GW càng lớn càng dễ gộp cụm"
```

Mỗi tổ hợp chạy đầy đủ lưới `tau∈{30,45,60} × spatial_mode(2) × supply_ratio(3) ×
seed(10)` = 180 lần/tổ hợp × 3 = 540 lần — **nhỏ hơn** lưới B=3 cũ (720) vì tau đã giảm từ
6 xuống 3 giá trị (do bỏ tau=10,15,20 — bất khả thi cấu trúc, xem patch OD trước).

---

## Việc 4 — Gộp với patch OD-corridor-bias đang chờ chạy

Patch OD-corridor-bias (`AREA_KM=8`, corridor bias 70/30, `tau∈{30,45,60}`, stable-seed) đã
được duyệt nhưng **CHƯA chạy pipeline lớn** — đây là điểm gộp:

```
Thứ tự thực hiện, MỘT lần duy nhất, không tách nhiều đợt:
1. Sửa instance_gen.py: corridor bias + AREA_KM=8 + stable_seed()      [đã duyệt trước]
2. Sửa dp_labeling.py / t6_dp.py: tách B_gw/B_od + thêm PCF             [đợt này]
3. Gate 0 (đã sửa để nhận B_gw/B_od riêng)                              → PASS trước
4. Gate T4-B (Việc 2.3, PCF correctness)                                → PASS trước
5. feasibility_rate_k1 check (đã làm ở patch trước, xác nhận lại
   với generator + B mới không đổi kết luận tau≥30 khả thi)             → xác nhận
6. run_2a.py (lưới MỚI theo Việc 3.1, gồm cả bước đo lợi ích PCF)
7. run_2b.py (3 tổ hợp B theo Việc 3.2)
8. viec1_speedup_estimate.py + viec_extra_real_wdp_speedup.py (CPLEX)
   — chạy lại trên route pool MỚI (có OD thật + PCF)
```

**Không chạy bước 6-8 của patch OD-corridor-bias riêng trước, rồi chạy lại lần 2 cho
B_gw/B_od+PCF sau** — gộp bước 1+2 thành một bản code hoàn chỉnh, qua đủ gate 3+4+5, rồi
mới chạy pipeline lớn (6-8) đúng một lần.

---

## Việc 5 — Cập nhật `main_guideline.md` (thư mục gốc) sau khi hoàn thiện

Sau khi Việc 1-4 hoàn tất và có kết quả, cập nhật các mục sau trong `main_guideline.md` để
không bị quên khi mở conversation mới:

```
[ ] §2.1 (Input) / §6.1 (Phạm vi): B (số ít) → B_GW, B_OD (tách riêng), ghi rõ lý do
    thiết kế (τ của OD gián tiếp giới hạn kích thước, GW thì không)
[ ] §T4 (Algorithm A): thêm mục "Bộ lọc tương thích cặp (PCF)" — mô tả ngắn gọn thuật
    toán (§2.2 file này), TRẠNG THÁI cuối cùng sau Việc 2.4:
      - nếu PCF có tác dụng rõ: đánh dấu [VALIDATED] — lời giải cho bài toán mở A-T4
      - nếu không: giữ [OPEN], ghi rõ đã thử PCF và mức cải thiện đo được (dù nhỏ)
[ ] §Phần A (giới hạn scaling theo B): thay bảng cũ (B chung 2-4) bằng bảng mới theo
    B_GW (2-5), B_OD cố định=2 — trích số liệu mới từ Việc 3.1 Bước B
[ ] §Phần B (component structure, Hướng A/B): thêm dòng ghi chú dữ liệu này được đo
    SAU KHI sửa OD-corridor-bias — đánh dấu rõ báo cáo cũ (component luôn ≥0.44) là
    "dữ liệu có bug OD, đã phát hiện và sửa" — không xóa, giữ làm dấu vết lịch sử
[ ] §T5 (nếu speedup thật ở Việc 4 bước 8 cho kết quả khác báo cáo cũ 0.93-0.98×):
    cập nhật lại toàn bộ kết luận T5 theo số liệu MỚI (route pool có OD thật) — đây
    là lần đo speedup thật ĐÁNG TIN CẬY ĐẦU TIÊN, vì lần trước OD gần như vắng mặt
[ ] Ghi rõ ngày cập nhật + lý do (link tới patch OD-corridor-bias + patch này) ở đầu
    main_guideline.md, để phân biệt với các đoạn nội dung chưa cập nhật kịp
```

**Không tự ý viết lại toàn bộ main_guideline.md** — chỉ sửa đúng các mục trên, giữ nguyên
cấu trúc và các phần không liên quan (T4 correctness đã PASS, Test6/6.1/6.2, v.v. không
đổi).

---

## Việc KHÔNG được làm

- Không nới lỏng Gate T4-B để "cho PCF qua" nếu nó làm mất bundle hợp lệ — nếu fail, sửa
  compat_graph hoặc quay lại kiểm điều kiện tam giác, không hạ chuẩn gate.
- Không nhân chéo đầy đủ `B_gw × B_od` cho lưới 2b — chỉ 3 tổ hợp đại diện như Việc 3.2, vì
  nhân chéo đầy đủ sẽ tái diễn đúng vấn đề "chạy hàng chục giờ" đang muốn tránh.
- Không chạy pipeline lớn (bước 6-8 Việc 4) trước khi cả Gate 0 và Gate T4-B đều PASS.
- Không tách chạy OD-corridor-bias riêng rồi B_gw/B_od+PCF riêng thành 2 lần pipeline lớn —
  gộp thành 1 lần theo đúng Việc 4.
- Không xóa/ghi đè các báo cáo cũ khi cập nhật `main_guideline.md` — chỉ thêm ghi chú
  "đã phát hiện bug, đã sửa, xem báo cáo mới" bên cạnh, giữ dấu vết lịch sử nghiên cứu.

---

## Sau khi hoàn thành

Gửi lại theo thứ tự: (1) kết quả Gate 0 + Gate T4-B, (2) bảng feasibility_rate_k1 xác nhận
lại với B mới, (3) kết quả Việc 2.4 (PCF có giúp gì không — đây là câu trả lời trực tiếp
cho câu hỏi gốc), (4) kết quả 2a/2b đầy đủ theo lưới mới, (5) so sánh speedup thật CPLEX
mới vs báo cáo cũ (0.93-0.98×) để biết liệu cả OD-fix lẫn PCF có đổi kết luận T5 hay không.

