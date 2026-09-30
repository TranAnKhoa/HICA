# Báo cáo: Test C — Relaxed-Key Upper-Bound (hướng NG-route-style)

> Theo đúng thứ tự đề xuất trong `Test_C.md`: (1) đo optimistic upper-bound trên
> n=10-15 trước, (2) nếu tiềm năng lớn (>50%) mới chuyển sang `audit_relaxed_key_safety`
> trên n≤6 để tìm phản ví dụ.

---

## Kết luận ngắn gọn

**Upper-bound rất lớn (87.1% giảm frontier trung bình) nhưng CẢ HAI biến thể relaxed-key
đều KHÔNG AN TOÀN** — đã tìm được phản ví dụ cụ thể, tỷ lệ vi phạm cao (~46-47% instance
trên gate n≤6), và đã xác định được **cơ chế lỗi cấu trúc rõ ràng**: `C` (tập order đã giao
xong) không phải thông tin dư thừa — nó xác định *bundle cuối cùng nào* một label có thể còn
tiếp tục hoàn thành, nên hai label cùng `(v, IV)` nhưng khác `C` đại diện cho hai tương lai
không thể hoán đổi cho nhau, dù `(K,W)` một cái "tốt hơn" cái kia theo nghĩa thông thường.

Theo đúng bảng tiêu chí ở mục 4 và hướng dẫn ở mục 5 của `Test_C.md`: đây là **kết luận cấu
trúc đáng viết** (structural REJECTED), tương tự các hướng bị bác trước đó trong dự án —
không phải "chưa tìm ra điều kiện safe", mà là bằng chứng cho thấy `C` mang thông tin thực
sự cần thiết cho tính đúng đắn của dominance.

---

## Bước 1-3: Đo optimistic upper-bound

Chạy trên n=10, n=15 (B_gw=4, tw=240 — gần vùng hot-zone đã xác định ở Case 1 vs Case 2),
3 seed mỗi cỡ, log **toàn bộ label sống sót sau dominance gốc ở mọi round** (không chỉ
frontier cuối), áp lại dominance theo key thô hơn.

| n | B_gw | tw | seed | frontier (key_full) | frontier (key_drop_C) | % giảm | frontier (key_drop_C_size_only) | % giảm |
|---|---|---|---|---:|---:|---:|---:|---:|
| 10 | 4 | 240 | 0 | 138,580 | 16,725 | 87.9% | 26,327 | 81.0% |
| 10 | 4 | 240 | 1 | 64,272 | 9,884 | 84.6% | 15,610 | 75.7% |
| 10 | 4 | 240 | 2 | 80,958 | 11,478 | 85.8% | 18,637 | 77.0% |
| 15 | 4 | 240 | 0 | 560,658 | 74,362 | 86.7% | 100,686 | 82.0% |
| 15 | 4 | 240 | 1 | 770,826 | 86,617 | 88.8% | 122,986 | 84.0% |
| 15 | 4 | 240 | 2 | 961,152 | 108,989 | 88.7% | 149,297 | 84.5% |

**Trung bình % giảm (key_drop_C): 87.1%** — ổn định qua mọi seed (84.6-88.8%), xu hướng
tăng nhẹ theo n (không giảm dần — tiềm năng không "biến mất" khi instance lớn hơn).

Theo bảng tiêu chí mục 4 (`Test_C.md`): **>50% → đáng đầu tư, chuyển sang
`audit_relaxed_key_safety`.**

Script: `spec_2a_2b/src/test_C_relaxed_key.py`.

---

## Bước 4: audit_relaxed_key_safety (n≤6 vs brute-force)

Chạy DP THẬT với key nới lỏng thay `key_full` trong toàn bộ dominance (closure-BFS và
pickup-round), so route_pool cuối với `brute_force.py` trên n∈{3,4,5,6}, B_gw∈{2,3,4},
tw∈{60,120,240}, 5 seed/cell = 720 instance mỗi key.

| Key | Instances checked | Mismatches | Tỷ lệ | Verdict |
|---|---:|---:|---:|---|
| `key_drop_C` = `(v, IV)` | 720 | 333 | 46.3% | **KHÔNG AN TOÀN** |
| `key_drop_C_size_only` = `(v, IV, \|C\|)` | 720 | 339 | 47.1% | **KHÔNG AN TOÀN** |

