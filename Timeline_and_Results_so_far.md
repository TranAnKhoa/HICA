# Timeline & Results So Far — nội dung cho slide

> Mốc ngày lấy từ thời điểm tạo/sửa file + ghi chú memory của dự án (năm 2026), nên là **xấp xỉ**:
> ngày bắt đầu = lúc thư mục/spec được tạo, ngày kết thúc = lúc report cuối được ghi.
> Giai đoạn 0 (nền tảng) chỉ có ngày tạo thư mục nên khoảng thời gian mang tính ước lượng.

---

## PHẦN 1 — Timeline (dùng cho Gantt chart)

### Bảng Gantt (copy vào Excel/PPT: cột Task / Start / End)

| # | Giai đoạn | Task | Start | End | Trạng thái |
|---|---|---|---|---|---|
| 0 | Nền tảng | Dựng mô hình MILP open-route PDP + VCG, code CPLEX (`Src_Cplex`) | 2026-04-27 | 2026-08-10 | Xong |
| 1 | Kiểm chứng giả thuyết | Verification round 4: H1 (phân bổ đa tham số), H2 (vi phạm submodularity) | 2026-08-09 | 2026-08-09 | Xong |
| 2 | Tổng quan tài liệu | Đọc/tóm tắt paper, cross-check HICA, khởi tạo `Master_Thesis_Q1.md` | 2026-08-12 | 2026-08-13 | Xong |
| 3 | Dữ liệu | Sinh dataset Atlanta ARC (main / scale_a / urgency) | 2026-08-19 | 2026-08-21 | Xong |
| 4 | Dữ liệu | Data Fix v2: cluster hub, B=5, 7,680 instance main + 480 scale_a + 120 urgency | 2026-08-21 | 2026-08-28 | Xong |
| 5 | Thử nghiệm T4 | Pruning hình học T4: 3 vòng (synthetic → Atlanta → Data Fix v2) | 2026-08-19 | 2026-08-28 | Xong (kết luận âm) |
| 6 | Algorithm A | Test2: BFS sinh bundle (completeness) | 2026-09-07 | 2026-09-07 | Xong (đúng, nhưng bùng nổ) |
| 7 | Algorithm A | Test3: Pareto dominance + vá lỗi OD | 2026-09-07 | 2026-09-07 | Pareto bị loại |
| 8 | Algorithm A | Test4/4.1/5: representative rule, self-survival bound | 2026-09-08 | 2026-09-08 | Bị loại |
| 9 | Algorithm A | **Test6/6.1/6.2: DP label-setting tiến theo thời gian** (kiểm tra 1D + 2D) | 2026-09-09 | 2026-09-09 | **Thành công** |
| 10 | Đóng góp T5 | Test7 (probe, đúng) + Test8 (CPLEX 12.10 + CBC, instance tổng hợp): tách component cho VCG counterfactual | 2026-09-09 | 2026-09-09 | Đúng đắn; speedup thật còn có điều kiện (xem Slide B) |
| 11 | Quy mô lớn | Spec 2a/2b: DP ở n lớn + phân bố component (720 + 720 lưới) | 2026-09-10 | 2026-09-16 | Xong |
| 12 | Hướng EJOR | Case1 vs Case2, Activation rate, Lemma C, LP dual, compact arc MILP | 2026-09-14 | 2026-09-18 | Xong (nhiều hướng loại) |
| 13 | Chẩn đoán | Convex-hull dominance + checklist chẩn đoán component ~0.999 | 2026-09-15 | 2026-09-16 | Xong (hull bị loại) |
| 14 | RQ | RQ1 (complementarity GW×OD) | 2026-09-16 | 2026-09-16 | Xong |
| 15 | RQ | RQ2–RQ5 chạy toàn bộ + follow-up checklist | 2026-09-27 | 2026-09-28 | Xong |
| 16 | Báo cáo | Figures (14 hình) + `Hica_S_Master_Writeup.md` | 2026-09-28 | 2026-09-30 | Xong (thiếu FIG 1, A6, A7) |
| 17 | Paper | `Paper.tex` bản đầu | 2026-10-01 | 2026-10-01 | Xong (bản đầu) |
| 18 | Audit | Audit FD label rule (C1 vs C2) | 2026-09-30 | 2026-10-01 | Xong |
| 19 | Thử nghiệm | Tiers + in-loop frontier vs FD-dominance (C3–C7) | 2026-10-02 | 2026-10-02 | Xong |
| 20 | Luận văn | Thesis LaTeX theo format IU (Ch1–4 + App. A) | 2026-10-01 | 2026-10-04 | Đang làm (Ch5, Ch6 còn trống) |

