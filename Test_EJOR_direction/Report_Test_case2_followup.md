# Báo cáo: Test_case2_followup.md (Test A / A2 / B)

> Chạy song song với `run_2b_v2.py` (không ảnh hưởng), tại đúng cell nóng nhất đã xác nhận
> trước đó: **n=20, B_gw=4, tw=240, seed=0, 5 GW driver**.

---

## Bảng tổng kết

| Test | Nội dung | Gate (n≤6, brute-force) | Kết quả chính | Verdict |
|---|---|:---:|---|---|
| **A** | Đếm `attempts_per_closure` | — (đo thuần, không patch) | mean=8.36, max=104; 22.4% closure toàn-bộ-chết (mean 3.69 attempts/closure chết) | **(b) có thật** |
| **A2** | Patch IV-completion feasibility check | ✅ PASS (288/288) | 170.03s → 222.96s, **0 label bị cắt** (xác nhận: 0/224,887 closure thật sự infeasible-delivery — "chết" trong Test A là artifact đếm do dominance chéo giữa closure, không phải infeasibility thật) | **Speedup 0.763x — CHẬM HƠN, premise sai ngay từ đầu** |
| **B** | Bucket-hoá dominance (engineering) | ✅ PASS (288/288) | 180.44s → 177.43s | **Speedup 1.017x — không đáng kể** |

---

## Chi tiết từng test

### Test A — attempts_per_closure

```
So closure quan sat:                 845,727
Trung binh attempts/closure:          8.361
Max attempts trong 1 closure:         104
So closure toan-bo-chet (0 survivor): 189,071 (22.4%)
Attempts trung binh CHI trong closure toan-chet: 3.691
```

Kết luận theo đúng ngưỡng file đặt ra (>3-4 → kịch bản b): **8.36 rõ ràng thuộc kịch bản
(b)** — có "công lãng phí" thật sự khi mở rộng closure trước khi phát hiện toàn bộ chết.
Đây là lý do hợp lý để tiến hành Test A2.

### Test A2 — Patch IV-completion feasibility check

**Gate: PASS tuyệt đối** (288/288 instance n≤6, khớp brute-force 100%) — patch **đúng đắn
về mặt logic** (tính chất đơn điệu "thêm order tương lai không cứu được deadline IV đã lỡ"
đã được xác nhận thực nghiệm, không làm mất route hợp lệ nào).

**Nhưng về tốc độ: phản tác dụng.** `170.03s → 222.96s` (chậm hơn 31%), và **quan trọng
nhất: 0 label bị cắt bởi patch**. Điều này giải thích trực tiếp tại sao chậm hơn — patch
thêm chi phí gọi `itertools.permutations` ở **mọi** lần pickup thành công, nhưng không cắt
được gì cả.

**[CẬP NHẬT — điều tra sâu thêm sau khi user chỉ ra mâu thuẫn]** Ban đầu có vẻ mâu thuẫn:
Test A đo được 22.4-31.1% closure "chết hoàn toàn" (0 survivor), nhưng Test A2 lại cắt 0
label — nếu closure thật sự chết vì infeasible, `iv_completion_feasible` (kiểm đúng logic
với `_try_delivery` thật) đáng lẽ phải bắt được. Đã điều tra bằng 4 script debug độc lập
(`debug_test_a2_mismatch.py`, `debug_trace_one.py`, `debug_dominance_cross_closure.py`,
`debug_confirm_dominance_cause.py`) và xác định **root cause dứt điểm**:

- "Closure chết" trong định nghĩa Test A đo trên **route_pool SAU dominance**. Dominance
  trong `t6_dp.py::run_dp` được áp dụng ở **mọi bước trung gian** trong chuỗi giao hàng
  (vòng `while active:`), không chỉ ở bước cuối cùng — nên một closure có đường giao hàng
  khả thi thật sự vẫn có thể bị đếm "0 survivor" nếu label trung gian của nó bị một closure
  **khác** (tốt hơn, cùng key `(v,IV,C)`) đè mất (dominate) giữa chừng.
- Kiểm chứng trực tiếp: khi tắt hoàn toàn dominance trong closure BFS (chỉ để đo, không
  dùng sản xuất) trên toàn bộ 224,887 closure của 1 driver, **0/224,887 closure "chết thật
  sự"** — nghĩa là **không hề tồn tại closure nào thật sự infeasible-delivery** ở cell này;
  toàn bộ 22.4-31.1% "chết" trong Test A gốc là **artifact của cách đếm survivor theo
  closure riêng lẻ**, không phản ánh infeasibility thật.
- Đây là **hành vi ĐÚNG của thuật toán** (dominance chéo giữa các closure không làm mất
  route tối ưu ở route_pool cuối cùng — đã qua Gate T4-B 0/616 violation từ trước), chỉ làm
  sai lệch phép đo "survivor per closure" trong harness nghiên cứu Test A.
- Hệ quả: `iv_completion_feasible` cắt 0 label không phải vì "overhead vô ích trên premise
  đúng" như diễn giải ban đầu, mà vì **premise sai ngay từ đầu** — không có nhánh nào thật
  sự chết-vì-infeasible-delivery để cắt ở cell này.

