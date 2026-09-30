# Test6.1 — Kiểm chứng đối kháng cho Test6 (trước khi tin kết quả tích cực)

**Bối cảnh:** Test6 báo cáo kết quả tích cực nhất trong toàn bộ chuỗi (Gate 1 A/B/C pass tuyệt
đối trên 616 instance, §2.3 pass trên 160 instance, nén 5-16%, speedup 5-10×). Đây là kết quả
đủ lớn để viết lại phần đóng góp kỹ thuật của thesis — **chính vì vậy nó cần mức độ hoài nghi
cao hơn hẳn, không phải thấp hơn, so với các test trước.**

**Ba lỗ hổng cụ thể trong Test6 cần vá trước khi tin:**
1. `SEEDS_PER_CELL` của §2.3 (câu hỏi trung tâm — dominance có an toàn giữa chừng không) chỉ
   dùng 4, thấp hơn Gate 1 chính (8), với lý do "0 vi phạm không đổi giá trị dù seed ít" — đây
   là **suy luận sai**: 0 vi phạm quan sát được trên vùng dò tìm hẹp hơn là bằng chứng **yếu
   hơn**, không phải "không đổi". Việc 1 vá lại điều này.
2. Mọi phản ví dụ đã hạ gục các hướng trước (Test3 Pareto, Test4 Việc 4 D2/D3) đều được tìm
   bằng **dựng tay có chủ đích** (hình học crisscross, nút thắt hai đầu tuyến), không phải bằng
   quét seed ngẫu nhiên. Grid ngẫu nhiên của Test6 (dù bao nhiêu seed) có thể đơn giản không
   tình cờ sinh ra đúng cấu hình hiếm làm lộ lỗi. Việc 2 tấn công trực diện bằng chính các
   phản ví dụ đã biết.
3. Người thiết kế thuật toán và người thiết kế gate kiểm tra dùng chung một khung suy luận —
   rủi ro cùng điểm mù. Việc 3 dùng brute-force làm trọng tài độc lập tuyệt đối, không dùng bất
   kỳ logic nào từ `t6_dp.py`.

**Nguyên tắc xuyên suốt Test6.1:** không thêm gate mới dễ hơn — chỉ **siết chặt** gate đã có
hoặc **tấn công trực diện** đúng chỗ đã biết là nguy hiểm. Nếu Test6.1 pass hết, kết luận của
Test6 mới đủ vững để đưa vào thesis.

---

## 0. Không được làm

1. Không viết lại `is_feasible()`, `bfs_generate()`, hay bất kỳ hàm ground-truth nào — dùng
   nguyên bản đã validate xuyên suốt Test2-6.
2. Không nới lỏng bất kỳ ngưỡng nào đã khoá ở Test2-6 (ví dụ không đổi `SPEED_KMH`, `capacity`,
   generator OD đã patch).
3. Không chấp nhận "pass gần tuyệt đối" — mọi gate ở đây vẫn là đúng/sai tuyệt đối như Test6.
4. Không chỉ chạy lại y hệt Test6 với seed nhiều hơn rồi dừng — Việc 2 và Việc 3 bắt buộc phải
   chạy, vì chúng nhắm vào loại lỗi mà tăng seed ngẫu nhiên không phát hiện được.

---

## 1. Việc 1 — Vá §2.3: tăng seed, đúng chuẩn Gate 1 chính

### 1.1 Cách chạy

Chạy lại nguyên vẹn `t6_run_gate1_dominance_midway.py`, chỉ đổi:
```
SEEDS_PER_CELL: 4 → 8      (khớp Gate 1 chính, không hơn không kém — để so sánh công bằng)
```
Trên đúng grid đã dùng ở Test6 §2.3 (n∈{3,4,5}, B∈{2,3,4}, GW+OD).

### 1.2 Mở rộng bắt buộc — không chỉ tăng seed, còn phải tăng n

Test6 §2.3 chỉ chạy tới n=5 (thấp hơn cả Gate 1 chính, vốn chạy tới n=6). Đây là điểm yếu
riêng biệt với vấn đề seed. Chạy thêm:
```
n ∈ {6}   (khớp đúng biên trên của Gate 1 chính)
```

### 1.3 Ngưỡng — vẫn tuyệt đối, không đổi

```
violation (DP_full tìm được label hoàn chỉnh mà DP_prune bỏ sót) PHẢI = 0
```
Bất kỳ vi phạm nào (dù 1 lần trên n=6 mới thêm, hoặc ở seed 5-8 mới thêm) đều là tín hiệu
nghiêm trọng — dừng ngay, không tiếp tục Việc 2/3, quay lại phân tích chỗ hỏng của Test6.

---

## 2. Việc 2 — ★ Tấn công bằng phản ví dụ đã biết (quan trọng nhất của Test6.1)

### 2.1 Bộ phản ví dụ bắt buộc — dựng tay, không sinh ngẫu nhiên

Dùng lại đúng số liệu đã dựng trong lịch sử hội thoại (không đổi một con số nào, để có thể đối
chiếu ngược nếu cần):

