# Test4.1 Report — Đối chứng tại n=10: compression có giữ vững khi m lớn hơn không?

**Bối cảnh:** `Test4_report.md` viết kết luận "đủ để vào thesis" cho Việc 2 (compression) và
"đáng theo đuổi" cho §5.4 (activation_rate) chỉ dựa trên grid **n≤6** (pool tối đa 6 order). Câu
hỏi đặt ra: compression/activation_rate phụ thuộc khả năng phân biệt của `Γ(R)` qua từng
`j ∈ Rem(S)`, tức phụ thuộc `m=|Rem(S)|`. Ở n≤6, m tối đa chỉ 3-4 — rất nhỏ so với quy mô chính
dự kiến (n=10-50). Test4.1 kiểm tra bằng số liệu thật tại **n=10**, thay vì suy luận suông.

**Phạm vi (đã thu hẹp có chủ đích, không chạy lại toàn bộ 6-10 giờ):**
- §5.4: **chỉ n=10** (không phải 4 giá trị {8,10,12,15}), GW/B=4/tw∈{120,240}, đủ 8 seed.
- Việc 2: **chỉ n=10**, đúng 3 ô trọng tâm của báo cáo gốc, 3 seed/ô (giữ số seed như Việc 2 gốc
  để so sánh công bằng).

**Code:** `experiments/T2BFS/t4_run_viec54_n10.py`, `t4_run_viec2_n10.py` (tái dùng logic
`run_cell`/`LB_greedy`/`UB_of`/`compute_gamma`/`filter_dominated` từ file gốc, không viết lại).

---

## 1. §5.4 (activation_rate) tại n=10 — vẫn qua ngưỡng, nhưng THẤP HƠN rõ rệt

```
n=10: total pairs=21.098, activated=6.838, activation_rate=32,4107%
n≤6:  total pairs=14.596, activated=6.415, activation_rate=43,9504%
```

| n | activation_rate |
|---|---|
| ≤6 | 43,95% |
| **10** | **32,41%** |

**Kết quả:** activation_rate **giảm ~11,5 điểm phần trăm** khi n tăng từ ≤6 lên 10 — **ngược
hướng** với giả thuyết "m lớn hơn → dễ phân biệt hơn → activation cao hơn" nêu trong câu hỏi mở
đầu. Cơ chế thực tế nhiều khả năng ngược lại: `UB_R(T) = min_{j∈T} σ_j(R)` là **min** qua nhiều
order hơn khi m lớn — càng nhiều order trong `T`, min càng dễ bị kéo xuống bởi order "khó" nhất,
làm `UB_{Rb}(T)` nhỏ hơn (dễ đạt) nhưng đồng thời `LB_{Ra}(T)` (greedy qua nhiều order hơn) cũng
tích lũy sai số/xấu đi nhanh hơn — cần T càng lớn (m càng lớn khi xét `|T|≤2` trên nền m lớn hơn)
thì rule càng khó kích hoạt đồng thời cho MỌI T.

**Vẫn PASS ngưỡng "≥10%, đáng theo đuổi"** (32,41% ≫ 10%) — kết luận định tính của báo cáo gốc
**không đổi**, nhưng biên độ an toàn hẹp hơn nhiều so với con số 43,95% ban đầu gợi ý. Không có
cơ sở để nói activation_rate "còn giữ vững" theo nghĩa ổn định — nó **giảm có hệ thống theo n**,
và **chưa biết xu hướng này có tiếp tục giảm qua ngưỡng 10% ở n=20-50 hay không** (ngoài phạm vi
đã đo).

---

## 2. Việc 2 (compression) tại n=10 — kém đi rõ rệt so với n≤6

| Ô | n≤6 D2 | **n=10 D2** | n≤6 D3 | **n=10 D3** |
|---|---|---|---|---|
| GW, B=4, k=3, tw=120 | 0,0667 (rất tốt) | **0,1444** (có giá trị) | 0,1760 | **0,2701** |
| GW, B=4, k=3, tw=240 | 0,0611 (rất tốt) | **0,1222** (có giá trị) | 0,1000 (rất tốt) | **0,2556** (có giá trị) |
| GW, B=3, k=2, tw=240 | 0,500 (yếu) | **0,667** (yếu) | 0,667 (yếu) | **0,833** (sát ngưỡng vô dụng) |

