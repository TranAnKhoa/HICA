# Test5 Report — Self-Survival Bound (UB1/UB2, cắt route một chiều)

**Bối cảnh:** Test4 Việc 4 xác nhận dominance cặp D2/D3 (depth-1, so sánh route với route
khác) KHÔNG sound ở d≥2 (violation 66-72%); §5.4 (rule LB≥UB thay thế cặp) hoạt động nhưng
activation_rate giảm dần theo n (44%→32% khi n=6→10, xu hướng chưa rõ điểm dừng — xem Test4.1).
Test5 thử một hướng khác hẳn: **rule một chiều, không cần route đối chứng** — route R tự hỏi
"tôi có tự cứu được mình không" bằng một cận trên (UB) trên chính `Rem(S)`, xoá R nếu cận < 0.

**Sai lệch so với spec:** không có. Grid, ngưỡng, cấu trúc gate đúng như `Test5.md` §5, §3.
`N_ORDERS_VIEC1 = {3,4,5,6}` (không phải `t2_gen.N_ORDERS_SMALL = {4,5,6}` — thêm n=3 theo yêu
cầu spec §5, cần thiết để B=3,k=1,d=2 có instance nhỏ nhất).

**Code:** `experiments/T2BFS/t5_ub.py` (UB1/UB2), `t5_run_viec1.py` (gate), `t5_run_viec2.py`
(so UB1 vs UB2), `t5_run_viec3.py` (prune_rate thật). Tái dùng `t4_profile.py` (`sigma_j`,
`compute_gamma`, `reachable_orders`) và `t4_run_viec4.bfs_from_front` (động cơ chèn tuần tự
cho ground truth) — không viết lại logic insertion, đúng cảnh báo §1.1/§7.3 của spec.

---

## 1. Việc 1 — Gate exactness: PASS TUYỆT ĐỐI

```
Grid: n∈{3,4,5,6}, B∈{3,4} (n≥B), tw_width∈{30,60,120,240}, GW, SEEDS_PER_CELL=8
Tổng (S,R) đã kiểm: 62.728
violation_UB1: 0
violation_UB2: 0
```

Không một vi phạm nào trên toàn bộ grid nhỏ: mọi lần `UB1_R(d) < 0` hoặc `UB2_R(d) < 0`, route
đó **thực sự** không tự cứu được (đối chiếu brute-force chèn tuần tự qua `bfs_from_front`, đúng
động cơ BFS gốc — không mô phỏng riêng). Chứng minh sound trong `Test5.md` §0 (downward-
closedness áp dụng lặp) **không bị bác bỏ** trong phạm vi đã kiểm — khác hẳn số phận của
Pareto-dominance (Test3) và D2/D3 depth-1 ở d≥2 (Test4 Việc 4), cả hai đều bị bác bỏ bằng phản
ví dụ cụ thể. Đây là kết quả tích cực quan trọng nhất của Test5: **rule một chiều này an toàn
tuyệt đối, không có ngoại lệ đã tìm thấy.**

File: `Output/Test5/gate_viec1.csv` (62.728 dòng).

---

## 2. Việc 2 — UB1 vs UB2: UB1 đã đủ, không cần UB2

```
total (S,R): 62.728
UB1 prune: 718 (1,1446%)
UB2 prune: 718 (1,1446%)
extra_prune_by_UB2 (UB2<0, UB1≥0): 0 (0,0000%)
tight_ratio median (UB2/UB1, cùng dấu): 1,0
cost_ratio (t_UB2/t_UB1): 2,10×
```

`extra_prune_by_UB2 = 0` **tuyệt đối** trên toàn bộ 62.728 điểm — UB2 (chặt hơn về lý thuyết,
tốn `O(C(m,d))`) không bao giờ cắt được thứ mà UB1 (rẻ, `O(m log m)`) đã bỏ lỡ, trên grid này.
`tight_ratio` median = 1,0 nghĩa là khi cả hai cùng dấu, chúng thường **bằng nhau tuyệt đối** —
gợi ý rằng khi `d` order tốt nhất theo `σ_j` không "cản nhau" (trường hợp phổ biến ở GW, route
ngắn, `d≤2`), tổng top-d và max-min qua tổ hợp trùng nhau tự nhiên.

**Đọc theo ngưỡng khoá sẵn (§2 spec):** `extra_prune_by_UB2 ≈ 0` → **dùng UB1**, không cần UB2.
Tất cả kết quả Việc 3 dưới đây dùng UB1 theo đúng khuyến nghị này.

File: `Output/Test5/viec2_ub_compare.csv`.

---

## 3. Việc 3 — prune_rate thật: BẰNG 0 TUYỆT ĐỐI ở cả 3 ô trọng tâm

```
                         median prune_rate
Ô                        n≤6        n=10
GW,B=4,k=2(d=2),tw=120   0,0000     0,0000
GW,B=4,k=2(d=2),tw=240   0,0000     0,0000
GW,B=3,k=1(d=2),tw=240   0,0000     0,0000
```

Không phải gần 0 — **đúng 0 tuyệt đối**: kiểm tra trực tiếp trên toàn bộ 916 subset / 4.702
route ở 3 ô này, `n_pruned=0` ở **mọi dòng**, không một route nào bị UB1 cắt.

**Đọc theo ngưỡng khoá sẵn (§3 spec):**
```
< 0,05  →  Gần như vô dụng ở vùng d=2 GW. Đóng hướng self-survival cho d≥2.
```
Cả 3 ô đều rơi vào mức này, rõ ràng và dứt khoát (0,0000 ≪ 0,05, không phải biên). **Theo §6
(thứ tự thực thi), Việc 4 (chi phí cận biên) BỊ BỎ QUA** — spec quy định rõ chỉ chạy Việc 4 khi
có ≥1 ô đạt ngưỡng ≥0,05.

