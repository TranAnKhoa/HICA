# BÁO CÁO THỰC NGHIỆM: Có thể tăng tốc Algorithm A bằng tier theo số sự kiện, frontier trong vòng lặp, hay FD-dominance giữa các label thật không?

Viết cho: tác giả luận văn (người quyết định Algorithm A trong Paper.tex trông thế nào và được claim gì). Đặc tả: `AlgorithmA_Test/Experiment_trial.md`. Log gốc: `audit_logs2/`; mã nguồn: `audit_fd_rule2/`. Mọi thứ được so với **C1** (Algorithm A production). Tỉ lệ lớn hơn 1 nghĩa là biến thể **nhanh hơn** C1. Bản tiếng Anh tương ứng: `EXPERIMENT_REPORT.md` (cùng số liệu).

## 0. Tóm tắt (đọc phần này trước)

| Biến thể | Là gì | Đúng không? (mọi gate) | Công việc (số extension so với C1) | Thời gian so với C1 (t_total) | Kết luận |
|---|---|---|---|---|---|
| **C3** | rule lười (đường tắt ảo) chỉ chạy trên label sống sót sau FilterDominated | có | giảm 15–37% | **0,64–0,79× (chậm hơn)** | giữ C1 |
| **C4** | tier theo số sự kiện (`m = abs(IV) + 2 abs(C)`), tắt rule | có, R trùng hệt C1 | giảm 12,5–16,8% (B=3), 19,9–28,2% (B=4) | **1,07–1,22× (B=3), 1,22–1,30× (B=4)** | **tăng tốc thật** |
| **C5** | C4 + frontier trong vòng lặp, xuất thẳng K\* | có (K\* trùng) | như C4 | **1,15–1,23× (B=3), 1,33–1,43× (B=4)** | **tốt nhất**; không bao giờ lưu R |
| **C6** | C4 + FD-dominance giữa label thật (Idea 3) | có, 0 vi phạm trên 6.239 completion | giảm 23–42% | 0,81–0,90× (B=3), 0,86–1,01× (B=4) | ít extension hơn nhưng **không nhanh hơn** |
| **C7** | C6 + frontier trong vòng lặp | có | như C6 | 0,86–0,94× (B=3), 0,88–1,05× (B=4) | không nhanh hơn C5 |

Ba phát hiện quan trọng cho bản thảo:

1. **Vòng lặp production có bỏ sót dominance, và tier lấy lại toàn bộ.** Trong `run_dp`, các label cùng key rơi vào các batch Layer-1 khác nhau; 7,9–22,1% công việc extension tiêu cho những label mà một label cùng key đã dominate. Với tier, lượng waste đo được đúng bằng 0 và số extension tiết kiệm bằng đúng trần ước lượng ở Phase 1 (Bảng C).
2. **Mức tăng tốc của Method A là thật nhưng khiêm tốn (khoảng 1,1–1,4×) và tăng theo B.** Đó không phải hiệu ứng 2–3×. Nó đến từ việc làm ít việc hơn, với mọi đầu ra không đổi (R với C4, K\* với C5).
3. **FD-dominance giữa label thật (Idea 3) an toàn trong mọi test đã chạy nhưng không tự bù chi phí trong cài đặt này.** Nó bỏ thêm 9–19% extension so với C4, nhưng việc tra cứu các bundle con tốn hơn phần tiết kiệm (Bảng E: 82% thời gian FD-dominance là tra cứu bundle con, 18% là số hạng hấp thụ A). Ở kích thước lớn nhất đã chạy (n15_s7, B=4) nó chỉ đạt khoảng 1,0–1,05× so với C1, vẫn thấp xa so với C4/C5.

Tình trạng lý thuyết: Idea 3 và giả thuyết frontier-trong-vòng-lặp là **giả thuyết được kiểm bằng test, chưa phải định lý.** Không có gì ở đây chứng minh chúng.

## 1. Môi trường và kiểm tra sha256

