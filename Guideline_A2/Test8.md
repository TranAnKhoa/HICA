# Test8 — Component Decomposition có tiết kiệm THỜI GIAN THẬT không, hay chỉ là điều solver đã tự làm?

**Bối cảnh:** Test7 xác nhận component decomposition cho VCG payment **đúng** (Z*_{-i} tính theo
2 cách khớp tuyệt đối ở mọi case, kể cả khi FD rẻ hơn route). Nhưng đây gần như là **hệ quả cấu
trúc hiển nhiên** của một MILP block-diagonal (objective tách rời theo order/driver, ràng buộc
không bắc cầu giữa các component) — không phải phát hiện mới. **Rủi ro lớn hơn:** các MILP
solver hiện đại (CPLEX, Gurobi) có bước **presolve** tự động phát hiện và tách khối độc lập
trong ma trận ràng buộc. Nếu presolve đã làm việc này miễn phí, code `build_conflict_graph` +
giải riêng từng component **không tiết kiệm được gì** so với việc cứ đưa toàn bộ `Z*_{-i}` cho
solver tự lo — và khi đó "component decomposition" không còn là một đóng góp thuật toán, dù nó
đúng.


**Câu hỏi duy nhất Test8 cần trả lời:** tính **TỔNG** thời gian để có đủ n payment (n = số
winner), theo 2 cách:
1. **Naive** — với mỗi winner, đưa **toàn bộ** instance (trừ route của winner đó) cho solver
   giải từ đầu, để presolve tự lo (đúng cách `§9.2` đề cương gốc mô tả cho "naive exact").
2. **Decomposed** — tính component 1 lần, cache giá trị tối ưu từng component; với mỗi winner
   chỉ giải lại **sub-instance giới hạn trong component chứa họ**, cộng cache của phần còn lại.

Nếu (2) nhanh hơn (1) một cách **có hệ thống và tăng theo quy mô phần không liên quan**, đó là
bằng chứng thật cho giá trị của decomposition. Nếu không, T5 cần được nhìn nhận như T4: đúng về
kỹ thuật, không đủ mạnh làm trụ cột novelty riêng.

---

## 0. Yêu cầu môi trường — đọc trước khi code

- Dùng **CPLEX thật**, qua đúng cấu hình đã có sẵn trong `Src_Cplex/config.py` của dự án — không
  cài solver khác, không dùng brute-force (khác Test7, ở đây cần solver thật vì mục đích chính
  là đo hành vi presolve của MILP solver, một brute-force Python không có presolve để so sánh).
- Nếu `Src_Cplex/config.py` không tồn tại hoặc không rõ cách gọi CPLEX trong dự án, dừng lại và
  hỏi trước khi tự ý cài `docplex`/`cplex` qua pip — có thể dự án đã có license/setup riêng.
- Ghi lại **phiên bản CPLEX**, **thông số máy** (CPU, RAM) vào report — thời gian tuyệt đối phụ
  thuộc máy, nhưng **xu hướng tương đối** (naive vs decomposed, tăng theo quy mô) mới là thứ cần
  tin, không phải số giây tuyệt đối.

---

## 1. Sinh instance — tổng hợp, có kiểm soát cấu trúc component

**Không dùng lại Test2-7.** Đây là instance tổng hợp mới, thiết kế để **kiểm soát chính xác** số
lượng và kích thước component — điều brute-force nhỏ của Test7 không cần nhưng Test8 bắt buộc
phải kiểm soát để đo đúng quy luật tăng trưởng.

### 1.1 Tham số sinh — một component "đơn vị"

```python
def make_component(component_id: int, n_drivers: int, n_routes_per_driver: int,
                    n_orders: int, seed: int) -> dict:
    """
    Sinh 1 component ĐỘC LẬP: n_drivers tài xế, mỗi người n_routes_per_driver route,
    mỗi route phủ 1-2 order NGẪU NHIÊN trong đúng n_orders order CỦA COMPONENT NÀY
    (không đụng order của component khác — đảm bảo tách biệt thật, không chỉ "tình cờ"
    không đụng nhau).
    Chi phí route: random dương, cost = base + random offset (đủ đa dạng để tạo cạnh
    tranh thật giữa các driver, không phải cost giống hệt nhau).
    fd_cost mỗi order: random, đặt ~50% cơ hội THẤP hơn route rẻ nhất phủ nó (để P(FD
    thắng) không phải 0 hay 1 tuyệt đối — theo đúng bài học Case C của Test7, muốn FD
    có tham gia thật vào lời giải, không phải luôn thua).
    Trả về: drivers (dict), orders (list), fd_cost (dict) — CHỈ của component này,
    với driver id và order id có prefix component_id để không trùng giữa các component
    khi ghép lại (ví dụ driver "C3_A", order "C3_o1").
    """
```

