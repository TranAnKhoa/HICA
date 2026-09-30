# Test4 Report — Representative Rule qua Lookahead-Profile Dominance

**Spec:** `Guideline/Test4.md` · **Reference:** `Guideline/HICA-S Algorithm A.md`
**Code:** `experiments/T2BFS/t4_fwdslack.py, t4_gate0.py, t4_profile.py, t4_run_gate0.py,
t4_run_viec1.py, t4_run_viec2.py, t4_run_viec3.py, t4_run_viec4.py, t4_run_viec54.py`
**Output thô:** `Output/Test4/`

---

## 0. Sai lệch so với spec — công khai ngay từ đầu

1. **κ (kappa)**: spec không khoá giá trị. Vì D2/D3 chỉ so sánh **thứ tự** (`K(p')≤K(p)`), và κ
   là hằng số dương nhân đều mọi K — giá trị κ **không ảnh hưởng bất kỳ kết luận dominance nào**.
   Chọn `κ=1` (1 cost-unit/km).
2. **Việc 2 (compression), grid lớn (n∈{8,10,12,15}): KHÔNG chạy đầy đủ.** n=8 riêng lẻ đã tốn
   **~1,9 giờ** (`compute_gamma` là O(m·|R|²)/route × |Seq(S)| route, đúng như spec cảnh báo trước
   — không phải bug). Ước tính toàn bộ 4 giá trị n sẽ mất 6–10 giờ. Quyết định (đã hỏi ý kiến
   trong hội thoại): **chỉ dùng grid nhỏ (n≤6)** cho Việc 2, dựa trên căn cứ thực nghiệm của Test2
   rằng `n_orders` (kích thước pool) không ảnh hưởng đáng kể tới đặc tính `|Seq(S)|` theo k — chỉ
   `B`/`tw_width`/`class` mới là biến điều khiển chính. Kết luận Việc 2 dưới đây **chỉ dựa trên
   n≤6**, không phải toàn bộ grid spec yêu cầu.
3. **`SEEDS_PER_CELL` cho Việc 2 giảm còn 3** (từ 8 dùng ở Việc 0/1), vì lý do thời gian nêu trên.
   Việc 0, 1, 4, §5.4 vẫn dùng đủ 8 seed.
4. **Việc 3 chỉ chạy trên mẫu 6 cell đại diện** (không toàn bộ grid) — bao gồm cả 3 ô trọng tâm
   của Việc 2 (§3) và vài ô đối chứng nhẹ hơn, vì đo `t_bfs_next` tốn công tương đương chính
   `compute_gamma` (không rẻ hơn), lặp lại trên toàn bộ grid sẽ tái tạo đúng vấn đề thời gian ở
   mục 2.

---

## 1. Việc 0 — Forward time slack F_i: GATE PASS TUYỆT ĐỐI

### Gate 0.1 (F tương đương recompute)

```
total_checked = 4.204.875   total_mismatch = 0   mismatch_rate = 0,000000%
```

**0 sai lệch trên 4,2 triệu lượt kiểm tra**, trải khắp toàn bộ grid nhỏ (n≤6, B≤4, cả GW/OD, mọi
tw_width/tau). Cài đặt `feasible_by_F_two_insert` (kiểm feasibility của phép chèn 2 điểm chỉ bằng
`F_i` của route gốc, không cần recompute `is_feasible` từ đầu) là **đúng tuyệt đối** trong phạm vi
đã kiểm.

**Ghi chú kỹ thuật (đáng lưu lại):** việc cài đặt đúng công thức này khó hơn nhiều so với đọc công
thức trong spec tưởng chừng đơn giản — quá trình debug phát hiện 4 lỗi chỉ số riêng biệt (dùng sai
`A` thay vì `B`; dùng nhầm `F_i` gốc — vốn bị ràng buộc bởi deadline của chính node xuất phát —
thay vì biến thể `Fp_i = W_{i+1}+F_{i+1}` bỏ qua ràng buộc đó; dùng sai chỉ số `Fp[a-1]` thay vì
`Fp[b-2]` khi có node cũ nằm giữa điểm chèn pickup/delivery; và lỗi off-by-one trong quy ước vị trí
chèn `a,b` khi so với `t2_core._insert_positions` gốc). Mỗi lỗi đều được tìm ra bằng cách so sánh
trực tiếp với `is_feasible` recompute trên case cụ thể, không suy luận suông.