**Phản ví dụ A — Route1/Route2/O3 (crisscross, khe hở đầu tuyến):**
```
X=0. O1: P1=10,D1=12. O2: P2=30,D2=32. O3, O4: theo đúng số liệu "τ=11 đơn vị mỗi cái" đã
dùng để minh hoạ Test4 §4.2 (giữ đúng để tái dùng kết quả tính tay đã có).
```
Kỳ vọng: DP phải tìm được đúng route dùng khe hở ở đầu tuyến (đã tính tay: slack tốt hơn hẳn
route "gọn"). Kiểm bằng cách so `Front_DP` cho instance NÀY với đáp án tính tay đã có trong
lịch sử hội thoại (không phải ground truth code, mà đáp án đại số đã tính ở phần đầu chuỗi hội
thoại dẫn tới Test4).

**Phản ví dụ B — nút thắt hai đầu tuyến (đã dùng để phá D1 ở Test4 §Đào sâu):**
```
X=0. O1: P1=10,D1=12. O2: P2=30,D2=32.
Route A: X-P1-D1-P2-D2 (nút thắt ở D2, cuối tuyến, slack=19)
Route B: X-P2-D2-P1-D1 (nút thắt ở P2, đầu tuyến, slack=2)
O3, O4: mỗi order tốn thêm τ=11 khi chèn riêng lẻ; τ=22 khi chèn CẢ HAI cùng lúc (đã tính tay:
        A không cứu được khi chèn cả O3+O4, B cứu được).
```
Kỳ vọng: DP tìm được bundle `{O1,O2,O3,O4}` (nhánh mang tính chất giống Route B), và **không**
để dominance-giữa-chừng của Test6 vô tình loại mất nhánh dẫn tới kết quả này.

**Phản ví dụ C — tổng hợp, B=4, một biến thể trộn A và B** (thiết kế mới, mục đích: hai phản ví
dụ trên đều chỉ có 2 order "nền" + 2 order "chèn thêm"; dựng thêm một case có **3 order nền +
1 order chèn** để kiểm dominance giữa chừng ở độ sâu khác — tự thiết kế theo đúng khuôn mẫu A/B,
ghi rõ toàn bộ số liệu vào report, không được giấu bớt để "cho gọn").

### 2.2 Cách chạy và ngưỡng

Với mỗi phản ví dụ (A, B, C):
```
1. Chạy is_feasible() gốc + brute_force() gốc để có đáp án chắc chắn (không dùng đáp án tính
   tay làm ground truth cuối cùng — dùng nó làm KỲ VỌNG để đối chiếu, brute_force() mới là
   trọng tài).
2. Chạy t6_dp.run_dp() trên đúng instance đó.
3. So Front_DP với Pareto front từ brute_force(): PHẢI khớp tuyệt đối (Gate giống 1.B/1.C của
   Test6, áp dụng cho đúng 3 instance này).
4. Nếu Front_DP khớp brute_force() nhưng KHÔNG khớp đáp án tính tay ban đầu → không phải lỗi
   DP, mà là đáp án tính tay ở các lượt hội thoại trước có sai số nhỏ (khả năng thật, vì đó là
   tính tay) → ghi rõ, không coi là violation của DP.
5. Nếu Front_DP KHÔNG khớp brute_force() → VIOLATION THẬT, dừng ngay, đây là ưu tiên cao nhất
   để debug, vì đây chính là kiểu phản ví dụ đã hạ gục 3 hướng trước.
```

**Đặc biệt chú ý khi debug nếu fail:** kiểm xem violation có xảy ra đúng ở bước dominance khi
`IV≠∅` (giữa chừng) hay không — nếu đúng, đây là bằng chứng trực tiếp bác bỏ giả thuyết §0 của
Test6, mạnh hơn hẳn bất kỳ con số % nào từ grid ngẫu nhiên.

---

## 3. Việc 3 — Kiểm bằng brute-force độc lập trên grid mở rộng, không dùng logic t6_dp.py

### 3.1 Mục đích

Loại bỏ rủi ro "cùng điểm mù" (§Bối cảnh mục 3): viết một bộ so sánh **hoàn toàn tách biệt**
khỏi mọi thứ trong `t6_dp.py`, chỉ dùng `is_feasible()` và `brute_force()` gốc.

### 3.2 Cách chạy

```
for mỗi instance (n∈{4,5,6,7}, B∈{2,3,4}, GW+OD, mở rộng thêm n=7 so với Test6 gốc):
    for mỗi subset S, 1≤|S|≤B:
        pareto_truth = Pareto-front (K,W) từ brute_force(S) — TÍNH LẠI TỪ ĐẦU, không đọc
                       lại kết quả đã lưu của Test2/Test4 (dù có thể trùng, để tránh khả năng
                       một bug cũ trong pipeline tính K,W bị kế thừa xuyên suốt các test)
        pareto_dp    = Pareto-front (K,W) trích từ Front_DP của t6_dp.run_dp() cho instance đó

    So sánh pareto_truth và pareto_dp: PHẢI khớp tuyệt đối cho MỌI S, MỌI instance
```