- Nhánh `exp-tiers-fd-dominance`, tạo từ `audit-fd-rule`. Chưa merge, chưa push. File mới chưa được track (`audit_fd_rule2/`, `audit_logs2/`); không file nào đã track bị sửa.
- AMD Ryzen AI 5 340 w/ Radeon 840M, Windows 11, **Python 3.7.7** (interpreter production), CPLEX 12.10 cho G3, chế độ nguồn **Balanced** (`audit_logs2/environment.txt`). Một luồng; các lần đo thời gian chạy một mình trên máy.
- Hai file tham số khóa, sha256 trước = sau (`audit_logs2/lock_sha256_before.txt`, `lock_sha256_after.txt`, `diff` rỗng):
  - `spec_2a_2b/results/rq1_locked_params.json` 638e3957...04e8
  - `spec_2a_2b/results/rq_all/rq_all_locked_params.json` 861378ba...f7be
- **Kiểm tra machine drift.** C1 của audit cũ (`audit_fd_rule/fdrule_dp`, tắt rule) được đo lại trên 5 instance nhãn ở B=3 và so với Bảng B của `AUDIT_REPORT.md`: lượt đầu −3,8% đến +19,3% (hai instance vượt 10%), lượt lặp −3,0% đến +11,6% (một instance vượt 10%, là instance nhỏ nhất, 0,35 s). Vì quy tắc yêu cầu lặp lại khi drift trên 10%, toàn bộ phần đo B=3 được chạy lại (`timing_label3.json`). Các tỉ lệ tăng tốc lặp lại được (thay đổi tối đa 0,10 ở tỉ lệ, tại instance nhỏ nhất; xem bảng lặp ở Mục 6), nên kết luận không phụ thuộc drift. Mọi biến thể được đo xen kẽ trong cùng phiên, nên drift tuyệt đối triệt tiêu trong các tỉ lệ.

## 2. Vòng lặp hiện tại hoạt động thế nào (Phase 1.1–1.2, bằng chứng)

Câu trả lời đầy đủ: `audit_logs2/phase1_answers.md`. Tóm tắt (`experiments/T2BFS/t6_dp.py`):

- Label đang chờ nằm trong list thường và dict `frontier[touched]` (:227, :237-266); không có heap, deque hay đệ quy.
- Label được mở rộng theo từng round trên `touched = abs(IV) + abs(C)` (:229); trong mỗi round có một closure lặp lại việc mở rộng giao hàng/về nhà (:239-266), rồi pickup chuyển sang round kế (:273-291).
- Dominance (`_filter_dominated_labels`) được áp **theo batch**, không phải lúc chèn: mỗi lần lặp closure (:258-266), mỗi round pickup (:284-291), và cuối cùng trên các label hoàn chỉnh theo (C, v) (:293-308). Hai label chỉ được so sánh nếu cùng batch.
- **Giả thuyết "đây là DFS": sai.** Nó là DP đồng bộ theo tầng. Lỗi nằm ở chỗ ranh giới batch (round, lần lặp closure) không trùng với key `(v, IV, C)`. Ví dụ tìm thấy trong dữ liệu (n10_s999, B=3, gw0), key v=n11, IV={}, C={o0,o2}: label `p0 d0 p2 d2` (batch: round 2, lần lặp 1, (t,K,W) = (71,16; 17,053; 71,16)) dominate chặt label `p2 p0 d0 d2` (batch: round 2, lần lặp 2, (71,78; 17,259; 71,78)), chúng không bao giờ được so sánh, và label bị dominate vẫn được mở rộng.
- Route hoàn chỉnh: `complete_by_C` (:221, :250, :255), Layer 1 trên label hoàn chỉnh theo (C, v) (:293-308), Layer 2 `_pareto_front` theo bundle ở `spec_2a_2b/src/dp_labeling.py:28,82`.

## 3. Trần cải thiện (Phase 1.3) và tier đạt được gì

C1 đã gắn công cụ đo (hành vi không đổi; tái tạo đúng production trên 48/48 driver). `wasted_share` theo đặc tả (`wasted_children / ext_attempts`); `wasted_attempt_share` đếm số *lần thử mở rộng* của các label lãng phí, đây mới là đại lượng thực sự biến thành tiết kiệm.