Cả hai fail ngay ở n=3, B_gw=2 — không phải cạnh biên hiếm, mà là lỗi phổ biến, xảy ra
trên gần một nửa số instance kiểm tra.

Script: `spec_2a_2b/src/test_C_audit_safety.py`.

---

## Cơ chế lỗi cụ thể (trace tay 1 phản ví dụ)

**Instance:** n=3, B_gw=2, tw=60, seed=2, driver gw0 (GW), 3 order `o0, o1, o2`.

Brute-force tìm được đúng 1 điểm cho bundle `{o0, o2}`: **K=16.246216, W=5.567214**
(sau `finalize_KW`) — DP với `key_full` cũng tìm đúng điểm này. Nhưng DP với `key_drop_C`
**mất hẳn** điểm này khỏi route_pool.

Trace từng bước bằng `_try_pickup`/`_try_delivery` thật (không qua patch nào):

```
Con duong DUY NHAT dan toi bundle {o0,o2} hoan chinh (interleaved, khong phai
pickup-ca-2-roi-giao-ca-2 - thu tu do bi chan boi deadline pickup cua o0):

  start (t=0)
    --pickup o0--> v=n6  IV={o0}      Cd={}     t=23.76
    --deliver o0-->v=n7  IV={}        Cd={o0}   t=33.17  K=6.01  W=33.17
    --pickup o2 -->v=n10 IV={o2}      Cd={o0}   t=319.33 K=13.01 W=319.33   <-- LABEL B
    --deliver o2-->v=n11 IV={}        Cd={o0,o2} t=334.03 K=16.25 W=334.03  (final: K=16.246216 W=5.567214)

Trong khi do, o mot nhanh KHAC (pickup o2 truc tiep tu start, khong qua o0):
    start (t=0)
    --pickup o2 -->v=n10 IV={o2}      Cd={}     t=319.33 K=3.49  W=319.33   <-- LABEL A

LABEL A va LABEL B CUNG (v=n10, IV={o2}) nhung KHAC C ({} vs {o0}).
Voi key_full: 2 key khac nhau -> ca 2 cung ton tai song song, khong canh tranh nhau.
Voi key_drop_C: CUNG mot bucket (n10, {o2}) -> so dominance THUAN theo (K,W):
   A: K=3.49  W=319.33
   B: K=13.01 W=319.33
   A dominate B (K thap hon, W bang nhau) -> B BI XOA.

Nhung B la con duong DUY NHAT dan toi bundle {o0,o2} (A khong con "quyen" giao o0 nua -
o0 chua duoc pickup trong nhanh A, va deadline pickup cua o0 (l=78.76) da troi qua tu lau
o thoi diem t=319.33). Xoa B => mat vinh vien diem (16.246216, 5.567214) khoi route_pool.
```

**Diễn giải cấu trúc:** `C` không phải "thông tin phụ, không ảnh hưởng tương lai" như giả
thuyết ban đầu trong `Test_C.md` mục 1 — nó **xác định bundle mục tiêu cuối cùng** mà một
label còn có thể hướng tới. Hai label cùng `(v, IV)` nhưng khác `C` không hề "dẫn tới cùng
một tương lai với chi phí khác nhau" (điều kiện cần để dominance hợp lệ) — chúng dẫn tới
**hai tập bundle hoàn chỉnh khác nhau** (A có thể hoàn thành `{o2}`, `{o1,o2}`... nhưng
không bao giờ `{o0,o2}` nữa; B có thể hoàn thành `{o0,o2}`). So sánh `(K,W)` giữa chúng và
giữ lại "cái rẻ hơn" là so sánh sai đối tượng — tương đương so sánh chi phí của hai kế hoạch
khác nhau rồi tưởng nhầm là đang chọn giữa hai cách thực hiện cùng một kế hoạch.

Đây chính xác là lý do vì sao dominance nguyên bản của `t6_dp.py` phải dùng key đầy đủ
`(v, IV, C)` — không phải một lựa chọn thận trọng thừa, mà là **điều kiện cần** để dominance
không phá vỡ tính đúng đắn (Sec1.2 trong `t6_dp.py`).