**Diễn giải theo khung Case 1 vs Case 2 đã xác lập trước đó:** kết luận cuối cùng **không
đổi, mà còn được củng cố mạnh hơn**: nút thắt hoàn toàn nằm ở kích thước frontier (số nhánh
sống sót không dominate lẫn nhau), không có "công lãng phí" nào ở delivery-infeasibility để
tận dụng — không chỉ 100% death_age=0 (Report_Case1_vs_Case2.md), mà thực chất **không hề
tồn tại "death do infeasibility" nào cần phát hiện sớm** ở vùng hot-zone này.

### Test B — Bucket-hoá dominance

**Gate: PASS tuyệt đối** (288/288, khớp brute-force 100%) — kỹ thuật bucket/sort-theo-K
đúng đắn, không đổi route_pool.

**Tốc độ: gần như không đổi** (`180.44s → 177.43s`, speedup 1.017x). Điều này cho thấy chi
phí so sánh dominance (`O(F)` quét toàn bucket) **không phải là nút thắt chính** ở cell này
— phần lớn thời gian nằm ở việc **sinh label** (số lần `attempted` khổng lồ đã đo ở Test A:
845,727 closure × trung bình 8.36 attempts = ~7 triệu lượt thử), không phải ở việc so sánh
dominance sau khi đã sinh ra.

---

## Kết luận tổng hợp

**Cả 3 hướng thử nghiệm trong `Test_case2_followup.md` đều không mang lại lợi ích tốc độ đo
được ở cell nóng nhất** — nhất quán hoàn toàn với kết luận đã có trong
`Report_Case1_vs_Case2.md`: vấn đề tại vùng B_gw lớn/tw rộng là **Case 2 thuần tuý** (frontier
Pareto bùng nổ vì các label không thể so sánh với nhau), không phải do:
- feasibility phát hiện muộn (Test A2 xác nhận: 0 label bị cắt bởi kiểm tra sớm hơn)
- chi phí so sánh dominance chậm (Test B xác nhận: bucket-hoá không đổi lại gì đáng kể)

Điểm nghẽn thật sự nằm ở **số lượng tuyệt đối các lần thử mở rộng label** (`attempted` —
gần 7 triệu lượt cho 5 driver ở 1 cell), phản ánh đúng độ phức tạp tổ hợp `(2k)!/2^k` đã nêu
ở §7.3 thesis — không có cách nào giảm con số này mà không giảm được kích thước frontier
trước, và đã xác nhận (Case 1 vs Case 2 + Test A2) rằng không có cách pruning hợp lệ nào làm
được điều đó ở vùng này mà vẫn giữ exactness.

**Test C (relaxed key / NG-route, đo upper-bound) chưa được chạy** — theo đúng thứ tự đề
xuất trong file gốc, đây là bước tiếp theo nếu muốn tiếp tục thăm dò, nhưng cần lưu ý: đây
là hướng **not-safe-by-default**, chỉ dùng để đo tiềm năng lý thuyết trước khi đầu tư chứng
minh — không phải giải pháp có thể dùng ngay.

---

## Trạng thái xử lý

- Trong lúc viết Test B/A2, phát hiện và sửa 1 bug trong chính harness test (không phải bug
  thuật toán gốc): thiếu bước re-Pareto-front qua các node cuối `v` khác nhau trước khi so
  với brute-force (do `t6_dp.py`'s dominance cuối chỉ lọc trong cùng `v`, còn brute-force
  Pareto trên toàn bộ). Đã sửa cả 2 script (`test_case2_followup_B.py`,
  `test_case2_followup_A2.py`), xác nhận cả 2 gate đều PASS 100% sau khi sửa.
- Sau khi user chỉ ra mâu thuẫn 22.4-31.1% closure "chết" (Test A) vs 0 label bị cắt (Test
  A2), điều tra sâu bằng 4 script debug độc lập (`debug_test_a2_mismatch.py`,
  `debug_trace_one.py`, `debug_dominance_cross_closure.py`,
  `debug_confirm_dominance_cause.py`, tất cả giữ lại làm tài liệu tham khảo) và xác định dứt
  điểm: đây **không phải bug** trong `iv_completion_feasible` hay `t6_dp.py` — mà là do
  dominance áp dụng ở mọi bước trung gian trong closure BFS (không chỉ bước cuối), khiến
  định nghĩa "survivor per closure" trong Test A là artifact đếm, không phản ánh
  infeasibility thật. Đã kiểm chứng trực tiếp: tắt dominance trong closure BFS → 0/224,887
  closure "chết thật sự". Xem chi tiết trong phần "Test A2" ở trên.
- `run_2b_v2.py` (lưới 2b chính thức, không liên quan nhánh nghiên cứu này) chạy độc lập
  suốt quá trình, không bị ảnh hưởng — tại thời điểm báo cáo đang ở ~140/1080 (~13%).
- File script giữ lại làm tài liệu tham khảo: `spec_2a_2b/src/test_case2_followup_A.py`,
  `test_case2_followup_A2.py`, `test_case2_followup_B.py`.