### 1.2 Ghép nhiều component thành 1 instance lớn

```python
def make_instance(n_components: int, n_drivers_per_component: int = 4,
                   n_routes_per_driver: int = 3, n_orders_per_component: int = 4,
                   seed: int = 0) -> dict:
    """
    Gọi make_component() n_components lần với seed khác nhau (seed + component_id),
    GỘP toàn bộ drivers/orders/fd_cost vào 1 instance duy nhất — không thêm bất kỳ
    route/cạnh nào nối giữa các component (đây là ĐIỂM QUAN TRỌNG: instance được XÂY
    để có đúng n_components component tách biệt, dùng làm oracle kiểm ngược
    build_conflict_graph() có tìm ra đúng số component không — nếu build_conflict_graph
    tìm ra khác n_components, dừng lại, có bug ở bước sinh hoặc bước tìm component
    trước khi đo bất cứ gì về tốc độ).
    """
```

### 1.3 Grid quét — biến độc lập chính là `n_components`, GIỮ NGUYÊN kích thước 1 component

```
n_components: {2, 4, 8, 16, 32}
n_drivers_per_component: 4   (CỐ ĐỊNH — đây là biến kiểm soát chính, xem §2)
n_routes_per_driver: 3       (CỐ ĐỊNH)
n_orders_per_component: 4    (CỐ ĐỊNH)
seed: {0, 1, 2}   (3 lần lặp mỗi cấu hình n_components, lấy median)
```

**Lý do thiết kế này — đọc kỹ, đây là logic cốt lõi của cả Test8:** giữ nguyên kích thước MỘT
component (4 driver, luôn thế), chỉ tăng SỐ LƯỢNG component độc lập không liên quan. Đây là cách
duy nhất tách bạch được 2 khả năng:
- Nếu **naive** cũng nhanh như decomposed dù `n_components` tăng → presolve đã tự lo, quy mô
  "phần không liên quan" không ảnh hưởng gì tới nó → **decomposition thủ công vô giá trị**.
- Nếu **naive** chậm dần khi `n_components` tăng (dù mỗi payment cần tính vẫn chỉ liên quan tới
  ĐÚNG 1 component 4-driver không đổi) trong khi **decomposed** giữ nguyên tốc độ → bằng chứng
  rõ ràng cho giá trị thật của decomposition thủ công.

---

## 2. Hai phương pháp cần cài đặt và đo

### 2.1 Naive (baseline — đúng cách "naive exact" của đề cương gốc §9.2)

```python
def naive_payment_all_winners(instance: dict, alloc_star: dict, Z_star: float,
                                winners: list[str]) -> tuple[dict, float]:
    """
    Với MỖI winner i trong winners:
        - Build model CPLEX cho TOÀN BỘ instance (mọi driver, mọi order, mọi route)
        - Đặt upper bound = 0 cho MỌI biến x_{i,route} của driver i (đúng §9.2:
          "clone model, đặt upper bound mọi x_ir của i về 0")
        - Solve to OPTIMAL
        - Ghi lại Z_{-i} và THỜI GIAN GIẢI (chỉ tính thời gian solver.solve(), KHÔNG
          tính thời gian build model — nếu build model cũng tốn đáng kể, ghi riêng,
          đừng gộp lẫn để tránh đổ lỗi sai cho solver)
    Trả về: dict {winner: (Z_minus_i, solve_time)}, tổng thời gian.
    """
```

### 2.2 Decomposed

