# Test4 — Representative Rule qua Lookahead-Profile Dominance

**Mục tiêu:** kiểm chứng xem có thể **xoá bớt route trong `Seq(S)`** mà vẫn giữ nguyên kết quả
cuối của Algorithm A hay không, bằng một quan hệ dominance có tham chiếu tới **các order còn
lại cụ thể** (khác hẳn Pareto 4 chiều đã bị bác bỏ ở Test3).

**Đọc trước khi làm:** `HICA-S_AlgorithmA_reference.md` (§2.4, §3.4, §4) — hai điều đã bị
[REJECTED] và **không được thử lại theo cách cũ**:
1. Chọn **một sequence đại diện** của tập cha theo bất kỳ scalar/vector nào.
2. Nén Pareto trên label `(end_node, arrival, load, elapsed)` — không tham chiếu order tương lai.

Test4 **không** vi phạm hai điều trên: nó giữ lại **một tập** route (antichain), và tiêu chí
dominance **có tham chiếu trực tiếp** tới từng order còn lại trong `Rem(S)`.

---

## 0. Ký hiệu và định nghĩa — khoá trước khi code

### 0.1 Sửa xung đột tên biến (bắt buộc, xem reference §4.4)

Test3 đã dùng nhầm tên `K, W` cho `(load, elapsed)`. Test4 dùng tên tách bạch:

| Ký hiệu | Nghĩa | Dùng ở đâu |
|---|---|---|
| `K(R)` | `κ · total_distance(R)` — chi phí quãng đường (cost-unit) | Output kinh tế của Algorithm A |
| `W(R)` | `active_route_time(R) / 60` — thời lượng tính phí (giờ) | Output kinh tế của Algorithm A |
| `load_i`, `A_i`, `B_i`, `D_i` | trạng thái feasibility tại node i | Kiểm khả thi |
| `slack(R)` | `min_i (l_i - B_i)` trên mọi node của R (gồm `home` với OD) | Như Test2 |

**Với OD:** `W` tính theo detour (`route_time − direct_time`), `K` theo detour distance, đúng
công thức §2.2 của đề cương HICA-S. Với GW: tính trên toàn tuyến.

### 0.2 Forward time slack (MỚI — thay cho min-slack toàn tuyến)

Với route `R = (v_0, ..., v_N)`, waiting time `W_p = max(0, e_p - A_p)`:

```
F_i = min_{i ≤ j ≤ N} { Σ_{i < p ≤ j} W_p + (l_j - B_j) }
```

`F_i` = lượng delay tối đa có thể đẩy vào **sau vị trí i** mà route vẫn khả thi (Savelsbergh
1985, 1992). Tính toàn bộ `F_i` cho một route mất **O(|R|)** bằng một lượt quét ngược.

**Lý do bắt buộc dùng `F_i` thay vì `slack(R)`:** delay chèn ở vị trí sớm **không** truyền
nguyên vẹn tới cuối tuyến — waiting time dọc đường hấp thụ bớt. Dùng `slack(R)` làm "arc
capacity" chung cho mọi vị trí là một cận **đúng nhưng lỏng**, sẽ loại nhầm nhiều insertion
hợp lệ, làm sai lệch mọi số đo compression bên dưới.

### 0.3 Tập order còn lại

```
Rem(S) = reachable_orders(driver) \ S
m = |Rem(S)|
```
`reachable_orders(driver)` = danh sách order khả thi đơn lẻ của tài xế đó (đã có từ Test2,
tính **không đọc bid**). `Rem(S)` phải xác định **deterministic** và độc lập bid.

### 0.4 Profile của một route

Với `R ∈ Seq(S)` và `j ∈ Rem(S)`:

```
A_j(R) = { ( K(R⊕j), W(R⊕j), slack(R⊕j) ) : mọi vị trí chèn (a,b) hợp lệ, a < b }
```
trong đó `R⊕j` = chèn `pickup_j` tại vị trí a, `delivery_j` tại vị trí b. `A_j(R) = ∅` nếu
không chèn được j vào R.

