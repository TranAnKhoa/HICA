# Việc cần làm tiếp — snapshot tại 2026-09-15

> Đọc file này đầu tiên khi mở hội thoại mới. Trạng thái các pipeline nền + việc còn treo.

---

## 1. `run_2b_v2.py` — ĐÃ ĐÓNG (720/1080, dừng có chủ đích) — KHÔNG chạy lại

- **Kết quả cuối**: `(B_gw=3,B_od=1)` 360/360 và `(B_gw=3,B_od=2)` 360/360 — cả 2 HOÀN TẤT
  100%. `(B_gw=5,B_od=2)` = 0/360 — **bỏ qua vĩnh viễn**, ghi nhận là giới hạn thực nghiệm
  (ngay cell đầu tiên n=30 đã ăn ~24GB RAM trên máy 32GB dù đã giảm xuống 1 worker tuần tự —
  không phải vấn đề song song hóa). Quyết định người dùng 2026-09-15: không chạy lại tổ hợp
  này, không hạ B_gw/n để né RAM.
- **Report đã cập nhật đầy đủ**: `Guideline_Total/Report_2b_Component_Distribution.md` —
  phản ánh đúng 720/720 của 2 tổ hợp `B_gw=3`, giải thích lý do dừng `(5,2)`, kết luận
  **hướng (B)** giữ nguyên (component conflict-graph luôn gộp gần hết driver,
  `largest_component_fraction` ≥ 0.889 trên toàn bộ 720 cell, hầu như luôn = 1.000).
- **Không còn process nền nào chạy cho mục này** — không cần theo dõi/resume gì thêm.

## 2. new03.md — các việc còn treo sau khi 2b v2 xong

- [ ] Re-run `viec1_speedup_estimate.py` trỏ vào `2b_v2_raw` (hiện đang hardcode path cũ
      `2b_raw`) — cần sửa path trước khi chạy.
- [ ] Re-confirm `feasibility_rate_k1` trên dữ liệu B_gw/B_od mới.
- [ ] So sánh CPLEX speedup cũ vs mới (dùng dữ liệu 2b v2).
- [ ] Rework `viec_extra_real_wdp_speedup.py`'s hardcoded `CASES` (seed đại diện) — cấu trúc
      component đã đổi với dữ liệu B_gw/B_od+PCF mới, các case cũ có thể không còn đại diện.
- [ ] Cập nhật `main_guideline.md` theo checklist Việc 5 của new03.md — **chỉ thêm ghi chú
      bên cạnh, KHÔNG xoá/viết lại phần cũ** (quy tắc đã khoá từ trước).
- [ ] Viết báo cáo tổng hợp cuối theo đúng thứ tự new03.md "Sau khi hoàn thành": Gate 0+T4-B
      → feasibility_rate_k1 → Việc 2.4 PCF benefit → toàn bộ kết quả 2a/2b → CPLEX speedup
      so sánh.

## 3. Test_EJOR_direction/ — Test C (relaxed-key) — ĐÃ CÓ KẾT LUẬN, cần viết report cuối

Đã hoàn thành đủ dữ liệu, **chưa viết file report cuối cùng** (`Report_Test_C.md` đang mở
trong IDE nhưng theo trạng thái phiên trước là còn trống/chưa được tôi điền) — đây là việc
ưu tiên cao cho hội thoại mới nếu chưa làm:

- **Bước 1-3 (upper-bound optimistic)**: đo trên n=10,15 (`test_C_relaxed_key.py`), kết quả
  **87.1% giảm frontier trung bình** (key_drop_C), rất ổn định qua 6 cell (n=10/15 × 3 seed)
  → vượt xa ngưỡng >50% "đáng đầu tư" trong `Test_C.md`.
- **Bước 4 (audit safety, n≤6 vs brute-force)**: `test_C_audit_safety.py` — **GATE FAIL cho
  cả 2 biến thể**: `key_drop_C` (333/720 mismatch, 46.3%), `key_drop_C_size_only` (339/720,
  47.1%). Cả hai đều KHÔNG AN TOÀN — mất route hợp lệ thật sự (không phải false positive).
- **Đã viết `Lemma_C.md`** (trong `Test_EJOR_direction/`) chứng minh cơ chế unsoundness cụ
  thể (Lemma 1: khi tồn tại order `j` đã giao ở nhãn B nhưng deadline pickup của nó đã trôi
  qua so với thời điểm nhãn A, hai nhãn không thể so dominance dù cùng (v,IV)) — **đã kiểm
  chứng đúng** cả về logic chứng minh lẫn đối chiếu với code thật (`t6_dp.py`, giả thiết A1
  "đồng hồ không lùi" đã xác nhận đúng 100% qua đọc trực tiếp `_try_pickup`/`_try_delivery`/
  `_try_home`) và khớp số liệu thực nghiệm.
