# T4 — Kết quả chạy Final_t4_Speedup.md (2026-09-24/25)

Chạy tuần tự đủ §1–§4 của runbook, trên 5 instance RQ1 thật (n∈{10,12,15}, seed∈{42,1,7,123,999}),
Python 3.13 (anaconda) cho §1–§3, Python 3.7.7 + CPLEX cho §4. Toàn bộ đạt tiêu chí đạt của
từng mục — không có mục nào fail, không có bug mới lộ ra khi mở rộng patch.

## §2 — Full completion-level bound-violation audit (đã chạy, không chỉ 2 mà cả 5/5 instance)

Script: `New_t4/files/audit_rq1_bounds.py`. Dùng lại chính `dp_fast.py` (bản đo timing), không
viết engine audit riêng — mọi lần rule fire được log lại `(L, j, dK, dW, q_j)`, rồi so với
`K(ρ)-K(ρ∖j)` / `W(ρ)-W(ρ∖j)` tính trực tiếp trên **mọi** completion khả thi thật có prefix `L`
(không phải mẫu).

**B=3** (5/5 instance, 15/15 driver, 9 GW + 6 OD):
```
TOTAL B=3 mode=fixed: firings=78163 completions_checked=114627 violations=0 kstar_changed_drivers=0
```
Cộng thêm bước (0) brute-force: `dp_fast` không rule khớp tuyệt đối tập sequence khả thi liệt kê
bằng brute force, trên mọi driver.

**B=4** (5/5 instance, 15/15 driver):
```
TOTAL B=4 mode=fixed: firings=2261235 completions_checked=5539924 violations=0 kstar_changed_drivers=0
```

**Mutation test** (2 phép, đúng như đã dùng cho bản synthetic gốc), chạy trên seed 42+999, cả B=3 và B=4 —
audit vẫn bắt được lỗi sau khi mở rộng code cho ready_time_d, xác nhận audit script không bị "hỏng
cùng nhịp" với patch:

| mutation | B=3 violations | B=3 kstar_changed | B=4 violations | B=4 kstar_changed |
|---|---:|---:|---:|---:|
| `no_absorb` (bỏ hệ số hấp thụ A) | 4279 / 21406 | 3/4 driver GW | 123237 / 735023 | 3/4 |
| `no_junction` (bỏ hệ số nối) | 3149 / 21969 | 2/4 driver GW | 96112 / 738770 | 4/4 |

Cả hai mutation đều gây vi phạm bound rõ rệt và đổi K* — đúng chức năng "must catch a real bug"
mà §2.2 yêu cầu.

**Kết luận §2:** 0 vi phạm / 5.654.551 completion kiểm (114.627 + 5.539.924) trên toàn bộ 5 instance,
cả B=3 lẫn B=4. Mutation test xác nhận audit vẫn nhạy đúng lỗi sau khi patch. Tiêu chí đạt §2.3: ✅.

## §1 — Timing lặp lại, median + IQR (B=3)

Script: `New_t4/files/repeat_timing.py`. Xen kẽ thứ tự đo `with_rule`/`no_rule` theo từng rep
(rep chẵn: off→on; rep lẻ: on→off), `gc.collect()` trước mỗi lần đo + tắt GC trong lúc đo.

| instance | N | median speedup | IQR | min–max | stdev/median | ext saved |
|---|---:|---:|---|---|---:|---:|
| n=12 seed=42 | 10 | 1.48× | 1.42–1.57 | 1.32–1.63 | 0.073 | 44.2% |
| n=10 seed=1 | 10 | 1.32× | 1.26–1.36 | 1.21–1.50 | 0.067 | 35.5% |
| n=15 seed=7 | 10 | 2.10× | 2.02–2.19 | 1.65–2.23 | 0.084 | 57.3% |
| n=12 seed=123 | 10 | 1.74× | 1.67–1.81 | 1.62–1.90 | 0.051 | 50.1% |
| n=10 seed=999 | 10→20* | 1.41× | 1.36–1.53 | 1.24–1.75 | 0.098 | 39.4% |
| **ALL (tổng thời gian)** | | **1.72×** | 1.69–1.75 | | 0.039 | |