```
σ_j(R) = max{ slack : (·,·,slack) ∈ A_j(R) },   = −∞ nếu A_j(R) = ∅
Γ(R)   = ( A_j(R) )_{j ∈ Rem(S)}
```

**Chi phí tính:** `O(|R|²)` vị trí × `O(1)` check nhờ `F_i` ⟹ `O(m · |R|²)` mỗi route, với
`|R| = 2k + 1` (GW) hoặc `2k + 2` (OD) ≤ 10.

### 0.5 Ba biến thể quan hệ dominance (test cả ba, đừng chọn sẵn)

```
D1 — FEAS (rẻ nhất, bitmask):
     Feas(R) = { j ∈ Rem(S) : A_j(R) ≠ ∅ }  ∈ {0,1}^m
     R_a ⪰ R_b  ⟺  Feas(R_b) ⊆ Feas(R_a)

D2 — KW (dùng cho d = 1, bỏ chiều slack):
     R_a ⪰ R_b  ⟺  ∀j ∈ Rem(S), ∀p ∈ A_j(R_b), ∃p' ∈ A_j(R_a):
                     K(p') ≤ K(p)  ∧  W(p') ≤ W(p)

D3 — KWS (giữ chiều slack, cần cho mọi ý định dùng ở d ≥ 2):
     R_a ⪰ R_b  ⟺  ∀j ∈ Rem(S), ∀p ∈ A_j(R_b), ∃p' ∈ A_j(R_a):
                     K(p') ≤ K(p)  ∧  W(p') ≤ W(p)  ∧  slack(p') ≥ slack(p)
```

Quan hệ nào cũng **không toàn phần** — kết quả lọc là một **antichain**, không phải một route
duy nhất. Ghi rõ trong code: nếu `|front| == 1` thường xuyên, đó là dấu hiệu nghi ngờ, kiểm lại.

**Tie-break khi `R_a ⪰ R_b` và `R_b ⪰ R_a`:** giữ route có `canonical()` nhỏ hơn theo thứ tự
từ điển. Deterministic, không đọc bid.

---

## 1. Việc 0 — Cài và kiểm `F_i` (điều kiện tiên quyết)

**Cài:** `forward_slack(R) -> list[float]`, một lượt quét ngược O(|R|).

**Gate 0.1 — tương đương với recompute đầy đủ.** Với mọi route trong `Seq(S)` của toàn bộ
grid nhỏ (n≤6), mọi vị trí chèn `(a,b)` của mọi `j ∈ Rem(S)`:
```
feasible_by_F(R, j, a, b)  ==  is_feasible(insert(R, j, a, b))
```
Yêu cầu: **khớp 100%**. Sai một ca là bug, dừng, không chạy tiếp Việc 1.

**Gate 0.2 — so mức chặt với min-slack.** Đếm số `(R, j, a, b)` mà `F_i` cho KEEP nhưng
`slack(R)` (dùng như capacity chung) cho PRUNE. Đây là số insertion mà cách cũ **loại nhầm**.
Báo cáo tỷ lệ theo `k`, `class`, `tw_width`. Nếu tỷ lệ này ≈ 0 thì `F_i` không mang lại gì và
phải nói thẳng như vậy.

---

## 2. Việc 1 — ★ Gate exactness tại d = 1 (thí nghiệm quan trọng nhất)

`d = B − k` = số level còn lại. Việc 1 chỉ xét `k = B − 1` (tức `d = 1`).

### 2.1 Định lý cần kiểm (Định lý R1)

> Nếu `d = 1` và `Γ(R_a) ⪰ Γ(R_b)` theo **D2**, thì xoá `R_b` khỏi `Seq(S)` không làm mất:
> (i) bất kỳ **bundle** khả thi nào ở level B;
> (ii) bất kỳ điểm **(K,W)-Pareto-optimal** nào của bất kỳ bundle nào ở level B.

