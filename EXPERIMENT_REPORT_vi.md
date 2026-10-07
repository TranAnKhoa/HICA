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


## 6. Bảng A–E (Phase 4; instance nhãn: 10 lần đo, 5 lần cho n15_s7 ở B=4; lưới: 5 lần đo)

Bảng A–D do `audit_fd_rule2/make_tables.py` tạo từ JSON đã lưu. Cột tăng tốc là trung vị của tỉ lệ ghép cặp theo từng lần lặp `t_total(C1)/t_total(biến thể)`, IQR trong ngoặc vuông.

### Bảng A: công việc (instance nhãn; cộng trên mọi driver của instance)

| instance | B | ext C1 | ext C3 | ext C4 | ext C6 | bị FD-dominance loại (C6) | bị Layer 1 loại C1 | bị Layer 1 loại C4 | route giữ lại R: C1 / C4 / C6 | K* (C5=C7=C1) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| n12_s42 | 3 | 71870 | 52627 | 62875 | 54895 | 5377 | 16937 | 17751 | 879 / 879 / 708 | 28 |
| n10_s1 | 3 | 51361 | 40057 | 43548 | 38090 | 4356 | 15079 | 16988 | 714 / 714 / 657 | 165 |
| n15_s7 | 3 | 187895 | 118506 | 156332 | 126363 | 19429 | 63402 | 66908 | 1561 / 1561 / 1121 | 165 |
| n12_s123 | 3 | 111944 | 78879 | 94338 | 81056 | 9752 | 35512 | 37689 | 1416 / 1416 / 1183 | 208 |
| n10_s999 | 3 | 37800 | 29553 | 32574 | 28927 | 2750 | 10661 | 11432 | 510 / 510 / 471 | 77 |
| n12_s42 | 4 | 658706 | 512837 | 527545 | 459607 | 29551 | 198297 | 159186 | 2648 / 2648 / 2249 | 74 |
| n10_s1 | 4 | 530486 | 436193 | 389497 | 339916 | 24248 | 212727 | 183991 | 1845 / 1845 / 1708 | 416 |
| n15_s7 | 4 | 2635861 | 1783862 | 1893101 | 1539907 | 152749 | 1261511 | 999112 | 5401 / 5401 / 4396 | 603 |
| n12_s123 | 4 | 1208860 | 896323 | 881938 | 763227 | 62731 | 537534 | 423932 | 4199 / 4199 / 3704 | 482 |
| n10_s999 | 4 | 316079 | 267626 | 238575 | 216584 | 11029 | 125889 | 102365 | 1104 / 1104 / 1041 | 193 |

Mức tiết kiệm extension so với C1 (phần trăm):

| instance | B | C3 | C4 | C6 |
|---|---|---:|---:|---:|
| n12_s42 | 3 | 26.8 | 12.5 | 23.6 |
| n10_s1 | 3 | 22.0 | 15.2 | 25.8 |
| n15_s7 | 3 | 36.9 | 16.8 | 32.7 |
| n12_s123 | 3 | 29.5 | 15.7 | 27.6 |
| n10_s999 | 3 | 21.8 | 13.8 | 23.5 |
| n12_s42 | 4 | 22.1 | 19.9 | 30.2 |
| n10_s1 | 4 | 17.8 | 26.6 | 35.9 |
| n15_s7 | 4 | 32.3 | 28.2 | 41.6 |
| n12_s123 | 4 | 25.9 | 27.0 | 36.9 |
| n10_s999 | 4 | 15.3 | 24.5 | 31.5 |

### Bảng B: thời gian (giây, trung vị các lần đo; t_total = t_A + t_F; x = trung vị tỉ lệ ghép cặp t_total(C1)/t_total(biến thể), >1 = biến thể nhanh hơn; trong ngoặc là IQR)