```python
def decomposed_payment_all_winners(instance: dict, alloc_star: dict, Z_star: float,
                                     winners: list[str]) -> tuple[dict, float]:
    """
    BƯỚC 1 (làm 1 LẦN DUY NHẤT, không lặp lại cho từng winner):
        - build_conflict_graph(instance['drivers'])  →  graph
        - connected_components(graph)  →  list các component
        - Với MỖI component P: tính Z_P_star = phần đóng góp của P trong Z* (dựa vào
          alloc_star đã có sẵn — KHÔNG giải lại, chỉ cộng cost các route/FD thuộc P
          trong alloc_star)
        - Lưu cache: {component_id: Z_P_star}

    BƯỚC 2, với MỖI winner i:
        - Tìm P chứa i
        - Build model CPLEX CHỈ cho sub-instance của P (driver, order, route CHỈ
          thuộc P — không đụng biến của component khác trong model CPLEX, không chỉ
          "bound=0" như naive, mà THỰC SỰ không tạo biến cho phần ngoài P)
        - Đặt upper bound=0 cho x_{i,route} của i (trong P)
        - Solve to OPTIMAL trên model NHỎ này → Z_P_minus_i
        - Z_{-i} = Z_P_minus_i + Σ (Z_Q_star của mọi component Q ≠ P)  # tra cache, O(1)
        - Ghi lại THỜI GIAN GIẢI (chỉ solver.solve() trên model nhỏ)
    Trả về: dict {winner: (Z_minus_i, solve_time)}, TỔNG thời gian (gồm cả bước 1,
    tính 1 lần, cộng vào tổng — không được "quên" chi phí này khi so sánh).
    """
```

**Chú ý bắt buộc:** bước 1 (tìm component) phải tính **đúng 1 lần** cho toàn bộ batch n winner,
không lặp lại — đây chính là điểm khác biệt cấu trúc so với naive (naive phải build lại model
toàn bộ cho MỖI winner). Thời gian bước 1 vẫn phải cộng vào tổng thời gian decomposed để so sánh
công bằng, nhưng nó chỉ trả 1 lần, không nhân theo n.

### 2.3 Kiểm tra đúng đắn (rẻ, làm trước khi đo tốc độ — kế thừa tinh thần Test7)

```
Với MỌI winner i: |Z_naive[i] - Z_decomposed[i]| phải < 1e-6
```
Nếu sai lệch xuất hiện, DỪNG — đừng đo tốc độ trên một cài đặt có bug đúng đắn.

---

## 3. Thí nghiệm chính — quét `n_components`, đo tổng thời gian

```
for n_components in [2, 4, 8, 16, 32]:
    for seed in [0, 1, 2]:
        instance = make_instance(n_components, seed=seed)
        Solve full instance ONE TIME → Z_star, alloc_star
        winners = { driver id có route trong alloc_star }

        t_naive = naive_payment_all_winners(...)       # tổng thời gian, n winner
        t_decomp = decomposed_payment_all_winners(...)  # tổng thời gian, n winner

        speedup = t_naive / t_decomp
        ghi: n_components, seed, n_winners, t_naive, t_decomp, speedup,
             max |Z_naive - Z_decomposed| (đúng đắn)
```

### 3.1 Đồ thị/bảng bắt buộc trong report

```
Bảng: n_components | median t_naive (s) | median t_decomp (s) | median speedup
   2  |    ?        |     ?              |    ?
   4  |    ?        |     ?              |    ?
   8  |    ?        |     ?              |    ?
  16  |    ?        |     ?              |    ?
  32  |    ?        |     ?              |    ?
```

**Đọc kết quả theo đúng logic §1.3:**
- `t_naive` **tăng** rõ rệt theo `n_components` (dù mỗi payment về bản chất chỉ cần thông tin
  của 1 component 4-driver cố định) → presolve KHÔNG tự tách khối hiệu quả bằng decomposition
  thủ công → **T5 có giá trị thật**.
- `t_naive` **không đổi/gần như phẳng** theo `n_components` → presolve đã tự lo tốt →
  **T5 không tạo thêm giá trị so với việc cứ để solver tự làm** → nên viết vào thesis là "quan
  sát phủ định có giá trị" (giống Test4 Việc 4), không phải trụ cột novelty.
- `speedup` tăng theo `n_components` (bất kể `t_naive` tăng hay phẳng) là tín hiệu mạnh nhất —
  nếu speedup ở `n_components=32` gấp nhiều lần speedup ở `n_components=2`, đó là bằng chứng số
  rõ ràng nhất cho luận điểm `O(Σ|component|)` so với `O(n × full problem)` của đề cương gốc.

---

## 4. Thí nghiệm phụ — bật/tắt presolve của CPLEX

Đây là phép kiểm trực tiếp nhất cho câu hỏi "presolve có tự làm việc này không":

