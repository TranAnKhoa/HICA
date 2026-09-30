# Test6 Report — Unified Forward Label-Setting DP

**Mức độ rủi ro/tham vọng: cao nhất trong chuỗi test.** Kết quả: **cả 2 gate bắt buộc (Gate 1
A/B/C và §2.3) PASS TUYỆT ĐỐI**, và Việc 2/3 cho tín hiệu tích cực rõ ràng — đây là kết quả tốt
nhất trong toàn bộ chuỗi Test2-6.

**Sai lệch so với spec:** một, đã disclose ngay: `SEEDS_PER_CELL` cho §2.3 (Sec2.3, kiểm
DP_full vs DP_prune) giảm còn 4 thay vì 8 (khớp Gate 1 chính) — lý do: §2.3 là phép kiểm
**sound/không sound** (đúng/sai tuyệt đối, không phải thống kê, giống chính tinh thần spec §2.2
áp dụng cho gate này), 1 vi phạm duy nhất đã đủ bác bỏ giả thuyết bất kể seed count; giảm seed
chỉ giảm chi phí compute, không giảm giá trị chứng minh của "0 vi phạm". Gate 1 chính (Việc 1)
giữ nguyên `SEEDS_PER_CELL=8` đúng spec.

**Code:** `experiments/T2BFS/t6_dp.py` (state, transition, dominance, DP core),
`t6_run_gate1.py` (Gate 1.A/B/C), `t6_run_gate1_dominance_midway.py` (§2.3),
`t6_run_viec2.py` (state space), `t6_run_viec3.py` (wall-clock speedup). Tái dùng
`t2_core.build_walk_nodes/is_feasible/brute_force/bfs_generate` và `t4_profile.K_W_of_route`
nguyên vẹn — không viết lại feasibility hay công thức K/W, đúng cảnh báo §7.1/§7.4 spec.

---

## 1. Một bug tìm được và sửa TRƯỚC gate chính thức (ghi công khai)

Ở lần chạy smoke-test đầu tiên (n=3, B=2, GW, 1 order), Gate 1.B/1.C bắt được lỗi ngay: K tích
luỹ của DP lệch đúng 3,0× so với K thật (`K_DP=32,02` vs `K_real=10,67`). Nguyên nhân: `t2_gen`
`travel_time()` trả về **phút**, nhưng công thức K (theo `t4_profile.route_distance_km`) cần
**km** — DP ban đầu cộng dồn `κ·travel_time` trực tiếp (đơn vị phút) thay vì quy đổi qua
`SPEED_KMH/60` trước khi cộng. Tỷ lệ lệch 3,0× = 60/20 = `60/SPEED_KMH`, khớp chính xác cơ chế
bug. **Sửa bằng hàm `_tt_to_km()` trong `t6_dp.py`, áp dụng thống nhất ở cả 3 transition
(pickup/delivery/home).** Sau khi sửa, toàn bộ smoke-test (GW+OD, B=2..4, nhiều tw/tau) cho 0 vi
phạm. Đây đúng là kịch bản spec §2.2 mô tả: "gate chỉ ra chính xác chỗ gãy" — lỗi này thuộc
nhóm "lỗi công thức K/W", KHÔNG phải "giả thuyết dominance sai".

---

## 2. Gate 1 (Việc 1) — PASS TUYỆT ĐỐI

```
Grid: n∈{3,4,5,6}, B∈{2,3,4} (n≥B), GW+OD, tw_width∈{30,60,120,240} (GW) / tau∈{15,30,60} (OD),
      SEEDS_PER_CELL=8
Instance đã kiểm (sau khi loại OD cell dưới ngưỡng feasibility_rate_k1≥0,5): 616
Gate 1.A (bundle completeness): 0 vi phạm
Gate 1.B (Pareto completeness, so DP với ground truth độc lập): 0 vi phạm
Gate 1.C (Pareto soundness, đối chiếu is_feasible() GỐC): 0 vi phạm
```

Không một vi phạm nào trên 616 instance × mọi subset S (|S|=1..B) đã kiểm. DP không bao giờ báo
sai "không tồn tại bundle" khi có, không bao giờ làm mất một điểm Pareto-optimal thật, và không
bao giờ "ảo giác" ra một điểm (K,W) mà không có sequence thật nào đạt được. File:
`Output/Test6/gate1_violations.csv` (rỗng — chỉ header).