| instance | B | reps | C1 t_A | C1 t_F | C1 total | C3 total | C4 total | C5 total | C6 total | C7 total | C3 x | C4 x | C5 x | C6 x | C7 x |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| n12_s42 | 3 | 10 | 0.604 | 0.0405 | 0.644 | 0.967 | 0.556 | 0.539 | 0.779 | 0.748 | 0.65 [0.63-0.71] | 1.12 [1.08-1.23] | 1.15 [1.04-1.29] | 0.81 [0.75-0.97] | 0.86 [0.83-0.89] |
| n10_s1 | 3 | 10 | 0.533 | 0.0549 | 0.592 | 0.830 | 0.498 | 0.486 | 0.696 | 0.693 | 0.69 [0.66-0.73] | 1.14 [1.11-1.28] | 1.20 [1.12-1.27] | 0.84 [0.75-0.94] | 0.86 [0.76-0.92] |
| n15_s7 | 3 | 10 | 1.879 | 0.0827 | 1.957 | 2.479 | 1.689 | 1.612 | 2.234 | 1.979 | 0.79 [0.78-0.84] | 1.15 [1.11-1.18] | 1.18 [1.14-1.30] | 0.90 [0.86-0.95] | 0.94 [0.92-1.02] |
| n12_s123 | 3 | 10 | 1.099 | 0.0664 | 1.165 | 1.604 | 1.016 | 0.988 | 1.413 | 1.288 | 0.74 [0.71-0.82] | 1.22 [1.04-1.29] | 1.23 [1.14-1.31] | 0.88 [0.80-0.92] | 0.94 [0.88-0.98] |
| n10_s999 | 3 | 10 | 0.315 | 0.0252 | 0.340 | 0.541 | 0.314 | 0.278 | 0.396 | 0.395 | 0.64 [0.61-0.67] | 1.07 [1.07-1.08] | 1.23 [1.10-1.35] | 0.83 [0.76-0.96] | 0.90 [0.81-1.04] |
| n12_s42 | 4 | 10 | 4.557 | 0.3853 | 4.971 | 7.346 | 3.941 | 3.720 | 5.760 | 5.500 | 0.69 [0.67-0.69] | 1.22 [1.13-1.29] | 1.33 [1.24-1.42] | 0.86 [0.85-0.88] | 0.88 [0.86-0.92] |
| n10_s1 | 4 | 10 | 4.409 | 0.5079 | 4.896 | 7.104 | 3.773 | 3.421 | 5.338 | 4.915 | 0.69 [0.68-0.71] | 1.29 [1.24-1.37] | 1.43 [1.38-1.54] | 0.93 [0.90-0.96] | 1.00 [0.97-1.01] |
| n15_s7 | 4 | 5 | 21.702 | 0.8320 | 22.530 | 29.167 | 17.220 | 16.620 | 22.304 | 21.764 | 0.78 [0.76-0.78] | 1.28 [1.26-1.33] | 1.35 [1.32-1.39] | 1.01 [0.99-1.03] | 1.05 [0.99-1.06] |
| n12_s123 | 4 | 10 | 9.764 | 0.6799 | 10.414 | 13.818 | 8.194 | 7.522 | 10.943 | 10.561 | 0.75 [0.74-0.76] | 1.28 [1.24-1.31] | 1.38 [1.37-1.42] | 0.95 [0.94-1.00] | 0.99 [0.95-1.02] |
| n10_s999 | 4 | 10 | 2.383 | 0.1521 | 2.526 | 3.905 | 1.964 | 1.834 | 2.837 | 2.683 | 0.66 [0.65-0.66] | 1.30 [1.26-1.31] | 1.38 [1.33-1.41] | 0.90 [0.86-0.92] | 0.94 [0.93-0.98] |

B=3: tăng tốc trung vị theo instance C3 0.69, C4 1.14, C5 1.20, C6 0.84, C7 0.90 ; tỉ lệ gộp tổng thời gian C3 0.73, C4 1.15, C5 1.20, C6 0.85, C7 0.92
B=4: tăng tốc trung vị theo instance C3 0.69, C4 1.28, C5 1.38, C6 0.93, C7 0.99 ; tỉ lệ gộp tổng thời gian C3 0.74, C4 1.29, C5 1.37, C6 0.96, C7 1.00

### Bảng C: trần so với thực tế (wasted_share = wasted_children / ext_attempts)