Chứng minh trên giấy đã có (mọi thứ sinh từ `Seq(S)` ở d=1 đều có dạng `R⊕j`; giả thiết ⪰ cho
điểm thay thế tốt hơn hoặc bằng theo cả K lẫn W). **Việc 1 là kiểm thực nghiệm chứng minh đó,
không phải đi tìm nó.** Kỳ vọng: **0 violation**. Nếu có violation → chứng minh sai ở đâu đó,
**dừng lại và tìm cho ra lỗi** trước khi làm gì tiếp.

### 2.2 Cách chạy

```
for mỗi instance nhỏ (n ≤ 6, đã có ground truth Test2):
    k = B - 1
    for mỗi subset S, |S| = k:
        Seq_full  = Seq[S]                          # BFS gốc, đã validated
        Front_D1  = filter_dominated(Seq_full, D1)
        Front_D2  = filter_dominated(Seq_full, D2)
        Front_D3  = filter_dominated(Seq_full, D3)

        # sinh level B từ từng nguồn
        for src in {Seq_full, Front_D1, Front_D2, Front_D3}:
            bundles[src]  = { S∪{j} : sinh được ít nhất 1 sequence khả thi }
            pareto[src][S∪{j}] = Pareto-front theo (K,W) của mọi sequence sinh được
```

### 2.3 Hai gate

| Gate | Nội dung | Ngưỡng |
|---|---|---|
| **1.A** `bundle_loss` | `bundles[Seq_full] \ bundles[Front_X]` phải rỗng | **= 0 tuyệt đối** |
| **1.B** `pareto_loss` | Với mỗi bundle, mọi điểm trong `pareto[Seq_full]` phải có điểm trong `pareto[Front_X]` với `K' ≤ K` và `W' ≤ W` (dung sai 1e-9) | **= 0 tuyệt đối** cho D2, D3 |

**Ghi chú về D1 (FEAS):** D1 chỉ bảo toàn **bundle**, **không** bảo toàn Pareto front — đây là
điều đã biết trước, không phải lỗi. Vì vậy:
- D1 chỉ cần pass gate 1.A. Nếu D1 fail 1.B, ghi nhận và đi tiếp, **không** coi là bug.
- D2, D3 phải pass **cả hai** gate.

Nếu D2 fail gate 1.A hoặc 1.B → in ra phản ví dụ đầy đủ (instance seed, S, `R_a`, `R_b`, `j`,
hai sequence, hai bộ (K,W)) và dừng toàn bộ Test4.

---

## 3. Việc 2 — Đo compression thật (con số quyết định có đáng làm không)

Đo trên **cả grid nhỏ lẫn grid lớn** (`n ∈ {8,10,12,15}`), tại **mọi** `k` (không chỉ `k=B−1`):

```
compression(S, X) = |Front_X(S)| / |Seq(S)|          # X ∈ {D1, D2, D3}
```

**Báo cáo bắt buộc:** median + p25/p75 + max, tách theo `class × k × tw_width × B`.

Ba ô cần nhìn kỹ nhất, vì đó là nơi Test2 ghi nhận bùng nổ (`median |Seq(S)| = 1.399` và
`2.520`):
```
GW, B = 4, k = 3, tw_width = 120
GW, B = 4, k = 3, tw_width = 240
GW, B = 3, k = 2, tw_width = 240
```

### Ngưỡng đọc kết quả (khoá trước khi chạy)

