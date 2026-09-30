# Audit report 2 — kstar_rule.py trên instance RQ1 thật, đối chiếu log activation-rate

**Ngày chạy:** 2026-09-22
**Môi trường:** Python 3.7.7 + CPLEX 12.10 (Python API, in-process) — đúng môi trường
production của thesis, không phải Python 3.13/scipy như `AUDIT_REPORT.md`.
**Script:** `spec_2a_2b/src/kstar_rq1_crosscheck.py`
**Lý do viết report này:** `AUDIT_REPORT.md` (report trước) chỉ chạy lại code do chính
tác giả viết (`hica_core.py`) trên instance tổng hợp — không phải kiểm chứng độc lập,
chỉ là kiểm tra tái lập được (xem `AUDIT_SCOPE_NOTE.md`). Report này làm đúng 2 việc còn
thiếu đã nêu ở đó:

1. Chạy `kstar_rule.py` (pure Python, viết cho môi trường thesis — xem docstring của
   chính file: *"so it can run next to the thesis code (Py 3.7 + CPLEX)"*) trực tiếp
   trên **route pool thật của RQ1** (`dp_labeling.build_route_pool`, không phải
   `hica_core.enumerate_pool` tổng hợp), báo cáo tỉ lệ cắt.
2. Đối chiếu với **log activation-rate cũ** đã có
   (`Test_EJOR_direction/Report_ActivationRate.md`, §2 — 5 instance, 1000 bid vector
   Latin Hypercube Sampling/instance, giải WDP thật qua CPLEX): mọi route từng active
   thật trong log đó có nằm trong K* hay không (Định lý 4(a) — an toàn — cấm điều
   ngược lại; nếu có vi phạm là bug ở đâu đó, không phải ở chứng minh).

---

## 1. Phương pháp

- Dùng lại **chính xác 5 instance** đã báo cáo trong `Report_ActivationRate.md` §2
  (cùng `n`, `n_drivers`, `seed` — để route-id và `activated_route_names` khớp 1-1).
- Với mỗi instance: sinh lại route pool thật qua `instance_gen.generate_instance` +
  `dp_labeling.build_route_pool` (Algorithm A thật, không đổi tham số so với log gốc:
  `B_gw=B_od=3`, `tw_width=120`, `tau=30.0`, `spatial_mode="dispersed"`).
- Chạy lại `testC2_activation_rate.run_activation_rate` **nguyên vẹn** (1000 bid vector
  LHS trên `Theta=[18,25]^m`, giải WDP thật qua `rq1_wdp.solve_wdp_for_instance` →
  CPLEX) để lấy `activated_route_names` — route nào từng active thật.
- Gom route theo từng driver, chạy `kstar_rule.local_frontier(routes, q, lo, hi)`
  **cho từng driver riêng** (đúng semantics của K*: rule là **local per-driver**,
  không phải rule toàn cục) → hợp lại `kept_all` = K* của toàn instance.
- **Gate kiểm chứng:** `activated_route_names \ kept_all` phải rỗng. Nếu không rỗng —
  có route từng thực sự tối ưu (WDP CPLEX thật chọn) mà K* lại loại bỏ — đây là vi phạm
  trực tiếp Định lý 4(a) (an toàn), tức là có bug (ở `kstar_rule.py`, hoặc ở cách route
  pool/route-id được map giữa hai script), cần điều tra ngay, không được báo cáo là
  "gần đúng".

---

## 2. Kết quả — 5 instance, 1000 bid vector/instance, đúng seed log gốc

| n | n_drivers | seed | pool_size | K* giữ lại | tỉ lệ cắt | route active (WDP thật) | vi phạm Định lý 4(a) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 5 | 42 | 879 | 28 | 96.81% | 6 | **0** |
| 10 | 4 | 1 | 714 | 165 | 76.89% | 11 | **0** |
| 15 | 5 | 7 | 1561 | 165 | 89.43% | 7 | **0** |
| 12 | 6 | 123 | 1416 | 208 | 85.31% | 6 | **0** |
| 10 | 4 | 999 | 510 | 77 | 84.90% | 4 | **0** |