| B | instance | wasted_share C1 (Phase 1.3) | wasted_share sau tier (C4) | cặp cross-batch C1 | sau tier | bản sao được mở rộng sau tier |
|---|---|---:|---:|---:|---:|---:|
| 3 | n12_s42 | 7.87% | 0.00% | 20788 | 0 | 0 |
| 3 | n10_s1 | 9.88% | 0.00% | 24125 | 0 | 0 |
| 3 | n15_s7 | 11.66% | 0.00% | 87486 | 0 | 0 |
| 3 | n12_s123 | 11.14% | 0.00% | 50319 | 0 | 0 |
| 3 | n10_s999 | 9.25% | 0.00% | 14826 | 0 | 0 |
| 4 | n12_s42 | 13.32% | 0.00% | 350243 | 0 | 0 |
| 4 | n10_s1 | 17.97% | 0.00% | 563277 | 0 | 0 |
| 4 | n15_s7 | 22.08% | 0.00% | 2792992 | 0 | 3 |
| 4 | n12_s123 | 20.88% | 0.00% | 1143059 | 0 | 0 |
| 4 | n10_s999 | 17.67% | 0.00% | 288178 | 0 | 0 |

### Bảng D: mẫu lưới chính (n=15, supply (3,3), B=3, rep 0–9; cộng trên 10 instance mỗi alignment)

| alignment | variant | ext | t_A | t_F | t_total | tỉ lệ C1/biến thể (gộp) | tỉ lệ trung vị theo instance | route giữ lại | K* trùng trên tất cả | FD kích hoạt, driver GW | FD kích hoạt, driver OD |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 0.90 | C1 | 2963369 | 29.16 | 1.340 | 30.62 | 1.00 | 1.00 | 26792 | True | - | - |
| 0.90 | C3 | 1679529 | 34.15 | 0.945 | 35.19 | 0.87 | 0.91 | 20741 | True | 30/30 | 30/30 |
| 0.90 | C4 | 2411163 | 24.83 | 1.387 | 26.29 | 1.16 | 1.15 | 26792 | True | - | - |
| 0.90 | C5 | 2411163 | 25.69 | 0.000 | 25.69 | 1.19 | 1.19 | 4742 | True | - | - |
| 0.90 | C6 | 1824917 | 30.18 | 0.800 | 30.94 | 0.99 | 1.00 | 17921 | True | 30/30 | 30/30 |
| 0.90 | C7 | 1824917 | 30.25 | 0.000 | 30.25 | 1.01 | 1.02 | 4742 | True | 30/30 | 30/30 |
| 0.50 | C1 | 1530283 | 11.05 | 1.318 | 12.36 | 1.00 | 1.00 | 29860 | True | - | - |
| 0.50 | C3 | 1107420 | 17.68 | 0.476 | 18.17 | 0.68 | 0.67 | 11420 | True | 30/30 | 30/30 |
| 0.50 | C4 | 1392547 | 10.25 | 1.287 | 11.57 | 1.07 | 1.04 | 29860 | True | - | - |
| 0.50 | C5 | 1392547 | 10.88 | 0.000 | 10.88 | 1.14 | 1.14 | 12 | True | - | - |
| 0.50 | C6 | 1254429 | 15.57 | 0.998 | 16.60 | 0.74 | 0.75 | 25157 | True | 30/30 | 30/30 |
| 0.50 | C7 | 1254429 | 15.51 | 0.000 | 15.51 | 0.80 | 0.79 | 12 | True | 30/30 | 30/30 |

### Closeness to K*: |route giữ lại| / |K*|

| tập | C1 | C3 | C6 | C5 / C7 |
|---|---:|---:|---:|---|
| instance nhãn B=3 (gộp) | 7.90 | 4.60 | 6.44 | 1 |
| instance nhãn B=4 (gộp) | 8.60 | 5.06 | 7.41 | 1 |
| lưới alignment 0,90 (gộp) | 5.65 | 4.37 | 3.78 | 1 |
| lưới alignment 0,50 (gộp) | 2488.33 | 951.67 | 2096.42 | 1 |

### Đo lặp phần B=3 (giao thức machine-drift)

Tăng tốc so với C1: lần 1 (10 lần lặp) / lần 2 (đo lại, 10 lần lặp). Dữ liệu thô: `timing_label.json`, `timing_label3.json`.

