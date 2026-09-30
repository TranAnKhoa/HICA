# Test5 — Self-Survival Bound: cắt route một chiều, không cần route đối chứng

**Spec liên quan:** `Guideline/Test4.md`, `Guideline/Test4.1` (đối chứng n=10), reference
`HICA-S Algorithm A.md`. **Đọc trước:** kết luận Test4 Việc 4 (dominance cặp D2/D3 depth-1
KHÔNG sound ở d≥2, violation 66–72%) và §5.4 (rule LB≥UB, activation 44%→32% khi n=6→10, xu
hướng giảm chưa rõ điểm dừng).

**Ý tưởng cốt lõi, khác biệt với mọi thứ đã thử trước:** mọi rule ở Test3/Test4 đều là
**so sánh giữa hai route** (`Γ(R_a) ⪰ Γ(R_b)` ⟹ xoá `R_b`). Test5 thử một loại rule khác hẳn:
**khảo sát một route với chính nó**, không cần route đối chứng nào:

```
Route R có tự cứu được mình không, tức: tồn tại cách chèn đủ d = B−k đơn hàng nữa
(lấy từ Rem(S)) sao cho kết quả vẫn khả thi (slack ≥ 0)?

Nếu KHÔNG — bằng một cận rẻ, không cần enumerate — thì xoá R. AN TOÀN TUYỆT ĐỐI,
vì đây không phải so sánh "ai tốt hơn ai", mà là kết luận "R chắc chắn chết", đúng với
định lý downward-closedness đã có (reference §2.3) áp dụng cho chính R.
```

**Vì sao rule này không mắc lỗi của D2/D3 ở d≥2:** D2/D3 sai vì chúng dùng một route khác
(route "tốt hơn") để **thay thế** route bị xoá — và hai route có tập cạnh khác nhau nên
"tốt hơn" không di truyền sang tương lai đúng cách. Rule ở đây **không thay thế ai bằng ai**
— nó chỉ khẳng định về chính R: nếu cận trên (upper bound) của khả năng sống sót của R là
âm, R chết, chấm hết, không liên quan gì đến route khác. Đây chính là bản chất của
`slack_star`/`FILTER_SLACK_STAR` (reference §3) và `Feas(R)` (Test4 D1) — Test5 mở rộng ý
tưởng đó ra depth d ≥ 2 thay vì chỉ depth 1.

**Cảnh báo phải nhớ trước khi code:** "cứu được không" **không được** trả lời bằng cách thử
MỘT cách chèn cụ thể (ví dụ "cách chèn slack cao nhất ngay lúc đó") — đây là đúng lỗi đã bị
Test3/Test4 bác bỏ (chọn 1 đại diện thay vì xét cận đúng nghĩa). Phải dùng một **cận trên**
(upper bound) sao cho: nếu cận nói "không cứu được" thì chắc chắn không có tổ hợp chèn nào
cứu được, dù chưa thử hết tổ hợp.

---

## 0. Định nghĩa cận — UB_R(d)

Tái dùng hạ tầng đã có từ Test4 (`σ_j(R)`, `Γ(R)`), không viết lại:

```
σ_j(R) = max slack đạt được khi chèn riêng lẻ order j vào R    (đã có, Test4 §0.4)
Rem(S) = order khả thi đơn lẻ còn lại, |Rem(S)| = m            (đã có, Test4 §0.3)
```

**Cận UB cấp 1 (rẻ nhất, dùng ngay được):**

```
UB1_R(d) = tổng d giá trị σ_j(R) LỚN NHẤT trong { σ_j(R) : j ∈ Rem(S) }
```

Đây là cận trên **lạc quan nhất có thể** theo nghĩa tổ hợp: nó giả định d order tốt nhất khi
chèn riêng lẻ có thể cùng lúc đạt slack tốt của mình **mà không cản nhau và không cộng dồn
delay cho nhau**. Đây rõ ràng là một cận lỏng (tổng của các max riêng lẻ luôn ≥ slack thật
khi chèn cùng lúc, vì mỗi lần chèn thêm chỉ có thể giữ nguyên hoặc làm giảm slack còn lại của
những lần chèn sau — chứng minh trực tiếp từ downward-closedness reference §2.3 áp dụng lặp).

**Vì sao lấy TỔNG chứ không phải MIN (khác `UB_R(T) = min_j σ_j(R)` đã dùng ở Test4 §5.4):**
`min` là cận đúng cho "chèn 1 order bất kỳ trong T", còn ở đây ta cần cận cho "chèn ĐỦ d order
cùng lúc" — dùng min sẽ quá lỏng theo chiều ngược (không phản ánh việc mỗi lần chèn đều ăn vào
slack chung). Cả hai cận đều **sound** (một chiều, không sai), nhưng phục vụ câu hỏi khác nhau.
Test5 dùng **cả hai**, xem §2, để so sánh độ chặt.