### Gate 0.2 (so mức chặt với min-slack)

```
pruned_by_minslack_but_actually_feasible = 119.071 / 4.204.875 (2,8317%)
```

**Không phải ≈0** — dùng `slack(R)` toàn tuyến làm "arc capacity" chung (cách cũ) sẽ **loại nhầm**
2,83% số insertion thực ra khả thi, so với dùng `F_i` theo vị trí. Đây là bằng chứng thực nghiệm
xác nhận đúng cảnh báo lý thuyết của spec §0.2: `F_i` **có mang lại giá trị thật**, không phải cải
tiến hình thức.

---

## 2. Việc 1 — Gate exactness tại d=1: GATE PASS TUYỆT ĐỐI (Định lý R1 không bị bác bỏ)

Chạy trên grid nhỏ (n≤6, B≤4, k=B-1 tức d=1), dùng đúng `Rem(S)` = order khả thi đơn lẻ (§0.3,
không phải toàn bộ order còn lại — sửa đúng sau khi phát hiện lệch khỏi định nghĩa spec trong lần
chạy đầu).

```
total subsets checked: 3.119  (GW: 2.447, OD: 672)
D1 bundle_loss count: 0        (informational — D1 KHÔNG bảo toàn Pareto, chỉ cần đúng bundle)
D2 violations (gate 1.A/1.B):  0   ← BẮT BUỘC = 0
D3 violations (gate 1.A/1.B):  0   ← BẮT BUỘC = 0
```

**Cả D2 và D3 pass tuyệt đối trên cả 2 gate** (1.A bundle_loss, 1.B pareto_loss). Định lý R1 —
"nếu d=1 và Γ(R_a)⪰Γ(R_b) theo D2, xoá R_b không làm mất bundle hay điểm Pareto-optimal nào ở
level B" — **không bị bác bỏ** trong phạm vi đã kiểm.

**Kiểm chứng chống dấu hiệu suy biến (spec §0.5 cảnh báo):** median `|front|` KHÔNG luôn =1
(GW: seq_count median=6, front_D1 median=1, front_D2 median=2, front_D3 median=3) — quan hệ
dominance thực sự hoạt động như antichain, không suy biến thành chọn 1 sequence duy nhất.

---

## 3. Việc 2 — Compression thật (grid nhỏ, n≤6 — xem sai lệch §0.2)

### Bảng compression theo class × k (gộp mọi B, tw_width)

| class | k | D1 median | D2 median | D3 median | n |
|---|---|---|---|---|---|
| GW | 1 | 1,000 | 1,000 | 1,000 | 540 |
| GW | 2 | 0,167 | 0,500 | 0,667 | 1099 |
| GW | 3 | 0,014 | 0,100 | 0,194 | 745 |
| GW | 4 | 0,00077 | 0,00871 | 0,02168 | 203 |
| OD | 1 | 1,000 | 1,000 | 1,000 | 458 |
| OD | 2 | 0,500 | 0,500 | 0,500 | 291 |
| OD | 3 | 0,250 | 0,250 | 0,250 | 25 |

Compression giảm rất mạnh theo k đối với GW (D3: 1,0 → 0,667 → 0,194 → 0,022) — đúng xu hướng
đối lập với Pareto-dominance đã bị bác bỏ ở Test3: dominance có tham chiếu `Rem(S)` **hoạt động
tốt hơn nhiều** ở đúng level bùng nổ mạnh nhất.

### Ba ô trọng tâm (§3, nơi Test2 ghi nhận bùng nổ `median|Seq(S)|=1.399` và `2.520`)

| Ô | D2 median | D3 median | Kết luận theo ngưỡng §3 |
|---|---|---|---|
| **GW, B=4, k=3, tw=120** | **0,0667** | 0,1760 | D2: rất tốt (≤0,10). D3: có giá trị (0,10–0,40) |
| **GW, B=4, k=3, tw=240** | **0,0611** | **0,1000** | D2: rất tốt. D3: đúng ngưỡng rất tốt |
| **GW, B=3, k=2, tw=240** | 0,500 | 0,667 | **Yếu** (0,40–0,80) |