---

## Đối chiếu với mục 5 của `Test_C.md` (bước tiếp theo nếu key không safe)

Mục 5 đề xuất 2 hướng chặt hơn nếu `key_drop_C` thất bại:

1. **`key_drop_C_size_only`** (giữ `|C|`, bỏ danh tính) — đã thử, **cũng thất bại**
   (47.1% mismatch) với cùng cơ chế: `|C|=1` không phân biệt được "đã giao o0" vs "đã giao
   o1" vs "đã giao o2" — vẫn gộp nhầm các nhánh dẫn tới bundle đích khác nhau.
2. **Nới lỏng theo `t`** (cho phép lệch trong ngưỡng ε cố định) — **không thử**, vì cơ chế
   lỗi vừa xác định không nằm ở `t` mà ở chính `C`/danh tính order đã giao — nới lỏng `t`
   không giải quyết được vấn đề "label nào còn quyền hướng tới bundle nào", nên không có cơ
   sở để kỳ vọng nó khác kết quả của 2 biến thể trên.

Theo đúng câu cuối mục 5: **"Nếu cả hai đều không an toàn — đây tự nó là bằng chứng cho
thấy C (hoặc t chính xác) mang thông tin thực sự cần thiết cho tính đúng đắn, không phải dư
thừa — một kết luận cấu trúc đáng viết ra, tương tự các REJECTED trước đó trong dự án."**
Đây chính xác là kết quả thu được.

---

## Kết luận tổng hợp và vị trí trong bức tranh chung

- **Upper-bound lạc quan lớn (87%) nhưng KHÔNG đạt được trong thực tế** — vì điều kiện
  "an toàn tuyệt đối khi nới lỏng" (giả định ở mục 2 của `Test_C.md`) **không đúng**: đã có
  phản ví dụ cụ thể, cơ chế rõ ràng, tỷ lệ vi phạm cao (không phải cạnh biên).
- Đây là hướng **thứ 4** (sau PCF, MST, IV-completion) không giúp gì cho vùng Case 2
  (frontier Pareto bùng nổ), nhưng khác 3 hướng trước ở chỗ: 3 hướng trước thuộc họ
  "phát hiện chết sớm" (bất lực vì *không có gì chết* ở vùng này — xem
  `Report_Test_case2_followup.md`), còn Test C thuộc họ "gộp nhóm dominance rộng hơn" —
  bất lực vì **gộp nhóm sai sẽ phá vỡ tính đúng đắn**, không phải vì tiềm năng nhỏ.
- Kết hợp với phát hiện Case 1 vs Case 2 (100% death_age=0, không có nhánh chết muộn) và
  Test A/A2/B (0 label thật sự infeasible-delivery ở hot-zone), bức tranh tổng thể giờ đã
  đầy đủ: **frontier lớn ở vùng B_gw lớn/tw rộng là kết quả tất yếu của bài toán** (mỗi label
  sống sót đại diện cho một bundle-đích khác nhau, không thể gộp nhóm rộng hơn mà giữ đúng),
  không phải một khiếm khuyết có thể sửa bằng kỹ thuật pruning/dominance thông minh hơn mà
  vẫn giữ exactness.
- **Không có hướng nào trong 4 hướng đã thử (PCF nới rộng, MST, IV-completion, relaxed-key)
  cải thiện được vùng hot-zone.** Kết luận cho thesis: vùng B_gw lớn/tw rộng là giới hạn cấu
  trúc của bài toán exact dưới DSIC condition #3, không phải giới hạn kỹ thuật của cách hiện
  thực hoá Algorithm A.

---

## Trạng thái xử lý

- Script giữ lại làm tài liệu tham khảo: `spec_2a_2b/src/test_C_relaxed_key.py`,
  `test_C_audit_safety.py`, `debug_test_c_mechanism.py`.
- `run_2b_v2.py` (lưới 2b chính thức, không liên quan nhánh nghiên cứu này) chạy độc lập
  suốt quá trình, không bị ảnh hưởng.