**Rule dùng UB1:**
```
if UB1_R(d) < 0:  XOÁ R      # an toàn tuyệt đối theo lập luận trên
```

**Cận UB cấp 2 (chặt hơn, tốn thêm chút chi phí — tuỳ chọn, làm nếu UB1 quá lỏng):**

```
UB2_R(d) = max over mọi tổ hợp {j1,...,jd} ⊆ Rem(S), |{j1..jd}|=d, của:
              min_{j ∈ {j1..jd}} σ_j(R)
```
tức: duyệt `C(m,d)` tổ hợp, với mỗi tổ hợp lấy **min** (giống logic Test4 §5.4), rồi lấy
**max** qua các tổ hợp. Vẫn chưa phải enumerate insertion — chỉ tổ hợp trên `σ_j` đã tính sẵn,
chi phí `O(C(m,d))`, rẻ hơn hẳn enumerate vị trí chèn thật.

```
UB2_R(d) ≤ UB1_R(d)     luôn đúng (dễ chứng minh: min ≤ từng phần tử ≤ trong top-d, tổng > 1 phần tử)
```
Cận UB2 **chặt hơn hoặc bằng** UB1. Cả hai đều sound; UB2 tốn hơn nhưng cắt được nhiều hơn.

---

## 1. Việc 1 — ★ Gate exactness (bắt buộc trước mọi thứ khác)

Đây là gate quan trọng nhất: rule chỉ được dùng nếu nó **không bao giờ xoá nhầm** một route
mà thực ra có thể mở rộng đủ d order để khả thi.

### Cách chạy — trên grid nhỏ (n≤6, có ground truth từ Test2/Test4)

```
for mỗi instance, mỗi subset S (|S|=k, d = B-k, d ≥ 1):
    for mỗi R ∈ Seq(S):
        ub1 = UB1_R(d)
        ub2 = UB2_R(d)
        actually_survives = BRUTE_FORCE kiểm: tồn tại ít nhất 1 tổ hợp d order từ Rem(S)
                             và 1 cách chèn toàn bộ khiến route cuối khả thi (slack ≥ 0)?

        violation_UB1 = (ub1 < 0) AND (actually_survives == True)
        violation_UB2 = (ub2 < 0) AND (actually_survives == True)
```

### Ngưỡng — BẮT BUỘC

```
violation_UB1 phải = 0 TUYỆT ĐỐI trên toàn bộ grid nhỏ
violation_UB2 phải = 0 TUYỆT ĐỐI trên toàn bộ grid nhỏ
```

Đây không phải ngưỡng thống kê (như compression) — đây là kiểm chứng một khẳng định **sound
hay không sound**. Một vi phạm duy nhất nghĩa là chứng minh lỏng ở đâu đó (rất có thể ở bước
"mỗi lần chèn chỉ giữ nguyên hoặc giảm slack còn lại" khi áp dụng cho **chèn đồng thời nhiều
order**, chứ không phải chèn tuần tự từng cái một — đây là chỗ dễ sai nhất, xem §1.1).

Nếu có violation: **dừng ngay, in phản ví dụ đầy đủ** (S, R, Rem(S), d, tổ hợp order thật sự
cứu được route, UB1/UB2 tính được), không chạy tiếp bất kỳ việc nào bên dưới.

### 1.1 Điểm cần cẩn thận nhất khi cài đặt

`σ_j(R)` trong Test4 được tính bằng cách chèn **riêng lẻ** j vào R **gốc** (chưa có j' nào
khác). Khi kiểm `actually_survives`, brute force phải chèn **tuần tự** d order vào **cùng một
route đang bị biến đổi dần** (route sau khi chèn j1 mới là nền để chèn j2, không phải chèn cả
hai vào R gốc song song rồi hợp kết quả). Đây chính là điểm khác biệt giữa "cận" (UB, tính trên
R gốc, không cần biết thứ tự) và "giá trị thật" (phải mô phỏng đúng trình tự chèn tuần tự).
Nếu cài sai chỗ này (ví dụ tính `actually_survives` cũng trên R gốc song song thay vì tuần
tự), gate sẽ pass giả — **phải dùng đúng `bfs_generate` gốc của Test2/Test4 làm brute force**,
không viết lại logic mô phỏng insertion từ đầu.

---

## 2. Việc 2 — So sánh độ chặt và chi phí giữa UB1 và UB2