| instance | C3 | C4 | C5 | C6 | C7 |
|---|---|---|---|---|---|
| n12_s42 | 0,65 / 0,67 | 1,12 / 1,18 | 1,15 / 1,19 | 0,81 / 0,88 | 0,86 / 0,85 |
| n10_s1 | 0,69 / 0,66 | 1,14 / 1,11 | 1,20 / 1,19 | 0,84 / 0,85 | 0,86 / 0,89 |
| n15_s7 | 0,79 / 0,78 | 1,15 / 1,18 | 1,18 / 1,16 | 0,90 / 0,93 | 0,94 / 0,96 |
| n12_s123 | 0,74 / 0,77 | 1,22 / 1,22 | 1,23 / 1,25 | 0,88 / 0,95 | 0,94 / 0,96 |
| n10_s999 | 0,64 / 0,67 | 1,07 / 1,17 | 1,23 / 1,34 | 0,83 / 0,90 | 0,90 / 0,90 |

Thứ tự các biến thể giống nhau ở cả hai lần trên mọi instance. Thay đổi lớn nhất của một tỉ lệ là 0,11 (C5 trên instance nhỏ nhất, 0,3 s mỗi lần chạy).

### Bảng E: thời gian đi đâu (cProfile, n12_s42, B=3, giây cho một lần chạy đủ 5 driver, đã gồm overhead của profiler)

| hạng | C1 | C4 | C6 |
|---|---|---|---|
| 1 | `run_round` 0,625 | `run_tier` 0,716 | `run_tier` 0,993 |
| 2 | `_try_delivery` 0,182 (34.827 lần gọi) | `_try_delivery` 0,207 | **`fd_dominated` 0,323 (19.553 lần gọi)** |
| 3 | `_try_pickup` 0,125 (32.724) | `_try_pickup` 0,147 | `_try_delivery` 0,159 |
| 4 | `_filter_dominated_labels` 0,106 (23.334) | `_filter_dominated_labels` 0,113 (18.539) | `_try_pickup` 0,138 |
| 5 | `travel_time` 0,073 | `travel_time` 0,082 | `travel_time` 0,096 |
| 6 | `kstar_pool` 0,058 | `kstar_pool` 0,066 | `_filter_dominated_labels` 0,095 (17.962) |

(Bỏ các dòng wrapper `build_all`/`run_cN`; đầu ra đầy đủ ở `audit_logs2/profile.log`.) Chi phí bên trong FD-dominance của C6: **tổng 0,323 s, trong đó số hạng hấp thụ A là 0,057 s (18%), còn tra cứu và test các bundle con là 0,266 s (82%).** Bản thân engine tier (C4 so với C1) thêm rất ít chi phí quản lý: cùng các hàm chiếm ưu thế, và `_filter_dominated_labels` được gọi ít lần hơn (18.539 so với 23.334 nhóm key) nhờ batch lớn hơn.

## 7. Diễn giải (mỗi biến thể một dòng)