| B | instance | ext_attempts | wasted_labels | wasted_children | wasted_share | wasted_attempt_share | cross_batch_pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| 3 | n12_s42 | 71870 | 6469 | 5655 | 7,87% | 12,52% | 20788 |
| 3 | n10_s1 | 51361 | 6982 | 5073 | 9,88% | 15,21% | 24125 |
| 3 | n15_s7 | 187895 | 25416 | 21910 | 11,66% | 16,80% | 87486 |
| 3 | n12_s123 | 111944 | 14648 | 12471 | 11,14% | 15,73% | 50319 |
| 3 | n10_s999 | 37800 | 4266 | 3495 | 9,25% | 13,83% | 14826 |
| 4 | n12_s42 | 658706 | 48655 | 87766 | 13,32% | 19,91% | 350243 |
| 4 | n10_s1 | 530486 | 66594 | 95330 | 17,97% | 26,58% | 563277 |
| 4 | n15_s7 | 2635861 | 319501 | 581900 | 22,08% | 28,18% | 2792992 |
| 4 | n12_s123 | 1208860 | 138785 | 252387 | 20,88% | 27,04% | 1143059 |
| 4 | n10_s999 | 316079 | 32330 | 55854 | 17,67% | 24,52% | 288178 |

`wasted_share` vượt ngưỡng 5% ở cả 10 cấu hình (7,9–11,7% ở B=3, 13,3–22,1% ở B=4), nên Idea 2a không bị loại. Khoảng hai phần ba label lãng phí có label dominate nó được tạo **trước**.

**Kiểm chứng thực tế.** Mức tiết kiệm extension của C4 so với C1 (Bảng A, khối thứ hai) là 12,5; 15,2; 16,8; 15,7; 13,8% ở B=3 và 19,9; 26,6; 28,2; 27,0; 24,5% ở B=4, bằng `wasted_attempt_share` đến độ chính xác đã in. Vậy tier đạt đúng trần; `wasted_share` theo đặc tả (chỉ đếm label con) đánh giá thấp khoảng một phần ba.

## 4. Tóm tắt cài đặt và hồi quy

File trong `audit_fd_rule2/`: `variants.py` (mọi engine), `phase1_ceiling.py`, `phase1_after_tier.py`, `regress.py`, `gate_equal.py`, `gate_wdp.py`, `gate_audit.py`, `timing.py`, `profile_tables.py`, `anchor.py`, `make_tables.py`, `run_chain*.sh`.

Mọi biến thể dùng lại nguyên `_try_pickup/_try_delivery/_try_home`, `_filter_dominated_labels`, `finalize_KW`, `_pareto_front`, cùng lớp `Label` và cùng bộ đếm. Không biến thể nào được tối ưu vi mô riêng. C3 dùng lại nguyên `_next_sc/_rule_fires` của audit trước.

- **C1**: cấu trúc round production kèm bộ đếm (đồng nhất với `t6_dp.run_dp` + `dp_labeling.run_pool`).
- **C3**: như C1, nhưng rule chỉ chạy trên label sống sót sau FilterDominated; bộ ba shortcut tính tại thời điểm đó từ bộ ba của cha.
- **C4**: tier theo `m = abs(IV) + 2 abs(C)`; FilterDominated một lần trên cả tier trước khi mở rộng; Layer 2 theo bundle ngay khi tier `2k` xong.
- **C5**: C4 + sau tier `2k`: Pareto theo bundle, rồi giữ route khi và chỉ khi margin dương so với route rỗng, các route khác cùng bundle và các route **K\* của bundle nhỏ hơn**; chỉ lưu K\*.
- **C6**: C4 + FD-dominance (Idea 3): với mỗi label L2 sống sót sau FilterDominated có C khác rỗng, duyệt các tập con thực sự C1 của C2 (kể cả tập rỗng), tra key (v, IV, C1) trong số label sống sót của các tier trước, test rẻ với A=0 trước, chỉ tính số hạng hấp thụ A khi test đó qua.
- **C7**: C6 + frontier trong vòng lặp.

Các lựa chọn thiết kế cần biết: (i) dict label sống sót cho FD-dominance chứa mọi label sống sót sau FilterDominated, kể cả những label sau đó bị chính FD-dominance loại (phác thảo chứng minh nói chỉ tính khả thi của tiền tố L1 là quan trọng); (ii) test frontier trong vòng lặp cũng dùng các route Pareto khác *cùng bundle* (chúng thuộc D(r)); đặc tả chỉ liệt kê bundle nhỏ hơn và route rỗng; (iii) A dùng F(L2) của bản thảo (pickup còn với tới được từ L2, giao hàng của đơn đang trên xe, giao hàng của các đơn thuộc những pickup đó).