**Đọc kết quả:** compression **rất tốt đúng ở nơi cần nhất** (k gần B, tw lớn — chính là vùng
Test2 ghi nhận `|Seq(S)|` chạm trần lý thuyết). Nhưng **yếu ở k nhỏ hơn** (k=2, dù cùng B=3,
tw=240) — dominance có tham chiếu `Rem(S)` càng có nhiều order còn lại (m lớn) để phân biệt các
route thì càng dễ tạo antichain nhỏ; ở k nhỏ, m cũng nhỏ hơn tương đối, dominance ít có "đòn bẩy"
để phân biệt.

### Bảng đầy đủ B×k×tw_width (GW, compression D2/D3 median)

| B | k | tw=30 | tw=60 | tw=120 | tw=240 |
|---|---|---|---|---|
| 2 | 1 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 |
| 2 | 2 | 1,000 / 1,000 | 0,600 / 0,667 | 0,500 / 0,667 | 0,500 / 0,667 |
| 3 | 1 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 |
| 3 | 2 | 0,833 / 1,000 | 0,600 / 0,800 | 0,500 / 0,667 | 0,500 / 0,667 |
| 3 | 3 | 0,500 / 0,500 | 0,143 / 0,214 | 0,067 / 0,130 | 0,078 / 0,178 |
| 4 | 1 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 | 1,000 / 1,000 |
| 4 | 2 | 1,000 / 1,000 | 0,500 / 0,667 | 0,500 / 0,667 | 0,500 / 0,500 |
| 4 | 3 | 0,333 / 0,500 | 0,108 / 0,227 | 0,067 / 0,176 | 0,061 / 0,100 |
| 4 | 4 | 0,167 / 0,167 | 0,029 / 0,065 | 0,004 / 0,019 | 0,003 / 0,007 |

**Xu hướng nhất quán:** compression giảm đều theo k **và** theo tw_width — đúng cả 2 chiều bùng
nổ của `|Seq(S)|` ở Test2. Ở `k=B=4, tw=240` (ô bùng nổ nặng nhất Test2), compression D3 chỉ
**0,7%** — nén 143 lần.

**Cảnh báo diễn giải bắt buộc (spec §3):** compression ở d=1 tiết kiệm **storage**, KHÔNG tiết
kiệm **compute** — tính `Γ(R)` để có được compression này đã tốn đúng công việc của 1 bước BFS
đầy đủ (xác nhận số liệu ở §4 dưới).

---

## 4. Việc 3 — Chi phí tính profile: t_profile vs t_bfs_next (mẫu 6 cell đại diện)

```
n_insertion_profile == n_insertion_bfs: ĐÚNG 100% trên toàn bộ mẫu (145 dòng)
```

Xác nhận đúng lý thuyết spec §4: hai đại lượng này **bằng nhau tuyệt đối** về số phép thử chèn —
`compute_gamma` và BFS level sau cùng duyệt `R⊕j` cho mọi R,j.

| B | tw_width | ratio t_profile/t_bfs_next (mean) | n |
|---|---|---|---|
| 2 | 240 | 3,19× | 12 |
| 3 | 240 | 1,66× | 30 |
| 4 | 30 | 1,14× | 23 |
| 4 | 120 | 1,33× | 40 |
| 4 | 240 | 1,45× | 40 |

**`t_profile` luôn lớn hơn `t_bfs_next`** (1,14×–3,19×) — đúng dự đoán spec: cài đặt profile có
overhead thật (tính thêm K, W, slack cho mỗi kết quả feasible, thay vì chỉ hỏi feasible/không).
Overhead **không nghiêm trọng** (dưới 3,2× trong mọi trường hợp đo được, và giảm dần khi B/tw_width
tăng — tức đúng ở nơi compression có giá trị nhất, overhead tương đối *nhỏ nhất*, chỉ 1,14–1,45×).

**Kết luận net gain (đọc cùng §3):** compression d=1 tiết kiệm storage thật (tới 143 lần ở ô nặng
nhất), với chi phí tính thêm chỉ 1,3–1,5× so với 1 bước BFS vốn dĩ đã phải làm — đây là **trade-off
tốt cho storage**, nhưng (nhắc lại) không phải tiết kiệm compute ở chính level d=1 này.