\* seed=999 lần đầu (N=10) có sd/med=0.158 > 0.15 → theo §1.3, chạy lại riêng với N=20, kết quả
sd/med=0.098, đạt ngưỡng.

**Kết luận §1:** cả 5/5 instance đạt `stdev/median < 0.15` (sau khi tăng N cho seed=999 đúng quy
trình §1.3). Con số chốt cho B=3: **median 1.72× [IQR 1.69–1.75]**, thấp hơn con số đo một lần
trước đó (2.10×) — con số cũ nằm ngoài khoảng median±IQR mới, đúng lý do §1 tồn tại: đo một lần
không đáng tin bằng median nhiều lần.

## §3 — B=4 trên RQ1 thật (timing)

Cùng `repeat_timing.py`, N=10, cả 5/5 instance đạt sd/med < 0.15 ngay từ N=10:

| instance | median speedup | IQR | sd/median | ext saved |
|---|---:|---|---:|---:|
| n=12 seed=42 | 2.19× | 2.17–2.22 | 0.105 | 61.0% |
| n=10 seed=1 | 1.70× | 1.67–1.70 | 0.033 | 49.5% |
| n=15 seed=7 | 3.76× | 3.71–3.79 | 0.052 | 76.2% |
| n=12 seed=123 | 2.94× | 2.92–2.94 | 0.029 | 69.7% |
| n=10 seed=999 | 1.98× | 1.97–1.98 | 0.004 | 55.8% |
| **ALL** | **2.94×** | 2.93–2.96 | 0.029 | |

**Kết luận §3:** B=4 cho speedup cao hơn hẳn B=3 (median tổng 2.94× so với 1.72×), đúng dự đoán từ
ceiling gap (§3 lý do runbook: gap 50% ở B=4 so với 45% ở B=3). §2 (bound audit) đã chạy đủ ở B=4
song song (0 vi phạm/5.539.924 completion). Tiêu chí đạt: ✅ cả an toàn lẫn tốc độ.

## §4 — Runtime Algorithm B+C: pool đầy đủ vs pool đã cắt K*

Script: `spec_2a_2b/src/compare_bc_runtime.py`. Mỗi bid profile: 1 full-solve + 1 removal-solve/driver
(VCG), CPLEX 12.10, thứ tự full/K* xen kẽ theo profile, 20 profile/instance. `Z*` và mọi `Z*_{-i}`
được so trực tiếp (assert < 1e-6) trên từng profile.

| n | seed | pool full→K* | cut | median B+C: full | K* | speedup [IQR] | max|ΔZ| |
|---:|---:|---|---:|---:|---:|---|---:|
| 12 | 42 | 879→28 | 96.81% | 0.147s | 0.029s | **5.02× [4.32–5.48]** | 2.8e-14 |
| 10 | 1 | 714→165 | 76.89% | 0.096s | 0.044s | 2.17× [2.03–2.31] | 2.8e-14 |
| 15 | 7 | 1561→165 | 89.43% | 0.168s | 0.059s | 2.87× [2.76–3.01] | 5.7e-14 |
| 12 | 123 | 1416→208 | 85.31% | 0.208s | 0.075s | 2.79× [2.61–2.88] | 2.8e-14 |
| 10 | 999 | 510→77 | 84.90% | 0.088s | 0.025s | 3.63× [3.35–3.75] | 2.8e-14 |
| **ALL** (tổng 100 profile) | | | | 14.69s | 4.85s | **3.03×** | — |

