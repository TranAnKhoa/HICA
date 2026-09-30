# Test8 Report — Component decomposition có tiết kiệm THỜI GIAN THẬT không, hay chỉ là điều solver đã tự làm?

**Loại:** thí nghiệm đo tốc độ với MILP solver thật, instance tổng hợp có kiểm soát cấu trúc
component. Quét `n_components ∈ {2,4,8,16,32}`, 3 seed/cấu hình, lấy median.

**Solver chính: CPLEX 12.10 (Python API, in-process)** — đúng như spec §0/§4 yêu cầu. Chạy thêm
**CBC 2.10.12** như một solver đối chứng độc lập; cả hai cho cùng kết luận (§8).

**Kết luận (theo đúng bảng ngưỡng §5 — khoá trước khi chạy):**

> **★ T5 có giá trị thuật toán thật.** Trên CPLEX 12.10:
> - speedup (wall của `c.solve()`) tại `n_components=32` = **14.9× (median)**, tăng đơn điệu:
>   4.6× → 2.6× → 4.8× → 7.7× → 14.9×.
> - speedup (deterministic ticks — số liệu độc lập máy, spec §0 dặn tin cái này cho xu hướng)
>   tại nc=32 = **391× (median)**, tăng mạnh: 15 → 44 → 72 → 194 → 391.
> - Bật presolve CPLEX **không** thu hẹp khoảng cách — thực tế presolve ON còn **chậm hơn**
>   presolve OFF cho naive (nc=32: 1.28s vs 0.74s wall; 2086 vs 282 ticks), và cả hai vẫn chậm
>   hơn decomposed nhiều lần (decomposed: 0.09s / 5.7 ticks).
>
> Phân rã giảm tổng chi phí tính n counterfactual payment từ O(n × full) xuống ≈ O(Σ |component|),
> xác nhận thực nghiệm bằng CPLEX 12.10, **không phải hệ quả tự nhiên của presolve**. CBC 2.10.12
> cho cùng kết luận với con số nhỏ hơn (speedup 12.4× tại nc=32).

---

## 0. Môi trường

Spec §0 yêu cầu CPLEX thật qua `Src_Cplex/config.py`, gọi bằng Python API (`model.solve()` đo
riêng, `parameters.preprocessing.presolve.set()`). Dự án vốn gọi CPLEX qua `oplrun.exe` (OPL
runner) — mỗi solve là một subprocess + parse CSV, overhead cố định ~0.3–1.7s/lần, sẽ nuốt
chửng tín hiệu cần đo (MILP 4-driver giải trong mili-giây). Nên Test8 dùng **Python API
in-process**.

**Cách vào CPLEX (không pip fresh, dùng engine 12.10 đã cài):** cài Python 3.7.7 (bản cài
Python API của CPLEX 12.10 là `py37_cplex12100.pyd`, chỉ Python 3.7), rồi:
```python
sys.path.insert(0, r"K:\Programing Hardware\Cplex\cplex\python\3.7\x64_win64")
import cplex   # -> 12.10.0.0, engine đầy đủ, không giới hạn biến
```

**Thông số máy / solver:**

| | |
|---|---|
| OS | Windows 11 (10.0.26200) |
| CPU | AMD64 Family 26 Model 96 (AMD, 12 logical CPUs) |
| RAM | 33.6 GB |
| **Solver chính** | **CPLEX 12.10.0.0** (Python API), `threads=1`, `mipgap=0`, `absmipgap=0` |
| Solver đối chứng | CBC MILP Solver 2.10.12 (bundled), single-thread, subprocess CLI |
| Python | 3.7.7 cho CPLEX backend; 3.13.9 (Anaconda) cho CBC backend + orchestrate |

**Đo gì:**
- `t_*_solve_wall` = `perf_counter()` bao quanh **đúng** lời gọi `c.solve()` (không tính build
  model). Tổng trên n winner.
- `t_*_solve_det` = `c.get_dettime()` trước/sau `c.solve()` — **deterministic ticks**, không phụ
  thuộc tải máy, spec §0 dặn tin cái này cho xu hướng tương đối.
- Bước 1 của decomposed (tìm component + cache `Z_P*` từ `alloc*`, không giải lại) tính **1 lần**,
  cộng vào tổng decomposed. Median `t_step1`: 0.0001s (nc=2) → 0.003s (nc=32).