**`pool_size` và số route active khớp chính xác 100%** với bảng gốc trong
`Report_ActivationRate.md` §2 (879/714/1561/1416/510 và 6/11/7/6/4 tương ứng) — xác
nhận cùng instance, cùng route pool, không có sai lệch dữ liệu đầu vào giữa hai lần
chạy.

**Kết quả gate: PASS tuyệt đối trên cả 5 instance — tổng vi phạm = 0/5.** Mọi route
từng thực sự được WDP CPLEX chọn tối ưu (qua 1000 bid vector LHS mỗi instance) đều nằm
trong K* — không có trường hợp nào K* loại bỏ một route đang/sẽ tối ưu thật. Đây là
kiểm chứng thực nghiệm trực tiếp cho **Định lý 4(a)** trên dữ liệu production thật của
thesis (không phải instance tổng hợp).

---

## 3. Tỉ lệ cắt (prune rate) của K*

K* cắt **76.89% – 96.81%** route khỏi pool, tuỳ instance — trung bình quanh **86.7%**
trên 5 instance. So với activation_rate thật (0.42% – 1.54%, từ log gốc), K* vẫn giữ
lại **nhiều hơn đáng kể** số route thực sự từng active (28 route giữ lại so với 6 route
active ở instance n=12,seed=42, tức K* giữ lại gấp ~4.7 lần số route "cần" theo quan sát
thực nghiệm) — đúng như kỳ vọng lý thuyết: K* là điều kiện **đủ để an toàn** (giữ mọi
route có thể tối ưu với **bất kỳ** bid nào trong dải Theta đã khóa), không phải điều
kiện **khít nhất có thể** theo observed activation trên một tập bid vector hữu hạn (dù
đã sample 1000 vector/instance) — khoảng cách giữa "prune rate của K*" và "1 −
activation_rate quan sát" chính là phần dư địa lý thuyết chưa khai thác được bằng rule
rẻ hơn (đã thử 4 hướng, cả 4 đều REJECTED — xem `Report_ActivationRate.md` §5-8).

---

## 4. Ý nghĩa — khác biệt so với `AUDIT_REPORT.md`

| | `AUDIT_REPORT.md` (report 1) | Report này (report 2) |
|---|---|---|
| Route pool | Tổng hợp (`hica_core.enumerate_pool`, instance ngẫu nhiên riêng) | **Thật** (`dp_labeling.build_route_pool`, instance RQ1 production) |
| Môi trường | Python 3.13 + scipy | **Python 3.7.7 + CPLEX 12.10** (đúng môi trường thesis) |
| Ground truth đối chiếu | Tự giải lại bằng chính `hica_core.solve_wdp` (cùng 1 implementation) | **Log activation-rate đã có từ trước** (`Report_ActivationRate.md`, chạy độc lập trước đó bằng `rq1_wdp`/CPLEX) |
| Loại kiểm chứng | Tái lập được (reproducibility) trên môi trường khác | **Đối chiếu với ground-truth độc lập trên dữ liệu thật** |

Report này giải quyết đúng khoảng trống mà `AUDIT_SCOPE_NOTE.md` §3 mục 2 đã nêu.
Mục 1 của `AUDIT_SCOPE_NOTE.md` (viết lại brute-force/ILP theo cách khác để đối chiếu
chéo thuật toán) **vẫn chưa làm** — report này không thay thế việc đó, chỉ đóng phần
"kiểm trên dữ liệu thật + đối chiếu ground-truth có sẵn".

---

## File & tái tạo

```
spec_2a_2b/src/kstar_rq1_crosscheck.py        Script chinh (buoc 1+2+3 o tren)
spec_2a_2b/results/kstar_rq1_crosscheck.csv   Ket qua day du (5 dong + danh sach
                                                violations neu co)
```

Chạy lại (Python 3.7.7, cần CPLEX active):
```
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" \
    spec_2a_2b\src\kstar_rq1_crosscheck.py
```

Đổi/thêm instance qua biến `INSTANCES` trong file (list of `dict(n=..., n_drivers=..., seed=...)`).