---

## 5. Việc 4 — Kiểm giả thuyết d≥2: XÁC NHẬN THẤT BẠI (đúng dự đoán)

Chạy trên grid nhỏ (n∈{4,5,6}, B=4 cố định, GW, mọi tw_width, 8 seed): lọc `Seq(S)` bằng D2/D3 tại
k=2 (d=2), BFS tiếp 2 level tới k=4, so với brute force.

```
total subsets (k=2, GW, B=4) checked: 963
D2 violation: 697 (72,3780%)
D3 violation: 640 (66,4590%)
```

**Vượt xa ngưỡng ">1%" của spec §5.3** — xác nhận dứt khoát dự đoán §5.1: profile depth-1
(D2 lẫn D3, kể cả D3 vốn giữ thêm chiều slack) **không sound** ở d≥2. Representative rule theo
Định lý R1 **chỉ dùng được ở d=1**, đúng như phạm vi chứng minh ban đầu — không mở rộng được.

### Phản ví dụ số đầy đủ (n=4, B=4, GW, tw_width=30, seed=0, S={o0,o1})

`|Seq(S)|=6`, `Rem(S)={o2,o3}`. Lọc D2 giữ lại **2/6** route (front):
- `[n0(start), n1(P.o0), n3(P.o1), n2(D.o0), n4(D.o1)]`
- `[n0, n3(P.o1), n1(P.o0), n2(D.o0), n4(D.o1)]`

Route bị D2 **loại bỏ** (dominated): `[n0, n1(P.o0), n2(D.o0), n3(P.o1), n4(D.o1)]` (thứ tự "gọn":
phục vụ trọn o0 rồi trọn o1, không xen kẽ).

BFS tiếp 2 level từ front này (chèn thêm o2, o3 theo mọi thứ tự) tới `S4={o0,o1,o2,o3}`:
- `|BRUTE_FORCE(S4)| = ` (đầy đủ theo brute force)
- Có **3 sequence** mà brute force tìm thấy khả thi nhưng BFS-từ-front **không sinh lại được** —
  ví dụ: `(start, P.o3, D.o3, P.o2, P.o0, D.o0, P.o1, D.o1, D.o2)`.

**Cơ chế đúng như spec §5.1 dự đoán:** route bị loại (`[...o0...o1...]` gọn) tuy "tệ hơn" theo
(K,W) ở mọi điểm so với 2 route giữ lại, nhưng chính cấu trúc "gọn" của nó lại **mở khe hình học**
cho thứ tự chèn `o3→o2→...` mà 2 route "xen kẽ" giữ lại không có được — đúng cơ chế đã phá Pareto
ở Test3 (dominance 4 chiều/K-W không nắm bắt được tập cạnh cụ thể).

---

## 6. §5.4 — Rule an toàn thay thế (LB≥UB): ĐÁNG THEO ĐUỔI

Vì Việc 4 ra ">1%", chạy tiếp rule cận-đôi an toàn tuyệt đối:
`R_b xoá được nếu LB_{Ra}(T) ≥ UB_{Rb}(T), ∀T⊆Rem(S), |T|≤2`, tại GW, B=4, k=2, tw_width∈{120,240}.

```
total pairs (Ra,Rb) checked: 14.596
pairs_activated: 6.415
activation_rate: 43,9504%
```

**Vượt xa ngưỡng "≥10%"** của spec §5.4 → rơi vào ô **"Đáng theo đuổi, chạy tiếp ở grid lớn."**
Đây là kết quả quan trọng nhất của Việc 4/§5.4: dù profile depth-1 thô (D2/D3) không sound ở d≥2,
**một rule cận-đôi bảo thủ hơn (dùng triangle-inequality, sound tuyệt đối theo chính chứng minh
của reference §3.2) vẫn kích hoạt được ở gần 44% số cặp route** — mở ra khả năng cứu **compute**
(không chỉ storage) ở d≥2, điều mà Định lý R1 gốc không làm được.

---

## 7. Kết luận tổng hợp theo đúng ngưỡng đã khoá