Trên cùng grid đã chạy Việc 1, với mọi `(S, R)` mà **cả hai đều PRUNE được** (không phải chỗ
một trong hai lỡ giữ), ghi nhận:

```
tight_ratio = UB2_R(d) / UB1_R(d)     (khi cả hai cùng dấu, để so độ chặt)
extra_prune_by_UB2 = số (S,R) mà UB2 < 0 NHƯNG UB1 ≥ 0   (UB2 cắt được, UB1 bỏ lỡ)
cost_ratio = t(UB2) / t(UB1)
```

**Đọc kết quả:**
- Nếu `extra_prune_by_UB2` nhỏ (≈0) → UB1 đã đủ, dùng UB1 cho rẻ, không cần UB2.
- Nếu `extra_prune_by_UB2` đáng kể (>10% số route bị lọt qua UB1) và `cost_ratio` chấp nhận
  được (≤5×, vì `C(m,d)` với `d≤3,4` và `m≤15` vẫn nhỏ) → dùng UB2.

---

## 3. Việc 3 — Đo tỷ lệ prune thật (prune_rate), đây là con số quyết định

Khác với Test4 (đo compression = tỷ lệ route **giữ lại** sau lọc theo cặp), Test5 đo tỷ lệ
route **bị xoá hẳn** bởi rule một chiều — hai đại lượng bổ trợ, không thay thế nhau, vì Test5
có thể chạy **trước** Test4's D2/D3 như một bước lọc thô rẻ hơn.

```
prune_rate_UB1(S) = |{ R ∈ Seq(S) : UB1_R(d) < 0 }| / |Seq(S)|
prune_rate_UB2(S) = |{ R ∈ Seq(S) : UB2_R(d) < 0 }| / |Seq(S)|
```

**Chạy trên đúng 3 ô trọng tâm của Test4 §3** (nơi bùng nổ nặng nhất), cả grid nhỏ (n≤6) VÀ
tại n=10 (đối chứng, theo đúng bài học Test4.1: đo một điểm ngoài n≤6 trước khi kết luận):

```
GW, B=4, k=2 (d=2), tw=120
GW, B=4, k=2 (d=2), tw=240
GW, B=3, k=1 (d=2), tw=240
```

Lưu ý: **k ở đây khác Test4 §3** — Test4 đo compression tại `k=B-1` (d=1) và `k=2` cho ô thứ
3; Test5 cố tình chọn `k` sao cho `d=2` xuyên suốt, vì đây là vùng D2/D3 đã biết fail
(Test4 Việc 4) và Test5 muốn biết rule một chiều có cứu được vùng đó không — đúng câu hỏi mở
đầu hội thoại.

### Ngưỡng đọc kết quả (khoá trước khi chạy)

| median prune_rate tại 3 ô trên | Kết luận |
|---|---|
| ≥ 0,30 | **Có giá trị rõ** — cắt được ≥30% route trước khi cần enumerate gì, an toàn tuyệt đối, không cần route đối chứng. Kết hợp thêm với D2/D3 (Test4) hoặc §5.4 cho phần còn lại. |
| 0,05 – 0,30 | **Biên** — có ích nhưng khiêm tốn, cần cân nhắc so với chi phí tính `σ_j` (đã trả ở Test4 rồi nếu chạy chung pipeline — xem §4). |
| < 0,05 | **Gần như vô dụng** ở vùng d=2 GW. Ghi nhận và đóng hướng self-survival cho d≥2; hướng còn lại quay về §5.4 (cặp so sánh) hoặc arc-charging/PMTN. |

---

## 4. Việc 4 — Chi phí cận biên (marginal cost), vì hạ tầng đã có sẵn từ Test4

**Điểm quan trọng cần làm rõ trong report:** nếu pipeline đã chạy Test4 (tính `σ_j(R)` cho
mọi route để phục vụ D2/D3/§5.4), thì `UB1_R(d)` gần như **miễn phí** — chỉ cần sort các
`σ_j` đã có sẵn và lấy tổng top-d, `O(m log m)`. Đo và báo cáo:

```
t_marginal_UB1 = thời gian tính UB1 cho toàn bộ Seq(S), GIẢ SỬ σ_j đã có sẵn từ Test4
t_marginal_UB2 = tương tự, cho UB2 (thêm C(m,d) tổ hợp)
```
so với `t_profile` đã đo ở Test4 Việc 3 — kỳ vọng `t_marginal ≪ t_profile` vì không cần tính
lại `σ_j` từ đầu.

**Nếu Test5 chạy độc lập, không có sẵn `σ_j`** thì phải cộng thêm chi phí tính `σ_j` (bằng
đúng `t_profile` của Test4) — ghi rõ trường hợp nào đang đo trong report, đừng nhập nhằng.