| median compression tại các ô trên | Kết luận |
|---|---|
| ≤ 0,10 | **Rất tốt** — giảm ≥10 lần lượng route phải lưu ở level cuối. Đủ để viết vào thesis như một kết quả. |
| 0,10 – 0,40 | **Có giá trị** — đáng dùng, nhưng phải trình bày kèm chi phí tính profile (§4). |
| 0,40 – 0,80 | **Yếu** — tiết kiệm không bù nổi chi phí tính `Γ`; báo cáo trung thực là hướng này biên. |
| > 0,80 | **Vô dụng** — dominance gần như không kích hoạt. Dừng hướng representative, ghi rõ vào report. |

**Cảnh báo diễn giải, phải viết vào report:** compression ở `d = 1` tiết kiệm **storage**, **không**
tiết kiệm **compute** — vì để tính `A_j(R)` ta đã phải làm đúng công việc của level B rồi. Không
được viết trong report như thể nó giảm thời gian chạy. Muốn giảm compute thì phải qua Việc 3–4.

---

## 4. Việc 3 — Đo chi phí tính profile (để biết net gain, không chỉ gross)

Đo và báo cáo, tách theo `k` và `class`:

| Đại lượng | Cách đo |
|---|---|
| `t_profile(S)` | thời gian tính toàn bộ `Γ(R)` cho mọi `R ∈ Seq(S)` |
| `t_bfs_next(S)` | thời gian BFS sinh level `k+1` từ `Seq(S)` (đầy đủ) |
| `n_insertion_profile` | số phép thử chèn khi tính profile |
| `n_insertion_bfs` | số phép thử chèn của BFS level sau |

Ở `d = 1` hai đại lượng này về lý thuyết **bằng nhau** (cùng duyệt `R ⊕ j` cho mọi `R`, `j`).
Nếu đo được `t_profile ≫ t_bfs_next` thì cài đặt profile đang dư thừa, phải tối ưu trước khi
kết luận về net gain.

---

## 5. Việc 4 — ★ Kiểm giả thuyết d ≥ 2 (kỳ vọng THẤT BẠI, phải xác nhận)

### 5.1 Vì sao phải làm

Định lý R1 chỉ đúng ở `d = 1`. Ở `d ≥ 2`, profile depth-1 **được dự đoán là không sound**, theo
đúng cơ chế đã phá Pareto ở Test3: `A_j(R_a)` tốt hơn `A_j(R_b)` ở mọi điểm, nhưng route
`R_a ⊕ j` tốt nhất lại có **tập cạnh** xấu cho order `j'` kế tiếp, trong khi `R_b ⊕ j` mở khe
cho `j'`.

**Đây là dự đoán, chưa phải kết quả.** Việc 4 phải xác nhận bằng số, không được giả định.

### 5.2 Cách chạy

Trên grid nhỏ (n ≤ 6, có ground truth), với `B = 4`, lọc bằng `Γ` tại `k = 2` (`d = 2`), rồi
BFS tiếp hai level tới `k = 4`, so với brute force:

```
violation_d2(S) = tồn tại bundle S'' (|S''| = 4, S ⊂ S'') khả thi theo BRUTE_FORCE
                  mà không sinh được từ Front_X(S)
```

Đo cho cả D2 và D3 (D3 giữ chiều slack, có thể sống sót lâu hơn — cần biết).

### 5.3 Ngưỡng

| violation rate d=2 | Kết luận |
|---|---|
| **> 1%** | Xác nhận dự đoán. Representative rule **chỉ dùng được ở d = 1**. Ghi rõ, kèm ít nhất **một phản ví dụ số đầy đủ** để đưa vào thesis (giá trị học thuật: nó chứng minh ranh giới của phương pháp, không phải thất bại). |
| **0,01% – 1%** | Hiếm nhưng có thật — không dùng được ở dạng thô, nhưng đáng tìm điều kiện bổ sung. Ghi lại toàn bộ ca violation để phân tích cấu trúc chung. |
| **= 0% trên toàn grid** | **Tín hiệu mạnh, cần đào tiếp.** Không được kết luận "sound" từ thực nghiệm — nhưng đây là căn cứ để đầu tư thời gian tìm chứng minh cho `d ≥ 2`. Đây là kịch bản duy nhất mở đường cứu **compute**, không chỉ storage. |

