# T4 — Runbook kiểm chứng speedup label rule trên dữ liệu RQ1 thật

**Mục đích của file này:** trước khi con số "2.10× speedup, 56.8% extension saved"
được ghi cố định vào thesis, chạy lại ba phép kiểm dưới đây để biến nó từ "đo một lần"
thành "kết quả đáng tin". Không cần hiểu lại toàn bộ lý thuyết Part I/Part II — chỉ cần
làm theo thứ tự, script nào không có sẵn thì viết theo khung đã cho.

**Không làm gì khác trước khi ba mục ở đây xong.** Đây là điều kiện để con số hiện tại
được coi là "chốt" thay vì "sơ bộ" (xem `T4_Handoff.md` §4, mục 5–8).

---

## 0. Trước khi bắt đầu — xác định lại vị trí file

Theo handoff, các script này nằm rải trên máy cá nhân của bạn (không nằm trong
container của phiên chat), dưới hai thư mục:

- `New_t4/files/` — chứa `dp_fast_rq1.py` (script bridge đo RQ1), file kết quả CSV, và
  bản đã patch của `hica_core.py` / `dp_rules.py` / `dp_fast.py` với 3 fix mô tả ở
  §2.6 của handoff (SERVICE_MIN=5.0, delivery có ready_d=ready_p, t1=+∞ cho GW/OD).
- `spec_2a_2b/src/` — pipeline sản xuất thật của thesis: `dp_labeling.py`,
  `rq1_wdp.py`, `rq1_cost_gen.py`, `t2_gen.py`, `t6_dp.py`, `instance_gen.py`,
  `t8_cplex.py`.

Mở `New_t4/files/dp_fast_rq1.py` trước — mọi việc dưới đây thao tác trên script này
và các file nó import.

```bash
cd New_t4/files/
ls -la
python3 --version   # phải khớp môi trường đã dùng để đo lần trước
```

Ghi lại đúng 5 instance RQ1 đã dùng để đo K*/speedup, để mọi phép đo dưới đây chạy
trên cùng tập:

| instance | n | seed | ghi chú |
|---|---:|---:|---|
| 1 | 12 | 42 | cut ratio K* = 96.81% (aggressive nhất) |
| 2 | 10 | 1 | cut ratio K* = 76.89% |
| 3 | 15 | 7 | cut ratio K* = 89.43% |
| 4 | 12 | 123 | cut ratio K* = 85.31% — driver `od2` có pool rỗng, đã xác nhận không phải bug |
| 5 | 10 | 999 | cut ratio K* = 84.90% — instance dùng để cross-check pool size = 254 routes cho gw0 |

---

## 1. Lặp lại timing, lấy trung vị (ưu tiên 1)

**Vì sao:** thời gian tuyệt đối đang ở mức 0.1–0.9 giây/driver — đủ nhỏ để nhiễu hệ
thống (GC, scheduler, CPU throttling) ảnh hưởng tới tỉ lệ speedup đo được. Hướng kết
quả gần như chắc (10/10 cặp driver-instance GW đều speedup >1×), nhưng **con số chính
xác** (2.10× hay 1.8× hay 2.4×) cần trung vị nhiều lần chạy, không phải một lần.

### 1.1 Cách chạy

Nếu `dp_fast_rq1.py` chưa có sẵn vòng lặp lấy trung vị, bọc nó như sau (script wrapper,
không sửa logic đo bên trong):

