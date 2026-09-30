# Audit report cuối — T4 Local Pruning Frontier: tổng hợp theo Add_test.md

**Ngày chạy:** 2026-09-22
**Phạm vi:** tổng hợp kết quả của 3 việc bắt buộc trong `Add_test.md` trước khi đưa
thầy xem `T4_Local_Pruning_Frontier.tex`. Thay thế/bổ sung hai report trước
(`AUDIT_REPORT.md`, `AUDIT_REPORT_2_RQ1_CROSSCHECK.md`) — report đó chỉ đóng một phần
phạm vi, xem `AUDIT_SCOPE_NOTE.md` cho lý do.

| # | Việc (theo Add_test.md) | Trạng thái |
|---|---|---|
| 1 | Independent re-implementation (grid brute-force, khác cấu trúc tính toán với kink-based) | **Xong — PASS** |
| 2 | `kstar_rule.py` trên môi trường thesis thật (Py 3.7 + CPLEX) + instance RQ1 thật, so Z*/Z*_{-i} full vs pruned | **Xong — PASS** |
| 3 | Đối chiếu activation-rate log cũ: mọi route active ⊆ K* | **Xong — PASS** (đã báo cáo ở `AUDIT_REPORT_2_RQ1_CROSSCHECK.md`, nhắc lại ở đây) |
| 4 | Literature check (Desrosiers & Lübbecke, Barnhart et al.) | Không làm — không bắt buộc trước khi đưa thầy |
| 5 | Kiểm metadata reference | Không làm — không bắt buộc trước khi đưa thầy |

**Kết luận một câu:** cả 3 việc bắt buộc đều PASS, không có vi phạm nào ở bất kỳ
instance/seed/bid profile nào đã thử — theo `Add_test.md` §6, file
`T4_Local_Pruning_Frontier.tex` sẵn sàng đưa thầy xem, kèm bảng số ở dưới làm phụ lục.

---

## 1. Independent re-implementation (Add_test.md §1)

### 1.1 Cách làm

Viết `kstar_gridcheck.py` — tính margin `μ_r(b) = E_r(b) - c_r(b)` bằng **grid
brute-force thô** (5000 điểm chia đều trên `[18,25]`, tại mỗi điểm duyệt lại toàn bộ
`D(r)` để tính `E_r(b) = min` trực tiếp), **không** dùng cấu trúc affine `(a,w)` +
envelope + kink-point mà `kstar_rule.py` dùng, và **không import bất kỳ hàm nào** của
`kstar_rule.py`. Đây là "đường tính toán" khác hẳn về cấu trúc, đúng khuyến nghị cụ thể
của `Add_test.md` §1.2.

### 1.2 Kết quả — Phần A: 5 seed tổng hợp (giống `test_theorem.py`)

Python 3.13 + scipy (chỉ cần `hica_core.random_instance`/`enumerate_pool`, không cần
giải WDP ở bước này).

| seed | driver | pool | kept (kink) | kept (grid) | khớp? |
|---:|---|---:|---:|---:|---|
| 0 | gw0 | 169 | 77 | 77 | OK |
| 0 | gw1 | 165 | 82 | 82 | OK |
| 0 | od0 | 2 | 1 | 1 | OK |
| 1 | gw0 | 164 | 81 | 81 | OK |
| 1 | gw1 | 165 | 83 | 83 | OK |
| 1 | od0 | 2 | 1 | 1 | OK |
| 1 | od1 | 2 | 1 | 1 | OK |
| 2 | gw0 | 174 | 55 | 55 | OK |
| 2 | gw1 | 171 | 58 | 58 | OK |
| 2 | od0 | 3 | 1 | 1 | OK |
| 2 | od1 | 1 | 0 | 0 | OK |
| 3 | gw0 | 138 | 58 | 58 | OK |
| 3 | gw1 | 155 | 58 | 58 | OK |
| 3 | od0 | 2 | 0 | 0 | OK |
| 3 | od1 | 20 | 7 | 7 | OK |
| 4 | gw0 | 193 | 36 | 36 | OK |
| 4 | gw1 | 188 | 36 | 36 | OK |
| 4 | od0 | 8 | 3 | 3 | OK |
| 4 | od1 | 7 | 4 | 4 | OK |