- **Kết luận cuối cho Test C**: relaxed-key **không khả thi** như một phép rút gọn độc lập-
  theo-nhãn (Corollary 2 trong Lemma_C.md giải thích lý do cấu trúc: điều kiện an toàn là
  ràng buộc theo cặp, không quy giản được thành key). Đây là kết quả REJECTED có giá trị
  (giải thích được *tại sao* C không dư thừa trong dominance key) — đáng đưa vào bài chính
  theo đúng gợi ý mục 4 của `Lemma_C.md` (đặt ngay sau phần mô tả dominance rule gốc).
- **Việc còn thiếu**: viết `Report_Test_C.md` tổng hợp (bảng upper-bound + gate audit +
  tham chiếu Lemma_C.md), đặt trong `Test_EJOR_direction/` như user yêu cầu ban đầu.

## 4. Trạng thái các nhánh nghiên cứu phụ đã đóng (không cần làm lại)

- **MST/1-tree bound**: REJECTED — 0% cut rate, quá lỏng vì bỏ qua precedence
  pickup-before-delivery. (`research_mst_bound.py`, đã dừng theo yêu cầu user.)
- **Case 1 vs Case 2**: đã xác định dứt điểm — hot-zone (n=20,B_gw=4,tw=240) là **Case 2**
  thuần túy (frontier Pareto bùng nổ), không phải Case 1 (feasibility phát hiện muộn).
  Report: `Report_Case1_vs_Case2.md`.
- **Test_case2_followup (Test A/A2/B)**: đã xong + đã sửa 1 hiểu lầm quan trọng sau khi user
  chỉ ra mâu thuẫn — "22.4-31.1% closure chết" trong Test A là **artifact đếm** do dominance
  chéo giữa các closure ở bước trung gian, KHÔNG phải infeasibility thật (đã kiểm chứng: tắt
  dominance trong closure BFS → 0/224,887 closure thật sự infeasible). Kết luận Case 2 được
  củng cố thêm, không suy yếu. Report đã cập nhật: `Report_Test_case2_followup.md`.

## 5. Việc cần cẩn thận khi tiếp tục (nhắc lại các ràng buộc đã khoá)

- **Không bao giờ chạy lại pipeline đã hoàn thành** (2a Bước B, Gate T4-B, Gate 0 đều đã
  PASS — chỉ trích dẫn, không chạy lại).
- **Giữ nguyên toàn bộ dữ liệu lịch sử** — không xoá/ghi đè các file `*_raw/`, `*_summary.csv`
  cũ.
- **Mọi thay đổi vào `t6_dp.py`/dominance rule đều phải qua gate n≤6 vs brute-force trước khi
  tin bất kỳ số liệu tốc độ nào** — đã áp dụng nghiêm ngặt cho Test A2/B/C, tiếp tục giữ
  nguyên tắc này cho mọi thử nghiệm sau.
- **Không tự ý nới lỏng exactness** (không dùng ε-dominance, không heuristic) — khoá theo
  DSIC điều kiện #3 từ đầu dự án.
- **Nếu process nền (`run_2b_v2.py` hoặc tương tự) bị dừng đột ngột khi phiên kết thúc**:
  kiểm tra bằng `tasklist //FI "IMAGENAME eq python.exe"`, nếu không thấy process → resume
  bằng cách chạy lại đúng lệnh gốc (script đã có cơ chế resume qua CSV, an toàn).

## 6. File tham khảo nhanh

- `Guideline_Total/Spec 2a,2b.md` — spec gốc 2a/2b (đã hoàn thành phần lớn, xem báo cáo).
- `Guideline_Total/new03.md` — spec B_gw/B_od split + PCF (đang dở, xem mục 2 ở trên).
- `Guideline_Total/Report_2b_Component_Distribution.md` — báo cáo phân phối component (sơ
  bộ, cần cập nhật khi 2b v2 xong).
- `Test_EJOR_direction/Test_C.md`, `Lemma_C.md` — spec + proof cho hướng relaxed-key
  (đã REJECTED, cần viết report cuối — xem mục 3).
- `Report_Case1_vs_Case2.md`, `Report_Test_case2_followup.md` — 2 báo cáo nhánh phụ đã đóng.
- `Algorithm_A_Description.md` — mô tả chi tiết Algorithm A (dùng làm tham chiếu ký hiệu cho
  Lemma_C.md và mọi báo cáo sau).