**Hồi quy (STOP 2).** `audit_logs2/regression.log` và, sau một lần tái cấu trúc nhỏ (tách số hạng hấp thụ thành hàm riêng để profile được), `regression_after_refactor.log`: C1 == production `dp_labeling.run_pool` trên mọi driver của 10 cấu hình nhãn: **PASS**; C4 tái tạo cùng R với C1: **PASS**. Kết quả G5/G6 giống hệt trước và sau tái cấu trúc.

## 5. Bảng gate

| gate | phạm vi | kết quả |
|---|---|---|
| **G1** K\* bằng C1 | 10 cấu hình nhãn (B=3,4) + 20 instance lưới chính (n=15, alignment 0,90/0,50, rep 0–9, B=3), mọi driver, biến thể C3–C7 | **PASS**, 0 sai lệch |
| **G2** R(C4) = R(C1) | cùng 30 instance | **PASS** |
| **G3** V, V₋ₖ, payment trong 1e-9, 20 profile | 10 cấu hình nhãn, C3–C7 so với C1 (CPLEX 12.10) | **PASS**; lệch tối đa 5,7e-14 (C3 5,7e-14, C4 2,8e-14, C5 2,8e-14, C6 5,7e-14, C7 5,7e-14); không profile nào có tập người thắng khác |
| **G4** brute force n=5,6, mỗi cỡ 3 seed | K\*(brute) = K\*(C1) = K\*(biến thể), cả 5 biến thể | **PASS** (6/6 instance) |
| **G5** audit mức completion cho Idea 3 (n10_s1, n10_s999 ở B=3 + sáu instance n=5,6) | bộ đánh giá độc lập (mô phỏng lại route từ dãy điểm dừng). Bộ đánh giá được kiểm trước: **2.811 label hoàn chỉnh, 0 sai lệch** so với `finalize_KW` | **9.517 lần discard được kiểm (GW 4.557, OD 4.960), 6.239 completion, 0 vi phạm**; margin nhỏ nhất `c(L2.sigma) − c(L1.sigma) − q(T)` = +0,0030 tại theta = 18 |
| **G6** mutation của C6 (G1 trên 5 cấu hình nhãn ở B=3 + n10_s999 ở B=4; G5 như trên) | xem dưới | mọi mutation không hợp lệ bị phát hiện, control qua |
| **G7** K\* trong vòng lặp = Frontier(R) | C5, C7 trên cùng 30 instance; **cộng** một đợt săn phản ví dụ: 80 instance ngẫu nhiên (n=6..9, B=3, 4 driver, seed 100–119) = 960 driver, C5/C6/C7 so với Frontier(R_C1) | **PASS**, 0 sai lệch |

Chi tiết G6 (`audit_logs2/gate_audit.log`):

| mutation | G1 fail tại | G5 vi phạm / completion | phát hiện? |
|---|---|---:|---|
| (a) A = 0 (bỏ hấp thụ) | n15_s7, n10_s999, n10_s999 (B=4) | 1.186 / 11.154 | có (G1 và G5) |
| (b) bỏ số hạng `K2−K1` | không | 4 / 1.839 | có, **chỉ G5** |
| (c) `t1 <= t2 + 5` | không | 2 / 6.241 | có, **chỉ G5** |
| thêm: ngưỡng `q(T) − 1,0` | cả 6 | 820 / 7.183 | có (G1 và G5) |
| control (hợp lệ): ngưỡng `q(T) + 1,0` | không | 0 / 5.424, margin nhỏ nhất +1,002 | qua, như phải thế |

Ghi chú: (1) mutation (b) và (c) qua G1 (K\* không đổi trên các instance này) và chỉ bị audit mức completion G5 bắt. Một test chỉ so K\* sẽ không lộ chúng; đó là lý do G5 tồn tại. (2) Đặc tả viết control hợp lệ là "hạ ngưỡng xuống `q(T) − 1,0` (test yếu hơn thì bắn ít hơn)". Hạ ngưỡng làm test bắn *nhiều hơn*; vì vậy tôi dùng `q(T) + 1,0` làm control hợp lệ (bắn ít hơn), và chạy `q(T) − 1,0` như một mutation không hợp lệ bổ sung.