File: `Output/Test5/viec3_prune_rate.csv`.

### 3.1 Vì sao 0 tuyệt đối — không phải lỗi, có cơ chế rõ

Đối chiếu lại với 718 lần UB1 thực sự cắt được ở Việc 1/2 (trên toàn bộ grid, không giới hạn 3
ô), toàn bộ 718 lần này rơi vào `tw_width ∈ {30, 60}` — **không một lần nào ở `tw_width ∈
{120, 240}**:

```
(n=4,k=3,d=1,tw=60): 239   (n=6,k=3,d=1,tw=30): 76   (n=5,k=3,d=1,tw=60): 64
(n=4,k=2,d=2,tw=30): 48    (n=6,k=2,d=2,tw=30): 48   (n=6,k=3,d=1,tw=60): 46
... (toàn bộ 718 dòng đều tw∈{30,60})
```

3 ô trọng tâm của Test5 (đúng 3 ô "bùng nổ" của Test4 §3) đều dùng `tw_width∈{120,240}` — cửa
sổ thời gian rộng. Cơ chế: `UB1_R(d) < 0` nghĩa là ngay cả tổng slack lạc quan nhất của d order
tốt nhất cũng âm — chỉ xảy ra khi route đã rất chật (tw hẹp, ít dư địa thời gian). Ở tw rộng,
route hầu như luôn còn đủ slack để bất kỳ order khả thi đơn lẻ nào cũng "có vẻ" chèn được, nên
UB1 (vốn là cận LỎNG, lạc quan nhất có thể — chính spec §0 đã nêu rõ) gần như không bao giờ âm.
**Đây chính là điểm yếu cấu trúc của UB1: nó chặt (hữu ích) đúng ở vùng route đã chật (tw hẹp),
nhưng vùng "bùng nổ" cần cắt lại là vùng tw rộng — hai vùng không trùng nhau.**

---

## 4. Việc 4 — không chạy (theo §6, điều kiện dừng đã kích hoạt ở Việc 3)

---

## 5. Kết luận

**Self-survival bound (UB1) là một rule an toàn tuyệt đối (Việc 1 pass 0 vi phạm trên 62.728
điểm) nhưng KHÔNG PHẢI một rule bổ trợ hữu ích cho vùng bùng nổ thực tế** (tw rộng, k gần B/2 —
đúng 3 ô mà Test4 D2/D3 và §5.4 đang cố giải quyết). Prune_rate = 0 tuyệt đối tại các ô đó, dưới
xa ngưỡng "gần như vô dụng" (<0,05).

Điều này **không mâu thuẫn** với việc UB1 sound tuyệt đối — nó chỉ có nghĩa cận UB1 quá lỏng
đúng ở vùng cần cắt. Cơ chế đã xác định rõ (§3.1): route chỉ "chắc chắn chết" theo UB1 khi cửa
sổ thời gian đã chật sẵn — một điều kiện gần như loại trừ lẫn nhau với vùng bùng nổ (tw rộng).

**Không cần thử UB2** — Việc 2 đã xác nhận UB2 không cắt được gì thêm so với UB1 trên toàn bộ
grid (extra_prune=0), nên kết luận "vô dụng ở vùng bùng nổ" áp dụng cho cả hai biến thể, không
chỉ riêng UB1.

**Hướng còn lại quay về đúng như spec §3 đã dự liệu**: §5.4 (rule cặp LB≥UB, Test4) vẫn là
hướng khả thi duy nhất đã có tín hiệu dương cho d≥2 (activation 32-44% tuỳ n) — Test5 không thay
thế được nó, chỉ xác nhận thêm rằng lối tắt "rẻ hơn, không cần route đối chứng" không tồn tại ở
vùng tw rộng. Self-survival có thể vẫn có giá trị như một **bộ lọc tiền xử lý rẻ** cho vùng tw
hẹp (nơi nó cắt 1,14% trên toàn grid, tập trung ở `tw∈{30,60}`) trước khi chạy D2/D3/§5.4, nhưng
đây là lợi ích phụ, nhỏ, khác hẳn kỳ vọng ban đầu ("cắt được phần bùng nổ mà D2/D3 chưa cắt
được" — không đúng ở tw rộng).

---

## 6. File

| File | Nội dung |
|---|---|
| `Output/Test5/gate_viec1.csv` | 62.728 dòng — gate Việc 1, UB1/UB2 + ground truth |
| `Output/Test5/viec2_ub_compare.csv` | So sánh UB1/UB2 (độ chặt, chi phí) |
| `Output/Test5/viec3_prune_rate.csv` | 916 dòng — prune_rate thật tại 3 ô trọng tâm, n≤6 và n=10 |
| `experiments/T2BFS/t5_ub.py` | `UB1_R(d)`, `UB2_R(d)` |
| `experiments/T2BFS/t5_run_viec1.py` | Gate exactness |
| `experiments/T2BFS/t5_run_viec2.py` | So UB1 vs UB2 |
| `experiments/T2BFS/t5_run_viec3.py` | prune_rate tại 3 ô, n≤6 + n=10 |

Tổng thời gian chạy: Việc 1 ≈ 480s (8 phút), Việc 2 ≈ vài giây (đọc lại CSV), Việc 3 ≈ 69s —
toàn bộ Test5 xong trong khoảng 10 phút, rẻ hơn nhiều so với Test4.