### 5.4 Rule an toàn thay thế (chỉ chạy nếu §5.3 ra "> 1%")

Cận trên rẻ, đúng theo lập luận tam giác (cùng kiểu chứng minh §3.2 của reference):
```
V_R(T) ≤ UB_R(T) := min_{j ∈ T} σ_j(R)          ∀T ⊆ Rem(S)
```
`V_R(T)` = slack tốt nhất đạt được khi chèn **toàn bộ** T vào R. Lấy `LB_{R}(T)` = slack của một
nhân chứng greedy (chèn lần lượt từng order của T, mỗi bước chọn vị trí maximin slack).

```
R_b xoá được (sound) nếu:  LB_{R_a}(T) ≥ UB_{R_b}(T)   ∀T ⊆ Rem(S), |T| ≤ d
```
Sound tuyệt đối kể cả khi hai cận lỏng (vì `V_{R_a}(T) ≥ LB_{R_a}(T) ≥ UB_{R_b}(T) ≥ V_{R_b}(T)`).

**Đo duy nhất một con số:** `activation_rate` = % cặp `(R_a, R_b)` mà rule này kích hoạt, tại
`GW, B = 4, k = 2, tw_width ∈ {120, 240}`.

| activation_rate | Kết luận |
|---|---|
| ≥ 10% | Đáng theo đuổi, chạy tiếp ở grid lớn |
| 1% – 10% | Biên, ghi nhận, không đầu tư thêm trong vòng này |
| < 1% | Rule quá lỏng để dùng. Đóng hướng `d ≥ 2`. T4 quay lại arc-charging + PMTN hoặc chuyển sang T5. |

---

## 6. Grid và tham số

**Giữ nguyên grid Test2 §5**, không đổi bất kỳ tham số nào đã khoá:
```
n_orders:  {3,4,5,6} (grid nhỏ, có ground truth) · {8,10,12,15} (grid lớn)
B:         {2, 3, 4}
tw_width:  {30, 60, 120, 240}
tau:       {15, 30, 60}          (chỉ OD)
speed:     20 km/h · service: 5 phút · area: 10 km
capacity:  = B (mỗi order demand = 1) — giữ nguyên lựa chọn Test2, capacity không là nút thắt
SEEDS_PER_CELL: 8                 (giữ đúng Test2 để so sánh trực tiếp được)
```

**OD — hai điều kiện bắt buộc:**
1. Dùng generator **đã patch** (Test3: `ready_time = t0 + U[0, tau]`, corridor-weighted P/D với
   `CORRIDOR_BUFFER_KM = 3.0`, `CORRIDOR_SHARE = 0.7`).
2. Chỉ chạy các cell có `feasibility_rate_k1 ≥ 0.5`, đúng như Test3.

**Trọng tâm là GW.** Test3 cho thấy OD bundling ở `k ≥ 2` vẫn hiếm (22,4% ở `tau=60`, gần 0% ở
`tau=30`), nên `|Seq(S)|` của OD nhỏ và compression trên OD **không có sức thuyết phục thống kê**.
Vẫn chạy OD để đối chứng, nhưng mọi kết luận chính phải rút từ GW. Nếu một ô OD có
`|Seq(S)| < 5` thì loại khỏi thống kê compression (ghi rõ số ô bị loại).

---

## 7. Schema output

`Output/Test4/f_slack_check.csv` (Việc 0):
```
n, B, class, tw_width, tau, seed, k, subset_id, route_id, j, pos_a, pos_b,
feasible_by_F (bool), feasible_by_recompute (bool), mismatch (bool),
pruned_by_minslack (bool)
```