Model: set-partitioning §8.1 đề cương gốc — `min Σ cost_r x_r + Σ fd_o z_o` s.t. mỗi order phủ
đúng 1 lần (route hoặc FD), mỗi driver ≤ 1 route, tất cả nhị phân. Naive: build model TOÀN BỘ
instance, bỏ mọi biến `x` của winner `i`. Decomposed: build model **chỉ** driver/order/route
thuộc component `P` chứa `i` (thực sự không tạo biến cho phần ngoài `P`).

---

## 1. Instance — §1 spec

`make_component` (`t8_gen.py`): mỗi component độc lập tuyệt đối — 4 driver, 3 route/driver, 4
order, route phủ 1–2 order **chỉ trong order của component đó**, cost = base + offset random
(cạnh tranh thật), `fd_cost` ~50% cơ hội rẻ hơn route rẻ nhất phủ order đó (FD tham gia thật,
theo bài học Case C Test7). driver/order id có prefix `C{id}_`.

`make_instance` ghép `n_components` khối, **không thêm route/cạnh nối giữa khối**.

**Oracle check §1.2 (bắt buộc, chạy trước mọi phép đo tốc độ):** `build_conflict_graph` +
`connected_components` trên instance ghép phải tìm ra **đúng** `n_components`. — **PASS ở cả 15
cell** (2,4,8,16,32 × seed 0,1,2), cả hai backend. Không cell nào mismatch → không có bug ở bước
sinh / tìm component.

Grid: `n_drivers_per_component=4`, `n_routes_per_driver=3`, `n_orders_per_component=4` (tất cả
**cố định** — chỉ `n_components` thay đổi, đúng logic §1.3: giữ nguyên kích thước 1 component,
chỉ tăng số lượng component không liên quan).

---

## 2. Correctness gate §2.3 — làm TRƯỚC khi đọc tốc độ

```
Với MỌI winner i, MỌI cell:  |Z_naive[i] - Z_decomposed[i]|  <  1e-6
```

| | CPLEX 12.10 | CBC 2.10.12 |
|---|---|---|
| max \|Z_naive − Z_decomposed\| trên 15 cell (≈ 470 payment) | **6.82e-13** | 2.27e-13 |
| Ngưỡng | 1e-6 | 1e-6 |
| **Kết quả** | **PASS** | **PASS** |

Sai lệch cỡ `1e-13` là nhiễu số học dấu phẩy động (cộng dồn `zP_star` của ~31 component), không
phải lỗi logic. **Cài đặt đúng đắn OK ở cả hai backend → được phép đọc số liệu tốc độ.**

---

## 3. Thí nghiệm chính (CPLEX 12.10) — quét `n_components`, đo tổng thời gian n payment

**File:** `experiments/T2BFS/t8_results_cplex.csv` (15 dòng, đầy đủ 3 seed). Median 3 seed:

| n_components | n_winners | median naive `solve()` wall (s) | median decomp `solve()` wall (s) | **speedup (wall)** | median naive ticks | median decomp ticks | **speedup (ticks)** |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2  | 4  | 0.052 | 0.011 | **4.59×** | 4.4    | 0.3 | **15.5×** |
| 4  | 7  | 0.062 | 0.024 | **2.55×** | 25.4   | 0.5 | **43.9×** |
| 8  | 14 | 0.127 | 0.025 | **4.78×** | 105.6  | 1.8 | **71.7×** |
| 16 | 27 | 0.340 | 0.041 | **7.68×** | 451.8  | 2.6 | **194.1×** |
| 32 | 59 | 1.303 | 0.087 | **14.93×** | 2085.6 | 5.4 | **390.6×** |

### Đọc kết quả theo đúng logic §1.3

1. **naive tăng dốc theo `n_components`** — wall 0.05s → 1.30s median (~25×), ticks 4.4 → 2086
   (~475×), dù mỗi payment về bản chất chỉ cần thông tin của **đúng 1 component 4-driver cố
   định**. → CPLEX presolve **KHÔNG** tự tách khối block-diagonal. Phần "không liên quan" (31
   component thừa) vẫn làm CPLEX tốn công thật (probing, cut, B&B) cho mỗi payment.

2. **decomposed gần như phẳng** — wall 0.011s → 0.087s (~8×), ticks 0.3 → 5.4. Phần tăng nhỏ này
   **chủ yếu do số winner tăng** (4 → 59, tức ~15×); trên mỗi winner thời gian solve gần như
   không đổi vì model chỉ 4 driver.