**Kết luận §4:** speedup B+C (median 3.03× tổng thể, đỉnh 5.02× ở instance cut mạnh nhất) **lớn
hơn hẳn** speedup 2× của riêng Algorithm A (label rule). Đúng đúng luận điểm đưa ra ở §4: K* không
chỉ là một định lý đẹp mà giải quyết đúng chỗ tốn thời gian nhất của pipeline thật — chi phí xây
K* gần như miễn phí (17–75ms, tức 12–36% của một lần full-solve) so với lợi ích thu được xuyên suốt
toàn bộ B+C. `Z*` khớp tuyệt đối (chỉ nhiễu số học ~1e-14) trên toàn bộ 100 bid profile × 2 nhánh.

---

## Checklist tổng kết (đối chiếu §5 của Final_t4_Speedup.md)

- [x] §1: median speedup ổn định (stdev/median < 0.15) trên cả 5 instance, B=3 — **1.72× [IQR 1.69–1.75]**
- [x] §2: 0 bound violation trên code mở rộng (0/114.627 ở B=3, 0/5.539.924 ở B=4), cả 2 mutation
      test vẫn bắt lỗi đúng ở cả B=3 và B=4
- [x] §3: B=4 đo xong trên RQ1 thật, cùng chuẩn an toàn như B=3 — **2.94× [IQR 2.93–2.96]**, mọi
      instance sd/med < 0.15 ngay N=10
- [x] §4: đo runtime B+C full vs K* — **3.03× tổng thể, đỉnh 5.02×**, lớn hơn 2× của Algorithm A,
      xác nhận đây là con số nên làm nổi bật nhất trong phần thực nghiệm
- [x] Mọi số liệu cuối cùng ghi ở trên là **median + IQR** (trừ §4 dùng median+IQR per-instance,
      tổng thể dùng tổng thời gian — cả hai đều không phải số một lần chạy đơn lẻ)
- [x] Không có mục nào fail — không cần dừng lại sửa gì thêm trước khi ghi số vào thesis

## Ghi chú cho thesis

1. **Con số cần dùng cho Algorithm A (label rule), B=3:** median **1.72×** [IQR 1.69–1.75], không
   phải 2.10× (số đo một lần trước đó, đã bị vượt qua bởi phép đo lặp lại chuẩn hơn — nằm ngoài
   khoảng tin cậy mới).
2. **Con số cho Algorithm A, B=4:** median **2.94×** [IQR 2.93–2.96] — cao hơn B=3, đúng dự đoán
   ceiling gap.
3. **Con số nổi bật nhất, nên dẫn đầu phần thực nghiệm:** speedup Algorithm B+C (WDP + VCG) khi
   dùng pool đã cắt K* so với pool đầy đủ — **median 3.03× tổng thể, đỉnh 5.02×** ở instance bị cắt
   mạnh nhất (96.81%). Đây là bằng chứng K* giải quyết đúng nút thắt cổ chai thật của pipeline,
   không chỉ một kết quả lý thuyết cô lập.
4. Toàn bộ instance dùng để đo là 5 instance RQ1 thật đã liệt kê ở §0 của runbook gốc — không dùng
   instance tổng hợp cho bất kỳ con số nào ở trên.

## File tạo ra trong lần chạy này

```
New_t4/files/audit_rq1_bounds.py          Script audit đầy đủ + mutation test (§2)
New_t4/files/repeat_timing.py             Script timing lặp lại, median+IQR (§1, §3)
New_t4/files/timing_medians_B3*.json      Kết quả thô §1
New_t4/files/timing_medians_B4.json       Kết quả thô §3
spec_2a_2b/src/compare_bc_runtime.py      Script so runtime B+C full vs K* (§4)
spec_2a_2b/results/compare_bc_runtime.csv Kết quả thô §4
```

Các file patch cũ (`hica_core.py`, `dp_rules.py`, `dp_fast.py`, `dp_fast_rq1.py`) đã được sửa thêm
trong lần này (thêm cờ `MUT`/`LEGACY` trong `dp_fast.py` để chạy được mutation test và so sánh
legacy-vs-fixed mà không cần hai bản file riêng; thêm tham số `B` cho `build_hica_instance` trong
`dp_fast_rq1.py` để dùng chung cho §3).