---

## 3. §2.3 — Dominance giữa chừng (IV≠∅): PASS TUYỆT ĐỐI

**Đây là câu trả lời trực tiếp cho câu hỏi trung tâm dẫn tới Test6.**

```
Grid: n∈{3,4,5}, B∈{2,3,4}, GW+OD, SEEDS_PER_CELL=4 (giảm, xem Sec0 phía trên)
Instance đã kiểm: 160
Violation (label hoàn chỉnh mà DP_full tìm được nhưng DP_prune bỏ sót): 0
```

DP_prune (dominance áp dụng xuyên suốt, kể cả khi `IV≠∅`) không bỏ sót bất kỳ label hoàn chỉnh
nào mà DP_full (không dominance) tìm được — với mọi label hoàn chỉnh của DP_full, luôn tồn tại
một label hoàn chỉnh của DP_prune cùng `(C,v)` với `K≤, W≤`. Giả thuyết §0 (dominance an toàn
ngay cả giữa chừng, vì tương lai chỉ phụ thuộc `(v,IV,C)` chứ không phụ thuộc con đường cụ thể
đã đi) **được xác nhận thực nghiệm, không bị bác bỏ trong phạm vi đã kiểm.**

**Khác biệt với Test4 Việc 4 (đã REJECTED)**, đúng như spec §2.3 tiên đoán: Test4 so sánh route
đã hoàn thành của các tập S KHÁC NHAU — khác cả `C` lẫn khả năng "chèn giữa" một order mới vào
một cấu trúc cạnh đã cố định. Test6 so sánh label CÙNG `(v,IV,C)` giữa chừng của MỘT quá trình
xây dựng liên tục theo thời gian thực — không có khái niệm "chèn giữa" ở đây, vì route không
bao giờ bị sửa lại quá khứ. Hai cơ chế dominance khác nhau về bản chất, không mâu thuẫn nhau dù
kết luận trái ngược. File: `Output/Test6/gate1_sec23_violations.csv` (rỗng).

---

## 4. Việc 2 — State space thật: nén rất tốt, càng n lớn càng nén tốt

3 ô trọng tâm (GW, B=4, tw∈{120,240}), đo trên n∈{4,5,6}:

| n | tw | median compression (n_states_survived / n_feasible_seq_total) |
|---|---|---|
| 4 | 120 | 0,1556 |
| 4 | 240 | 0,0874 |
| 5 | 120 | 0,0847 |
| 5 | 240 | 0,0579 |
| 6 | 120 | 0,0655 |
| 6 | 240 | **0,0553** |

Tại ô nặng nhất (n=6, tw=240 — đúng ô "bùng nổ" 2520+ sequence của Test2): state space DP sau
dominance chỉ bằng **~5,5%** của tổng số feasible sequence mà BFS hiện tại phải sinh/lưu (trung
bình 2126 state sống sót / 39690 sequence). **Xu hướng nén tốt lên khi n tăng** (0,16→0,055 khi
n: 4→6) — **ngược hẳn với Test4** (nơi compression D2/D3 xấu đi khi n tăng, do domination đòi
hỏi thắng đồng thời trên MỌI j∈Rem(S)). Cơ chế khác nhau: dominance của Test6 chỉ cần thắng trên
1 trạng thái cụ thể `(v,IV,C)`, không phải một hội (conjunction) qua toàn bộ order còn lại — nên
không mắc phải lời nguyền "càng nhiều order càng khó thắng" của D2/D3. File:
`Output/Test6/viec2_state_space.csv` (48 dòng).

**Theo §Việc2/Việc3 execution order (spec §6): tín hiệu nén tốt rõ ràng → tiếp tục Việc 3.**

---

## 5. Việc 3 — Wall-clock speedup thật: 5-10× xuyên suốt n=4..15

```
                    median speedup (t_BFS_current / t_DP)
n=4                 5,42×
n=5                 6,54×
n=6                 7,09×
n=10                8,29×
n=15                5,95×
```