**Điểm khác biệt quan trọng với Gate 1 gốc của Test6:** ở đây `pareto_truth` được tính **độc
lập, từ đầu**, không tái sử dụng bất kỳ pipeline trung gian nào (kể cả `t4_profile.K_W_of_route`
nếu hàm đó có khả năng chứa cùng loại bug với `t6_dp.py` — ví dụ nếu cả hai đều dùng chung một
hàm quy đổi đơn vị km/phút sai, Gate 1 gốc sẽ pass giả). Viết một hàm `compute_KW_independent()`
riêng cho Test6.1, tính trực tiếp từ toạ độ + κ + speed, không import từ `t4_profile.py`.

### 3.3 Ngưỡng

```
= 0 vi phạm tuyệt đối, trên n mở rộng tới 7 (Test6 gốc chỉ tới 6)
```

**Nếu Việc 3 phát hiện vi phạm mà Gate 1 gốc của Test6 không phát hiện được** → xác nhận nghi
ngờ "cùng điểm mù" ở §Bối cảnh mục 3 là có cơ sở → toàn bộ kết luận Test6 cần viết lại, không
chỉ vá.

---

## 4. Việc 4 — Đối chứng B=5 (tuỳ chọn, chỉ chạy nếu Việc 1-3 đều pass)

Đề cương gốc coi B≤2 (thận trọng) hoặc B≤4 (theo model đã khoá) là giới hạn cho GW. Nếu DP
label-setting của Test6 thực sự tổng quát hơn BFS cũ (không phụ thuộc cấu trúc "chèn vào giữa"
gây bùng nổ giai thừa), nó có thể vẫn đúng ở B=5 dù B=5 ngoài phạm vi chính của model.

```
Chạy Gate 1 (A/B/C) với B=5, n∈{5,6,7} (n≥B), GW only (đủ đại diện, không cần OD)
Đo thêm: n_states_visited có còn nhỏ so với (2·5)!/2^5 = 113.400 (trần lý thuyết ở k=5) không?
```

**Không bắt buộc pass để Test6.1 kết luận thành công** — đây là thông tin bổ sung cho thesis
(ví dụ: "giới hạn B≤4 của model không phải giới hạn thuật toán, mà là lựa chọn thiết kế"), ghi
rõ là tuỳ chọn trong report.

---

## 5. Thứ tự thực thi và điều kiện dừng

```
Việc 1 (vá seed §2.3)     →  violation > 0  ⟹  DỪNG, Test6 §2.3 gốc pass giả do seed ít
        ↓ pass (0 violation, kể cả n=6 mới thêm)
Việc 2 (phản ví dụ tay)   →  BẤT KỲ phản ví dụ nào fail (so brute_force, không phải so đáp án
                              tính tay)  ⟹  DỪNG NGAY, đây là violation nghiêm trọng nhất có thể
                              tìm được, ưu tiên debug cao nhất
        ↓ pass cả 3 phản ví dụ A, B, C
Việc 3 (brute-force độc lập, n tới 7)  →  bất kỳ violation nào  ⟹  DỪNG, so sánh với Gate 1 gốc
                              của Test6 xem có bị bỏ sót do "cùng điểm mù" không
        ↓ pass
Việc 4 (B=5, tuỳ chọn)    →  chạy nếu có thời gian, không chặn kết luận chính
```

---

## 6. Báo cáo cần trả về

`Test6.1_report.md`:

1. Việc 1: bảng seed 4 vs 8 (và n=6 mới thêm) — có đổi kết luận §2.3 gốc không.
2. Việc 2: với TỪNG phản ví dụ A/B/C — số liệu đầy đủ, kết quả brute_force, kết quả DP, so
   sánh, và nếu có sai lệch với đáp án tính tay cũ thì giải thích rõ do đâu (đáp án tay sai hay
   DP sai).
3. Việc 3: kết quả brute-force độc lập, đặc biệt nêu rõ có phát hiện gì mà Gate 1 gốc của Test6
   bỏ sót hay không.
4. Việc 4 (nếu chạy): B=5 có còn đúng không, và so sánh state space với trần lý thuyết.
5. **Kết luận cuối cùng, viết thẳng theo 1 trong 2 hướng:**
   - Nếu TẤT CẢ pass: "Kết luận của Test6 được xác nhận qua kiểm chứng đối kháng — đủ căn cứ
     đưa vào thesis làm đóng góp kỹ thuật chính, thay thế Định lý R1 (depth-1) làm trọng tâm."
   - Nếu BẤT KỲ đâu fail: mô tả chính xác violation đầu tiên tìm được, phân loại nguyên nhân
     (lỗi cài đặt cụ thể sửa được / giả thuyết dominance-giữa-chừng bị bác bỏ), và đánh giá lại
     toàn bộ kết luận Test6 dựa trên phát hiện mới — không được giữ nguyên kết luận cũ "vì đa số
     vẫn pass".