```python
# repeat_timing.py — đặt cùng thư mục với dp_fast_rq1.py
import subprocess, json, statistics, sys

N_REPEATS = 10
INSTANCES = [
    (12, 42), (10, 1), (15, 7), (12, 123), (10, 999)
]

results = {}
for n, seed in INSTANCES:
    runs = []
    for rep in range(N_REPEATS):
        # gọi lại đúng entrypoint đo timing hiện có của dp_fast_rq1.py
        # thay bằng cách gọi thật của bạn nếu khác (import function trực tiếp
        # thường ổn định hơn subprocess vì tránh chi phí khởi động interpreter)
        out = subprocess.run(
            [sys.executable, "dp_fast_rq1.py", "--n", str(n), "--seed", str(seed),
             "--mode", "timing_only"],
            capture_output=True, text=True
        )
        # parse dòng cuối stdout thành JSON {"wall_clock_with_rule": ..., "wall_clock_no_rule": ...}
        metrics = json.loads(out.stdout.strip().splitlines()[-1])
        runs.append(metrics)

    with_rule = [r["wall_clock_with_rule"] for r in runs]
    no_rule   = [r["wall_clock_no_rule"] for r in runs]
    speedups  = [b / a for a, b in zip(with_rule, no_rule)]

    results[f"n{n}_seed{seed}"] = {
        "median_with_rule": statistics.median(with_rule),
        "median_no_rule": statistics.median(no_rule),
        "median_speedup": statistics.median(speedups),
        "min_speedup": min(speedups),
        "max_speedup": max(speedups),
        "stdev_speedup": statistics.stdev(speedups) if len(speedups) > 1 else 0.0,
        "n_repeats": N_REPEATS,
    }

for k, v in results.items():
    print(k, v)

json.dump(results, open("timing_medians.json", "w"), indent=2)
```

Nếu `dp_fast_rq1.py` đo bằng cách import trực tiếp thay vì CLI, thay `subprocess.run`
bằng gọi hàm timing trực tiếp trong vòng lặp `for rep in range(N_REPEATS)` — cách này
tốt hơn vì loại bỏ overhead khởi động Python mỗi lần.

### 1.2 Việc phải làm thêm khi chạy

- Chạy trên máy **rảnh** (không có tác vụ nền nặng), cùng một máy cho cả `with_rule`
  và `no_rule` trong cùng một lần lặp (không interleave hai máy khác nhau).
- Xen kẽ thứ tự đo `with_rule` / `no_rule` trong mỗi rep (không đo hết 10 lần
  `with_rule` rồi mới đo `no_rule`) để tránh nhiễu hệ thống lệch có hướng (thermal
  throttling tăng dần theo thời gian, ví dụ).
- Ghi cả **wall-clock** lẫn **số label extension** (đếm được, không phụ thuộc máy) —
  nếu speedup đo bằng extension count ổn định hơn wall-clock, dùng extension count làm
  số liệu chính trong thesis, wall-clock chỉ minh họa.

### 1.3 Tiêu chí đạt

- `stdev_speedup / median_speedup` < 0.15 cho mỗi instance → đủ ổn định để báo cáo.
- Nếu instance nào vượt ngưỡng này, tăng N_REPEATS lên 20 cho riêng instance đó trước
  khi kết luận.
- Ghi **median + IQR** vào thesis, không ghi số của một lần chạy đơn lẻ (đúng chuẩn
  đã đặt ở §12.5 của đề cương chính — "luôn báo median + IQR").

---

## 2. Full completion-level bound-violation audit trên code đã sửa (ưu tiên 2)

**Vì sao:** code hiện tại đã sửa 3 chỗ để khớp dữ liệu RQ1 thật (SERVICE_MIN=5.0,
delivery có ready time, t1=+∞). Phép kiểm lại duy nhất đã chạy sau khi sửa là
`kstar_equal=True` — đây là kiểm tra **ở tầng pool cuối cùng**, yếu hơn hẳn phép audit
đầy đủ đã bắt được 2 lỗi mutation test trước đó (thiếu absorption term → 1339 vi phạm;
thiếu junction term → 4173 vi phạm). Quan trọng: cả hai lỗi mutation đó đều **không**
bị phát hiện bằng lấy mẫu WDP-value ngẫu nhiên — chỉ audit ở đúng tầng bất biến (bound
per-completion, hoặc K* equality) mới bắt được. `kstar_equal` chỉ là nửa sau, chưa đủ.

### 2.1 Script tham chiếu

Dùng lại cấu trúc của `test_dp_rules.py` (bản gốc, đã audit Part II trên dữ liệu
synthetic n=8) nhưng trỏ vào patched `dp_fast_rq1.py` thay vì generator synthetic.