`Output/Test4/exactness_d1.csv` (Việc 1):
```
n, B, class, tw_width, tau, seed, subset_id, k,
seq_count, front_D1, front_D2, front_D3,
bundle_loss_D1, bundle_loss_D2, bundle_loss_D3,
pareto_loss_D1, pareto_loss_D2, pareto_loss_D3,
violation_detail
```

`Output/Test4/compression.csv` (Việc 2–3):
```
n, B, class, tw_width, tau, seed, subset_id, k, m_rem,
seq_count, front_D1, front_D2, front_D3,
compression_D1, compression_D2, compression_D3,
t_profile_ms, t_bfs_next_ms, n_insertion_profile, n_insertion_bfs
```

`Output/Test4/depth2.csv` (Việc 4):
```
n, B, class, tw_width, tau, seed, subset_id,
violation_D2 (bool), violation_D3 (bool), lost_bundles,
ub_lb_activation_pairs, ub_lb_total_pairs, activation_rate
```

Kèm `Output/Test4/counterexamples/` — mỗi phản ví dụ một file JSON đầy đủ (toạ độ node, time
window, hai sequence, mọi giá trị trung gian) để tái dựng được bằng tay.

---

## 8. Thứ tự thực thi và điều kiện dừng

```
Việc 0  →  gate 0.1 fail  ⟹  DỪNG, sửa bug F_i
        ↓ pass
Việc 1  →  D2 fail gate 1.A/1.B  ⟹  DỪNG, chứng minh R1 sai, tìm cho ra lỗi
        ↓ pass (kỳ vọng)
Việc 2  →  compression > 0,80 ở các ô trọng tâm  ⟹  DỪNG, đóng hướng representative
        ↓
Việc 3  (đo chi phí, không có điều kiện dừng)
        ↓
Việc 4  →  quyết định d ≥ 2 có đường đi hay không
```

Không chạy Việc 4 trước Việc 1: nếu `d = 1` đã sai thì `d = 2` không cần bàn.

---

## 9. Những điều KHÔNG được làm trong Test4

1. **Không** chọn một sequence đại diện duy nhất từ `Front_X`. Kết quả lọc là antichain; nếu code
   trả về đúng 1 route, kiểm lại quan hệ dominance có bị cài thành thứ tự toàn phần không.
2. **Không** dùng `slack(R)` làm arc capacity chung — phải dùng `F_i` (§0.2).
3. **Không** đọc bid ở bất kỳ bước nào. Chạy regression: đổi mọi `b_i`, `Front_X(S)` và
   `allocation_range_hash` phải bất biến.
4. **Không** báo cáo compression ở `d = 1` như tiết kiệm thời gian chạy (§3, cảnh báo diễn giải).
5. **Không** điều chỉnh tham số grid sau khi thấy kết quả yếu. Ngưỡng ở §3, §5.3, §5.4 đã khoá
   trong file này; kết luận theo đúng ngưỡng đó dù ra sao.
6. **Không** kết luận "sound" cho `d ≥ 2` từ việc violation = 0 trên grid nhỏ — chỉ được viết là
   "không tìm thấy phản ví dụ trong phạm vi đã kiểm, cần chứng minh".

---

## 10. Báo cáo cần trả về

`Test4_report.md`, theo đúng cấu trúc Test2/Test3 report:

1. Sai lệch so với spec (nếu có), công khai ngay đầu file.
2. Bảng gate Việc 0 và Việc 1 — pass/fail tuyệt đối.
3. Bảng compression theo `class × k × tw_width × B`, có đánh dấu ba ô trọng tâm §3.
4. So sánh `t_profile` vs `t_bfs_next` và kết luận net gain.
5. Kết quả `d = 2`: violation rate + ít nhất một phản ví dụ số đầy đủ nếu có.
6. `activation_rate` của rule `LB ≥ UB` nếu chạy tới §5.4.
7. Kết luận theo đúng ngưỡng đã khoá, kể cả khi ngưỡng đó bác bỏ hướng tiếp cận.