**Compression kém đi ở CẢ 3 ô**, cùng hướng với §5.4 — xác nhận cùng một cơ chế đang chi phối cả
hai: **m lớn hơn không giúp `Γ(R)` phân biệt route tốt hơn; ngược lại, dominance khó xảy ra hơn**
khi phải đồng thời tốt hơn trên nhiều `j∈Rem(S)` hơn (điều kiện `∀j∈Rem(S)` trong định nghĩa D2/D3
càng khó thỏa khi Rem(S) càng lớn — mỗi order thêm vào là một điều kiện ràng buộc bổ sung phải
đồng thời đúng để một route dominate route khác).

**Thay đổi kết luận cụ thể so với báo cáo gốc:**
- **GW,B=4,k=3,tw=120 (D2)**: từ "rất tốt" (≤0,10) → **"có giá trị"** (0,10–0,40). Không còn đạt
  ngưỡng cao nhất khi n=10.
- **GW,B=4,k=3,tw=240 (D3)**: từ "rất tốt" → **"có giá trị"**, D2 vẫn giữ "có giá trị" nhưng
  tăng gấp đôi (0,061→0,122).
- **GW,B=3,k=2,tw=240**: vẫn "yếu" ở cả 2 mức n, nhưng D3 (0,833) giờ sát ngay ngưỡng "vô dụng"
  (>0,80).

**Không ô nào đảo chiều hoàn toàn** (không ô nào rơi xuống "vô dụng" hay tăng lên "rất tốt") —
nhưng xu hướng nhất quán, đơn điệu tăng (kém đi) theo n ở mọi ô đã đo là dấu hiệu đáng lưu ý cho
main experiment (n=10-50): **không nên trích dẫn con số n≤6 làm đại diện cho quy mô thật.**

---

## 3. Kết luận sửa đổi cho Test4_report.md

Câu "**Đủ để viết vào thesis**" (§7 báo cáo gốc, dựa trên n≤6, D2 median 0,061–0,067 ở 2/3 ô
trọng tâm) cần được **làm rõ điều kiện phạm vi**, không rút lại hoàn toàn:

1. **Định tính vẫn đúng**: compression rất tốt/có giá trị đúng ở k gần B, tw lớn (xu hướng không
   đổi giữa n≤6 và n=10); §5.4 vẫn đáng theo đuổi (32% ≫ ngưỡng 10%).
2. **Định lượng cần cập nhật**: các con số cụ thể "0,061" "43,95%" trong báo cáo gốc là **cận
   dưới lạc quan** đo trên pool quá nhỏ (n≤6) — con số thật ở quy mô main experiment (n=10-50)
   nhiều khả năng **kém hơn**, và Test4.1 đã đo trực tiếp mức kém đi tại 1 điểm (n=10): compression
   D2/D3 tăng gấp đôi ở 2/3 ô, activation_rate giảm ~26% tương đối.
3. **Chưa xác định được điểm giới hạn**: dữ liệu hiện có (n≤6 và n=10, chỉ 2 điểm) đủ để xác nhận
   **có xu hướng kém đi theo n** nhưng KHÔNG đủ để ngoại suy compression/activation_rate ở n=20-50
   sẽ còn nằm trong ngưỡng "đáng dùng" hay không. Đây là **việc cần làm tiếp** trước khi khoá kết
   luận cuối cùng cho thesis, không phải kết luận của vòng đo này.

---

## 4. File

| File | Nội dung |
|---|---|
| `Output/Test4/activation_rate_n10.csv` | 16 dòng — §5.4 tại n=10 |
| `Output/Test4/compression_n10.csv` | 855 dòng — Việc 2, 3 ô trọng tâm tại n=10 |
| `experiments/T2BFS/t4_run_viec54_n10.py` | Runner §5.4 @ n=10 |
| `experiments/T2BFS/t4_run_viec2_n10.py` | Runner Việc 2 @ n=10, 3 ô mục tiêu |

Tổng thời gian chạy: §5.4 @ n=10 = 387,5s (~6,5 phút); Việc 2 @ n=10 = 405,1s (~6,8 phút) — đúng
như dự kiến, rẻ hơn nhiều so với 6-10 giờ của việc chạy toàn bộ grid lớn {8,10,12,15} × mọi B/k/tw.