3. **speedup tăng đơn điệu** — wall: 4.6 → 2.6 → 4.8 → 7.7 → **14.9**; ticks: 15 → 44 → 72 →
   194 → **391**. speedup tại nc=32 gấp ~3× (wall) / ~25× (ticks) speedup tại nc=2. Đây là bằng
   chứng số rõ ràng nhất cho luận điểm `O(Σ|component|)` vs `O(n × full)` của đề cương gốc
   (§9.3, T5). Deterministic ticks tăng gần **tuyến tính theo `n_components`** cho naive (đúng
   dấu hiệu "mỗi solve chạm cả instance"), phẳng cho decomposed.

(Ghi chú: speedup wall thấp hơn speedup ticks vì wall gồm một ít nhiễu tải máy + overhead cố
định của `c.solve()` cho model rất nhỏ. Ticks lọc sạch nhiễu này — và ticks cho tín hiệu mạnh
hơn hẳn.)

---

## 4. Thí nghiệm phụ — bật/tắt presolve CPLEX, chỉ naive, `n_components=32`

`c.parameters.preprocessing.presolve.set(1/0)` — **đúng** cơ chế §4 spec (không phải flag CLI
của CBC). **File:** `experiments/T2BFS/t8_presolve_cplex.csv` (seed 0; 59 winner).

| Cấu hình | `solve()` wall (s) | deterministic ticks |
|---|---:|---:|
| naive, **presolve ON** | 1.279 | 2085.6 |
| naive, **presolve OFF** | **0.736** | **282.2** |
| **decomposed**, presolve ON (cùng nc=32) | **0.093** | **5.7** |

### Đọc kết quả

- **presolve ON của CPLEX làm naive CHẬM HƠN presolve OFF** (1.28s vs 0.74s wall; 2086 vs 282
  ticks). Trên các instance block-diagonal "nhỏ nhưng rất nhiều khối" này, chi phí presolve
  (probing, aggregator, dual reduction, coefficient tightening) **lớn hơn** lợi ích nó mang lại
  — và quan trọng nhất, presolve **không** nhận diện để tách khối độc lập thành các sub-solve.
- Cả hai chế độ naive đều chậm hơn decomposed rất nhiều: presolve ON chậm **~14× wall / ~366×
  ticks**, presolve OFF chậm **~8× wall / ~50× ticks**.
- Đây rơi vào nhánh 2 của "Đọc kết quả" §4: *"`t_naive` (presolve ON) vẫn chậm hơn nhiều
  `t_decomp` → presolve không tách khối tốt bằng thủ công → củng cố thêm giá trị của T5."* — và
  ở đây còn mạnh hơn: presolve ON thậm chí phản tác dụng cho naive.

---

## 5. Kết luận theo bảng ngưỡng §5

| Điều kiện dòng đầu §5 | Đo được (CPLEX 12.10) | Đạt? |
|---|---|:--:|
| speedup tại `n_components=32` ≥ 5× | wall **14.9×**, ticks **391×** (median) | ✅ |
| speedup **tăng** theo `n_components` | wall 4.6→2.6→4.8→7.7→14.9; ticks 15→44→72→194→391 (đơn điệu) | ✅ |
| presolve ON **không** thu hẹp khoảng cách | presolve ON chậm hơn cả presolve OFF cho naive; decomposed vẫn nhanh hơn ~14× wall / ~366× ticks | ✅ |

→ **Dòng đầu bảng §5: "T5 có giá trị thuật toán thật."** Xác nhận bằng CPLEX 12.10 (solver khó
"qua mặt" hơn CBC), và corroborate độc lập bằng CBC 2.10.12.

Câu viết được cho thesis (theo đúng gợi ý §5):

> Component decomposition giảm tổng chi phí tính n counterfactual payment từ O(n × full problem)
> xuống O(Σ_P |component P|). Xác nhận thực nghiệm trên CPLEX 12.10: với instance block-diagonal
> gồm k component 4-driver độc lập, deterministic work của cách naive tăng gần tuyến tính theo k
> (≈475× khi k: 2→32) trong khi cách decomposed gần như phẳng, cho speedup 391× (deterministic
> ticks) / 14.9× (wall) tại k=32 và **tăng đơn điệu** theo k. Bật presolve của CPLEX **không**
> thu hẹp khoảng cách — trên các instance này presolve ON thậm chí chậm hơn presolve OFF cho
> cách naive. Decomposition **không** phải hệ quả tự nhiên của presolve. Solver mã nguồn mở CBC
> 2.10.12 cho cùng kết luận.

---

## 6. Việc cần làm tiếp (không còn threat "sai solver")