**19/19 driver-pool khớp tuyệt đối.**

### 1.3 Kết quả — Phần B: 5 instance RQ1 thật

Python 3.7.7 + CPLEX (route pool qua `dp_labeling.build_route_pool`, cùng 5 instance
với §3 bên dưới).

| n | n_drivers | seed | driver | pool | kept (kink) | kept (grid) | khớp? |
|---:|---:|---:|---|---:|---:|---:|---|
| 12 | 5 | 42 | gw0 | 441 | 10 | 10 | OK |
| 12 | 5 | 42 | gw1 | 429 | 11 | 11 | OK |
| 12 | 5 | 42 | od0 | 2 | 1 | 1 | OK |
| 12 | 5 | 42 | od1 | 3 | 3 | 3 | OK |
| 12 | 5 | 42 | od2 | 4 | 3 | 3 | OK |
| 10 | 4 | 1 | gw0 | 314 | 74 | 74 | OK |
| 10 | 4 | 1 | gw1 | 394 | 85 | 85 | OK |
| 10 | 4 | 1 | od0 | 3 | 3 | 3 | OK |
| 10 | 4 | 1 | od1 | 3 | 3 | 3 | OK |
| 15 | 5 | 7 | gw0 | 805 | 90 | 90 | OK |
| 15 | 5 | 7 | gw1 | 747 | 68 | 68 | OK |
| 15 | 5 | 7 | od0 | 3 | 3 | 3 | OK |
| 15 | 5 | 7 | od1 | 4 | 2 | 2 | OK |
| 15 | 5 | 7 | od2 | 2 | 2 | 2 | OK |
| 12 | 6 | 123 | gw0 | 463 | 64 | 64 | OK |
| 12 | 6 | 123 | gw1 | 491 | 69 | 69 | OK |
| 12 | 6 | 123 | gw2 | 452 | 68 | 68 | OK |
| 12 | 6 | 123 | od0 | 3 | 1 | 1 | OK |
| 12 | 6 | 123 | od1 | 7 | 6 | 6 | OK |
| 10 | 4 | 999 | gw0 | 254 | 32 | 32 | OK |
| 10 | 4 | 999 | gw1 | 246 | 38 | 38 | OK |
| 10 | 4 | 999 | od0 | 5 | 3 | 3 | OK |
| 10 | 4 | 999 | od1 | 5 | 4 | 4 | OK |

**23/23 driver-pool khớp tuyệt đối.**

**Ghi chú:** instance `n=12, n_drivers=6, seed=123` chỉ liệt kê 5 driver (gw0, gw1, gw2,
od0, od1) dù `n_drivers=6`. Đã xác nhận tường minh nguyên nhân (không giả định): driver
thứ 6, `od2`, có **route pool hoàn toàn rỗng** (0 route khả thi — mọi bundle vi phạm
ràng buộc time-window/τ) ở đúng instance/seed này, nên bị bỏ qua trong vòng lặp per-driver
(route pool rỗng thì không có gì để tính K*/grid-check cả). Không phải bug, không phải
driver bị bỏ sót do lỗi code — kiểm tra trực tiếp bằng
`dp_labeling.build_route_pool` xác nhận `od2` có đúng 0 route ở instance này.

### 1.4 Kết luận mục 1

**Tổng 42/42 driver-pool (19 tổng hợp + 23 RQ1 thật) khớp tuyệt đối** giữa hai cách
tính margin hoàn toàn khác cấu trúc (kink-based dùng tính lõm/envelope, grid-based
brute-force không giả định gì). Đây là kiểm chứng độc lập thật sự theo đúng nghĩa —
không phải rerun cùng code, mà hai đường tính toán khác nhau đồng ý với nhau trên toàn
bộ 5+5 instance đã thử. Không cần tăng `n_grid` (không có lệch ở biên).

---