```python
# audit_extended_code.py
"""
Kiểm từng completion thật (không phải mẫu) so với bound lý thuyết
beta(L, T) = kappa*delta_D + theta_min * max(0, delta - A) / 60
trên code đã mở rộng cho delivery opening time.
"""
import itertools
from patched.dp_rules import enumerate_completions, compute_bound, true_saving
from patched.instance_gen import load_rq1_instance

INSTANCES = [(12, 42), (10, 1), (15, 7), (12, 123), (10, 999)]

violations = []
total_checked = 0

for n, seed in INSTANCES:
    inst = load_rq1_instance(n=n, seed=seed)
    for driver in inst.gw_drivers:          # chỉ GW — rule chỉ fire trên GW
        for label, T, completion in enumerate_completions(driver, inst, B=3):
            bound = compute_bound(label, T, inst)      # beta(L,T)
            actual = true_saving(label, T, completion, inst)
            total_checked += 1
            if actual < bound - 1e-9:       # bound phải là cận DƯỚI của true saving
                violations.append((driver.id, label.id, tuple(T), bound, actual))

print(f"Checked {total_checked} completions across {len(INSTANCES)} instances")
print(f"Violations: {len(violations)}")
for v in violations[:20]:
    print(v)

assert len(violations) == 0, "SAFETY BROKEN on extended code — do not report speedup yet"
```

### 2.2 Việc phải làm thêm

- Chạy trên **ít nhất 2 instance** trong 5 instance RQ1 trước (khuyến nghị: seed=42 vì
  cut ratio cao nhất, và seed=999 vì đã dùng làm cross-check pool size) — nếu cả hai
  pass, mở rộng ra 5/5.
- Chạy lại đúng hai mutation test đã dùng cho bản synthetic (xóa absorption term, xóa
  junction term) **trên code đã mở rộng này**, xác nhận audit vẫn bắt được vi phạm.
  Nếu mutation test không còn bắt được lỗi sau khi mở rộng code, nghĩa là bản thân audit
  script đã hỏng theo cùng sự thay đổi — phải sửa trước khi tin kết quả pass ở §2.1.
- Log số completion checked phải **khớp cỡ dữ liệu thật** (ví dụ vài nghìn tới vài chục
  nghìn completion mỗi instance n=10–15, B=3) — nếu số quá nhỏ, có thể enumerate_completions
  đang bị giới hạn nhầm phạm vi.

### 2.3 Tiêu chí đạt

- 0 violation trên toàn bộ completion enumerate được, trên cả 5 instance.
- Mutation test (2 phép) vẫn bắt được vi phạm sau khi áp lên code mở rộng.
- Nếu có violation: **dừng lại, không báo cáo speedup**, quay lại sửa `stop_e` /
  `future_stops` / `absorption` cho đúng với delivery window mới, rồi audit lại từ đầu.

---

## 3. Đo B=4 trên dữ liệu RQ1 thật (ưu tiên 3)

**Vì sao:** ceiling lý thuyết (khoảng cách chưa khai thác giữa rule hiện tại và giới
hạn tuyệt đối của Theorem 4(c)) là 45-50% đã đóng ở B=3, nhưng B=4 rộng hơn — theo
bảng synthetic cũ, ceiling gap ở B=4 lớn hơn (50% so với 45%), tức rule có thể còn
nhiều dư địa hơn ở B=4. Hiện tại B=4 mới chỉ đo trên dữ liệu synthetic, chưa đo trên
RQ1 thật.

### 3.1 Cách chạy

Về cơ bản là chạy lại đúng §1 và §2 nhưng đổi `B=3` → `B=4` trong lời gọi route
generation. Không cần script mới — chỉ cần xác nhận `dp_fast_rq1.py` nhận tham số B và
đường dẫn `t2_gen.py` / `instance_gen.py` không hard-code B=3 ở đâu đó.

```bash
grep -rn "B *= *3\|bundle_cap" New_t4/files/ spec_2a_2b/src/instance_gen.py spec_2a_2b/src/t2_gen.py
```

Nếu tìm thấy B bị hard-code, sửa thành tham số truyền vào trước khi chạy.

### 3.2 Việc phải làm thêm

- Chạy đúng 5 instance RQ1 cũ, chỉ đổi B → 4 — **không** đổi seed hay n, để so sánh
  trực tiếp được với kết quả B=3 đã có.
