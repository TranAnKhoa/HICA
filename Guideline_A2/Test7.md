# Test7 — Thăm dò nhanh: Component Decomposition cho VCG Payment

**Đây là bản thăm dò (probe), KHÔNG phải bộ test đầy đủ như Test2-6.1.** Mục tiêu: trả lời
nhanh, rẻ, câu hỏi "ý tưởng này có đáng đầu tư thêm thời gian không" — bằng 3 tình huống dựng
tay, không cần grid, không cần seed, không cần solver phức tạp.

**Bối cảnh (đọc để hiểu, không cần code lại):** Đây là một nhánh nghiên cứu HOÀN TOÀN KHÁC với
mọi Test trước (Test2-6.2) — những test đó kiểm **Algorithm A** (sinh route cho MỘT tài xế).
Test7 kiểm **Algorithm B (chọn ai giao bundle nào) + Algorithm C (tính tiền VCG)** — bài toán
NHIỀU tài xế, NHIỀU bundle, có FD (fixed-capacity, giá công khai, backup). **Không có code nào
từ Test2-6 tái dùng được ở đây** — đây là một lớp bài toán khác của mô hình.

**Câu hỏi trung tâm:** Xây một "đồ thị xung đột" (conflict graph) — mỗi tài xế là 1 node, nối
2 tài xế nếu route của họ (trong route pool đã cho, không phải trong lời giải tối ưu) chia sẻ
ít nhất 1 order chung. Nếu tài xế `i` nằm trong 1 thành phần liên thông (component) `P`, thì khi
tính counterfactual `Z*_{-i}` (giải lại bài toán SAU KHI xoá hết route của `i`), có thể **chỉ
giải lại sub-instance giới hạn trong `P`** (giữ nguyên phần ngoài `P`) mà vẫn ra đúng giá trị,
hay không?

**Nguy cơ chính cần kiểm:** FD có thể phục vụ **bất kỳ** order nào với giá công khai cố định.
Nếu FD "nối" ngầm mọi tài xế lại (dù không hiện diện tường minh trong đồ thị), decomposition có
thể sai. Test7 kiểm trực tiếp điều này bằng số liệu cụ thể.

---

## 0. Dữ liệu dùng ở đây — QUAN TRỌNG, đọc kỹ trước khi code

**KHÔNG dùng generator ngẫu nhiên. KHÔNG dùng Algorithm A để sinh route.** Toàn bộ route/order/
driver/giá FD trong Test7 là **số liệu cho sẵn trực tiếp trong file này** (xem §2), viết thẳng
vào code dưới dạng literal (list/dict Python), không sinh ra bằng thuật toán nào khác.

**Vì sao làm vậy:** câu hỏi của Test7 là về **Algorithm B/C** (cách chọn allocation + tính
tiền), không phải về cách route được sinh ra. Dùng route pool cho sẵn, nhỏ, kiểm soát được từng
con số, giúp cô lập đúng câu hỏi cần trả lời, không lẫn với đúng/sai của Algorithm A.

**Không cần MILP solver (PuLP, OR-Tools, Gurobi...).** Mọi instance ở đây đủ nhỏ (≤4 tài xế,
≤3 route/tài xế, ≤6 order) để **brute-force liệt kê toàn bộ tổ hợp allocation hợp lệ** bằng vòng
lặp Python thuần, chọn tổ hợp có tổng chi phí nhỏ nhất. Làm vậy để giảm rủi ro cài đặt sai solver
external, và vì đây chỉ là bản thăm dò.

### 0.1 Định dạng dữ liệu

```python
# Driver: dict {id: {"routes": [ (route_id, frozenset(orders_covered), cost), ... ]} }
# Order: list các order_id, mỗi order có FD cost riêng: {order_id: fd_cost}
# Allocation hợp lệ: mỗi driver chọn ĐÚNG 1 route trong list của mình HOẶC không chọn gì (idle);
#                    mỗi order phải được phủ ĐÚNG 1 LẦN — hoặc bởi route của đúng 1 driver được
#                    chọn, hoặc bởi FD. Không được phủ 0 lần, không được phủ ≥2 lần.
```