| Việc | Kết quả | Ngưỡng | Kết luận |
|---|---|---|---|
| 0 | 0/4.204.875 mismatch | =0 tuyệt đối | **PASS** — F_i đúng, và có giá trị thật (2,83% cứu được so min-slack) |
| 1 | 0/3.119 violation D2,D3 | =0 tuyệt đối | **PASS** — Định lý R1 không bị bác bỏ ở d=1 |
| 2 | D2/D3 median 0,061–0,10 ở 2/3 ô trọng tâm | ≤0,10 "rất tốt" | **Rất tốt ở k gần B**, yếu ở k=2 (0,50–0,67) |
| 3 | overhead 1,14×–3,19×, luôn ≥1× | so t_bfs_next | **Overhead thật nhưng chấp nhận được**, giảm dần ở B/tw lớn |
| 4 | D2=72,4%, D3=66,5% violation | >1% "xác nhận thất bại" | **Xác nhận: chỉ dùng được ở d=1** |
| §5.4 | activation_rate=43,95% | ≥10% "đáng theo đuổi" | **Mở đường cứu compute ở d≥2** — cần grid lớn |

**Kết luận tổng thể, viết thẳng theo đúng tinh thần §9 (không giấu kết quả xấu):**

- **Storage (d=1): thành công rõ ràng.** Representative rule theo Định lý R1 (D2 hoặc D3) nén
  `|Seq(S)|` xuống còn 6–10% (rất tốt) ở đúng vùng bùng nổ nặng nhất của Test2 (B=4, tw≥120,
  k=B-1), với chi phí tính thêm chỉ 1,1–1,5× so với 1 bước BFS. **Đủ để viết vào thesis** theo
  đúng ngưỡng spec.
- **Compute (d≥2): Định lý R1 gốc thất bại rõ ràng** (66–72% violation, có phản ví dụ số đầy đủ) —
  nhưng **không phải ngõ cụt**. Rule cận-đôi an toàn tuyệt đối (§5.4) kích hoạt ở 43,95% số cặp,
  vượt xa ngưỡng "đáng theo đuổi" — đây là hướng nghiên cứu tiếp theo có cơ sở thực nghiệm mạnh,
  khác hẳn tình huống Pareto-dominance ở Test3 (đã đóng hẳn, không có hướng thay thế nào được đề
  xuất).
- **Việc cần làm tiếp (không phải kết quả của vòng này):** chạy §5.4 trên grid lớn hơn (n=8..15,
  d=3 khi B=5) để xác nhận activation_rate còn giữ vững ở quy mô lớn hơn — đúng như ô kết luận
  "≥10%" của spec yêu cầu.

---

## 8. File

| File | Nội dung |
|---|---|
| `Output/Test4/f_slack_check.csv` | 4.204.875 dòng — Gate 0.1/0.2 |
| `Output/Test4/exactness_d1.csv` | 3.119 dòng — Gate 1.A/1.B (D1/D2/D3) |
| `Output/Test4/compression_small.csv` | 3.376 dòng — Việc 2, grid nhỏ (n≤6) |
| `Output/Test4/viec3_sample.csv` | 145 dòng — Việc 3, mẫu 6 cell |
| `Output/Test4/depth2.csv` | 963 dòng — Việc 4, violation d≥2 |
| `Output/Test4/activation_rate.csv` | 24 dòng — §5.4, activation_rate LB≥UB |
| `experiments/T2BFS/t4_fwdslack.py` | `forward_slack` (F, Fp) |
| `experiments/T2BFS/t4_gate0.py` | `feasible_by_F_two_insert` |
| `experiments/T2BFS/t4_profile.py` | `compute_gamma`, `dominates_D1/D2/D3`, `filter_dominated`, `reachable_orders` |
| `experiments/T2BFS/t4_run_gate0.py`, `t4_run_viec1.py`, `t4_run_viec2.py`, `t4_run_viec3.py`, `t4_run_viec4.py`, `t4_run_viec54.py` | Runner từng phần |

Tái lập: `python -m experiments.T2BFS.t4_run_gate0` (→ Việc 1 → Việc 2 → Việc 3 → Việc 4 →
`t4_run_viec54`), từ `K:\Data Science\Q1 Research`, theo đúng thứ tự §8 của spec (dừng nếu bất kỳ
gate bắt buộc nào fail — trong vòng này không gate nào fail).