```python
# CPLEX cho phép tắt presolve:
model.parameters.preprocessing.presolve.set(0)   # tắt
model.parameters.preprocessing.presolve.set(1)   # bật (mặc định)
```

Chạy lại **naive** (chỉ naive, không cần decomposed) ở `n_components=32` (ô lớn nhất), với
presolve bật và tắt, so `t_naive` hai trường hợp:

```
presolve ON  : t_naive = ?
presolve OFF : t_naive = ?
```

**Đọc kết quả:**
- Nếu `t_naive` (presolve ON) **gần bằng** `t_decomp` ở cùng `n_components=32` → xác nhận dứt
  khoát: presolve của CPLEX **đã** tách khối hiệu quả, decomposition thủ công không cần thiết.
- Nếu `t_naive` (presolve ON) vẫn **chậm hơn nhiều** `t_decomp` → presolve không tách khối tốt
  bằng thủ công (có thể vì overhead build/return model lớn dù phần chính được tách nhanh, hoặc
  vì presolve không nhận diện được cấu trúc này) → củng cố thêm giá trị của T5.
- `t_naive` (presolve OFF) chỉ để tham khảo mức độ presolve đang giúp ích bao nhiêu nói chung,
  không phải phép so sánh chính.

---

## 5. Ngưỡng đọc kết quả tổng thể — khoá trước khi chạy

| Quan sát | Kết luận |
|---|---|
| `speedup` tại `n_components=32` ≥ 5× **và** tăng theo `n_components` **và** presolve ON không thu hẹp khoảng cách | **T5 có giá trị thuật toán thật** — đủ để viết như một đóng góp: "phân rã giảm tổng chi phí tính n payment từ O(n×full) xuống O(Σ component), xác nhận thực nghiệm bằng MILP solver thật, không phải hệ quả tự nhiên của presolve" |
| `speedup` khiêm tốn (1.5×-3×) hoặc không tăng rõ theo `n_components` | **Giá trị biên** — ghi nhận trung thực, có thể vẫn đáng đưa vào phần thực nghiệm (engineering contribution) nhưng không đủ mạnh làm trụ cột lý thuyết |
| `speedup` ≈ 1× ở mọi `n_components`, hoặc presolve ON làm `t_naive` ≈ `t_decomp` | **T5 không tạo giá trị tính toán vượt quá điều solver tự làm** — viết thẳng vào thesis như một phát hiện phủ định có giá trị (đúng tinh thần Test4 Việc 4), chuyển trọng tâm sang RQ1 hoặc khung thực nghiệm C&OR như đã bàn |

---

## 6. Những điều KHÔNG được làm

1. **Không** dùng brute-force Python để đo tốc độ — mục đích của Test8 là đo hành vi **presolve
   của MILP solver thật**, brute-force không có presolve nên không trả lời được câu hỏi.
2. **Không** để thời gian build model (Python, tạo constraint) lẫn vào thời gian solve — tách
   riêng 2 khoản, báo cáo cả hai, nhưng "speedup" chính phải dựa trên thời gian **solve**, vì đó
   là điều lý thuyết O(Σcomponent) vs O(n×full) nói tới.
3. **Không** dùng instance mà `build_conflict_graph` tìm ra số component KHÁC với
   `n_components` đã sinh — đây là bug ở bước sinh dữ liệu, phải sửa trước khi đo bất cứ gì.
4. **Không** kết luận dựa trên 1 seed — lấy median của ít nhất 3 seed mỗi cấu hình, vì thời gian
   solve MILP có thể dao động.
5. **Không** so sánh thời gian tuyệt đối giữa các máy khác nhau — chỉ tin xu hướng tương đối
   (naive vs decomposed, tăng theo n_components) trong cùng một lần chạy, cùng một máy.

---

## 7. Báo cáo cần trả về

`Test8_report.md`:
1. Thông số máy/CPLEX version.
2. Kiểm tra đúng đắn (§2.3) — pass/fail, trước khi đọc bất kỳ số liệu tốc độ nào.
3. Bảng chính (§3.1) — đầy đủ 5 giá trị `n_components`, median 3 seed.
4. Kết quả bật/tắt presolve (§4).
5. Kết luận theo đúng bảng ngưỡng §5 — viết thẳng, kể cả khi kết quả là "T5 không có giá trị
   tính toán vượt quá điều solver tự làm".