| Biến thể | Quan sát (bằng chứng) | Ý nghĩa | Nên làm gì |
|---|---|---|---|
| Trần / Idea 2a | `wasted_share` 7,9–22,1% (trên 5%); sau tier 0,00% và 0 cặp cross-batch ở cả 10 cấu hình (Bảng C) | Vòng lặp production lãng phí công việc mà việc gom batch theo số sự kiện lấy lại hoàn toàn | Idea 2a **không** bị loại; C4 lấy trọn trần |
| **C4** | Qua G1–G4; R trùng C1; ext giảm 12,5–28,2%; thời gian 1,07–1,30× trên instance nhãn, 1,16× (align 0,90) và 1,07× (align 0,50) trên lưới | **Tăng tốc thật cho Algorithm A**, khiêm tốn, tăng theo B (trung vị 1,14× ở B=3, 1,28× ở B=4) | Báo cáo kèm điều kiện chính xác (n ≤ 15, B = 3, 4); không ngoại suy lên n = 20 |
| **C5** | Qua G1–G4, G7 (K\* trùng, 960 driver ngẫu nhiên không có phản ví dụ); thời gian 1,15–1,43× trên instance nhãn, 1,19×/1,14× trên lưới; chỉ lưu K\* (ít hơn R khoảng 8× route ở instance nhãn B=3; 5,65× ở align 0,90; xem bảng "closeness") | Bỏ bước hậu xử lý (`t_F` là 4–11% tổng thời gian của C1) **và** có mức tăng tốc của C4. Phần tăng thêm của C5 so với C4 gần bằng hoặc dưới `t_F`, đúng dự đoán | Báo cáo là "xuất thẳng K\*; phần tăng thêm so với C4 là bước hậu xử lý". Tiết kiệm bộ nhớ chỉ suy ra từ số route, **chưa đo** |
| **C6** | Qua G1–G6 (0 vi phạm trên 6.239 completion, mutation bị bắt); ext giảm 23–42% so với C1 (9–19% so với C4), nhưng thời gian 0,81–0,90× (B=3) và 0,86–1,01× (B=4) so với C1, 0,99×/0,74× trên lưới | Ít extension hơn, **không tăng tốc**: tra cứu các bundle con (82% chi phí FD) và số hạng A tốn hơn số extension bỏ được | Không claim tăng tốc. Hướng sau: tra cứu nhanh hơn (ví dụ chỉ mục bundle con tính sẵn); mọi tối ưu như vậy phải áp cho cả C1/C4 |
| **C7** | An toàn như C6 cộng frontier trong vòng lặp; thời gian 0,86–1,05× so với C1 | Gộp C6 với frontier trong vòng lặp không vượt C5 (1,15–1,43×) | C5 là ứng viên tốt hơn cho Algorithm A production |
| **C3** | ext giảm 15–37% (giống C2 trước đó); thời gian 0,64–0,79× so với C1 | Đánh giá rule một cách lười tốt hơn C2 trước đó (C2 là 0,48–0,80× trong `AUDIT_REPORT.md`, cài đặt khác, không chạy lại ở đây) nhưng vẫn chậm hơn C1 | Giữ C1 làm baseline; rule đường tắt ảo không đáng trong cài đặt này |
| **Rule kích hoạt với driver OD** | G5: 4.960 trong 9.517 lần discard được kiểm là driver OD; lưới: kích hoạt cho 30/30 driver GW và 30/30 driver OD ở cả hai alignment (C3, C6, C7) | Mâu thuẫn câu "never fires for occasional drivers" đối với các cài đặt label-setting này | Nêu số liệu nếu vẫn giữ câu đó |

**Biến thể có tiến gần K\* hơn không?** `|route giữ lại| / |K*|` (gộp; 1 = đúng K\*):

| tập | C1 | C3 | C6 | C5, C7 |
|---|---:|---:|---:|---:|
| instance nhãn, B=3 | 7,90 | 4,60 | 6,44 | 1 (theo cấu tạo, đã kiểm bằng G1/G7) |
| instance nhãn, B=4 | 8,60 | 5,06 | 7,41 | 1 |
| lưới, alignment 0,90 | 5,65 | 4,37 | 3,78 | 1 |
| lưới, alignment 0,50 | 2488 | 952 | 2096 | 1 (K\* rất nhỏ ở đó: 12 route trên 10 instance, nên tỉ lệ không có nhiều ý nghĩa) |

C3 và C6 tiến gần K\* hơn C1 nhưng vẫn còn xa; chỉ frontier trong vòng lặp đạt đúng K\*. (C4 giữ nguyên R như C1.)

## 8. Báo cáo này KHÔNG chứng minh điều gì