### Cột mốc (milestone) — đánh dấu trên Gantt

| Ngày | Milestone |
|---|---|
| 2026-08-09 | Hoàn tất verification round 4 (H1/H2) |
| 2026-08-21 | Chuyển sang dataset Atlanta ARC (thay synthetic 20×20 km) |
| 2026-08-28 | Dataset Data Fix v2 hoàn tất (README + generator khoá) |
| 2026-09-09 | **Chốt Algorithm A = DP label-setting (Test6)** + T5 đúng đắn (Test7); tiềm năng trên instance tổng hợp (Test8) |
| 2026-09-16 | Xong Spec 2a/2b + chốt hướng (B) component; RQ1 xong |
| 2026-09-27/28 | **RQ1–RQ5 chạy xong toàn bộ** (tham số khoá trước khi chạy) |
| 2026-10-01 | Paper.tex bản đầu + audit FD label rule |
| 2026-10-02 | Experiment C4/C5 (tiers + frontier) |
| 2026-10-04 | Thesis LaTeX Ch1–4 |

### Mốc "âm" (hướng đã thử và loại — nên có 1 slide/1 dải màu khác trên Gantt)

T4 geometric pruning · Pareto dominance (Test3) · representative rule d≥2 (Test4) · self-survival bound (Test5) · convex-hull dominance · compact arc MILP · resource-extension bound (Case 1) · FD-dominance giữa các label (C6/C7).

---

## PHẦN 2 — Slide "Results So Far"

### Slide A. Tóm tắt một dòng

> Đã xây xong pipeline đầy đủ (dữ liệu → thuật toán sinh route chính xác → cơ chế VCG → 5 RQ). Giá trị kinh tế của cơ chế chỉ xuất hiện khi crowd cạnh tranh được với FD (alignment cao hoặc FD đắt).

### Slide B. Đóng góp kỹ thuật (Algorithm)

| Kết quả | Số liệu chính |
|---|---|
| **DP label-setting (Algorithm A) đúng tuyệt đối** | 0/616 vi phạm ở Test6; 0/160 ở dominance giữa chừng; kiểm tra lại độc lập (Test6.1, 6.2 gồm phản ví dụ 2D) vẫn 0 vi phạm |
| Nén tốt hơn khi n tăng | Nhanh hơn BFS cũ 5–10× với n tới 15 |
| Quy mô lớn | Gate 0/180 ở n lớn; nhưng bùng nổ siêu tuyến tính trước n=50 khi B≥3–4 (giới hạn cần báo cáo) |
| **T5: tách component cho counterfactual VCG** (đúng đắn: \|Δ\|=0) | **Dữ liệu thật (720 instance B=3, 720 B=2):** route pool luôn có 1 component lớn (largest fraction mean 0.586, 0/1,440 dưới 0.3). **Speedup ước lượng đại số** (chưa đo bằng solver) so với giải lại toàn bộ Z*₋ᵢ: median **3.3×** (winner phân bổ tỷ lệ), cận dưới **1.9×**, cận trên 18–50× (p=1). *Chưa có số đo thời gian thật trên route pool thật.* |
| *(Phụ, KHÔNG phải kết quả dữ liệu thật)* Test8 | 14.9× wall / 391× ticks (CPLEX), 12.4× (CBC) chỉ trên instance tổng hợp, component tách rời lý tưởng dựng tay — chỉ chứng minh tiềm năng, không đại diện route pool thật; nếu nêu phải ghi rõ nhãn này |
| K* frontier (payment chính xác) | Lệch ≤ 1.1e-13; tăng tốc C 3.0× tổng, nhưng chỉ **1.06×** nếu tính cả thời gian dựng K* cho 1 bid profile |
| Cải tiến thêm (Experiment 10/2) | C4 (tiers) 1.07–1.30×; **C5 (tiers + frontier trong vòng lặp) 1.15–1.43×** — ứng viên cho paper. Audit: FD label rule an toàn nhưng không nhanh hơn production |