## 2. Z*/Z*_{-i} full pool vs K*-pruned pool, instance RQ1 thật (Add_test.md §2.2 bước 4, §2.4)

### 2.1 Cách làm

Trên **cả 5 instance RQ1 thật** (cùng 5 instance với §1.3/§3 — bao phủ đầy đủ dải tỉ lệ
cắt đã quan sát, gồm cả instance bị cắt mạnh nhất seed=42, 96.81%, là phép thử khắc
nghiệt nhất), 20 bid profile ngẫu nhiên mỗi instance: giải Algorithm B (WDP, CPLEX)
**hai lần** — một lần trên pool đầy đủ, một lần trên pool đã cắt bởi K* — so `Z*`
(full-solve) và `Z*_{-i}` (removal-solve, nền tảng của payment Clarke pivot trong VCG)
cho **từng driver**.

Phiên bản đầu của báo cáo này chỉ chạy 2/5 instance (n=10, seed∈{1,999}) — không bao
phủ điểm cực đoan nhất (seed=42). Đã bổ sung chạy đủ 5/5 instance trước khi coi mục 2
là đóng.

### 2.2 Kết quả

| n | n_drivers | seed | pool đầy đủ | pool sau K* | tỉ lệ cắt | max\|Z*(full)−Z*(pruned)\| | max removal-solve gap (Z*_{-i}) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 5 | 42 | 879 | 28 | **96.81%** | 2.84e-14 | 2.84e-14 |
| 10 | 4 | 1 | 714 | 165 | 76.89% | 2.84e-14 | 2.84e-14 |
| 15 | 5 | 7 | 1561 | 165 | 89.43% | 2.84e-14 | 5.68e-14 |
| 12 | 6 | 123 | 1416 | 208 | 85.31% | 2.84e-14 | 2.84e-14 |
| 10 | 4 | 999 | 510 | 77 | 84.90% | 2.84e-14 | 2.84e-14 |

Mọi chỉ số chênh lệch đều **chỉ là nhiễu floating-point** (~1e-14, dưới ngưỡng
`1e-6` của gate), trên toàn bộ 20 bid profile × 5 instance × (1 full-solve + tối đa
6 removal-solve/driver) mỗi nhánh.

### 2.3 Kết luận mục 2

**PASS tuyệt đối trên cả 5/5 instance**, bao gồm instance bị K* cắt mạnh nhất
(seed=42, 96.81%) — `|Z*(full) − Z*(pruned)| ≤ 1e-6` giữ đúng trên mọi bid profile đã
thử (Add_test.md §2.3 tiêu chí pass), và **`Z*_{-i}` (removal-solve) cũng khớp** —
đây là điều kiện cần trực tiếp để payment Clarke pivot khớp giữa hai nhánh (payment =
`c_ir(b_i) + Z*_{-i} − Z*`; cả hai số hạng đều đã xác nhận khớp nên payment khớp theo).
Cắt 76.89%–96.81% route khỏi pool không làm thay đổi bất kỳ kết quả phân bổ/thanh toán
nào trên dữ liệu RQ1 thật, kể cả ở điểm cắt mạnh nhất đã quan sát.

---

## 3. Đối chiếu activation-rate log cũ (Add_test.md §3, đã chạy trước — nhắc lại)

Đã báo cáo đầy đủ ở `AUDIT_REPORT_2_RQ1_CROSSCHECK.md`. Tóm tắt lại theo đúng format
bảng §3.3 của `Add_test.md`:

| instance | # route active (log cũ) | # route active ⊆ K*? | ngoại lệ |
|---|---:|---|---|
| n=12, n_drivers=5, seed=42 | 6 | Có (6/6) | không |
| n=10, n_drivers=4, seed=1 | 11 | Có (11/11) | không |
| n=15, n_drivers=5, seed=7 | 7 | Có (7/7) | không |
| n=12, n_drivers=6, seed=123 | 6 | Có (6/6) | không |
| n=10, n_drivers=4, seed=999 | 4 | Có (4/4) | không |

**0/5 instance có ngoại lệ — PASS theo đúng tiêu chí §3.2** (0 route active nằm ngoài
K* trên toàn bộ 5 instance × 1000 bid vector).