- Ghi lại: pool size trước/sau K*, cut ratio, activation rate (nếu còn thời gian đo lại
  activation rate ở B=4 — không bắt buộc, nhưng nếu có sẽ củng cố thêm luận điểm ceiling
  gap lớn hơn).
- Chạy §1 (timing median) và §2 (safety audit) **lại từ đầu** cho B=4 — không tái sử
  dụng kết quả B=3, vì pool lớn hơn có thể đổi hành vi rule theo cách chưa kiểm.

### 3.3 Tiêu chí đạt

- Cùng chuẩn với B=3: 0 violation, stdev/median speedup < 0.15.
- Nếu speedup ở B=4 thật sự lớn hơn B=3 (như dự đoán từ ceiling gap), đây là bằng chứng
  tốt để đưa hẳn vào phần thực nghiệm chính, không chỉ audit note.

---

## 4. (Khuyến nghị thêm, không bắt buộc) Đo runtime B+C trên pool full vs pool K*

Ba mục trên chỉ đo tốc độ của **Algorithm A**. Nhưng A chỉ là một phần pipeline — nếu
B (WDP) và C (removal-solve VCG payment) chiếm phần lớn thời gian tổng, speedup 2× của
A gần như không ảnh hưởng runtime toàn hệ thống. Trong khi đó K* đã chứng minh cắt
77–97% pool — cắt pool cỡ đó rất có thể làm B/C nhanh hơn **nhiều** so với 2× của A.

```python
# compare_bc_runtime.py
import time
from patched.rq1_wdp import solve_wdp_for_instance
from patched.kstar_rule import prune_to_kstar

for n, seed in INSTANCES:
    inst = load_rq1_instance(n=n, seed=seed)
    pool_full = build_route_pool(inst)          # không prune
    pool_kstar = prune_to_kstar(pool_full, inst)

    t0 = time.perf_counter()
    Z_full, payments_full = solve_wdp_and_payments(inst, pool_full)
    t_full = time.perf_counter() - t0

    t0 = time.perf_counter()
    Z_kstar, payments_kstar = solve_wdp_and_payments(inst, pool_kstar)
    t_kstar = time.perf_counter() - t0

    assert abs(Z_full - Z_kstar) < 1e-6
    print(f"n={n} seed={seed}: full={t_full:.3f}s kstar={t_kstar:.3f}s "
          f"speedup={t_full/t_kstar:.2f}x")
```

Nếu con số này lớn hơn hẳn 2×, nó xứng đáng là **kết quả thực nghiệm chính** của cả
Part I — quan trọng hơn con số 2.10× của label rule, vì nó cho thấy K* không chỉ là
định lý đẹp mà còn giải quyết đúng chỗ tốn thời gian nhất trong pipeline thật (B, C),
chứ không chỉ A.

---

## 5. Checklist tổng kết trước khi ghi số vào thesis

- [x] §1: median speedup ổn định (stdev/median < 0.15) trên cả 5 instance, B=3 —
      **1.72× [IQR 1.69–1.75]** (seed=999 cần N=20 mới đạt ngưỡng, đúng quy trình §1.3)
- [x] §2: 0 bound violation trên code mở rộng (0/114.627 ở B=3, 0/5.539.924 ở B=4),
      cả 2 mutation test vẫn bắt lỗi đúng ở cả B=3 và B=4
- [x] §3: B=4 đo xong trên RQ1 thật, cùng chuẩn an toàn như B=3 —
      **2.94× [IQR 2.93–2.96]**
- [x] §4 (khuyến nghị): đo runtime B+C full vs K* — **median 3.03×, đỉnh 5.02×**,
      đây là con số nên làm nổi bật nhất trong phần thực nghiệm (lớn hơn hẳn 2× của
      riêng Algorithm A)
- [x] Mọi số liệu cuối cùng ghi vào thesis là **median + IQR**, không phải số của một
      lần chạy đơn lẻ
- [x] Không mục nào fail — không cần sửa/audit lại

**Kết quả đầy đủ, số liệu, script và file tái tạo: xem `Final_t4_Speedup_RESULTS.md`
(chạy 2026-09-24/25).**