### Slide C. Kết quả kinh tế (RQ1–RQ5)

| RQ | Câu hỏi | Kết quả (alignment 0.90) |
|---|---|---|
| RQ1 | Cùng bid GW+OD có giá trị? | Complementarity gain **5.9%** (≈0 ở alignment ≤ 0.50) |
| RQ2 | Endogenous bundling có giá trị? | Giảm **chi phí hệ thống tối ưu** (GW+OD+FD) so với B1 (không bundle, 1 order/route): B3 (≤3 order/route) **11.3%**; B4 (≤4) **15.2%**; heuristic bundle cố định chỉ ~5% |
| RQ3 | Truthful procurement tốn bao nhiêu? | VCG trả cao hơn first-best **14.1%**; posted price rẻ hơn VCG 9.1% nhưng mất 4.0% hiệu quả; pay-as-bid BR 5.8% (bị chặn bởi miền bid [18, 25], không phải equilibrium) |
| RQ4 | Exact payment khả thi? | Có: naive C ≤ 0.7 s median ở n=20 |
| RQ5 | Có bền không? | Dấu các effect giữ nguyên qua 10 biến thể; **giá FD là tham số chi phối**; n=30 median 18.5 s/instance |

Quy mô: 7,500 + 7,000 + 600 + 600 + 660 solve, **100% OPTIMAL**, các gate kiểm tra 0 vi phạm.

**Thông điệp:** ở cấu hình trung tính (alignment 0.50) FD phục vụ ~95% order nên mọi cơ chế cho kết quả gần như nhau; đây là kết quả hợp lệ, không phải thất bại.

### Slide D. Kết quả âm (trung thực về các hướng đã loại)

- **T4 pruning hình học**: recall bám theo tỉ lệ infeasible, không phải do bound chặt (Pearson 0.835); sụp xuống 0.14 khi bundle thật sự khả thi (xác nhận 3 lần độc lập).
- **Pareto dominance**: phá completeness (31% vi phạm trên GW).
- **Convex-hull dominance**: giảm 10.9–26.5% (mean 17.65%), dưới ngưỡng 20% → không đưa vào.
- **Compact arc MILP**: n=8 không giải xong trong 590 s, trong khi pool-based 0.11 s (>5000×).
- **Nguyên nhân chậm là bùng nổ Pareto frontier (Case 2)**, không phải phát hiện infeasible muộn → resource-extension bound không giúp.
- **Activation rate chỉ 0.42–1.54%**: gần như mọi route không bao giờ tối ưu với bất kỳ bid nào trong [18, 25] — cơ hội pruning chưa khai thác hết.

### Slide E. Việc còn lại

- Viết Ch5, Ch6 của luận văn; bổ sung FIG 1, A6, A7; xử lý A1 CHECK_FAIL.
- Quyết định đưa C5 vào paper; tỉ lệ tài liệu tham khảo gần đây 44% (guideline yêu cầu ≥ 50%).
- Caveat bắt buộc khi trình bày: K* speed-up 3.0× chỉ đúng khi chia đều thời gian dựng cho 20 bid profile; pay-as-bid BR bị chặn bởi miền bid.

---

## Ghi chú nguồn

`Guideline_Total/Report_RQ_All.md`, `Guideline_A2/Test8_report.md`, `Guideline_Total/report_2a_2b_full.md`, `Test_EJOR_direction/Report_*.md`, `EXPERIMENT_REPORT.md`, `AUDIT_REPORT.md`, `Output/*`, memory notes của dự án.