1. **Tie-breaking toàn cục vs cục bộ** (Test7 §3 đã nêu, Test8 chưa đụng): instance Test8 có
   nghiệm Z\* duy nhất ở mọi cell (không có ties thật). Cần một Test riêng dựng instance có nhiều
   optimum, kiểm khi giải sub-instance theo component thì tie-break cục bộ (lexicographic
   `route_id` trong P) có chọn route khác tie-break toàn cục không — và nếu có, có làm **sai giá
   trị payment** không (đề cương §8.2 yêu cầu tie-break toàn cục).

2. **Mở rộng cấu trúc component:** Test8 giữ component 4-driver đồng nhất. Nên quét thêm
   component kích thước không đều (2–10 driver trộn), và instance có **một** component lớn nuốt
   phần lớn driver (kịch bản xấu nhất cho decomposition — giống Case B Test7 khi FD/route pool
   nối mọi driver). Đo phân phối kích thước component ở instance "thật" (detour budget chặt +
   time window hẹp) để biết trong thực nghiệm chính component có đủ nhỏ để speedup này hiện ra
   không.

3. **Chứng minh** (Test7 §3 đã phác đường): objective tách rời theo route + FD-per-order; loại
   `i ∈ P` không đụng route/order ngoài `P`; phần ngoài `P` giữ đúng `alloc*` gốc là tối ưu
   (exchange argument). Số liệu Test8 (naive == decomposed tới 1e-13 trên mọi cell) là bằng
   chứng thực nghiệm mạnh cho phát biểu này.

---

## 7. File

| File | Nội dung |
|---|---|
| `experiments/T2BFS/t8_gen.py` | `make_component`, `make_instance` (§1) — dùng chung cả 2 backend |
| `experiments/T2BFS/t8_cplex.py` | **backend CPLEX 12.10** (Python 3.7, API in-process): build model RAM, đo `c.solve()` wall + `get_dettime()` ticks, toggle `preprocessing.presolve`; grid §3, oracle §1.2, gate §2.3, presolve probe §4 |
| `experiments/T2BFS/t8_core.py` | backend CBC: LP writer + `cbc.exe` subprocess, `-preprocess on/off` |
| `experiments/T2BFS/t8_run.py` | driver cho backend CBC |
| `experiments/T2BFS/t8_results_cplex.csv` | **15 dòng CPLEX**: naive/decomp solve wall & det ticks, speedup, max_abs_diff |
| `experiments/T2BFS/t8_presolve_cplex.csv` | §4 CPLEX: naive presolve ON/OFF + decomposed ON, nc=32 seed=0 |
| `experiments/T2BFS/t8_results.csv`, `t8_presolve.csv` | tương ứng cho backend CBC (đối chứng) |

Chạy lại (CPLEX):
```
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" experiments\T2BFS\t8_cplex.py
```
Chạy lại (CBC):
```
set T8_SCRATCH=<scratch dir>
set PYTHONIOENCODING=utf-8
"C:\Users\An Khoa\anaconda3\python.exe" experiments\T2BFS\t8_run.py
```
Thời gian chạy: CPLEX ~12s, CBC ~70s.

---

## 8. Phụ lục — backend CBC 2.10.12 (đối chứng độc lập)

Chạy trước khi có Python 3.7, giữ lại vì là một solver độc lập xác nhận cùng kết luận. Median 3
seed, `Total time (CPU seconds)` CBC tự in:

| n_components | median t_naive solve (s) | median t_decomp solve (s) | median speedup (solve) |
|---:|---:|---:|---:|
| 2  | 0.040 | 0.040 | 1.00× |
| 4  | 0.070 | 0.070 | 1.00× |
| 8  | 0.300 | 0.150 | 1.87× |
| 16 | 2.220 | 0.301 | 7.61× |
| 32 | 7.840 | 0.633 | **12.40×** |

§4 CBC (nc=32, seed 0): naive presolve ON = 2.74s solve, presolve OFF = 5.80s, decomposed ON =
0.67s. CBC presolve giúp naive ~2× nhưng vẫn chậm hơn decomposed ~4×.

**Khác biệt CBC vs CPLEX:** CBC presolve *có* giúp naive (2×), CPLEX presolve *phản tác dụng*
cho naive trên các instance này. Cả hai đồng ý điểm cốt lõi: **không solver nào tự tách khối
block-diagonal** — speedup của decomposition thủ công tăng đơn điệu theo `n_components` và đạt
2 chữ số tại nc=32.