- **n = 20 trở lên, và B = 4 trên lưới chính.** B=4 chỉ chạy trên năm instance nhãn (n ≤ 15). Mức tăng tốc của C4/C5 tăng theo B trong dữ liệu (trung vị C4 từ 1,14× lên 1,28×), nên kích thước lớn hơn có thể cho kết quả khác theo cả hai hướng.
- **Máy khác, bản Python khác.** Mọi thứ là Python thuần 3.7.7 trên một máy với chế độ nguồn Balanced. Chi phí tương đối của tra cứu dictionary (làm C6 chậm) và của batch lớn hơn (làm C4 nhanh) có thể khác ở nơi khác.
- **Các biến thể chưa được tối ưu.** Phần tra cứu của C6 chưa tối ưu, và đặc tả cấm tối ưu một biến thể mà không áp dụng cho C1. Một FD-dominance được tinh chỉnh có thể đổi kết luận; thí nghiệm này không nói được.
- **Machine drift.** Anchor lệch tới +19% ở một instance trong lượt đầu và +11,6% ở instance nhỏ nhất trong lượt lặp. Tỉ lệ lặp lại được ở B=3 (Mục 6), nhưng B=4 và lưới (5 lần lặp) chỉ đo một lần.
- **Chiều sâu thống kê.** Trung vị của 10 lần chạy ghép cặp (5 lần với các lần chạy trên 20 s và với lưới); có IQR nhưng không có khoảng tin cậy.
- **Tình trạng chứng minh.** Idea 3 (FD-dominance giữa label đã sinh) và giả thuyết frontier trong vòng lặp ("K\* của bundle nhỏ hơn là đủ") là **chưa được chứng minh**. Bằng chứng: 6.239 completion được kiểm với bộ đánh giá độc lập (B=3, n ≤ 10), K\* trùng trên 30 instance, 960 driver ngẫu nhiên (n=6..9, B=3), brute force cho n=5,6 và các mutation test. G5 chỉ bao phủ B=3; đợt săn ngẫu nhiên của G7 chỉ ở B=3; G3 dùng 20 profile mỗi instance.
- **Bộ nhớ.** Mức tiết kiệm bộ nhớ của frontier trong vòng lặp được suy ra từ số route, không đo.
- **Hòa phân bổ.** G3 so tập người thắng, giá trị và payment; các hòa giữa phân bổ cùng chi phí không được phân tích riêng (không profile nào khác nhau).
- **Bản sao.** Ba label cùng key có (t,K,W) bằng hệt nhau được mở rộng hai lần trên n15_s7 ở B=4 khi dùng tier (Bảng C). Không ảnh hưởng tính đúng, ghi để đầy đủ.

## 9. Câu đề xuất cho bản thảo (chỉ những gì bằng chứng ủng hộ)

1. *Algorithm A (xử lý theo số sự kiện).* "Processing labels in tiers of equal event count `m = abs(IV) + 2 abs(C)` puts all labels with the same key `(v, IV, C)` into one dominance batch. On the five experimental instances this removed 12.5–16.8% (B=3) and 19.9–28.2% (B=4) of the extension attempts, left the route pool and the frontier unchanged, and reduced running time by a median factor of 1.14 (B=3) and 1.28 (B=4) in our pure-Python implementation." Nêu rõ rằng vòng lặp production chỉ so sánh label trong cùng một round/lần lặp closure.
2. *Frontier trong vòng lặp.* "Testing frontier membership as soon as all routes of a bundle size are complete outputs the frontier directly and stores no other route; median speed-ups 1.20 (B=3) and 1.38 (B=4) relative to the baseline." Thêm rằng điều này được kiểm nghiệm thực nghiệm, chưa được chứng minh.
3. *FD-dominance giữa các label đã sinh.* "Safe in all tests (0 violations in 6,239 completions checked against an independent evaluator; mutations detected) and reduces extensions by a further 9–19% but did not reduce running time (0.8–1.05×)." **Không** gọi đó là tăng tốc và **không** gọi là đã chứng minh.
4. *Rule đường tắt ảo.* Giữ kết luận của audit trước: nó bỏ được extension nhưng chậm hơn baseline (ở đây 0,64–0,79× kể cả khi đánh giá lười).
5. Câu "never fires for occasional drivers" nên bỏ hoặc nêu điều kiện (nó kích hoạt cho mọi driver OD trong mẫu lưới).
6. Đừng bao giờ viết "K\* speeds up the pipeline" mà không kèm điều kiện; các mức tăng tốc ở trên chỉ cho Algorithm A, không cho B/C.

## Phụ lục: file

`audit_logs2/`: `phase1_answers.md`, `phase1_ceiling.{log,json}`, `phase1_example.log`, `phase1_after_tier.{log,json}`, `regression*.log`, `gate_equal.{log,json}`, `gate_wdp.{log,json}`, `gate_audit.{log,json}`, `gate_audit_after_refactor.log`, `timing_label.{log,json}`, `timing_label3.json`, `timing_label3_rerun.log`, `timing_grid.{log,json}`, `anchor*.log`, `profile.{log,json}`, `tables.md`, `environment.txt`, `lock_sha256_{before,mid,after}.txt`.