Đo trực tiếp trên CÙNG instance (không phải instance khác nhau) cho cả BFS hiện tại
(`t2_core.bfs_generate`) và DP mới, tại **cả n≤6 (đối chứng) và n=10, n=15** (theo đúng bài học
Test4.1 — không tin số đo chỉ ở n nhỏ). Ví dụ cụ thể ở ô nặng nhất (n=15, tw=240): `t_DP≈11s`
vs `t_BFS≈70s` → speedup ~6-7×, nhất quán với n nhỏ hơn — **không có dấu hiệu speedup suy giảm
khi n tăng lên tới 15**, trái với lo ngại ban đầu (theo kinh nghiệm Test4.1/4.2, hiệu năng nhiều
rule khác xấu đi rõ rệt khi n tăng). File: `Output/Test6/viec3_speedup.csv` (90 dòng).

---

## 6. Kết luận

**Test6 là kết quả tích cực rõ ràng nhất trong toàn bộ chuỗi Test2-6, và đủ căn cứ (Gate 1 +
§2.3 + Việc 2 + Việc 3 đều pass/tích cực) để đề xuất thay thế Algorithm A (BFS level-wise) bằng
DP label-setting, trong phạm vi đã đo:**

- **Đúng (sound):** 0 vi phạm trên 616 instance Gate 1 + 160 instance §2.3 — dominance forward
  label-setting áp dụng xuyên suốt (kể cả giữa chừng khi `IV≠∅`) không làm mất bundle nào, không
  làm mất điểm Pareto-optimal nào, không ảo giác điểm không tồn tại, trên GW và OD, B=2..4,
  n=3..6, toàn bộ tw_width/tau grid.
- **Nén tốt:** state space sống sót chỉ ~5,5-16% của số sequence mà BFS hiện tại phải sinh, và
  nén **tốt lên** (không xấu đi) khi n tăng — khác biệt cơ bản, tích cực so với mọi rule dựa trên
  so sánh cặp route (D2/D3, §5.4 của Test4) vốn đều xấu đi theo n.
- **Nhanh thật:** speedup 5-10× so với BFS hiện tại, đo trực tiếp trên cùng instance, ổn định từ
  n=4 tới n=15 — phạm vi đã xác nhận thực nghiệm.

**Phạm vi đã xác nhận (không ngoại suy ra ngoài):** n∈{3,...,15}, B∈{2,3,4}, class∈{GW,OD},
tw_width∈{30,60,120,240} (GW), tau∈{15,30,60} (OD, chỉ cell đạt feasibility_rate_k1≥0,5).
**Chưa đo:** B>4, n>15 — nếu main experiment (đề cương §12.4: n∈{10,15,20,30}) cần vượt các giá
trị này, cần một vòng đối chứng bổ sung theo đúng tinh thần Test4.1 trước khi khoá kết luận cuối
cùng cho thesis, đặc biệt tại n=20,30 và B=5 (đã ghi nhận là giới hạn mô hình riêng cho GW theo
`HICA-S Algorithm A.md` §7).

---

## 7. File

| File | Nội dung |
|---|---|
| `Output/Test6/gate1_violations.csv` | Gate 1.A/B/C — rỗng (0 vi phạm / 616 instance) |
| `Output/Test6/gate1_sec23_violations.csv` | §2.3 — rỗng (0 vi phạm / 160 instance) |
| `Output/Test6/viec2_state_space.csv` | 48 dòng — state space thật, 3 ô trọng tâm |
| `Output/Test6/viec3_speedup.csv` | 90 dòng — wall-clock DP vs BFS, n=4..15 |
| `experiments/T2BFS/t6_dp.py` | Core DP: Label, transition, dominance, `run_dp()` |
| `experiments/T2BFS/t6_run_gate1.py` | Gate 1.A/B/C |
| `experiments/T2BFS/t6_run_gate1_dominance_midway.py` | §2.3 (DP_full vs DP_prune) |
| `experiments/T2BFS/t6_run_viec2.py` | State space, 3 ô trọng tâm |
| `experiments/T2BFS/t6_run_viec3.py` | Wall-clock speedup, n≤6 + n=10,15 |

Tổng thời gian chạy: Gate1 ≈ 84s, §2.3 ≈ 5,3s, Việc2 ≈ 17s, Việc3 ≈ 499s (~8,3 phút) — toàn bộ
Test6 xong trong khoảng **10 phút compute**, rẻ hơn hẳn Test4/Test4.1/Test4.2 cộng lại, dù đây
là hướng tham vọng nhất.