### 0.2 Hàm cần viết (dùng chung cho cả 3 case)

```python
def solve_wdp_bruteforce(drivers: dict, orders: list, fd_cost: dict,
                          excluded_driver: str = None) -> tuple[float, dict]:
    """
    Liệt kê MỌI tổ hợp (driver -> route hoặc idle), lọc tổ hợp nào phủ mỗi order
    ĐÚNG 1 LẦN (qua route hoặc FD), trả về (Z*, allocation tốt nhất).
    Nếu excluded_driver được set: driver đó bị loại hoàn toàn khỏi tổ hợp (mọi route của họ
    coi như không tồn tại) — dùng để tính Z*_{-i}.
    """
    ...

def build_conflict_graph(drivers: dict) -> dict:
    """
    Trả về adjacency: driver i, k nối nhau nếu tồn tại route của i và route của k
    (BẤT KỲ route nào trong route pool, KHÔNG PHẢI chỉ route trong lời giải tối ưu)
    có chung ít nhất 1 order.
    QUAN TRỌNG: FD KHÔNG tham gia đồ thị này — đây chính là giả thuyết cần kiểm ở Case B.
    """
    ...

def connected_components(graph: dict) -> list[set]:
    """BFS/DFS chuẩn, trả về list các component (mỗi component là 1 set driver id)."""
    ...
```

---

## 1. Cách chạy mỗi case — quy trình chung cho cả 3 case

```
1. solve_wdp_bruteforce(drivers, orders, fd_cost)  →  Z*, allocation*
2. build_conflict_graph(drivers)  →  graph
3. connected_components(graph)  →  list các component

4. Với TỪNG driver i xuất hiện trong allocation* (tức i "thắng" 1 route):
   a. Z_full, _ = solve_wdp_bruteforce(drivers, orders, fd_cost, excluded_driver=i)
      # đây là Z*_{-i} tính trên TOÀN BỘ instance — cách làm hiện tại (Algorithm C gốc)

   b. Tìm component P chứa i.
      orders_P = hợp của mọi order xuất hiện trong route của BẤT KỲ driver nào trong P
      drivers_P = P
      Z_sub, _ = solve_wdp_bruteforce(
                     {d: drivers[d] for d in drivers_P}, orders_P, fd_cost,
                     excluded_driver=i)
      # giải LẠI, CHỈ trên sub-instance giới hạn ở component P

      Z_sub_rest = tổng cost tối ưu của các order KHÔNG thuộc orders_P, dùng CHÍNH allocation*
                   gốc cho phần đó (không giải lại — giả thuyết là phần này bất biến)

      Z_decomposed = Z_sub + Z_sub_rest

   c. SO SÁNH:  (Z_full - Z*)  ==  (Z_sub - Z*_P)  ?
      với Z*_P = phần đóng góp của component P trong Z* gốc (tính từ allocation*)

      Ghi lại: match (bool), Z_full, Z_decomposed, chênh lệch tuyệt đối
```

**Tiêu chí đọc kết quả (không cần ngưỡng phức tạp, đây là thăm dò):**
- **Khớp tuyệt đối ở cả 3 case** → tín hiệu tốt, đáng viết Test8.md đầy đủ (gate nghiêm ngặt,
  quét nhiều instance, như Test2-6 đã làm cho Algorithm A).
- **Khớp ở Case A, B nhưng KHÔNG khớp ở Case C (hoặc ngược lại)** → đã tìm ra đúng điều kiện
  ranh giới — đây tự nó là kết quả có giá trị (định dạng Proven/Rejected quen thuộc), viết vào
  report rõ ràng, không cần thăm dò thêm trước khi quyết định hướng tiếp theo.
- **Không khớp ở tất cả** → hướng này không đáng đầu tư thêm, quay lại các phương án khác đã bàn
  (khung thực nghiệm C&OR, hoặc dồn trọng tâm vào RQ1).

---

## 2. Ba case cụ thể — số liệu cho sẵn

### Case A — Baseline: hai "đảo" tách biệt hoàn toàn (kỳ vọng: decomposition ĐÚNG)