---

## 5. Grid và tham số — giữ nguyên, không đổi gì

Dùng đúng generator, đúng patch OD, đúng tham số đã khoá xuyên suốt Test2→Test4.1:
```
n_orders: {3,4,5,6} (grid nhỏ, Việc 1) · {10} (đối chứng Việc 3, theo đúng lý do Test4.1)
B: {3, 4}          (chỉ cần B đủ để có d=2; không cần quét B=2 vì d=2 đòi hỏi B≥3)
tw_width: {30, 60, 120, 240}
tau: {15, 30, 60}   (OD, dùng generator đã patch, chỉ chạy cell đạt feasibility_rate_k1≥0.5)
SEEDS_PER_CELL: 8 (Việc 1) · 3 (Việc 3, n=10 — giữ nhất quán với Test4.1)
capacity = B, speed = 20km/h, service = 5 phút, area = 10km   (không đổi)
```

**Trọng tâm là GW**, cùng lý do đã nêu ở Test4 §6 (OD bundling k≥2 hiếm, không đủ thống kê).

---

## 6. Thứ tự thực thi và điều kiện dừng

```
Việc 1  →  BẤT KỲ violation nào (UB1 hoặc UB2)  ⟹  DỪNG NGAY, tìm lỗi chứng minh
        ↓ pass tuyệt đối (kỳ vọng)
Việc 2  (so UB1 vs UB2, không có điều kiện dừng, chỉ để quyết dùng cái nào)
        ↓
Việc 3  →  median prune_rate < 0,05 ở CẢ 3 ô  ⟹  đóng hướng self-survival cho d≥2,
                                                    ghi nhận, không chạy Việc 4
        ↓ (nếu có ít nhất 1 ô ≥ 0,05)
Việc 4  (đo chi phí cận biên, để biết net gain thật khi tích hợp vào pipeline Test4)
```

---

## 7. Những điều KHÔNG được làm

1. **Không** kết luận "route cứu được" bằng cách thử một cách chèn cụ thể rồi dừng — phải
   dùng UB1/UB2 (cận), hoặc brute force đầy đủ khi làm ground truth cho Việc 1.
2. **Không** nhầm `UB_R(T) = min_j σ_j(R)` (cận cho "chèn 1 order bất kỳ trong T", dùng ở
   Test4 §5.4) với `UB1_R(d) = tổng top-d` hay `UB2_R(d)` (cận cho "chèn ĐỦ d order cùng
   lúc", dùng ở Test5) — ba đại lượng này trả lời ba câu hỏi khác nhau, đừng gộp code.
3. **Không** tính `actually_survives` (ground truth Việc 1) bằng cách chèn song song vào R
   gốc — phải chèn tuần tự, route sau biến đổi làm nền cho chèn tiếp theo (§1.1).
4. **Không** đọc bid ở bất kỳ đâu — `Rem(S)`, `σ_j`, `UB1`, `UB2` đều là hàm của dữ liệu công
   khai. Regression: đổi bid không đổi bất kỳ giá trị prune nào.
5. **Không** so sánh prune_rate của Test5 với compression của Test4 như hai con số cùng loại
   — Test4 đo tỷ lệ **giữ lại** sau lọc cặp (so sánh giữa các route), Test5 đo tỷ lệ **xoá**
   bởi lọc một chiều (không so sánh). Một route có thể sống sót Test5 (không tự chết) nhưng
   vẫn bị lọc bởi Test4 D2/D3 (có route khác tốt hơn) — hai bộ lọc áp dụng nối tiếp, không
   phải hai cách đo cùng một thứ.
6. **Không** điều chỉnh ngưỡng ở §3 sau khi thấy kết quả — ngưỡng đã khoá trong file này.

---

## 8. Báo cáo cần trả về

`Test5_report.md`, theo đúng cấu trúc Test2–Test4:

1. Sai lệch so với spec (nếu có), công khai ngay đầu file.
2. Bảng gate Việc 1 (UB1, UB2) — pass/fail tuyệt đối, kèm phản ví dụ nếu fail.
3. So sánh UB1 vs UB2 (Việc 2): độ chặt, chi phí, khuyến nghị dùng cái nào.
4. Bảng prune_rate theo 3 ô trọng tâm, cả n≤6 và n=10 — đọc theo đúng ngưỡng §3.
5. Chi phí cận biên (Việc 4) nếu chạy tới.
6. Kết luận: self-survival bound có phải một rule bổ trợ đáng đưa vào Algorithm A hay không,
   và nếu có, nó cắt được phần nào của bùng nổ mà D2/D3 (Test4) và §5.4 chưa cắt được.