---

## 4. Tổng kết

Ba việc bắt buộc của `Add_test.md` trước khi đưa thầy xem đều **PASS**:

1. **Independent re-implementation** (grid brute-force, khác cấu trúc tính toán hoàn
   toàn với kink-based): 42/42 driver-pool khớp tuyệt đối trên cả instance tổng hợp lẫn
   instance RQ1 thật.
2. **Môi trường thesis thật + so Z*/Z*_{-i} full vs pruned**: PASS trên **cả 5/5**
   instance RQ1 thật (bao gồm điểm cực đoan nhất, seed=42, cắt 96.81%), chênh lệch chỉ
   là nhiễu floating-point.
3. **Đối chiếu activation-rate log cũ**: 0/5 instance có route active nằm ngoài K*.

Không có instance/seed/bid-profile nào cho kết quả trái với Định lý 4(a) hay Định lý 1
(kink-based ↔ grid-based). Theo đúng `Add_test.md` §6: **`T4_Local_Pruning_Frontier.tex`
sẵn sàng đưa thầy xem**, kèm các bảng ở §1-3 báo cáo này làm phụ lục audit.

Ghi chú (không chặn việc đưa thầy, theo đúng `Add_test.md` §6 dòng cuối): tỉ lệ cắt của
K* trên instance RQ1 thật (76.89%–96.81%) cao hơn nhiều so với tỉ lệ mà kết quả
activation-rate quan sát gợi ý là "thực sự cần" (0.42%–1.54% route từng active qua
1000 bid vector) — đây là hiện tượng thật (K* là điều kiện đủ để an toàn trên toàn dải
Theta, không phải điều kiện khít nhất theo quan sát thực nghiệm hữu hạn), nên nêu rõ
trong phần "ý nghĩa thực tế" khi trình bày, không phải là dấu hiệu K* yếu hay sai.

---

## File & tái tạo

```
T4_audit_scripts/T4_audit/kstar_gridcheck.py             Grid brute-force, doc lap
                                                            voi kstar_rule.py (khong
                                                            import gi tu do)
T4_audit_scripts/T4_audit/test_gridcheck_crossvalidate.py Doi chieu kink vs grid,
                                                            Phan A (instance tong hop,
                                                            Python 3.13)
spec_2a_2b/src/kstar_gridcheck_rq1.py                     Doi chieu kink vs grid,
                                                            Phan B (instance RQ1 that,
                                                            Python 3.7.7 + CPLEX)
spec_2a_2b/src/kstar_zstar_payment_check.py               Z*/Z*_{-i} full vs pruned,
                                                            ca 5 instance RQ1 that
                                                            (INSTANCES da mo rong tu
                                                            2->5, gom ca seed=42 -
                                                            diem cuc doan nhat)
spec_2a_2b/src/kstar_rq1_crosscheck.py                    Doi chieu activation-rate
                                                            log cu (da chay truoc,
                                                            xem AUDIT_REPORT_2_RQ1_CROSSCHECK.md)
spec_2a_2b/results/kstar_gridcheck_rq1.csv                Ket qua Phan B (23 dong)
spec_2a_2b/results/kstar_zstar_payment_check.csv          Ket qua Z*/Z*_{-i}, 5 instance
                                                            x 20 bid profile = 100 dong
spec_2a_2b/results/kstar_rq1_crosscheck.csv               Ket qua doi chieu activation-rate
```

Chạy lại Phần A (Python 3.13, anaconda):
```
"C:\Users\An Khoa\anaconda3\python.exe" T4_audit_scripts\T4_audit\test_gridcheck_crossvalidate.py
```

Chạy lại Phần B + Z*/Z*_{-i} + activation-rate crosscheck (Python 3.7.7, cần CPLEX active):
```
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" spec_2a_2b\src\kstar_gridcheck_rq1.py
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" spec_2a_2b\src\kstar_zstar_payment_check.py
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" spec_2a_2b\src\kstar_rq1_crosscheck.py
```