```python
orders = ["o1", "o2", "o3", "o4"]
fd_cost = {"o1": 50, "o2": 50, "o3": 50, "o4": 50}   # cao, để FD không cạnh tranh trực tiếp

drivers = {
    "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                      ("rA2", frozenset({"o2"}), 12),
                      ("rA3", frozenset({"o1","o2"}), 18)]},
    "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                      ("rB2", frozenset({"o2"}), 9),
                      ("rB3", frozenset({"o1","o2"}), 19)]},
    "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                      ("rC2", frozenset({"o4"}), 14),
                      ("rC3", frozenset({"o3","o4"}), 20)]},
    "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                      ("rD2", frozenset({"o4"}), 13),
                      ("rD3", frozenset({"o3","o4"}), 21)]},
}
```

`A,B` chỉ đụng `{o1,o2}`; `C,D` chỉ đụng `{o3,o4}` — đồ thị xung đột phải cho ra ĐÚNG 2
component: `{A,B}` và `{C,D}`. Đây là case dễ nhất, mục đích: xác nhận cơ chế đo lường
(§1) cài đặt đúng trước khi thử case khó hơn.

**Kỳ vọng bằng tay (không phải ground truth — code brute-force mới là trọng tài):** `Z*` nên
xoay quanh việc dùng `A=rA3` (18đ, phủ cả o1,o2) và `C=rC3` (20đ, phủ cả o3,o4), `B,D` rảnh.
Khi loại `A`, chỉ phần `{o1,o2}` cần giải lại, phần `{o3,o4}` giữ nguyên `C=rC3`.

### Case B — ★ Stress test chính: FD nối "ảo" hai đảo qua một order chung (kỳ vọng: kiểm decomposition có còn đúng không khi mở rộng route pool để 2 tài xế ở "2 đảo" cùng reach một order)

```python
orders = ["o1", "o2", "o3", "o4", "o5"]
fd_cost = {"o1": 50, "o2": 50, "o3": 50, "o4": 50, "o5": 50}

drivers = {
    "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                      ("rA2", frozenset({"o2"}), 12),
                      ("rA3", frozenset({"o1","o2"}), 18),
                      ("rA4", frozenset({"o1","o5"}), 15)]},   # MỚI: A giờ reach được o5
    "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                      ("rB2", frozenset({"o2"}), 9),
                      ("rB3", frozenset({"o1","o2"}), 19)]},
    "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                      ("rC2", frozenset({"o4"}), 14),
                      ("rC3", frozenset({"o3","o4"}), 20),
                      ("rC4", frozenset({"o3","o5"}), 12)]},   # MỚI: C giờ reach được o5
    "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                      ("rD2", frozenset({"o4"}), 13),
                      ("rD3", frozenset({"o3","o4"}), 21)]},
}
```

Giờ `A` và `C` **cùng reach được `o5`** — dù trong lời giải tối ưu cuối cùng `o5` có thể được
phủ bởi `A`, bởi `C`, hay bởi FD. Theo định nghĩa `build_conflict_graph` (§0.2 — nối 2 driver
nếu CÓ route nào của họ chung order, không cần route đó nằm trong lời giải tối ưu), `A` và `C`
giờ phải **nối trực tiếp** → toàn bộ `{A,B,C,D}` hợp thành **1 component duy nhất**.

**Đây là điểm mấu chốt cần kiểm:** nếu decomposition đúng, khi giải lại `Z*_{-A}` (loại A), cả
`{B, C, D}` phải được coi là 1 khối và giải chung — **không được** tách nhỏ `{C,D}` ra giải riêng
kiểu Case A, vì `o5` là cầu nối thật (A và C cùng cạnh tranh route dùng o5). Code cần **tự phát
hiện** component đã hợp nhất qua `build_conflict_graph`, không hard-code "2 component" như Case
A. Nếu code confirm đúng 1 component duy nhất VÀ decomposition (giải trên component gộp) vẫn
khớp giải toàn bộ → đồ thị xung đột (không cần thêm FD làm cạnh) đã đủ để bắt đúng loại phụ
thuộc này.

### Case C — ★★ Stress test khó nhất: FD là lựa chọn RẺ HƠN route, kiểm xem FD tự nó có "làm giả" một sự phụ thuộc không cần thiết

```python
orders = ["o1", "o2", "o3", "o4"]
fd_cost = {"o1": 50, "o2": 50, "o3": 5, "o4": 50}   # o3: FD RẺ hơn hẳn mọi route driver

drivers = {
    "A": {"routes": [("rA1", frozenset({"o1"}), 10),
                      ("rA2", frozenset({"o2"}), 12),
                      ("rA3", frozenset({"o1","o2"}), 18)]},
    "B": {"routes": [("rB1", frozenset({"o1"}), 11),
                      ("rB2", frozenset({"o2"}), 9),
                      ("rB3", frozenset({"o1","o2"}), 19)]},
    "C": {"routes": [("rC1", frozenset({"o3"}), 8),
                      ("rC2", frozenset({"o4"}), 14),
                      ("rC3", frozenset({"o3","o4"}), 20)]},
    "D": {"routes": [("rD1", frozenset({"o3"}), 9),
                      ("rD2", frozenset({"o4"}), 13),
                      ("rD3", frozenset({"o3","o4"}), 21)]},
}
```

Cấu trúc route giống hệt Case A (2 đảo tách biệt trong route pool — KHÔNG có route nào của
A/B chạm o3/o4 hay ngược lại) — nhưng `o3` giờ có `fd_cost=5`, RẺ hơn mọi route (`rC1=8` là rẻ
nhất trong route). Kỳ vọng: `o3` sẽ được phủ bởi FD trong lời giải tối ưu, không phải bởi
`C` hay `D`.

**Câu hỏi cụ thể:** đồ thị xung đột (§0.2) chỉ nhìn ROUTE POOL, không nhìn `fd_cost` — nên với
Case C, đồ thị xung đột **giống hệt Case A** (2 component tách biệt `{A,B}`, `{C,D}`), dù trong
thực tế `o3` "thoát" khỏi cạnh tranh giữa C/D (đi thẳng vào FD). Kiểm xem: decomposition có vẫn
đúng khi một order trong component "bỏ qua" toàn bộ driver và dùng FD? Đây kiểm đúng lo ngại gốc
của đề cương (`§9.3`: *"FD cost là separable per-order nên có thể vẫn tách được, nhưng phải
chứng minh"*) — Case C là phép chứng minh/bác bỏ trực tiếp bằng số cho đúng câu đó.

---

## 3. Việc cần làm thêm nếu cả 3 case đều khớp — không bắt buộc, chỉ ghi chú

Nếu Test7 cho tín hiệu tốt, đây là 2 điều cần làm ở Test8.md (bộ test đầy đủ, không phải lúc
này):
1. Kiểm tie-breaking: đề cương gốc `§8.2` yêu cầu tie-break **toàn cục** (lexicographic theo
   route_id trên TOÀN BỘ instance). Cần kiểm: khi giải sub-instance theo component, tie-break
   cục bộ có chọn ra route khác với tie-break toàn cục hay không — và nếu có, liệu điều đó có
   làm sai GIÁ TRỊ payment (không chỉ sai việc chọn route nào trong các lựa chọn ngang giá).
2. Mở rộng lên n driver, m order lớn hơn (vẫn brute-force được tới ~8-10 driver, sau đó cần
   MILP solver thật).

---

## 4. Báo cáo cần trả về

`Test7_report.md`:
1. Với mỗi case A/B/C: bảng số liệu đầy đủ (Z*, allocation*, component tìm được, Z*_{-i} tính
   theo 2 cách — toàn bộ vs decomposed — và có khớp hay không).
2. Nếu có case không khớp: mô tả chính xác chỗ lệch, số liệu cụ thể, và thử đưa ra giả thuyết
   tại sao (ví dụ: cách định nghĩa đồ thị xung đột cần sửa thế nào).
3. Kết luận theo đúng 3 nhánh ở cuối §1 — không tự thêm ngưỡng mới.